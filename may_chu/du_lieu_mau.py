# -*- coding: utf-8 -*-
"""
DỮ LIỆU MẪU cho tài khoản demo. TẤT CẢ LÀ MÔ PHỎNG: doanh số sinh ngẫu nhiên, giá và hạn dùng là giả định minh hoạ.

Ba khách của dịch vụ:
  1. Kho bánh kẹo chợ Bến Thành: kho dịch vụ có 3 chủ hàng gửi hàng (ngành chính, 6 mặt hàng, ~2 năm doanh số)
  2. Sạp hoa tươi Đà Lạt: ngành thứ hai minh hoạ gói cấu hình ngành; có một mặt hàng mới chỉ có ước lượng ban đầu
  3. Tạp hoá chị Sáu: gói dùng thử đã hết hạn, chưa có dữ liệu (để minh hoạ dashboard gia hạn)

Chạy `python -m may_chu.du_lieu_mau --lam-lai` để XOÁ dữ liệu SmartStock hiện có và nạp lại dữ liệu mẫu.
"""
import sys

import numpy as np
import pandas as pd

from tinh_toan import loi
from tinh_toan import nganh

from . import dich_vu as dv
from .kho_du_lieu import PhamVi, mo_kho

BANG = ["khach", "tai_khoan", "phien", "chu_hang", "nha_cung_cap", "mat_hang", "doanh_so", "lo_hang", "don_hang"]


def _ngay(hn, lech):
    return dv.chuoi_ngay(hn + pd.Timedelta(days=lech))


def _don_da_ve(pv, hn, ma_ncc, cac_lan):
    """Các đơn cũ đã về: nguồn số đo "số ngày hàng về" của nhà cung cấp. cac_lan = [(đặt cách đây mấy ngày, số ngày hàng về)]."""
    for cach, lt in cac_lan:
        pv.them("don_hang", {"ma": dv._ma("don"), "ma_ncc": ma_ncc, "trang_thai": "da_ve", "dong": [], "ngay_tao": _ngay(hn, -cach),
                             "ngay_dat": _ngay(hn, -cach), "ngay_giao_du_kien": _ngay(hn, -cach + lt), "ngay_ve": _ngay(hn, -cach + lt),
                             "ma_lien_ket": None, "ghi_chu_ncc": ""})


