# -*- coding: utf-8 -*-
"""Lõi của SmartStock AI V1.1: dự báo có so sánh WAPE, SS / ROP / Q*, ngày đặt muộn nhất, lead time, gói ngành."""
import numpy as np
import pandas as pd
import pytest

from tinh_toan import du_bao_ai, nganh
from tinh_toan import khuyen_nghi as kn

from conftest import chuoi_co_tet

TP = {"lead_time_ngay": 2, "do_lech_lead_time": 0.5, "muc_phuc_vu": 0.95, "ty_le_giu_hang_nam": 0.25, "gia_von": 10000,
      "chi_phi_dat_hang": 40000, "han_dung_ngay": 90, "quy_cach": 1}
D, V = np.full(150, 10.0), np.full(150, 12.0)


def test_z_dung_va_ss_khong_giam_khi_csl_tang():
    assert kn.an_toan(D, V, TP, 0.95)["z"] == pytest.approx(1.645, abs=0.001)
    ss = [w["ss"] for w in kn.what_if(D, V, TP)]
    assert ss == sorted(ss) and ss[0] < ss[-1]
    assert [w["chi_phi_giu_ss_nam"] for w in kn.what_if(D, V, TP)] == sorted(w["chi_phi_giu_ss_nam"] for w in kn.what_if(D, V, TP))


def test_ss_rop_theo_cong_thuc():
    a = kn.an_toan(D, V, TP)
    sigma = np.sqrt(2 * 12 + (20 / 2) ** 2 * 0.5 ** 2)
    assert a["mu_L"] == pytest.approx(20) and a["ss"] == pytest.approx(a["z"] * sigma) and a["rop"] == pytest.approx(20 + a["ss"])


def test_dat_khi_cham_rop_va_n_nho_nhat():
    k = kn.tinh(D, V, TP, [(5, 60)], hom_nay="2026-01-10")
    assert k["nen_dat"] and k["so_don_vi_q"] >= 1
    assert k["kha_dung"] + k["so_luong_dat"] > k["rop"] >= k["kha_dung"] + (k["so_don_vi_q"] - 1) * k["q"]
    assert not kn.tinh(D, V, TP, [(500, 60)], hom_nay="2026-01-10")["nen_dat"]


def test_hang_dang_ve_va_giu_cho_tinh_vao_vi_the():
    k = kn.tinh(D, V, TP, [(5, 60)], dang_ve=[(1, 100)], giu_cho=10, hom_nay="2026-01-10")
    assert k["kha_dung"] == 95 and not k["nen_dat"]


def test_luong_dat_bi_chan_boi_han_dung_ngan_sach_va_quy_cach():
    assert kn.luong_dat(D, TP)["rang_buoc"] == "eoq"
    ngan = kn.luong_dat(D, dict(TP, han_dung_ngay=5))
    assert ngan["rang_buoc"] == "han_dung" and ngan["q"] == 30                 # 0,6 × 5 = 3 ngày × 10
    tien = kn.luong_dat(D, TP, ngan_sach=250000)
    assert tien["rang_buoc"] == "ngan_sach" and tien["q"] == 25
    assert kn.luong_dat(D, dict(TP, quy_cach=12), ngan_sach=250000)["q"] == 24  # làm tròn XUỐNG theo quy cách


def test_ngay_dat_muon_nhat_la_ngay_cham_ss_tru_lead_time():
    k = kn.tinh(D, V, TP, [(100, 60)], hom_nay="2026-01-10")
    t_ss = next(t for t in range(150) if 100 - 10 * (t + 1) <= k["ss"])          # tồn cuối ngày t
    assert k["ngay_dat_muon_nhat"] == pd.Timestamp("2026-01-10") + pd.Timedelta(days=t_ss - 2)
    assert k["so_ngay_du_ban"] == 10 and k["mau"] == "xanh"


def test_lo_sap_het_han_bi_loai_va_tinh_tien_mat():
    k = kn.tinh(D, V, TP, [(100, 3), (50, 60)], hom_nay="2026-01-10")
    assert k["luong_co_the_het_han"] == pytest.approx(70) and k["tien_co_the_mat"] == pytest.approx(700000)


def test_trang_thai_mau():
    assert kn.tinh(D, V, TP, [], hom_nay="2026-01-10")["mau"] == "do"
    assert kn.tinh(D, V, TP, [(25, 60)], hom_nay="2026-01-10")["mau"] == "cam"


def test_lead_time_it_lan_giao_thi_co_ve_mac_dinh():
    assert kn.uoc_luong_lead_time([], 2, 0.7) == {"tb": 2.0, "do_lech": 0.7, "so_lan": 0, "nguon": "mac_dinh"}
    it = kn.uoc_luong_lead_time([4, 4], 2, 0.7)
    assert it["nguon"] == "co_ve_mac_dinh" and it["do_lech"] == 0.7 and 2 < it["tb"] < 4
    du = kn.uoc_luong_lead_time([3, 3, 4, 3, 3, 4], 2, 0.7)
    assert du["nguon"] == "so_do" and du["tb"] == pytest.approx(10 / 3) and du["do_lech"] > 0


def test_do_muc_phuc_vu_tach_csl_va_fill_rate():
    mp = kn.do_muc_phuc_vu(D, V, TP, so_lan=8)
    assert 0 <= mp["csl_thuc_te"] <= 1 and mp["csl_thuc_te"] <= mp["fill_rate"] <= 1 and mp["so_chu_ky"] > 0


def test_du_bao_so_sanh_ba_cach_va_chon_wape_thap_nhat():
    r = du_bao_ai.du_bao(chuoi_co_tet(), 60)
    w = r["meta"]["wape"]
    assert set(w) == {"ai", "mua_vu", "trung_binh"} and r["meta"]["mo_hinh"] == min(w, key=w.get)
    assert (r["var"] >= r["d_hat"] - 1e-9).all() and len(r["d_hat"]) == 60 and r["meta"]["ghi_chu"]


def test_du_bao_nganh_khac_khong_dung_mo_hinh_tet():
    r = du_bao_ai.du_bao(chuoi_co_tet(), 30, su_kien=nganh.lay("hoa_tuoi")["su_kien"], co_mua_vu=False)
    assert "mua_vu" not in r["meta"]["wape"] and r["meta"]["mo_hinh"] in ("ai", "trung_binh")


def test_du_bao_it_du_lieu():
    y = chuoi_co_tet(so_ngay=30)
    kd = du_bao_ai.du_bao(y, 20, uoc_luong=(5, 10, 20))
    assert kd["meta"]["mo_hinh"] == "khoi_dong"
    ngan = du_bao_ai.du_bao(chuoi_co_tet(so_ngay=120), 20)
    assert ngan["meta"]["mo_hinh"] == "mua_vu" and not ngan["meta"]["ngoai_mau"] and ngan["meta"]["wape"] == {}


def test_su_kien_sap_toi():
    assert nganh.su_kien_sap_toi("banh_keo", "2026-11-24") == [("Tết", 74)]
    assert nganh.su_kien_sap_toi("hoa_tuoi", "2026-03-01", 30) == [("8/3", 7)]
    assert nganh.lay("khong_co")["ten"] == "Bánh kẹo"
