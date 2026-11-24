# -*- coding: utf-8 -*-
"""
TẦNG DỊCH VỤ: nối dữ liệu đã lưu (qua PhamVi) với lõi tính toán trong tinh_toan/.

Không import FastAPI ở đây (để kiểm thử được bằng hàm thường). Lỗi do người dùng nhập sai ném `LoiNhap`
với câu tiếng Việt; tầng API đổi thành mã 400.

Các nhóm hàm:
  1. Tiện ích ngày, đổi kiểu sang JSON
  2. Danh mục: chủ hàng, nhà cung cấp, mặt hàng
  3. Sổ bán hàng (ghi cuối ngày, tải file) và lô hàng tồn kho
  4. Tính: dự báo → khuyến nghị cho từng mặt hàng, tổng quan kho, chi tiết một mặt hàng
  5. Đơn hàng: gộp theo nhà cung cấp → đặt → nhà cung cấp xác nhận qua liên kết → nhận hàng (đo lead time)
  6. Quản trị: danh sách khách, gia hạn gói
"""
import hashlib
import io
import json
import os
import secrets

import numpy as np
import pandas as pd

from tinh_toan import du_bao_ai
from tinh_toan import khuyen_nghi as kn
from tinh_toan import loi
from tinh_toan import nganh

SO_NGAY_DU_BAO = 150
DON_DANG_VE = ("da_dat", "ncc_xac_nhan")
TEN_TRANG_THAI_DON = {"nhap": "Đơn nháp", "da_dat": "Đã đặt, chờ nhà cung cấp xác nhận", "ncc_xac_nhan": "Nhà cung cấp đã xác nhận",
                      "da_ve": "Hàng đã về", "huy": "Đã huỷ"}
GOI_DICH_VU = {"dung_thu": "Dùng thử", "co_ban": "Cơ bản", "nang_cao": "Nâng cao", "doanh_nghiep": "Doanh nghiệp"}


class LoiNhap(ValueError):
    """Người dùng nhập sai hoặc thao tác không hợp lệ: thông báo hiển thị nguyên văn."""


# ----------------------------------------------------------------------------
# 1. TIỆN ÍCH
# ----------------------------------------------------------------------------
def hom_nay():
    """Ngày hôm nay của máy chủ; đặt SMARTSTOCK_HOM_NAY=YYYY-MM-DD để cố định khi kiểm thử."""
    return pd.Timestamp(os.environ.get("SMARTSTOCK_HOM_NAY") or pd.Timestamp.today()).normalize()


def chuoi_ngay(d):
    return pd.Timestamp(d).strftime("%Y-%m-%d")


def doc_ngay(s, ten="Ngày"):
    try:
        return pd.Timestamp(str(s)).normalize()
    except Exception:                                        # noqa: BLE001
        raise LoiNhap(f"{ten} '{s}' không hợp lệ. Dùng dạng năm-tháng-ngày, ví dụ 2026-11-24.") from None


def ngay_vn(d):
    return pd.Timestamp(d).strftime("%d/%m")