def _kho_banh_keo(kho, hn):
    import pipeline                                            # bộ sinh doanh số mô phỏng của dự án
    pv = PhamVi(kho, "kho-ben-thanh")
    kho.them("khach", {"ma_kho": pv.ma_kho, "ten": "Kho bánh kẹo chợ Bến Thành", "chu": "Cô Lan", "nganh": "banh_keo", "goi": "nang_cao",
                       "ngay_bat_dau": _ngay(hn, -160), "ngay_het_han": _ngay(hn, 205), "da_nhac": None})
    for ma, ten in [("ch-lan", "Sạp cô Lan (chủ kho)"), ("ch-hung", "Sạp anh Hùng"), ("ch-mai", "Sạp chị Mai")]:
        pv.them("chu_hang", {"ma": ma, "ten": ten, "dien_thoai": ""})
    for ma, ten, lt, dl in [("ncc-dau-moi", "Chợ đầu mối Bình Tây", 1.0, 0.5), ("ncc-lo-pia", "Lò bánh pía Sóc Trăng", 2.0, 0.7),
                            ("ncc-trung-thu", "Nhà phân phối bánh trung thu", 3.0, 1.0)]:
        pv.them("nha_cung_cap", {"ma": ma, "ten": ten, "lien_he": "", "lead_time_ngay": lt, "do_lech_lead_time": dl})
    # (tên trong bộ mô phỏng, đơn vị, chủ hàng, nhà cung cấp, giá vốn, giá bán, hạn dùng, quy cách, các lô [(số lượng, còn hạn mấy ngày)])
    mat_hang = [
        ("Kẹo dừa Bến Tre (gói 200g)", "gói", "ch-lan", "ncc-dau-moi", 12000, 18000, 180, 10, [(25, 120)]),
        ("Bánh quy / bánh gạo (gói)", "gói", "ch-lan", "ncc-dau-moi", 8000, 12000, 240, 10, [(320, 200)]),
        ("Bánh pía (hộp)", "hộp", "ch-hung", "ncc-lo-pia", 28000, 40000, 30, 1, [(26, 3), (40, 24)]),
        ("Kẹo lạc / kẹo mè xửng", "gói", "ch-hung", "ncc-dau-moi", 10000, 15000, 90, 10, []),
        ("Mứt Tết (hộp)", "hộp", "ch-mai", "ncc-dau-moi", 45000, 70000, 120, 1, [(14, 90)]),
        ("Bánh trung thu (cái)", "cái", "ch-mai", "ncc-trung-thu", 60000, 95000, 60, 1, [(18, 9)]),
    ]
    ngay = pd.date_range(hn - pd.Timedelta(days=750), hn - pd.Timedelta(days=1))
    rng = np.random.default_rng(42)
    ma_theo_ten = {}
    for ten, don_vi, ch, ncc, gv, gb, han, qc, lo in mat_hang:
        ma = dv.luu_mat_hang(pv, {"ten": ten, "don_vi": don_vi, "ma_chu_hang": ch, "ma_ncc": ncc, "gia_von": gv, "gia_ban": gb,
                                  "han_dung_ngay": han, "quy_cach": qc})
        ma_theo_ten[ten] = ma
        ban = pipeline.sinh_nhu_cau(ten, ngay, rng)
        pv.them("doanh_so", {"ma_mat_hang": ma, "chuoi": {dv.chuoi_ngay(d): float(x) for d, x in zip(ngay, ban)}, "het_hang": []})
        for sl, con in lo:
            pv.them("lo_hang", {"ma": dv._ma("lo"), "ma_mat_hang": ma, "so_luong": float(sl), "han_su_dung": _ngay(hn, con),
                                "ngay_nhap": _ngay(hn, con - han)})
    _don_da_ve(pv, hn, "ncc-dau-moi", [(60, 1), (48, 1), (39, 2), (27, 1), (16, 1), (8, 2)])      # đủ 6 lần giao: dùng số đo
    _don_da_ve(pv, hn, "ncc-lo-pia", [(30, 2), (12, 3)])                                          # mới 2 lần: co về mặc định
    pv.them("don_hang", {"ma": dv._ma("don"), "ma_ncc": "ncc-dau-moi", "trang_thai": "da_dat", "ngay_tao": _ngay(hn, 0),
                         "dong": [{"ma_mat_hang": ma_theo_ten["Mứt Tết (hộp)"], "ten": "Mứt Tết (hộp)", "don_vi": "hộp", "so_luong": 40,
                                   "don_gia": 45000, "ten_chu_hang": "Sạp chị Mai", "dat_muon_nhat": None, "ly_do": ""}],
                         "ngay_dat": _ngay(hn, 0), "ngay_giao_du_kien": _ngay(hn, 1), "ngay_ve": None, "ma_lien_ket": "demo-ncc-dau-moi",
                         "ghi_chu_ncc": ""})
    for ma, ten, vai_tro, ch in [("ck-lan", "Cô Lan", "chu_kho", "ch-lan"), ("ch-hung", "Anh Hùng", "chu_hang", "ch-hung"),
                                 ("ch-mai", "Chị Mai", "chu_hang", "ch-mai")]:
        kho.them("tai_khoan", {"ma": ma, "ten": ten, "vai_tro": vai_tro, "ma_kho": pv.ma_kho, "ma_chu_hang": ch})


def _ban_hoa(ngay, muc, rng):
    """Doanh số hoa mô phỏng: cuối tuần bán hơn, tăng vọt 3 ngày trước mỗi ngày lễ của gói ngành hoa tươi."""
    he_so = np.where(ngay.dayofweek >= 5, 1.35, 1.0)
    for ds in nganh.GOI["hoa_tuoi"]["su_kien"].values():
        lech = loi._ngay_gan_nhat(ngay, pd.DatetimeIndex(ds))
        he_so = he_so * (1 + 3.5 * np.exp(-0.5 * ((lech + 1) / 1.5) ** 2) * (lech <= 0))
    return rng.poisson(muc * he_so).astype(float)


