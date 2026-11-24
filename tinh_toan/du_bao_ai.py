# -*- coding: utf-8 -*-
"""
DỰ BÁO NHU CẦU THEO MÙA VỤ BẰNG HỌC MÁY (đặc tả V1.1, mục 2.1).

Ba cách dự báo được so sánh NGOÀI MẪU (học 70 % đầu, kiểm tra 30 % cuối) bằng WAPE:
  - "ai"         : Gradient Boosting trên đặc trưng lịch (thứ, tháng, ngày trong năm, số ngày tới từng sự kiện mùa vụ);
  - "mua_vu"     : mô hình thống kê mùa vụ trong loi.py (chỉ có cho gói bánh kẹo: Tết, Trung thu);
  - "trung_binh" : trung bình đơn giản.
App dùng cách có WAPE thấp nhất và nói rõ đã dùng cách nào; AI không tốt hơn thì quay về cách đơn giản hơn.

Phương sai sai số: Var = a·d̂ + b·d̂², hệ số a, b ước lượng từ sai số ngoài mẫu, sàn bằng phương sai Poisson.
Dưới loi.NGAY_DAY_DU ngày đo: dự báo khởi động (ước lượng của người bán trộn số đo). Dưới 240 ngày: chưa đủ để
tách ngoài mẫu nên không so sánh được, dùng mô hình mùa vụ (hoặc trung bình với ngành khác).
"""
import numpy as np
import pandas as pd

from . import loi

NGAY_SO_SANH = 240            # cần ít nhất chừng này ngày để tách 70/30 và so sánh ngoài mẫu
TEN_MO_HINH = {"ai": "AI (Gradient Boosting)", "mua_vu": "Thống kê mùa vụ", "trung_binh": "Trung bình đơn giản",
               "khoi_dong": "Ước lượng ban đầu + số đo"}


def dac_trung(ngay, su_kien):
    """Ma trận đặc trưng lịch cho các ngày `ngay`. su_kien = {tên: DatetimeIndex các ngày sự kiện}."""
    ngay = pd.DatetimeIndex(ngay)
    cot = [ngay.dayofweek.values, ngay.month.values, ngay.dayofyear.values]
    for ds in su_kien.values():
        cot.append(np.clip(loi._ngay_gan_nhat(ngay, pd.DatetimeIndex(ds)), -90, 45))
    return np.column_stack(cot).astype(float)