def sach(o):
    """Đổi kiểu numpy / pandas sang kiểu JSON ghi được."""
    if isinstance(o, dict):
        return {k: sach(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, np.ndarray, pd.Index)):
        return [sach(v) for v in o]
    if isinstance(o, (pd.Timestamp, np.datetime64)):
        return chuoi_ngay(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return float(o) if np.isfinite(o) else None
    return o


def _ma(tien_to):
    return f"{tien_to}-{secrets.token_hex(4)}"


def _so(v, ten, thap=None, cao=None, nguyen=False, trong=False):
    if v in (None, "") and trong:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise LoiNhap(f"{ten} phải là một con số.") from None
    if not np.isfinite(x) or (thap is not None and x < thap) or (cao is not None and x > cao):
        khoang = f"từ {thap:g} đến {cao:g}" if thap is not None and cao is not None else f"không nhỏ hơn {thap:g}"
        raise LoiNhap(f"{ten} phải {khoang}.")
    return int(round(x)) if nguyen else x


# ----------------------------------------------------------------------------
# 2. DANH MỤC
# ----------------------------------------------------------------------------
def goi_nganh(pv):
    khach = pv.kho.tim_mot("khach", ma_kho=pv.ma_kho) or {}
    return khach.get("nganh") or nganh.MAC_DINH


def luu_chu_hang(pv, d, ma=None):
    ten = str(d.get("ten") or "").strip()
    if not ten:
        raise LoiNhap("Cần nhập tên chủ hàng.")
    gt = {"ten": ten, "dien_thoai": str(d.get("dien_thoai") or "").strip()}
    if ma:
        if not pv.sua("chu_hang", {"ma": ma}, gt):
            raise LoiNhap("Không tìm thấy chủ hàng.")
        return ma
    ma = _ma("ch")
    pv.them("chu_hang", dict(gt, ma=ma))
    return ma


def xoa_chu_hang(pv, ma):
    if pv.tim("mat_hang", ma_chu_hang=ma):
        raise LoiNhap("Chủ hàng này còn mặt hàng trong kho. Hãy chuyển hoặc xoá các mặt hàng đó trước.")
    pv.xoa("chu_hang", ma=ma)


def luu_nha_cung_cap(pv, d, ma=None):
    ten = str(d.get("ten") or "").strip()
    if not ten:
        raise LoiNhap("Cần nhập tên nhà cung cấp.")
    gt = {"ten": ten, "lien_he": str(d.get("lien_he") or "").strip(),
          "lead_time_ngay": _so(d.get("lead_time_ngay"), "Số ngày hàng về", 0.5, 60),
          "do_lech_lead_time": _so(d.get("do_lech_lead_time", 0.5), "Độ lệch số ngày hàng về", 0, 30)}
    if ma:
        if not pv.sua("nha_cung_cap", {"ma": ma}, gt):
            raise LoiNhap("Không tìm thấy nhà cung cấp.")
        return ma
    ma = _ma("ncc")
    pv.them("nha_cung_cap", dict(gt, ma=ma))
    return ma


def xoa_nha_cung_cap(pv, ma):
    if pv.tim("mat_hang", ma_ncc=ma):
        raise LoiNhap("Còn mặt hàng nhập từ nhà cung cấp này. Hãy đổi nhà cung cấp cho các mặt hàng đó trước.")
    pv.xoa("nha_cung_cap", ma=ma)


def _mat_hang_hop_le(pv, d, cu=None):
    md = nganh.lay(goi_nganh(pv))["mac_dinh"]
    lay = lambda k, mac=None: d.get(k, (cu or {}).get(k, mac))                # noqa: E731
    ten = str(lay("ten") or "").strip()
    if not ten:
        raise LoiNhap("Cần nhập tên mặt hàng.")
    if not pv.tim_mot("chu_hang", ma=lay("ma_chu_hang")):
        raise LoiNhap("Cần chọn chủ hàng (hàng này của ai).")
    if not pv.tim_mot("nha_cung_cap", ma=lay("ma_ncc")):
        raise LoiNhap("Cần chọn nhà cung cấp.")
    gt = {"ten": ten, "don_vi": str(lay("don_vi") or "cái").strip(), "ma_chu_hang": lay("ma_chu_hang"), "ma_ncc": lay("ma_ncc"),
          "gia_von": _so(lay("gia_von"), "Giá vốn", 1),
          "gia_ban": _so(lay("gia_ban", 0), "Giá bán", 0),
          "han_dung_ngay": _so(lay("han_dung_ngay", md["han_dung_ngay"]), "Hạn dùng (ngày)", 1, 3650, nguyen=True),
          "chi_phi_dat_hang": _so(lay("chi_phi_dat_hang", md["chi_phi_dat_hang"]), "Chi phí mỗi lần đặt hàng", 1),
          "ty_le_giu_hang_nam": _so(lay("ty_le_giu_hang_nam", md["ty_le_giu_hang_nam"]), "Tỷ lệ giữ hàng mỗi năm", 0.01, 2),
          "muc_phuc_vu": _so(lay("muc_phuc_vu", md["muc_phuc_vu"]), "Mức yên tâm không hết hàng", 0.5, 0.999),
          "quy_cach": _so(lay("quy_cach", 1), "Quy cách đóng gói", 1, 10000, nguyen=True),
          "alpha": _so(lay("alpha", kn.ALPHA_MAC_DINH), "Hệ số hạn dùng", *kn.ALPHA_KHOANG),
          "ngan_sach": _so(lay("ngan_sach"), "Ngân sách mỗi lần đặt", 0, trong=True) or None,
          "giu_cho": _so(lay("giu_cho", 0), "Hàng khách đã đặt giữ", 0)}
    ul = lay("uoc_luong")
    if ul:
        it, thuong, nhieu = (_so(x, "Ước lượng bán mỗi ngày", 0) for x in ul)
        if not it <= thuong <= nhieu:
            raise LoiNhap("Ước lượng bán mỗi ngày phải theo thứ tự: ít nhất ≤ thường ≤ nhiều nhất.")
        gt["uoc_luong"] = [it, thuong, nhieu]
    else:
        gt["uoc_luong"] = None
    return gt


def luu_mat_hang(pv, d, ma=None):
    if ma:
        cu = pv.tim_mot("mat_hang", ma=ma)
        if not cu:
            raise LoiNhap("Không tìm thấy mặt hàng.")
        pv.sua("mat_hang", {"ma": ma}, dict(_mat_hang_hop_le(pv, d, cu), can_bo_sung=False))
        return ma
    gt = _mat_hang_hop_le(pv, d)
    if any(loi._bo_dau(m["ten"]) == loi._bo_dau(gt["ten"]) for m in pv.tim("mat_hang")):
        raise LoiNhap(f"Đã có mặt hàng tên '{gt['ten']}'.")
    ma = _ma("mh")
    pv.them("mat_hang", dict(gt, ma=ma, can_bo_sung=bool(d.get("can_bo_sung"))))
    return ma


def xoa_mat_hang(pv, ma):
    pv.xoa("mat_hang", ma=ma)
    pv.xoa("doanh_so", ma_mat_hang=ma)
    pv.xoa("lo_hang", ma_mat_hang=ma)


# ----------------------------------------------------------------------------
# 3. SỔ BÁN HÀNG VÀ LÔ HÀNG
# ----------------------------------------------------------------------------
def _so_ban_doc(pv, ma):
    return pv.tim_mot("doanh_so", ma_mat_hang=ma) or {"ma_mat_hang": ma, "chuoi": {}, "het_hang": []}


def _so_ban_ghi(pv, doc):
    gt = {"chuoi": doc["chuoi"], "het_hang": sorted(set(doc["het_hang"]))}
    if not pv.sua("doanh_so", {"ma_mat_hang": doc["ma_mat_hang"]}, gt):
        pv.them("doanh_so", dict(gt, ma_mat_hang=doc["ma_mat_hang"]))


def chuoi_ban(pv, mh, hn):
    """Chuỗi bán theo ngày tới HẾT HÔM QUA (NaN = chưa ghi hoặc hôm đó hết hàng). None nếu chưa có gì để dự báo."""
    doc = _so_ban_doc(pv, mh["ma"])
    qua = hn - pd.Timedelta(days=1)
    ngay = sorted(k for k in doc["chuoi"] if pd.Timestamp(k) <= qua)
    if not ngay:
        return pd.Series([np.nan], index=pd.DatetimeIndex([qua]), name=mh["ten"]) if mh.get("uoc_luong") else None
    idx = pd.date_range(ngay[0], qua)
    y = pd.Series([doc["chuoi"].get(chuoi_ngay(d), np.nan) for d in idx], index=idx, name=mh["ten"], dtype=float)
    y.loc[[d for d in pd.to_datetime(doc["het_hang"]) if d in y.index]] = np.nan      # hết hàng: lượng bán < nhu cầu thật
    return y


def lo_cua(pv, ma_mat_hang=None):
    lo = pv.tim("lo_hang", **({"ma_mat_hang": ma_mat_hang} if ma_mat_hang else {}))
    return sorted((x for x in lo if x["so_luong"] > 0), key=lambda x: x["han_su_dung"])


def them_lo(pv, d, hn):
    mh = pv.tim_mot("mat_hang", ma=d.get("ma_mat_hang"))
    if not mh:
        raise LoiNhap("Cần chọn mặt hàng.")
    sl = _so(d.get("so_luong"), "Số lượng", 0.001)
    han = doc_ngay(d["han_su_dung"], "Hạn sử dụng") if d.get("han_su_dung") else hn + pd.Timedelta(days=int(mh["han_dung_ngay"]))
    lo = {"ma": _ma("lo"), "ma_mat_hang": mh["ma"], "so_luong": sl, "han_su_dung": chuoi_ngay(han), "ngay_nhap": chuoi_ngay(hn)}
    pv.them("lo_hang", lo)
    return lo["ma"]


def sua_lo(pv, ma, so_luong):
    sl = _so(so_luong, "Số lượng", 0)
    if sl <= 0:
        pv.xoa("lo_hang", ma=ma)
    elif not pv.sua("lo_hang", {"ma": ma}, {"so_luong": sl}):
        raise LoiNhap("Không tìm thấy lô hàng.")


def _tru_ton(pv, ma_mat_hang, luong):
    """Trừ (luong > 0) hoặc trả lại (luong < 0) tồn kho, lấy lô gần hết hạn trước (FEFO)."""
    lo = lo_cua(pv, ma_mat_hang)
    if luong < 0 and lo:
        pv.sua("lo_hang", {"ma": lo[0]["ma"]}, {"so_luong": lo[0]["so_luong"] - luong})
        return
    for b in lo:
        if luong <= 1e-9:
            break
        lay = min(b["so_luong"], luong)
        luong -= lay
        sua_lo(pv, b["ma"], b["so_luong"] - lay)


def so_ban_ngay(pv, ngay):
    ngay = chuoi_ngay(doc_ngay(ngay))
    ra = []
    for mh in sorted(pv.tim("mat_hang"), key=lambda m: m["ten"]):
        doc = _so_ban_doc(pv, mh["ma"])
        ra.append({"ma": mh["ma"], "ten": mh["ten"], "don_vi": mh["don_vi"], "so_luong": doc["chuoi"].get(ngay),
                   "het_hang": ngay in doc["het_hang"], "ton_kho": sum(b["so_luong"] for b in lo_cua(pv, mh["ma"]))})
    return ra


def ghi_so_ban(pv, ngay, dong, hn, tru_ton=True):
    """Ghi số bán cuối ngày. dong = [{ma, so_luong, het_hang}]. Ghi lại cùng ngày thì chỉ trừ tồn phần chênh lệch."""
    ngay = doc_ngay(ngay)
    if ngay > hn:
        raise LoiNhap("Không ghi số bán cho ngày chưa tới.")
    k, n = chuoi_ngay(ngay), 0
    for d in dong:
        mh = pv.tim_mot("mat_hang", ma=d.get("ma"))
        if not mh or d.get("so_luong") in (None, ""):
            continue
        sl = _so(d["so_luong"], f"Số bán của '{mh['ten']}'", 0)
        doc = _so_ban_doc(pv, mh["ma"])
        chenh = sl - float(doc["chuoi"].get(k) or 0)
        doc["chuoi"][k] = sl
        doc["het_hang"] = [x for x in doc["het_hang"] if x != k] + ([k] if d.get("het_hang") else [])
        _so_ban_ghi(pv, doc)
        if tru_ton and abs(chenh) > 1e-9:
            _tru_ton(pv, mh["ma"], chenh)
        n += 1
    return n


class _Tep(io.BytesIO):
    name = ""


def tai_len_doanh_so(pv, ten_file, du_lieu):
    """Nhập file CSV / Excel doanh số (dạng dài hoặc rộng). Mặt hàng chưa có thì tạo mới với tham số mặc định của ngành."""
    f = _Tep(du_lieu)
    f.name = ten_file or "doanh_so.csv"
    try:
        rong, canh_bao = loi.chuan_hoa_ban_hang(loi.doc_file(f))
    except ValueError as e:
        raise LoiNhap(str(e)) from None
    except Exception as e:                                   # noqa: BLE001
        raise LoiNhap(f"Không đọc được file: {e}") from None
    da_co = {loi._bo_dau(m["ten"]): m for m in pv.tim("mat_hang")}
    moi, cap_nhat = [], []
    for ten in rong.columns:
        mh = da_co.get(loi._bo_dau(ten))
        if not mh:
            ch, ncc = pv.tim("chu_hang"), pv.tim("nha_cung_cap")
            if not ch or not ncc:
                raise LoiNhap("Cần có ít nhất một chủ hàng và một nhà cung cấp trước khi tải file doanh số.")
            ma = luu_mat_hang(pv, {"ten": ten, "ma_chu_hang": ch[0]["ma"], "ma_ncc": ncc[0]["ma"], "gia_von": 10000,
                                   "gia_ban": 15000, "can_bo_sung": True})
            mh = pv.tim_mot("mat_hang", ma=ma)
            moi.append(ten)
        else:
            cap_nhat.append(mh["ten"])
        doc = _so_ban_doc(pv, mh["ma"])
        doc["chuoi"].update({chuoi_ngay(d): float(v) for d, v in rong[ten].items() if np.isfinite(v)})
        _so_ban_ghi(pv, doc)
    if moi:
        canh_bao.append(f"Đã tạo {len(moi)} mặt hàng mới với giá và hạn dùng MẶC ĐỊNH: {moi}. "
                        "Hãy vào Nhập liệu › Mặt hàng để sửa lại cho đúng, nếu không khuyến nghị sẽ sai.")
    return {"so_ngay": len(rong), "tu_ngay": rong.index[0], "den_ngay": rong.index[-1], "mat_hang_moi": moi,
            "mat_hang_cap_nhat": cap_nhat, "canh_bao": canh_bao}


# ----------------------------------------------------------------------------
# 4. TÍNH: DỰ BÁO → KHUYẾN NGHỊ
# ----------------------------------------------------------------------------
_NHO_DU_BAO = {}


def _du_bao(pv, mh, hn, ma_nganh):
    """Dự báo SO_NGAY_DU_BAO ngày kể từ hôm nay; nhớ kết quả theo nội dung sổ bán (học lại chỉ khi sổ đổi)."""
    y = chuoi_ban(pv, mh, hn)
    if y is None:
        return None, None
    khoa = hashlib.md5(json.dumps([pv.ma_kho, mh["ma"], chuoi_ngay(hn), ma_nganh, mh.get("uoc_luong"),
                                   [None if np.isnan(v) else v for v in y.values], chuoi_ngay(y.index[0])]).encode()).hexdigest()
    if khoa not in _NHO_DU_BAO:
        if len(_NHO_DU_BAO) > 500:
            _NHO_DU_BAO.clear()
        goi = nganh.lay(ma_nganh)
        try:
            _NHO_DU_BAO[khoa] = du_bao_ai.du_bao(y, SO_NGAY_DU_BAO, su_kien=goi["su_kien"], uoc_luong=mh.get("uoc_luong"),
                                                 co_mua_vu=ma_nganh == "banh_keo")
        except ValueError:
            _NHO_DU_BAO[khoa] = None
    return _NHO_DU_BAO[khoa], y


def lead_time_ncc(pv, ncc):
    """Số ngày hàng về của nhà cung cấp, ước lượng từ các đơn đã về (ít lần giao thì co về giá trị mặc định)."""
    cac_lan = [(pd.Timestamp(d["ngay_ve"]) - pd.Timestamp(d["ngay_dat"])).days
               for d in pv.tim("don_hang", ma_ncc=ncc["ma"], trang_thai="da_ve") if d.get("ngay_ve") and d.get("ngay_dat")]
    return kn.uoc_luong_lead_time(cac_lan, ncc["lead_time_ngay"], ncc["do_lech_lead_time"])


def _boi_canh(pv, hn):
    """Đọc một lần những thứ dùng chung khi tính nhiều mặt hàng."""
    ncc = {n["ma"]: n for n in pv.tim("nha_cung_cap")}
    dang_ve = {}
    for trang_thai in DON_DANG_VE:
        for don in pv.tim("don_hang", trang_thai=trang_thai):
            k = max(0, (pd.Timestamp(don["ngay_giao_du_kien"]) - hn).days)
            for d in don["dong"]:
                dang_ve.setdefault(d["ma_mat_hang"], []).append((k, float(d["so_luong"])))
    lo = {}
    for b in lo_cua(pv):
        lo.setdefault(b["ma_mat_hang"], []).append(b)
    return {"hn": hn, "nganh": goi_nganh(pv), "ncc": ncc, "lt": {m: lead_time_ncc(pv, n) for m, n in ncc.items()},
            "chu_hang": {c["ma"]: c for c in pv.tim("chu_hang")}, "dang_ve": dang_ve, "lo": lo}


def _tham_so(mh, lt):
    return {"lead_time_ngay": lt["tb"], "do_lech_lead_time": lt["do_lech"], "muc_phuc_vu": mh["muc_phuc_vu"],
            "ty_le_giu_hang_nam": mh["ty_le_giu_hang_nam"], "gia_von": mh["gia_von"], "chi_phi_dat_hang": mh["chi_phi_dat_hang"],
            "han_dung_ngay": mh["han_dung_ngay"], "quy_cach": mh.get("quy_cach", 1)}


def _so_gon(x):
    return f"{x:,.0f}".replace(",", ".")


def _loi_noi(mh, kq, bc):
    """Ba câu trả lời cho màn hình đầu: tình trạng, việc nên làm, lý do; kèm rủi ro nói bằng lời."""
    dv, hn, L = mh["don_vi"], bc["hn"], kq["L"]
    du = kq["so_ngay_du_ban"]
    con = f"Còn đủ bán khoảng {du} ngày" if du is not None else f"Còn đủ bán hơn {SO_NGAY_DU_BAO} ngày"
    if kq["ton_kho"] <= 0:
        tinh_trang = "Đã hết hàng" + (f", {_so_gon(kq['hang_dang_ve'])} {dv} đang về" if kq["hang_dang_ve"] else "")
    elif kq["mau"] == "do":
        tinh_trang = f"Chỉ còn {_so_gon(kq['ton_kho'])} {dv}, dưới mức hàng dự phòng ({_so_gon(kq['ss'])} {dv})"
    else:
        tinh_trang = con + (", đã tới mức báo đặt hàng" if kq["mau"] == "cam" else "")
    if kq["nen_dat"]:
        muon = kq["ngay_dat_muon_nhat"]
        khi = "đặt ngay hôm nay" if muon is None or muon <= hn else f"đặt chậm nhất ngày {ngay_vn(muon)}"
        viec = f"Nên đặt {_so_gon(kq['so_luong_dat'])} {dv}, {khi}"
    elif kq["so_ngay_toi_muc_bao"] is not None:
        viec = f"Chưa cần đặt. Dự kiến cần đặt khoảng ngày {ngay_vn(hn + pd.Timedelta(days=kq['so_ngay_toi_muc_bao']))}"
    else:
        viec = f"Chưa cần đặt trong {SO_NGAY_DU_BAO} ngày tới"
    sk = nganh.su_kien_sap_toi(bc["nganh"], hn, 60)
    a, b = kq["ban_7_ngay"]
    ly_do = (f"{sk[0][0]} còn {sk[0][1]} ngày nữa" if sk else f"Đang bán khoảng {_so_gon(a)}–{_so_gon(b)} {dv} mỗi ngày")
    ly_do += f", hàng về mất khoảng {L} ngày"
    if kq["nen_dat"] and kq["rang_buoc"] == "han_dung":
        ly_do += "; lượng đặt được giới hạn để bán kịp trước hạn dùng"
    elif kq["nen_dat"] and kq["rang_buoc"] == "ngan_sach":
        ly_do += "; lượng đặt được giới hạn theo ngân sách bạn nhập"
    k = int(round(kq["xac_suat_het_hang"] * 20))
    rui_ro = ("Nếu hôm nay không đặt thêm: gần như không lo hết hàng trước khi kịp nhập đợt mới." if k == 0 else
              "Nếu hôm nay không đặt thêm: gần như chắc chắn sẽ hết hàng trước khi hàng mới về." if k >= 19 else
              f"Nếu hôm nay không đặt thêm: trong 20 lần thì khoảng {k} lần sẽ hết hàng trước khi hàng mới về.")
    het_han = (f"Khoảng {_so_gon(kq['luong_co_the_het_han'])} {dv} có thể hết hạn trước khi bán kịp, tương đương "
               f"{_so_gon(kq['tien_co_the_mat'])} đ." if kq["luong_co_the_het_han"] >= 0.5 else None)
    du_bao = f"Dự báo bán khoảng {_so_gon(a)}–{_so_gon(b)} {dv} mỗi ngày trong 7 ngày tới. Dự báo có thể sai."
    return {"cau_tinh_trang": tinh_trang, "cau_viec": viec, "cau_ly_do": ly_do, "cau_rui_ro": rui_ro, "cau_het_han": het_han,
            "cau_du_bao": du_bao}


def tinh_mat_hang(pv, mh, bc, csl=None):
    """Khuyến nghị của một mặt hàng. Trả về (kết quả gọn cho giao diện, dữ liệu thô để vẽ chi tiết)."""
    hn = bc["hn"]
    ncc = bc["ncc"].get(mh["ma_ncc"]) or {"ma": None, "ten": "(chưa chọn)", "lead_time_ngay": 2, "do_lech_lead_time": 0.7}
    lt = bc["lt"].get(mh["ma_ncc"]) or kn.uoc_luong_lead_time([], 2, 0.7)
    lo = bc["lo"].get(mh["ma"], [])
    goc = {"ma": mh["ma"], "ten": mh["ten"], "don_vi": mh["don_vi"], "ma_chu_hang": mh["ma_chu_hang"],
           "ten_chu_hang": (bc["chu_hang"].get(mh["ma_chu_hang"]) or {}).get("ten", ""), "ma_ncc": mh["ma_ncc"],
           "ten_ncc": ncc["ten"], "gia_von": mh["gia_von"], "can_bo_sung": bool(mh.get("can_bo_sung")),
           "ton_kho": sum(b["so_luong"] for b in lo)}
    db, y = _du_bao(pv, mh, hn, bc["nganh"])
    if db is None:
        return dict(goc, co_du_lieu=False, mau="xam", nen_dat=False, cau_tinh_trang="Chưa có số bán nên chưa tính được",
                    cau_viec="Hãy ghi số bán cuối ngày, tải file doanh số, hoặc nhập ước lượng bán mỗi ngày",
                    cau_ly_do="Cần ít nhất một ước lượng ban đầu để bắt đầu"), None
    tp = _tham_so(mh, lt)
    lo_tinh = [(b["so_luong"], (pd.Timestamp(b["han_su_dung"]) - hn).days) for b in lo]
    qua_han = sum(sl for sl, con in lo_tinh if con <= 0)
    kq = kn.tinh(db["d_hat"], db["var"], tp, lo_tinh, bc["dang_ve"].get(mh["ma"], ()), mh.get("giu_cho", 0), csl,
                 mh.get("ngan_sach"), mh.get("alpha", kn.ALPHA_MAC_DINH), hn)
    ton = kq.pop("ton_du_phong")
    chua_ghi = int((hn - pd.Timedelta(days=1) - y.last_valid_index()).days) if y.last_valid_index() is not None else None
    sap_het_han = [b for b in lo if 0 < (pd.Timestamp(b["han_su_dung"]) - hn).days <= max(3, 0.2 * mh["han_dung_ngay"])]
    canh_bao = []
    if qua_han > 0:
        canh_bao.append(f"Có {_so_gon(qua_han)} {mh['don_vi']} đã quá hạn dùng trong sổ tồn kho: hãy kiểm tra và loại ra.")
    if chua_ghi and chua_ghi >= 2:
        canh_bao.append(f"Đã {chua_ghi} ngày chưa ghi số bán: tồn kho trong sổ có thể không còn đúng.")
    if mh.get("can_bo_sung"):
        canh_bao.append("Giá vốn và hạn dùng đang là số mặc định: hãy sửa lại cho đúng.")
    ra = dict(goc, co_du_lieu=True, **kq, **_loi_noi(mh, kq, bc), canh_bao=canh_bao, mo_hinh=db["meta"]["mo_hinh"],
              ten_mo_hinh=du_bao_ai.TEN_MO_HINH[db["meta"]["mo_hinh"]], so_ngay_chua_ghi=chua_ghi,
              gia_tri_ton=goc["ton_kho"] * mh["gia_von"], so_lo_sap_het_han=len(sap_het_han),
              luong_sap_het_han=sum(b["so_luong"] for b in sap_het_han))
    return ra, {"db": db, "y": y, "tp": tp, "lt": lt, "ton": ton, "lo": lo}


def tong_quan(pv, hn, ma_chu_hang=None):
    """Tình trạng kho + tình trạng từng mặt hàng. ma_chu_hang: chỉ lấy hàng của một chủ hàng (vai trò chủ hàng)."""
    bc = _boi_canh(pv, hn)
    ds = [m for m in pv.tim("mat_hang") if not ma_chu_hang or m["ma_chu_hang"] == ma_chu_hang]
    mat_hang = [tinh_mat_hang(pv, m, bc)[0] for m in ds]
    thu_tu = {"do": 0, "cam": 1, "xam": 2, "xanh": 3}
    mat_hang.sort(key=lambda r: (thu_tu[r["mau"]], r["ten"]))
    co = [r for r in mat_hang if r["co_du_lieu"]]
    kpi = {"so_mat_hang": len(mat_hang), "gia_tri_ton": sum(r["gia_tri_ton"] for r in co),
           "so_can_dat": sum(r["nen_dat"] for r in co), "so_nguy_cap": sum(r["mau"] == "do" for r in co),
           "so_sap_het_han": sum(r["so_lo_sap_het_han"] > 0 for r in co),
           "tien_co_the_mat": sum(r["tien_co_the_mat"] for r in co), "tien_can_dat": sum(r["tien_dat"] for r in co)}
    g = nganh.lay(bc["nganh"])
    return sach({"hom_nay": hn, "nganh": {"ma": bc["nganh"], "ten": g["ten"], "minh_hoa": g["minh_hoa"]},
                 "su_kien": [{"ten": t, "con_ngay": n} for t, n in nganh.su_kien_sap_toi(bc["nganh"], hn)],
                 "kpi": kpi, "mat_hang": mat_hang})


def _so_ngay_ve(ton):
    """Biểu đồ tồn kho: vẽ tới vài ngày sau khi hết hàng (tối thiểu 10, tối đa 45 ngày) cho khỏi toàn số 0."""
    het = np.nonzero(ton <= 1e-9)[0]
    return int(min(45, max(10, het[0] + 4))) if len(het) else 45


def chi_tiet(pv, ma, hn, csl=None):
    """Mọi thứ của mục "Xem chi tiết": what-if CSL, bảng WAPE, công thức với số thật, biểu đồ, CSL thực tế từ mô phỏng."""
    mh = pv.tim_mot("mat_hang", ma=ma)
    if not mh:
        raise LoiNhap("Không tìm thấy mặt hàng.")
    bc = _boi_canh(pv, hn)
    kq, tho = tinh_mat_hang(pv, mh, bc, csl)
    if tho is None:
        return sach({"ket_qua": kq, "mat_hang": mh})
    db, y, tp = tho["db"], tho["y"], tho["tp"]
    d, v = db["d_hat"], db["var"]
    them = max(0, 90 + loi.can_them_ngay(tp) - len(d))                       # hạn dùng dài: nối thêm mức trung bình
    d_mp, v_mp = np.r_[d, np.full(them, d.mean())], np.r_[v, np.full(them, v.mean())]
    wi = []
    for w in kn.what_if(d, v, tp):
        mp = kn.do_muc_phuc_vu(d_mp, v_mp, tp, w["csl"], so_lan=12)
        wi.append({"csl": w["csl"], "z": w["z"], "ss": w["ss"], "rop": w["rop"], "chi_phi_giu_ss_nam": w["chi_phi_giu_ss_nam"],
                   "trong_20_lan": int(round((1 - w["csl"]) * 20)), "mo_phong": mp})
    lich_su = y.iloc[-60:]
    sd = np.sqrt(v[:30])
    meta = db["meta"]
    return sach({
        "ket_qua": kq, "mat_hang": mh, "what_if": wi,
        "mo_phong": kn.do_muc_phuc_vu(d_mp, v_mp, tp, kq["csl"], so_lan=20),
        "du_bao": {"mo_hinh": meta["mo_hinh"], "ten_mo_hinh": du_bao_ai.TEN_MO_HINH[meta["mo_hinh"]], "ghi_chu": meta.get("ghi_chu"),
                   "wape": [{"ma": k, "ten": du_bao_ai.TEN_MO_HINH[k], "wape": w} for k, w in meta.get("wape", {}).items()],
                   "so_ngay_do": meta.get("so_ngay_do"), "ngoai_mau": meta.get("ngoai_mau", False),
                   "he_so_phuong_sai": meta.get("he_so_phuong_sai")},
        "bieu_do": {"lich_su": [{"ngay": i, "ban": x} for i, x in lich_su.items()],
                    "du_bao": [{"ngay": db["ngay"][i], "d": d[i], "thap": max(0.0, d[i] - 1.28 * sd[i]), "cao": d[i] + 1.28 * sd[i]}
                               for i in range(30)],
                    "ton": [{"ngay": hn + pd.Timedelta(days=i), "ton": tho["ton"][i]} for i in range(_so_ngay_ve(tho["ton"]))]},
        "lead_time": dict(tho["lt"], mac_dinh=bc["ncc"].get(mh["ma_ncc"], {}).get("lead_time_ngay")),
        "lo": [dict(b, con_ngay=(pd.Timestamp(b["han_su_dung"]) - hn).days) for b in tho["lo"]],
        "dang_ve": [{"sau_ngay": k, "so_luong": sl} for k, sl in bc["dang_ve"].get(ma, ())],
        "tham_so": tp,
    })


# ----------------------------------------------------------------------------
# 5. ĐƠN HÀNG
# ----------------------------------------------------------------------------
def ds_don(pv, hn):
    ncc = {n["ma"]: n["ten"] for n in pv.tim("nha_cung_cap")}
    ra = []
    for d in pv.tim("don_hang"):
        tre = d["trang_thai"] in DON_DANG_VE and pd.Timestamp(d["ngay_giao_du_kien"]) < hn
        ra.append(dict(d, ten_ncc=ncc.get(d["ma_ncc"], "?"), ten_trang_thai=TEN_TRANG_THAI_DON[d["trang_thai"]], tre_hen=tre,
                       tong_tien=sum(x["so_luong"] * x["don_gia"] for x in d["dong"])))
    thu_tu = {"nhap": 0, "da_dat": 1, "ncc_xac_nhan": 1, "da_ve": 2, "huy": 3}
    return sorted(ra, key=lambda d: (thu_tu[d["trang_thai"]], d.get("ngay_tao", "")), reverse=False)


def tao_don_nhap(pv, hn):
    """Gom mọi mặt hàng đang "nên đặt" thành đơn NHÁP, mỗi nhà cung cấp một đơn (đơn nháp cũ được làm mới)."""
    theo_ncc = {}
    for r in tong_quan(pv, hn)["mat_hang"]:
        if r["co_du_lieu"] and r["nen_dat"] and r["ma_ncc"]:
            theo_ncc.setdefault(r["ma_ncc"], []).append({"ma_mat_hang": r["ma"], "ten": r["ten"], "don_vi": r["don_vi"],
                                                         "so_luong": r["so_luong_dat"], "don_gia": r["gia_von"],
                                                         "ten_chu_hang": r["ten_chu_hang"],
                                                         "dat_muon_nhat": r["ngay_dat_muon_nhat"], "ly_do": r["cau_ly_do"]})
    pv.xoa("don_hang", trang_thai="nhap")
    for ma_ncc, dong in theo_ncc.items():
        pv.them("don_hang", {"ma": _ma("don"), "ma_ncc": ma_ncc, "trang_thai": "nhap", "dong": dong, "ngay_tao": chuoi_ngay(hn),
                             "ngay_dat": None, "ngay_giao_du_kien": None, "ngay_ve": None, "ma_lien_ket": None, "ghi_chu_ncc": ""})
    return len(theo_ncc)


def _don(pv, ma, trang_thai):
    d = pv.tim_mot("don_hang", ma=ma)
    if not d:
        raise LoiNhap("Không tìm thấy đơn hàng.")
    if d["trang_thai"] not in trang_thai:
        raise LoiNhap(f"Đơn đang ở trạng thái '{TEN_TRANG_THAI_DON[d['trang_thai']]}' nên không làm được việc này.")
    return d


def sua_don(pv, ma, so_luong):
    """Sửa số lượng từng dòng của đơn nháp. so_luong = {ma_mat_hang: số lượng}; 0 = bỏ dòng."""
    d = _don(pv, ma, ("nhap",))
    dong = []
    for x in d["dong"]:
        sl = _so(so_luong.get(x["ma_mat_hang"], x["so_luong"]), f"Số lượng '{x['ten']}'", 0)
        if sl > 0:
            dong.append(dict(x, so_luong=sl))
    if not dong:
        pv.xoa("don_hang", ma=ma)
    else:
        pv.sua("don_hang", {"ma": ma}, {"dong": dong})


def dat_don(pv, ma, hn):
    """Người dùng xác nhận đơn nháp: từ lúc này hàng được tính là "đang về". Sinh liên kết cho nhà cung cấp."""
    d = _don(pv, ma, ("nhap",))
    ncc = pv.tim_mot("nha_cung_cap", ma=d["ma_ncc"])
    L = max(1, int(round(lead_time_ncc(pv, ncc)["tb"])))
    gt = {"trang_thai": "da_dat", "ngay_dat": chuoi_ngay(hn), "ngay_giao_du_kien": chuoi_ngay(hn + pd.Timedelta(days=L)),
          "ma_lien_ket": secrets.token_urlsafe(16)}
    pv.sua("don_hang", {"ma": ma}, gt)
    return gt


def nhan_don(pv, ma, ngay_ve, hn):
    """Ghi hàng đã về: tạo lô tồn kho mới và lưu ngày về để đo số ngày hàng về của nhà cung cấp."""
    d = _don(pv, ma, DON_DANG_VE)
    ngay_ve = doc_ngay(ngay_ve or hn, "Ngày hàng về")
    if ngay_ve < pd.Timestamp(d["ngay_dat"]) or ngay_ve > hn:
        raise LoiNhap("Ngày hàng về phải từ ngày đặt đến hôm nay.")
    for x in d["dong"]:
        mh = pv.tim_mot("mat_hang", ma=x["ma_mat_hang"])
        if mh:
            pv.them("lo_hang", {"ma": _ma("lo"), "ma_mat_hang": mh["ma"], "so_luong": float(x["so_luong"]), "ngay_nhap": chuoi_ngay(ngay_ve),
                                "han_su_dung": chuoi_ngay(ngay_ve + pd.Timedelta(days=int(mh["han_dung_ngay"])))})
    pv.sua("don_hang", {"ma": ma}, {"trang_thai": "da_ve", "ngay_ve": chuoi_ngay(ngay_ve)})


def huy_don(pv, ma):
    d = _don(pv, ma, ("nhap",) + DON_DANG_VE)
    if d["trang_thai"] == "nhap":
        pv.xoa("don_hang", ma=ma)
    else:
        pv.sua("don_hang", {"ma": ma}, {"trang_thai": "huy"})


def don_cho_ncc(kho, ma_lien_ket):
    """Cổng nhà cung cấp: liên kết chính là chìa khoá, chỉ lộ đúng một đơn và không lộ giá vốn hay tồn kho của khách."""
    d = kho.tim_mot("don_hang", ma_lien_ket=ma_lien_ket) if ma_lien_ket else None
    if not d:
        raise LoiNhap("Liên kết không đúng hoặc đơn đã bị xoá.")
    khach = kho.tim_mot("khach", ma_kho=d["ma_kho"]) or {}
    ncc = kho.tim_mot("nha_cung_cap", ma_kho=d["ma_kho"], ma=d["ma_ncc"]) or {}
    return {"ten_khach": khach.get("ten", ""), "ten_ncc": ncc.get("ten", ""), "trang_thai": d["trang_thai"],
            "ten_trang_thai": TEN_TRANG_THAI_DON[d["trang_thai"]], "ngay_dat": d["ngay_dat"],
            "ngay_giao_du_kien": d["ngay_giao_du_kien"], "ngay_ve": d["ngay_ve"], "ghi_chu_ncc": d.get("ghi_chu_ncc", ""),
            "dong": [{"ten": x["ten"], "don_vi": x.get("don_vi", ""), "so_luong": x["so_luong"]} for x in d["dong"]]}


def ncc_xac_nhan(kho, ma_lien_ket, ngay_giao, ghi_chu=""):
    d = kho.tim_mot("don_hang", ma_lien_ket=ma_lien_ket) if ma_lien_ket else None
    if not d:
        raise LoiNhap("Liên kết không đúng hoặc đơn đã bị xoá.")
    if d["trang_thai"] not in DON_DANG_VE:
        raise LoiNhap("Đơn này không còn chờ xác nhận.")
    ngay = doc_ngay(ngay_giao, "Ngày giao")
    if ngay < pd.Timestamp(d["ngay_dat"]):
        raise LoiNhap("Ngày giao không thể trước ngày đặt.")
    kho.sua("don_hang", {"ma_kho": d["ma_kho"], "ma": d["ma"]},
            {"trang_thai": "ncc_xac_nhan", "ngay_giao_du_kien": chuoi_ngay(ngay), "ghi_chu_ncc": str(ghi_chu or "")[:300]})


# ----------------------------------------------------------------------------
# 6. QUẢN TRỊ (bên bán dịch vụ): KHÔNG đọc số liệu kinh doanh chi tiết của khách
# ----------------------------------------------------------------------------
def ds_khach(kho, hn):
    ra = []
    for k in kho.tim("khach"):
        con = (pd.Timestamp(k["ngay_het_han"]) - hn).days
        ra.append({"ma_kho": k["ma_kho"], "ten": k["ten"], "chu": k.get("chu", ""), "goi": k["goi"], "ten_goi": GOI_DICH_VU[k["goi"]],
                   "nganh": nganh.lay(k.get("nganh"))["ten"], "ngay_bat_dau": k.get("ngay_bat_dau"), "ngay_het_han": k["ngay_het_han"],
                   "con_ngay": con, "trang_thai": "het_han" if con < 0 else "sap_het" if con <= 14 else "con_han",
                   "so_tai_khoan": len(kho.tim("tai_khoan", ma_kho=k["ma_kho"])),
                   "so_mat_hang": len(kho.tim("mat_hang", ma_kho=k["ma_kho"])), "da_nhac": k.get("da_nhac")})
    return sorted(ra, key=lambda r: r["con_ngay"])


def gia_han(kho, ma_kho, so_thang, hn):
    k = kho.tim_mot("khach", ma_kho=ma_kho)
    if not k:
        raise LoiNhap("Không tìm thấy khách.")
    n = _so(so_thang, "Số tháng gia hạn", 1, 36, nguyen=True)
    goc = max(pd.Timestamp(k["ngay_het_han"]), hn)                         # hết hạn rồi thì tính từ hôm nay
    moi = chuoi_ngay(goc + pd.DateOffset(months=n))
    kho.sua("khach", {"ma_kho": ma_kho}, {"ngay_het_han": moi, "da_nhac": None})
    return moi


def ghi_da_nhac(kho, ma_kho, hn):
    if not kho.sua("khach", {"ma_kho": ma_kho}, {"da_nhac": chuoi_ngay(hn)}):
        raise LoiNhap("Không tìm thấy khách.")
