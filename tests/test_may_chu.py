# -*- coding: utf-8 -*-
"""Máy chủ SmartStock AI: vai trò, cách ly dữ liệu giữa các kho, sổ bán, tải file, vòng đời đơn hàng, quản trị, AI.
Dùng kho dữ liệu trong bộ nhớ: không đụng MongoDB, không gọi dịch vụ AI thật."""
import base64
import os

import pytest
from fastapi.testclient import TestClient

from may_chu import dich_vu as dv
from may_chu import du_lieu_mau, ung_dung
from may_chu.kho_du_lieu import KhoTep, PhamVi
from tro_ly_ai import nhan_dien as nd

from conftest import DU_LIEU_THU

HOM_NAY = "2026-11-24"


@pytest.fixture(scope="module")
def c():
    cu_ngay, cu_kho = os.environ.get("SMARTSTOCK_HOM_NAY"), ung_dung._kho
    os.environ["SMARTSTOCK_HOM_NAY"] = HOM_NAY
    ung_dung._kho = KhoTep()
    du_lieu_mau.nap(ung_dung._kho)
    yield TestClient(ung_dung.app)
    ung_dung._kho = cu_kho
    if cu_ngay is None:
        os.environ.pop("SMARTSTOCK_HOM_NAY")
    else:
        os.environ["SMARTSTOCK_HOM_NAY"] = cu_ngay


def vao(c, ma):
    return {"Authorization": "Bearer " + c.post("/api/dang-nhap", json={"ma": ma}).json()["token"]}


@pytest.fixture(scope="module")
def lan(c):
    return vao(c, "ck-lan")


def test_chua_dang_nhap_va_sai_vai_tro(c, lan):
    assert c.get("/api/tong-quan").status_code == 401
    assert c.post("/api/dang-nhap", json={"ma": "khong-co"}).status_code == 401
    assert c.get("/api/tong-quan", headers=vao(c, "qt-van-hanh")).status_code == 403      # quản trị không xem số liệu khách
    assert c.get("/api/quan-tri/khach", headers=lan).status_code == 403
    hung = vao(c, "ch-hung")
    assert c.get("/api/danh-muc", headers=hung).status_code == 403                         # chủ hàng chỉ được xem
    assert c.post("/api/so-ban", headers=hung, json={"dong": []}).status_code == 403


def test_tong_quan_ba_cau_va_kpi(c, lan):
    d = c.get("/api/tong-quan", headers=lan).json()
    assert d["kpi"]["so_mat_hang"] == 6 and d["su_kien"] == [{"ten": "Tết", "con_ngay": 74}]
    mau = [m["mau"] for m in d["mat_hang"]]
    assert mau == sorted(mau, key=["do", "cam", "xam", "xanh"].index)
    lac = next(m for m in d["mat_hang"] if m["ten"].startswith("Kẹo lạc"))
    assert lac["mau"] == "do" and lac["nen_dat"] and lac["cau_viec"].startswith("Nên đặt") and lac["cau_ly_do"]
    assert d["kpi"]["so_can_dat"] == sum(m["nen_dat"] for m in d["mat_hang"]) >= 2


def test_chu_hang_chi_thay_hang_cua_minh(c, lan):
    hung = vao(c, "ch-hung")
    cua_hung = c.get("/api/tong-quan", headers=hung).json()["mat_hang"]
    assert {m["ma_chu_hang"] for m in cua_hung} == {"ch-hung"} and len(cua_hung) == 2
    cua_nguoi_khac = next(m for m in c.get("/api/tong-quan", headers=lan).json()["mat_hang"] if m["ma_chu_hang"] == "ch-mai")
    assert c.get(f"/api/mat-hang/{cua_nguoi_khac['ma']}/chi-tiet", headers=hung).status_code == 404
    assert c.get(f"/api/mat-hang/{cua_hung[0]['ma']}/chi-tiet", headers=hung).status_code == 200