def _hoc_ai(y, su_kien):
    """Học Gradient Boosting trên các ngày có số đo. Trả về hàm dự báo f(ngày) -> mảng."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    v = y.values.astype(float)
    co = np.isfinite(v)
    mo_hinh = HistGradientBoostingRegressor(loss="poisson", max_iter=200, learning_rate=0.06, max_depth=4,
                                            min_samples_leaf=10, random_state=0)
    mo_hinh.fit(dac_trung(y.index[co], su_kien), v[co])
    # Cây quyết định không ngoại suy được mức bán đang đổi: nhân tỷ lệ (thực / dự báo) của 56 ngày đo gần nhất
    cuoi = np.where(co)[0][-56:]
    p_cuoi = mo_hinh.predict(dac_trung(y.index[cuoi], su_kien))
    ty_le = float(np.clip(v[cuoi].sum() / max(p_cuoi.sum(), 1e-9), 0.5, 2.0))
    return lambda ngay: np.clip(mo_hinh.predict(dac_trung(ngay, su_kien)) * ty_le, 0.05, None)


def _he_so_phuong_sai(thuc, p):
    m = np.isfinite(thuc) & np.isfinite(p)
    if m.sum() < 10:
        return np.array([1.0, 0.0])
    return np.clip(np.linalg.lstsq(np.c_[p[m], p[m] ** 2], (thuc[m] - p[m]) ** 2, rcond=None)[0], 0, None)


def du_bao(y, so_ngay, su_kien=None, uoc_luong=None, co_mua_vu=True, dung_ai=True):
    """Dự báo `so_ngay` ngày kế tiếp của chuỗi y (index ngày liên tục, NaN = thiếu dữ liệu / hết hàng).
    su_kien: lịch sự kiện của gói ngành (mặc định Tết + Trung thu). co_mua_vu=False với ngành không phải bánh kẹo.
    Trả về {"ngay", "d_hat", "var", "meta"}; meta["mo_hinh"] cho biết cách đã dùng, meta["wape"] là bảng so sánh."""
    su_kien = su_kien or {"Tết": loi.TET, "Trung thu": loi.TRUNG_THU}
    v, n = y.values.astype(float), len(y)
    so_ngay_do = int(np.isfinite(v).sum())
    ngay = pd.date_range(y.index[-1] + pd.Timedelta(days=1), periods=so_ngay)
    if so_ngay_do < loi.NGAY_DAY_DU:
        r = loi.du_bao_khoi_dong(y, so_ngay, uoc_luong)
        r["meta"].update(mo_hinh="khoi_dong", wape={}, ghi_chu="Chưa đủ 60 ngày số bán: dùng ước lượng ban đầu trộn với số đã đo.")
        return {k: r[k] for k in ("ngay", "d_hat", "var", "meta")}

    meta = {"so_ngay_du_lieu": n, "so_ngay_do": so_ngay_do, "khoi_dong": False, "ngoai_mau": n >= NGAY_SO_SANH, "wape": {}}
    tb = lambda x: loi._tb(x[-56:]) if np.isfinite(x[-56:]).any() else loi._tb(x)      # noqa: E731
    ung_vien = {"trung_binh": lambda yy: (lambda ng: np.full(len(ng), max(tb(yy.values.astype(float)), 0.05)))}
    if co_mua_vu:
        ung_vien["mua_vu"] = lambda yy: (lambda ng, mh=loi.hoc_mua_vu(yy): loi.du_bao_tu_mo_hinh(mh, ng))
    if dung_ai:
        ung_vien["ai"] = lambda yy: _hoc_ai(yy, su_kien)

    if n >= NGAY_SO_SANH:
        cut = int(n * 0.7)
        thuc, du_doan = v[cut:], {}
        for ten, hoc in ung_vien.items():
            try:
                du_doan[ten] = hoc(y.iloc[:cut])(y.index[cut:])
                meta["wape"][ten] = loi._wape(thuc, du_doan[ten])
            except Exception:                                    # noqa: BLE001  (ví dụ máy không có scikit-learn)
                pass
        hop_le = {k: w for k, w in meta["wape"].items() if np.isfinite(w)}
        chon = min(hop_le, key=hop_le.get) if hop_le else "trung_binh"
        coef = _he_so_phuong_sai(thuc, du_doan.get(chon, np.full(len(thuc), np.nan)))
        if chon == "ai":
            meta["ghi_chu"] = "AI có sai số thấp nhất trên phần dữ liệu kiểm tra nên được dùng."
        elif "ai" in hop_le:
            meta["ghi_chu"] = f"AI không tốt hơn cách '{TEN_MO_HINH[chon]}' trên phần dữ liệu kiểm tra, nên app dùng cách đó."
        else:
            meta["ghi_chu"] = f"Dùng cách '{TEN_MO_HINH[chon]}'."
    else:
        chon = "mua_vu" if co_mua_vu else "trung_binh"
        coef = _he_so_phuong_sai(v, ung_vien[chon](y)(y.index))
        meta["ghi_chu"] = (f"Mới có {n} ngày dữ liệu (dưới {NGAY_SO_SANH}): chưa đủ để kiểm tra AI ngoài mẫu, "
                           f"dùng cách '{TEN_MO_HINH[chon]}'.")
    d_hat = np.asarray(ung_vien[chon](y)(ngay), float)
    var = np.maximum(coef[0] * d_hat + coef[1] * d_hat ** 2, d_hat)          # sàn Poisson
    meta.update(mo_hinh=chon, he_so_phuong_sai=[float(coef[0]), float(coef[1])])
    return {"ngay": ngay, "d_hat": d_hat, "var": var, "meta": meta}
