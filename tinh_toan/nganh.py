# -*- coding: utf-8 -*-
"""
GÓI CẤU HÌNH NGÀNH (đặc tả V1.1, mục 3.4): lõi EOQ / SS / ROP giữ nguyên, mỗi ngành chỉ thay một gói gồm
lịch sự kiện mùa vụ, tham số mặc định và ràng buộc đặc thù.

Bánh kẹo là ngành chính (có mô hình mùa vụ riêng trong loi.py). Các ngành khác là MINH HOẠ: ngày sự kiện theo
dương lịch cố định, tham số mặc định là giả định, cần người trong ngành xác nhận trước khi dùng thật.
"""
import pandas as pd

from . import loi

NAM = range(2018, 2031)


def _co_dinh(thang, ngay):
    return pd.to_datetime([f"{n}-{thang:02d}-{ngay:02d}" for n in NAM])


GOI = {
    "banh_keo": {
        "ten": "Bánh kẹo",
        "su_kien": {"Tết": loi.TET, "Trung thu": loi.TRUNG_THU},
        "mac_dinh": {"han_dung_ngay": 90, "lead_time_ngay": 2.0, "do_lech_lead_time": 0.7, "chi_phi_dat_hang": 40000,
                     "ty_le_giu_hang_nam": 0.25, "muc_phuc_vu": 0.95},
        "rang_buoc": "Hàng mùa vụ (bánh trung thu, mứt Tết) gần như không bán được sau lễ.",
        "minh_hoa": False,
    },
    "hoa_tuoi": {
        "ten": "Hoa tươi (minh hoạ)",
        "su_kien": {"14/2": _co_dinh(2, 14), "8/3": _co_dinh(3, 8), "20/10": _co_dinh(10, 20), "20/11": _co_dinh(11, 20)},
        "mac_dinh": {"han_dung_ngay": 5, "lead_time_ngay": 1.0, "do_lech_lead_time": 0.3, "chi_phi_dat_hang": 30000,
                     "ty_le_giu_hang_nam": 0.25, "muc_phuc_vu": 0.90},
        "rang_buoc": "Hạn dùng rất ngắn: lượng đặt gần như luôn bị chặn bởi trần hạn dùng.",
        "minh_hoa": True,
    },
    "van_phong_pham": {
        "ten": "Văn phòng phẩm (minh hoạ)",
        "su_kien": {"Khai giảng": _co_dinh(9, 5)},
        "mac_dinh": {"han_dung_ngay": 720, "lead_time_ngay": 3.0, "do_lech_lead_time": 1.0, "chi_phi_dat_hang": 50000,
                     "ty_le_giu_hang_nam": 0.20, "muc_phuc_vu": 0.95},
        "rang_buoc": "Nhà phân phối thường có số lượng đặt tối thiểu (MOQ) và chiết khấu số lượng: chưa xử lý.",
        "minh_hoa": True,
    },
}
MAC_DINH = "banh_keo"


def lay(ma):
    return GOI.get(ma) or GOI[MAC_DINH]


def su_kien_sap_toi(ma, hom_nay, trong_ngay=90):
    """Các sự kiện mùa vụ còn không quá `trong_ngay` ngày nữa: [(tên, số ngày còn lại)], gần nhất trước."""
    hom_nay = pd.Timestamp(hom_nay).normalize()
    ra = []
    for ten, ds in lay(ma)["su_kien"].items():
        con = [(d - hom_nay).days for d in ds if 0 <= (d - hom_nay).days <= trong_ngay]
        if con:
            ra.append((ten, min(con)))
    return sorted(ra, key=lambda x: x[1])