def test_kho_nay_khong_doc_duoc_kho_khac(c, lan):
    ma = c.get("/api/tong-quan", headers=lan).json()["mat_hang"][0]["ma"]
    minh = vao(c, "ck-minh")
    assert c.get(f"/api/mat-hang/{ma}/chi-tiet", headers=minh).status_code == 404
    assert c.put(f"/api/mat-hang/{ma}", headers=minh, json={"gia_von": 1}).status_code == 400
    assert all("Hoa" in m["ten"] for m in c.get("/api/tong-quan", headers=minh).json()["mat_hang"])
    pv = PhamVi(ung_dung._kho, "kho-hoa-da-lat")
    pv.sua("mat_hang", {"ma": pv.tim("mat_hang")[0]["ma"]}, {"ma_kho": "kho-ben-thanh", "don_vi": "bó"})
    assert len(pv.tim("mat_hang")) == 3                                                    # không chuyển được bản ghi sang kho khác


def test_chi_tiet_what_if_va_mo_phong(c, lan):
    ma = next(m["ma"] for m in c.get("/api/tong-quan", headers=lan).json()["mat_hang"] if m["ten"].startswith("Bánh quy"))
    d = c.get(f"/api/mat-hang/{ma}/chi-tiet", headers=lan).json()
    assert [w["csl"] for w in d["what_if"]] == [0.9, 0.95, 0.99]
    assert d["what_if"][0]["ss"] < d["what_if"][1]["ss"] < d["what_if"][2]["ss"]
    assert {w["ma"] for w in d["du_bao"]["wape"]} == {"ai", "mua_vu", "trung_binh"}
    assert 0 <= d["mo_phong"]["csl_thuc_te"] <= 1 and len(d["bieu_do"]["du_bao"]) == 30
    assert d["lead_time"]["nguon"] == "so_do" and d["lead_time"]["so_lan"] == 6
    cao = c.get(f"/api/mat-hang/{ma}/chi-tiet?csl=0.99", headers=lan).json()["ket_qua"]
    assert cao["ss"] > d["ket_qua"]["ss"] and cao["rop"] > d["ket_qua"]["rop"]


def test_ghi_so_ban_tru_ton_theo_chenh_lech(c, lan):
    dong = next(x for x in c.get("/api/so-ban", headers=lan).json()["dong"] if x["ten"].startswith("Bánh pía"))
    assert dong["ton_kho"] == 66 and dong["so_luong"] is None

    def ghi(sl):
        return c.post("/api/so-ban", headers=lan, json={"ngay": HOM_NAY, "dong": [{"ma": dong["ma"], "so_luong": sl}]})

    def ton():
        return next(x for x in c.get("/api/so-ban", headers=lan).json()["dong"] if x["ma"] == dong["ma"])["ton_kho"]

    assert ghi(30).json() == {"so_dong": 1} and ton() == 36
    lo = [b for b in c.get("/api/lo-hang", headers=lan).json() if b["ma_mat_hang"] == dong["ma"]]
    assert [b["so_luong"] for b in lo] == [36]                                             # lô gần hết hạn (26) bị trừ hết trước
    assert ghi(20).status_code == 200 and ton() == 46                                      # ghi lại: chỉ trả phần chênh
    assert ghi(-1).status_code == 400
    assert c.post("/api/so-ban", headers=lan, json={"ngay": "2030-01-01", "dong": []}).status_code == 400


