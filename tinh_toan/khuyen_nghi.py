# -*- coding: utf-8 -*-
"""
KHUYẾN NGHỊ ĐẶT HÀNG CHO MỘT MẶT HÀNG (đặc tả V1.1, mục 2.2–2.5): từ dự báo theo ngày (d̂, Var) ra
"đặt bao nhiêu, muộn nhất ngày nào, vì sao".

Quy ước: d_hat[0], var[0] là HÔM NAY; quyết định đặt hàng đưa ra đầu ngày hôm nay.
  z   = Φ⁻¹(CSL)
  SS  = z · sqrt( Σ_{t<L} Var_t + (μ_L / L)² · σ_LT² ),   μ_L = Σ_{t<L} d̂_t
  ROP = μ_L + SS
  I_avail = tồn thực + hàng đang về − hàng giữ chỗ;  đặt khi I_avail ≤ ROP
  Q*  = min( EOQ, trần hạn dùng, trần ngân sách ),  EOQ = sqrt(2·D·S/H),  D = 365/30 · Σ_{t<30} d̂_t
        trần hạn dùng = lượng dự báo bán được trong α·(hạn dùng) ngày
  Số lượng đặt = n·Q*, n nhỏ nhất sao cho I_avail + n·Q* > ROP
  Ngày đặt muộn nhất = (ngày tồn thực dự kiến chạm SS nếu không đặt thêm) − L
"""
import math
from statistics import NormalDist

import numpy as np
import pandas as pd

from . import loi
from . import nhieu_mat_hang as nm

ALPHA_MAC_DINH = 0.6           # hệ số hạn dùng: không nhập quá lượng bán được trong 60 % hạn dùng
ALPHA_KHOANG = (0.5, 0.85)
CSL_WHAT_IF = (0.90, 0.95, 0.99)
LAN_GIAO_TOI_THIEU = 5         # dưới chừng này lần giao thì chưa tin độ lệch lead time đo được


def uoc_luong_lead_time(cac_lan, tb_mac_dinh, dl_mac_dinh, toi_thieu=LAN_GIAO_TOI_THIEU):
    """Ước lượng lead time của một nhà cung cấp từ các lần giao thực tế (số ngày từ đặt tới về).
    Ít lần giao: KHÔNG dùng độ lệch chuẩn vừa tính; trung bình co về giá trị mặc định (mặc định nặng bằng
    `toi_thieu` lần giao). Đủ lần giao: dùng số đo, độ lệch vẫn trộn nhẹ với mặc định cho khỏi bằng 0."""
    x = np.asarray([float(v) for v in cac_lan if v is not None and float(v) >= 0], float)     # 0 = về ngay trong ngày
    n, k = len(x), toi_thieu
    if n == 0:
        return {"tb": float(tb_mac_dinh), "do_lech": float(dl_mac_dinh), "so_lan": 0, "nguon": "mac_dinh"}
    tb = (k * tb_mac_dinh + x.sum()) / (k + n) if n < k else float(x.mean())
    if n < k:
        return {"tb": float(tb), "do_lech": float(dl_mac_dinh), "so_lan": n, "nguon": "co_ve_mac_dinh"}
    dl = math.sqrt((k * dl_mac_dinh ** 2 + (n - 1) * float(x.var(ddof=1))) / (k + n - 1))
    return {"tb": float(tb), "do_lech": float(dl), "so_lan": n, "nguon": "so_do"}


def _L(tp):
    return max(1, int(round(float(tp["lead_time_ngay"]))))


def an_toan(d_hat, var, tp, csl=None):
    """SS, ROP và các thành phần cho một mức phục vụ (dùng cho cả khuyến nghị và thanh trượt what-if)."""
    L = _L(tp)
    csl = float(csl if csl is not None else tp["muc_phuc_vu"])
    z = NormalDist().inv_cdf(min(max(csl, 0.5), 0.999))
    mu = float(np.sum(d_hat[:L]))
    sigma = math.sqrt(float(np.sum(var[:L])) + (mu / L) ** 2 * float(tp["do_lech_lead_time"]) ** 2)
    ss = z * sigma
    H = float(tp["ty_le_giu_hang_nam"]) * float(tp["gia_von"])
    return {"csl": csl, "z": z, "L": L, "mu_L": mu, "sigma_L": sigma, "ss": ss, "rop": mu + ss, "H": H,
            "chi_phi_giu_ss_nam": ss * H}


def what_if(d_hat, var, tp, cac_csl=CSL_WHAT_IF):
    return [an_toan(d_hat, var, tp, c) for c in cac_csl]


