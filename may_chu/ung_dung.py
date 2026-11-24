# -*- coding: utf-8 -*-
"""
MÁY CHỦ SmartStock AI (FastAPI): điểm vào của ứng dụng web.

    python -m uvicorn may_chu.ung_dung:app --port 8600        (chạy trong thư mục aie_project)

File này CHỈ khai báo đường dẫn API, kiểm tra vai trò rồi gọi may_chu/dich_vu.py; không chứa công thức.
Mỗi yêu cầu: token → tài khoản (xac_thuc) → PhamVi(ma_kho của tài khoản) → dich_vu → JSON.

Nhóm đường dẫn:
  /api/tai-khoan-demo, /api/dang-nhap, /api/toi           đăng nhập
  /api/tong-quan, /api/mat-hang/{ma}/chi-tiet             xem (chủ kho: cả kho; chủ hàng: chỉ hàng của mình)
  /api/mat-hang, /api/nha-cung-cap, /api/chu-hang          danh mục           (chủ kho)
  /api/so-ban, /api/doanh-so/tai-len, /api/lo-hang         nhập liệu          (chủ kho)
  /api/don-hang...                                         đơn hàng           (chủ kho)
  /api/nhan-dien, /api/ai/...                              AI                 (chủ kho)
  /api/quan-tri/...                                        dashboard quản trị (quản trị)
  /api/ncc/{liên kết}                                      cổng nhà cung cấp  (không cần tài khoản)
"""
import base64
import os

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from tinh_toan import nganh
from tro_ly_ai import nhan_dien as nd

from . import dich_vu as dv
from . import du_lieu_mau, xac_thuc
from .kho_du_lieu import PhamVi, mo_kho

THU_MUC_WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")

app = FastAPI(title="SmartStock AI", docs_url="/api/docs", openapi_url="/api/openapi.json")
_kho = None


def kho():
    """Kho dữ liệu dùng chung; lần đầu mở thì nạp dữ liệu mẫu nếu còn trống."""
    global _kho
    if _kho is None:
        _kho = mo_kho()
        du_lieu_mau.nap_neu_trong(_kho)
    return _kho


@app.exception_handler(dv.LoiNhap)
async def _loi_nhap(_: Request, e: dv.LoiNhap):
    return JSONResponse({"loi": str(e)}, status_code=400)


def tai_khoan(authorization: str = Header(default="")):
    tk = xac_thuc.nguoi_dung(kho(), authorization.removeprefix("Bearer ").strip())
    if not tk:
        raise HTTPException(401, "Chưa đăng nhập hoặc phiên đã hết.")
    return tk


def can(*vai_tro):
    def kiem(tk=Depends(tai_khoan)):
        if tk["vai_tro"] not in vai_tro:
            raise HTTPException(403, "Tài khoản của bạn không có quyền làm việc này.")
        return tk
    return kiem


CHU_KHO, XEM_KHO, QUAN_TRI = can("chu_kho"), can("chu_kho", "chu_hang"), can("quan_tri")


def pv(tk):
    return PhamVi(kho(), tk["ma_kho"])


def _chi_cua_toi(tk):
    """Chủ hàng chỉ được thấy hàng của mình; chủ kho thấy cả kho."""
    return tk["ma_chu_hang"] if tk["vai_tro"] == "chu_hang" else None


# ------------------------------------------------------------------ đăng nhập
@app.get("/api/tai-khoan-demo")
def tai_khoan_demo():
    don = kho().tim_mot("don_hang", ma_lien_ket="demo-ncc-dau-moi")
    return {"tai_khoan": xac_thuc.ds_tai_khoan_demo(kho()), "lien_ket_ncc_demo": "demo-ncc-dau-moi" if don else None,
            "noi_luu": kho().mo_ta()}


@app.post("/api/dang-nhap")
def dang_nhap(d: dict = Body(...)):
    token, tk = xac_thuc.dang_nhap(kho(), d.get("ma"))
    if not token:
        raise HTTPException(401, "Không tìm thấy tài khoản.")
    return {"token": token, "tai_khoan": _thong_tin(tk)}


def _thong_tin(tk):
    khach = kho().tim_mot("khach", ma_kho=tk["ma_kho"]) if tk.get("ma_kho") else None
    ra = {"ma": tk["ma"], "ten": tk["ten"], "vai_tro": tk["vai_tro"], "ten_vai_tro": xac_thuc.TEN_VAI_TRO[tk["vai_tro"]],
          "ma_chu_hang": tk.get("ma_chu_hang"), "hom_nay": dv.chuoi_ngay(dv.hom_nay())}
    if khach:
        con = (dv.doc_ngay(khach["ngay_het_han"]) - dv.hom_nay()).days
        g = nganh.lay(khach.get("nganh"))
        ra["kho"] = {"ma_kho": khach["ma_kho"], "ten": khach["ten"], "ten_goi": dv.GOI_DICH_VU[khach["goi"]], "ngay_het_han": khach["ngay_het_han"],
                     "con_ngay": con, "nganh": khach.get("nganh"), "ten_nganh": g["ten"], "nganh_minh_hoa": g["minh_hoa"]}
    return ra