def test_mat_hang_kiem_tra_va_bao_loi_tieng_viet(c, lan):
    dm = c.get("/api/danh-muc", headers=lan).json()
    goc = {"ten": "Kẹo thử", "ma_chu_hang": dm["chu_hang"][0]["ma"], "ma_ncc": dm["nha_cung_cap"][0]["ma"], "gia_von": 5000}
    r = c.post("/api/mat-hang", headers=lan, json=dict(goc, gia_von=-1))
    assert r.status_code == 400 and "Giá vốn" in r.json()["loi"]
    assert c.post("/api/mat-hang", headers=lan, json=dict(goc, uoc_luong=[9, 5, 1])).status_code == 400
    ma = c.post("/api/mat-hang", headers=lan, json=dict(goc, uoc_luong=[2, 5, 9])).json()["ma"]
    assert c.post("/api/mat-hang", headers=lan, json=goc).status_code == 400               # trùng tên
    moi = next(m for m in c.get("/api/tong-quan", headers=lan).json()["mat_hang"] if m["ma"] == ma)
    assert moi["co_du_lieu"] and moi["mo_hinh"] == "khoi_dong" and moi["mau"] == "do"
    assert c.delete(f"/api/mat-hang/{ma}", headers=lan).status_code == 200
    assert c.delete(f"/api/chu-hang/{dm['chu_hang'][0]['ma']}", headers=lan).status_code == 400   # còn hàng thì không xoá


def test_tai_file_doanh_so(c):
    sau = vao(c, "ck-sau")

    def gui(ten, noi_dung):
        return c.post("/api/doanh-so/tai-len", headers=sau, json={"ten_file": ten, "noi_dung_b64": base64.b64encode(noi_dung).decode()})

    with open(os.path.join(DU_LIEU_THU, "doanh_so_thu.csv"), "rb") as f:
        tep = f.read()
    assert gui("doanh_so.csv", tep).status_code == 400                                     # chưa có nhà cung cấp
    assert c.post("/api/nha-cung-cap", headers=sau, json={"ten": "Đại lý", "lead_time_ngay": 2}).status_code == 200
    r = gui("doanh_so.csv", tep).json()
    assert r["so_ngay"] >= 365 and len(r["mat_hang_moi"]) == 8 and any("MẶC ĐỊNH" in x for x in r["canh_bao"])
    assert all(m["can_bo_sung"] for m in c.get("/api/danh-muc", headers=sau).json()["mat_hang"])
    loi = gui("xau.csv", "ngay,mat_hang,so_luong_ban\n2026-01-01,Kẹo,abc\n".encode())
    assert loi.status_code == 400 and "không phải số" in loi.json()["loi"]
    assert "ít nhất 60 ngày" in gui("ngan.csv", "ngay,Kẹo\n2026-01-01,5\n2026-01-02,6\n".encode()).json()["loi"]


def test_vong_doi_don_hang_va_cong_nha_cung_cap(c, lan):
    assert c.post("/api/don-hang/tao-nhap", headers=lan).json()["so_don"] >= 1
    nhap = next(d for d in c.get("/api/don-hang", headers=lan).json() if d["trang_thai"] == "nhap")
    mh = nhap["dong"][0]["ma_mat_hang"]
    assert c.put(f"/api/don-hang/{nhap['ma']}", headers=lan, json={"so_luong": {mh: 50}}).status_code == 200
    dat = c.post(f"/api/don-hang/{nhap['ma']}/dat", headers=lan).json()
    assert dat["trang_thai"] == "da_dat" and dat["ngay_dat"] == HOM_NAY and len(dat["ma_lien_ket"]) > 15
    assert c.post(f"/api/don-hang/{nhap['ma']}/dat", headers=lan).status_code == 400       # không đặt hai lần
    ct = c.get(f"/api/mat-hang/{mh}/chi-tiet", headers=lan).json()
    assert ct["ket_qua"]["hang_dang_ve"] == 50
    so_lan = ct["lead_time"]["so_lan"]

    cong = c.get(f"/api/ncc/{dat['ma_lien_ket']}").json()                                  # không cần đăng nhập
    assert "don_gia" not in str(cong) and cong["dong"][0]["so_luong"] == 50
    assert c.get("/api/ncc/sai-lien-ket").status_code == 400
    assert c.post(f"/api/ncc/{dat['ma_lien_ket']}/xac-nhan", json={"ngay_giao": "2026-11-01"}).status_code == 400
    xn = c.post(f"/api/ncc/{dat['ma_lien_ket']}/xac-nhan", json={"ngay_giao": "2026-11-26", "ghi_chu": "giao sáng"}).json()
    assert xn["trang_thai"] == "ncc_xac_nhan" and xn["ngay_giao_du_kien"] == "2026-11-26"

    assert c.post(f"/api/don-hang/{nhap['ma']}/nhan", headers=lan, json={"ngay_ve": "2027-01-01"}).status_code == 400
    assert c.post(f"/api/don-hang/{nhap['ma']}/nhan", headers=lan, json={"ngay_ve": HOM_NAY}).status_code == 200
    sau = c.get(f"/api/mat-hang/{mh}/chi-tiet", headers=lan).json()
    assert sau["ket_qua"]["hang_dang_ve"] == 0 and any(b["so_luong"] == 50 for b in sau["lo"])
    assert sau["lead_time"]["so_lan"] == so_lan + 1                                        # thêm một số đo ngày hàng về