def luong_dat(d_hat, tp, alpha=ALPHA_MAC_DINH, ngan_sach=None):
    """Q* và ràng buộc đang chặn ("eoq" | "han_dung" | "ngan_sach")."""
    d = np.asarray(d_hat, float)
    H = float(tp["ty_le_giu_hang_nam"]) * float(tp["gia_von"])
    D = 365.0 / 30.0 * float(np.sum(d[:30])) * (30.0 / min(30, len(d)))
    eoq = math.sqrt(2.0 * D * float(tp["chi_phi_dat_hang"]) / max(H, 1e-9))
    ngay_tran = max(1, int(math.ceil(alpha * float(tp["han_dung_ngay"]))))
    tran_han = float(np.sum(d[:ngay_tran])) + max(0, ngay_tran - len(d)) * float(d.mean())
    ung_vien = {"eoq": eoq, "han_dung": tran_han}
    if ngan_sach:
        ung_vien["ngan_sach"] = float(ngan_sach) / max(float(tp["gia_von"]), 1e-9)
    rang_buoc = min(ung_vien, key=ung_vien.get)
    qc = max(1, int(tp.get("quy_cach") or 1))
    q = max(qc, int(math.floor(ung_vien[rang_buoc] / qc)) * qc)        # làm tròn XUỐNG theo quy cách để không vượt trần
    return {"q": q, "rang_buoc": rang_buoc, "eoq": eoq, "tran_han_dung": tran_han, "tran_ngan_sach": ung_vien.get("ngan_sach"),
            "so_ngay_tran": ngay_tran, "nhu_cau_nam": D}


def du_phong_ton(d_hat, han_dung, lo, dang_ve):
    """Dự phóng tồn kho THỰC từng ngày nếu không đặt thêm: bán hàng gần hết hạn trước, loại hàng quá hạn.
    lo = [(số lượng, số ngày còn hạn)], dang_ve = [(số ngày nữa về, số lượng)].
    Trả về (tồn cuối ngày, thiếu hàng từng ngày, tổng lượng hết hạn)."""
    T = len(d_hat)
    kho = sorted([[float(sl), float(con)] for sl, con in lo if sl > 0], key=lambda b: b[1])
    ton, thieu, het_han = np.zeros(T), np.zeros(T), 0.0
    for t in range(T):
        ve = sum(sl for k, sl in dang_ve if int(k) == t)
        if ve > 0:
            kho.append([float(ve), t + float(han_dung)])
        het_han += sum(b[0] for b in kho if b[1] <= t)
        kho = sorted([b for b in kho if b[1] > t], key=lambda b: b[1])
        can = float(d_hat[t])
        for b in kho:
            lay = min(b[0], can)
            b[0] -= lay
            can -= lay
            if can <= 1e-12:
                break
        kho = [b for b in kho if b[0] > 1e-9]
        ton[t], thieu[t] = sum(b[0] for b in kho), max(can, 0.0)
    return ton, thieu, het_han


