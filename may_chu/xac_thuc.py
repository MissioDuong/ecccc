# -*- coding: utf-8 -*-
"""
ĐĂNG NHẬP VÀ VAI TRÒ.

Bản này dùng TÀI KHOẢN DEMO: chọn một tài khoản mẫu là vào, không có mật khẩu (app không tự lưu mật khẩu,
đúng đặc tả V1.1 mục 5). Khi triển khai thật, thay `dang_nhap` bằng dịch vụ xác thực có sẵn (Google, Zalo,
Supabase...): dịch vụ đó trả về danh tính, hàm này chỉ còn việc tìm tài khoản tương ứng và cấp phiên.
Phần còn lại của app chỉ dùng `nguoi_dung(token)` nên không phải sửa.

Vai trò:
  quan_tri  : bên bán dịch vụ; xem danh sách khách và hạn gói, KHÔNG xem số liệu kinh doanh của khách
  chu_kho   : người dùng chính (tiểu thương / chủ kho); toàn quyền trong kho của mình
  chu_hang  : người gửi hàng trong kho; chỉ XEM phần hàng của mình
  (nhà cung cấp không có tài khoản: vào bằng liên kết của từng đơn hàng)
"""
import os
import secrets

TEN_VAI_TRO = {"quan_tri": "Quản trị dịch vụ", "chu_kho": "Chủ kho (người dùng chính)", "chu_hang": "Chủ hàng gửi kho"}


def che_do_demo():
    return os.environ.get("SMARTSTOCK_DEMO", "1") != "0"


def ds_tai_khoan_demo(kho):
    khach = {k["ma_kho"]: k["ten"] for k in kho.tim("khach")}
    return [{"ma": t["ma"], "ten": t["ten"], "vai_tro": t["vai_tro"], "ten_vai_tro": TEN_VAI_TRO[t["vai_tro"]],
             "ten_kho": khach.get(t.get("ma_kho"), "")} for t in kho.tim("tai_khoan")] if che_do_demo() else []


def dang_nhap(kho, ma_tai_khoan):
    """Cấp phiên cho một tài khoản demo. Trả về (token, tài khoản) hoặc (None, None)."""
    tk = kho.tim_mot("tai_khoan", ma=ma_tai_khoan) if che_do_demo() else None
    if not tk:
        return None, None
    token = secrets.token_urlsafe(24)
    kho.them("phien", {"token": token, "ma_tai_khoan": tk["ma"]})
    return token, tk


def nguoi_dung(kho, token):
    phien = kho.tim_mot("phien", token=token) if token else None
    return kho.tim_mot("tai_khoan", ma=phien["ma_tai_khoan"]) if phien else None


def dang_xuat(kho, token):
    kho.xoa("phien", token=token)