@app.get("/api/toi")
def toi(tk=Depends(tai_khoan)):
    return _thong_tin(tk)


@app.post("/api/dang-xuat")
def dang_xuat(authorization: str = Header(default="")):
    xac_thuc.dang_xuat(kho(), authorization.removeprefix("Bearer ").strip())
    return {"ok": True}


# ------------------------------------------------------------------ xem tình trạng, khuyến nghị
@app.get("/api/tong-quan")
def tong_quan(tk=Depends(XEM_KHO)):
    return dv.tong_quan(pv(tk), dv.hom_nay(), _chi_cua_toi(tk))


@app.get("/api/mat-hang/{ma}/chi-tiet")
def chi_tiet(ma: str, csl: float | None = None, tk=Depends(XEM_KHO)):
    p = pv(tk)
    mh = p.tim_mot("mat_hang", ma=ma)
    if not mh or (_chi_cua_toi(tk) and mh["ma_chu_hang"] != tk["ma_chu_hang"]):
        raise HTTPException(404, "Không tìm thấy mặt hàng.")
    return dv.chi_tiet(p, ma, dv.hom_nay(), csl)


# ------------------------------------------------------------------ danh mục (chủ kho)
@app.get("/api/danh-muc")
def danh_muc(tk=Depends(CHU_KHO)):
    p = pv(tk)
    g = nganh.lay(dv.goi_nganh(p))
    lt = {n["ma"]: dv.lead_time_ncc(p, n) for n in p.tim("nha_cung_cap")}
    return dv.sach({"mat_hang": sorted(p.tim("mat_hang"), key=lambda m: m["ten"]), "chu_hang": p.tim("chu_hang"),
                    "nha_cung_cap": [dict(n, do_duoc=lt[n["ma"]]) for n in p.tim("nha_cung_cap")],
                    "mac_dinh": g["mac_dinh"], "nganh": {"ten": g["ten"], "rang_buoc": g["rang_buoc"], "minh_hoa": g["minh_hoa"],
                                                         "su_kien": list(g["su_kien"])}})


def _crud(duong, luu, xoa):
    @app.post(f"/api/{duong}", name=f"them_{duong}")
    def them(d: dict = Body(...), tk=Depends(CHU_KHO)):
        return {"ma": luu(pv(tk), d)}

    @app.put(f"/api/{duong}/{{ma}}", name=f"sua_{duong}")
    def sua(ma: str, d: dict = Body(...), tk=Depends(CHU_KHO)):
        return {"ma": luu(pv(tk), d, ma)}

    @app.delete(f"/api/{duong}/{{ma}}", name=f"xoa_{duong}")
    def xoa_(ma: str, tk=Depends(CHU_KHO)):
        xoa(pv(tk), ma)
        return {"ok": True}


_crud("mat-hang", dv.luu_mat_hang, dv.xoa_mat_hang)
_crud("nha-cung-cap", dv.luu_nha_cung_cap, dv.xoa_nha_cung_cap)
_crud("chu-hang", dv.luu_chu_hang, dv.xoa_chu_hang)


# ------------------------------------------------------------------ nhập liệu (chủ kho)
@app.get("/api/so-ban")
def so_ban(ngay: str | None = None, tk=Depends(CHU_KHO)):
    ngay = ngay or dv.chuoi_ngay(dv.hom_nay())
    return {"ngay": ngay, "dong": dv.so_ban_ngay(pv(tk), ngay)}


@app.post("/api/so-ban")
def ghi_so_ban(d: dict = Body(...), tk=Depends(CHU_KHO)):
    n = dv.ghi_so_ban(pv(tk), d.get("ngay") or dv.hom_nay(), d.get("dong") or [], dv.hom_nay(), d.get("tru_ton", True))
    return {"so_dong": n}


@app.post("/api/doanh-so/tai-len")
def tai_len(d: dict = Body(...), tk=Depends(CHU_KHO)):
    try:
        du_lieu = base64.b64decode(d.get("noi_dung_b64") or "")
    except Exception:                                        # noqa: BLE001
        raise dv.LoiNhap("Không đọc được file tải lên.") from None
    return dv.sach(dv.tai_len_doanh_so(pv(tk), d.get("ten_file"), du_lieu))


@app.get("/api/lo-hang")
def lo_hang(tk=Depends(CHU_KHO)):
    p, hn = pv(tk), dv.hom_nay()
    ten = {m["ma"]: m for m in p.tim("mat_hang")}
    return [dict(b, ten=ten[b["ma_mat_hang"]]["ten"], don_vi=ten[b["ma_mat_hang"]]["don_vi"],
                 con_ngay=(dv.doc_ngay(b["han_su_dung"]) - hn).days) for b in dv.lo_cua(p) if b["ma_mat_hang"] in ten]


@app.post("/api/lo-hang")
def them_lo(d: dict = Body(...), tk=Depends(CHU_KHO)):
    return {"ma": dv.them_lo(pv(tk), d, dv.hom_nay())}


@app.put("/api/lo-hang/{ma}")
def sua_lo(ma: str, d: dict = Body(...), tk=Depends(CHU_KHO)):
    dv.sua_lo(pv(tk), ma, d.get("so_luong"))
    return {"ok": True}