def tinh(d_hat, var, tp, lo, dang_ve=(), giu_cho=0.0, csl=None, ngan_sach=None, alpha=ALPHA_MAC_DINH, hom_nay=None):
    """Khuyến nghị cho một mặt hàng. lo = [(số lượng, số ngày còn hạn)]; dang_ve = [(số ngày nữa về, số lượng)]."""
    d, v = np.asarray(d_hat, float), np.asarray(var, float)
    hom_nay = pd.Timestamp(hom_nay or pd.Timestamp.today()).normalize()
    at = an_toan(d, v, tp, csl)
    L, ss, rop = at["L"], at["ss"], at["rop"]
    ton_kho = float(sum(sl for sl, _ in lo))
    hang_ve = float(sum(sl for _, sl in dang_ve))
    kha_dung = ton_kho + hang_ve - float(giu_cho)
    ld = luong_dat(d, tp, alpha, ngan_sach)
    nen_dat = kha_dung <= rop
    n = int(math.floor((rop - kha_dung) / ld["q"])) + 1 if nen_dat else 0
    ton, thieu, het_han = du_phong_ton(d, tp["han_dung_ngay"], lo, dang_ve)

    duoi_ss = np.nonzero(ton <= ss + 1e-9)[0]
    t_ss = int(duoi_ss[0]) if len(duoi_ss) else None
    ngay_muon_nhat = hom_nay + pd.Timedelta(days=max(0, t_ss - L)) if t_ss is not None else None
    het = np.nonzero(thieu > 1e-9)[0]
    so_ngay_du_ban = int(het[0]) if len(het) else None                  # None: đủ bán hết khung dự báo
    cham = loi.ngay_cham_diem_dat(d, np.full(len(d), rop), kha_dung)     # ngày vị thế chạm mức báo đặt hàng

    # Nếu hôm nay không đặt: đơn sớm nhất đặt ngày mai, về sau L+1 ngày. Xác suất nhu cầu vượt hàng khả dụng.
    mu1 = float(np.sum(d[:L + 1]))
    sig1 = math.sqrt(float(np.sum(v[:L + 1])) + (mu1 / (L + 1)) ** 2 * float(tp["do_lech_lead_time"]) ** 2)
    p_het = 1.0 - NormalDist().cdf((kha_dung - mu1) / max(sig1, 1e-9))

    if ton_kho <= 0:
        mau, tinh_trang = "do", "Đã hết hàng"
    elif ton_kho < ss and not hang_ve:
        mau, tinh_trang = "do", "Hàng còn dưới mức dự phòng"
    elif nen_dat:
        mau, tinh_trang = "cam", "Đã tới mức báo đặt hàng"
    else:
        mau, tinh_trang = "xanh", "Còn đủ hàng"

    do_lech7 = np.sqrt(v[:7])
    return {
        "mau": mau, "tinh_trang": tinh_trang, "nen_dat": bool(nen_dat),
        "ton_kho": ton_kho, "hang_dang_ve": hang_ve, "giu_cho": float(giu_cho), "kha_dung": kha_dung,
        "ss": ss, "rop": rop, "z": at["z"], "csl": at["csl"], "L": L, "mu_L": at["mu_L"], "sigma_L": at["sigma_L"],
        "chi_phi_giu_ss_nam": at["chi_phi_giu_ss_nam"],
        "q": ld["q"], "so_don_vi_q": n, "so_luong_dat": n * ld["q"], "tien_dat": n * ld["q"] * float(tp["gia_von"]),
        "rang_buoc": ld["rang_buoc"], "eoq": ld["eoq"], "tran_han_dung": ld["tran_han_dung"],
        "tran_ngan_sach": ld["tran_ngan_sach"], "so_ngay_tran": ld["so_ngay_tran"], "nhu_cau_nam": ld["nhu_cau_nam"],
        "ngay_dat_muon_nhat": ngay_muon_nhat, "so_ngay_du_ban": so_ngay_du_ban, "so_ngay_toi_muc_bao": cham,
        "xac_suat_het_hang": float(min(max(p_het, 0.0), 1.0)),
        "luong_co_the_het_han": float(het_han), "tien_co_the_mat": float(het_han) * float(tp["gia_von"]),
        "ban_7_ngay": [float(max(0.0, (d[:7] - 1.28 * do_lech7).mean())), float((d[:7] + 1.28 * do_lech7).mean())],
        "ton_du_phong": ton,
    }


def do_muc_phuc_vu(d_hat, var, tp, csl=None, so_lan=20, so_ngay=90, seed=0):
    """Đo CSL THỰC TẾ và fill rate bằng mô phỏng: nhu cầu ngẫu nhiên quanh dự báo (có sai số dự báo), lead time
    ngẫu nhiên. CSL = tỷ lệ chu kỳ đặt hàng không bị hết hàng; fill rate = lượng bán được / nhu cầu.
    Hai chỉ số KHÁC NHAU: một chu kỳ hết hàng có thể chỉ thiếu vài đơn vị."""
    tp = dict(tp, muc_phuc_vu=float(csl if csl is not None else tp["muc_phuc_vu"]))
    T = min(so_ngay, len(d_hat) - loi.can_them_ngay(tp))
    if T < 14:
        return None
    cs = loi.chinh_sach(d_hat, var, tp, T)
    L, sd = cs["L"], float(tp["do_lech_lead_time"])
    rng = np.random.default_rng(seed)
    chu_ky = het = 0
    nhu_cau = ban = het_han = 0.0
    for _ in range(so_lan):
        nc = nm.sinh_nhu_cau(d_hat[:T], var[:T], rng)
        lt = np.maximum(1, np.round(rng.normal(L, sd, T))).astype(int)
        sim = loi.mo_phong(d_hat, cs["rop"], cs["ss"], cs["q"], L, cs["rop"][0] + cs["q"][0], 0, int(tp["han_dung_ngay"]),
                           pd.Timestamp("2000-01-01"), so_ngay=T, nhu_cau=nc, lead_times=lt,
                           han_con_lai0=int(tp["han_dung_ngay"]))
        ve = np.nonzero(sim["hang_ve"].values > 0)[0]
        moc = [0] + list(ve) + [T]
        thieu = sim["thieu_hang"].values
        for a, b in zip(moc[:-1], moc[1:]):
            if b > a:
                chu_ky += 1
                het += int(thieu[a:b].sum() > 1e-9)
        nhu_cau += float(sim["nhu_cau"].sum())
        ban += float(sim["ban"].sum())
        het_han += float(sim["het_han"].sum())
    return {"csl_muc_tieu": tp["muc_phuc_vu"], "csl_thuc_te": 1 - het / max(chu_ky, 1), "fill_rate": ban / max(nhu_cau, 1e-9),
            "so_chu_ky": chu_ky, "so_lan": so_lan, "so_ngay": T, "het_han_tb": het_han / so_lan}