def _sap_hoa(kho, hn):
    pv = PhamVi(kho, "kho-hoa-da-lat")
    kho.them("khach", {"ma_kho": pv.ma_kho, "ten": "Sạp hoa tươi Đà Lạt", "chu": "Anh Minh", "nganh": "hoa_tuoi", "goi": "co_ban",
                       "ngay_bat_dau": _ngay(hn, -80), "ngay_het_han": _ngay(hn, 9), "da_nhac": None})
    pv.them("chu_hang", {"ma": "ch-minh", "ten": "Sạp anh Minh", "dien_thoai": ""})
    pv.them("nha_cung_cap", {"ma": "ncc-vua-hoa", "ten": "Vựa hoa Đà Lạt", "lien_he": "", "lead_time_ngay": 1.0, "do_lech_lead_time": 0.3})
    ngay = pd.date_range(hn - pd.Timedelta(days=500), hn - pd.Timedelta(days=1))
    rng = np.random.default_rng(7)
    for ten, don_vi, gv, gb, muc, lo in [("Hoa hồng Đà Lạt (bó)", "bó", 35000, 60000, 20, [(30, 3)]),
                                          ("Hoa cúc (bó)", "bó", 20000, 35000, 12, [(8, 2)])]:
        ma = dv.luu_mat_hang(pv, {"ten": ten, "don_vi": don_vi, "ma_chu_hang": "ch-minh", "ma_ncc": "ncc-vua-hoa", "gia_von": gv, "gia_ban": gb})
        pv.them("doanh_so", {"ma_mat_hang": ma, "chuoi": {dv.chuoi_ngay(d): x for d, x in zip(ngay, _ban_hoa(ngay, muc, rng))}, "het_hang": []})
        for sl, con in lo:
            pv.them("lo_hang", {"ma": dv._ma("lo"), "ma_mat_hang": ma, "so_luong": float(sl), "han_su_dung": _ngay(hn, con), "ngay_nhap": _ngay(hn, con - 5)})
    # Mặt hàng mới, chưa có số bán: chỉ có ước lượng của người bán (ít nhất, thường, nhiều nhất mỗi ngày)
    ma = dv.luu_mat_hang(pv, {"ten": "Hoa ly (cành)", "don_vi": "cành", "ma_chu_hang": "ch-minh", "ma_ncc": "ncc-vua-hoa", "gia_von": 25000,
                              "gia_ban": 45000, "han_dung_ngay": 7, "uoc_luong": [3, 6, 12]})
    pv.them("lo_hang", {"ma": dv._ma("lo"), "ma_mat_hang": ma, "so_luong": 10.0, "han_su_dung": _ngay(hn, 5), "ngay_nhap": _ngay(hn, -2)})
    kho.them("tai_khoan", {"ma": "ck-minh", "ten": "Anh Minh", "vai_tro": "chu_kho", "ma_kho": pv.ma_kho, "ma_chu_hang": "ch-minh"})


def nap(kho, hn=None):
    hn = hn or dv.hom_nay()
    kho.them("tai_khoan", {"ma": "qt-van-hanh", "ten": "Nhóm vận hành SmartStock", "vai_tro": "quan_tri", "ma_kho": None, "ma_chu_hang": None})
    _kho_banh_keo(kho, hn)
    _sap_hoa(kho, hn)
    kho.them("khach", {"ma_kho": "kho-chi-sau", "ten": "Tạp hoá chị Sáu", "chu": "Chị Sáu", "nganh": "banh_keo", "goi": "dung_thu",
                       "ngay_bat_dau": _ngay(hn, -35), "ngay_het_han": _ngay(hn, -5), "da_nhac": None})
    kho.them("chu_hang", {"ma_kho": "kho-chi-sau", "ma": "ch-sau", "ten": "Tạp hoá chị Sáu", "dien_thoai": ""})
    kho.them("tai_khoan", {"ma": "ck-sau", "ten": "Chị Sáu", "vai_tro": "chu_kho", "ma_kho": "kho-chi-sau", "ma_chu_hang": "ch-sau"})


def nap_neu_trong(kho):
    """Lần chạy đầu (chưa có khách nào): nạp dữ liệu mẫu."""
    if not kho.tim("khach"):
        nap(kho)
        return True
    return False


def lam_lai(kho):
    for b in BANG:
        kho.xoa(b)
    nap(kho)


if __name__ == "__main__":
    if "--lam-lai" not in sys.argv:
        sys.exit("Lệnh này XOÁ toàn bộ dữ liệu SmartStock rồi nạp lại dữ liệu mẫu. Thêm --lam-lai để xác nhận.")
    k = mo_kho()
    lam_lai(k)
    print("Đã nạp lại dữ liệu mẫu vào", k.mo_ta())