# ------------------------------------------------------------------ đơn hàng (chủ kho)
@app.get("/api/don-hang")
def don_hang(tk=Depends(CHU_KHO)):
    return dv.sach(dv.ds_don(pv(tk), dv.hom_nay()))


@app.post("/api/don-hang/tao-nhap")
def tao_don_nhap(tk=Depends(CHU_KHO)):
    return {"so_don": dv.tao_don_nhap(pv(tk), dv.hom_nay())}


@app.put("/api/don-hang/{ma}")
def sua_don(ma: str, d: dict = Body(...), tk=Depends(CHU_KHO)):
    dv.sua_don(pv(tk), ma, d.get("so_luong") or {})
    return {"ok": True}


@app.post("/api/don-hang/{ma}/dat")
def dat_don(ma: str, tk=Depends(CHU_KHO)):
    return dv.dat_don(pv(tk), ma, dv.hom_nay())


@app.post("/api/don-hang/{ma}/nhan")
def nhan_don(ma: str, d: dict = Body(default={}), tk=Depends(CHU_KHO)):
    dv.nhan_don(pv(tk), ma, d.get("ngay_ve"), dv.hom_nay())
    return {"ok": True}


@app.post("/api/don-hang/{ma}/huy")
def huy_don(ma: str, tk=Depends(CHU_KHO)):
    dv.huy_don(pv(tk), ma)
    return {"ok": True}


# ------------------------------------------------------------------ AI (chủ kho)
@app.get("/api/ai/trang-thai")
def ai_trang_thai(tk=Depends(XEM_KHO)):
    san_sang, mo_hinh = nd.trang_thai()
    return {"san_sang": san_sang, "mo_hinh": mo_hinh if san_sang else None}


@app.post("/api/nhan-dien")
def nhan_dien(d: dict = Body(...), tk=Depends(CHU_KHO)):
    danh_muc = [{"ma": m["ma"], "ten": m["ten"]} for m in pv(tk).tim("mat_hang")]
    return nd.nhan_dien(str(d.get("anh_b64") or ""), str(d.get("mime") or "image/jpeg"), danh_muc)


@app.post("/api/ai/giai-thich")
def ai_giai_thich(d: dict = Body(...), tk=Depends(XEM_KHO)):
    ct = chi_tiet(str(d.get("ma")), None, tk)
    k = ct["ket_qua"]
    if not k.get("co_du_lieu"):
        raise dv.LoiNhap("Mặt hàng này chưa có số liệu để giải thích.")
    giu = ["ten", "don_vi", "ton_kho", "hang_dang_ve", "ss", "rop", "csl", "L", "so_luong_dat", "q", "rang_buoc", "tien_dat",
           "ngay_dat_muon_nhat", "so_ngay_du_ban", "xac_suat_het_hang", "luong_co_the_het_han", "tien_co_the_mat", "ban_7_ngay",
           "cau_tinh_trang", "cau_viec", "cau_ly_do", "ten_mo_hinh"]
    return nd.giai_thich({"khuyen_nghi": {x: k.get(x) for x in giu}, "du_lieu_mo_phong": True})


# ------------------------------------------------------------------ quản trị
@app.get("/api/quan-tri/khach")
def qt_khach(tk=Depends(QUAN_TRI)):
    return {"hom_nay": dv.chuoi_ngay(dv.hom_nay()), "khach": dv.ds_khach(kho(), dv.hom_nay()), "noi_luu": kho().mo_ta()}


@app.post("/api/quan-tri/khach/{ma_kho}/gia-han")
def qt_gia_han(ma_kho: str, d: dict = Body(...), tk=Depends(QUAN_TRI)):
    return {"ngay_het_han": dv.gia_han(kho(), ma_kho, d.get("so_thang"), dv.hom_nay())}


@app.post("/api/quan-tri/khach/{ma_kho}/da-nhac")
def qt_da_nhac(ma_kho: str, tk=Depends(QUAN_TRI)):
    dv.ghi_da_nhac(kho(), ma_kho, dv.hom_nay())
    return {"ok": True}


# ------------------------------------------------------------------ cổng nhà cung cấp (liên kết = chìa khoá)
@app.get("/api/ncc/{ma_lien_ket}")
def ncc_xem(ma_lien_ket: str):
    return dv.don_cho_ncc(kho(), ma_lien_ket)


@app.post("/api/ncc/{ma_lien_ket}/xac-nhan")
def ncc_xac_nhan(ma_lien_ket: str, d: dict = Body(...)):
    dv.ncc_xac_nhan(kho(), ma_lien_ket, d.get("ngay_giao"), d.get("ghi_chu"))
    return dv.don_cho_ncc(kho(), ma_lien_ket)


# ------------------------------------------------------------------ giao diện web (file tĩnh)
@app.get("/")
def trang_chu():
    return FileResponse(os.path.join(THU_MUC_WEB, "index.html"), headers={"Cache-Control": "no-cache"})


app.mount("/", StaticFiles(directory=THU_MUC_WEB), name="web")