def test_quan_tri_chi_thay_goi_va_gia_han(c):
    qt = vao(c, "qt-van-hanh")
    ds = c.get("/api/quan-tri/khach", headers=qt).json()["khach"]
    assert [k["trang_thai"] for k in ds] == ["het_han", "sap_het", "con_han"]
    assert not {"gia_tri_ton", "doanh_so", "gia_von"} & set(ds[0])
    moi = c.post("/api/quan-tri/khach/kho-chi-sau/gia-han", headers=qt, json={"so_thang": 3}).json()["ngay_het_han"]
    assert moi == "2027-02-24"                                                             # đã hết hạn: tính từ hôm nay
    assert c.post("/api/quan-tri/khach/kho-chi-sau/gia-han", headers=qt, json={"so_thang": 0}).status_code == 400


class _TinNhan:
    content = '{"ung_vien": [{"ma": "a", "do_chac_chan": 0.93}], "chu_tren_nhan": "KẸO DỪA"}'


class _ClientGia:
    """Client giả thay cho dịch vụ AI: không gọi mạng."""

    class chat:                                                                            # noqa: N801
        class completions:                                                                 # noqa: N801
            @staticmethod
            def create(**kw):
                assert kw["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
                lua_chon = type("LuaChon", (), {"message": _TinNhan})
                return type("TraLoi", (), {"choices": [lua_chon]})


def test_nhan_dien_loc_ung_vien_va_khi_chua_co_khoa(c, lan, monkeypatch):
    dm = [{"ma": "a", "ten": "Kẹo dừa"}, {"ma": "b", "ten": "Bánh pía"}]
    kq = nd.loc_ung_vien({"ung_vien": [{"ma": "b", "do_chac_chan": 0.6}, {"ma": "x", "do_chac_chan": 0.99},
                                       {"ma": "a", "do_chac_chan": 0.2}]}, dm)
    assert [u["ma"] for u in kq["ung_vien"]] == ["b"] and kq["can_hoi_lai"] and not kq["khong_nhan_ra"]
    assert nd.loc_ung_vien({"ung_vien": [{"ma": "la", "do_chac_chan": 0.9}]}, dm)["khong_nhan_ra"]      # hàng lạ: không đoán
    r = nd.nhan_dien("AAAA", "image/jpeg", dm, client=_ClientGia, mo_hinh="gia")
    assert r["ung_vien"][0]["ma"] == "a" and not r["can_hoi_lai"]

    monkeypatch.setattr(nd.tl, "doc_cau_hinh", lambda: (None, "gia"))
    assert c.get("/api/ai/trang-thai", headers=lan).json() == {"san_sang": False, "mo_hinh": None}
    r = c.post("/api/nhan-dien", headers=lan, json={"anh_b64": "AAAA"}).json()
    assert r["san_sang"] is False and "tìm mặt hàng bằng tay" in r["loi"].lower()


def test_ham_sach_va_ngay(c):
    assert dv.sach({"a": float("nan"), "b": dv.doc_ngay("2026-01-05")}) == {"a": None, "b": "2026-01-05"}
    with pytest.raises(dv.LoiNhap):
        dv.doc_ngay("hôm qua")
