# -*- coding: utf-8 -*-
"""
NHẬN DIỆN MẶT HÀNG BẰNG ẢNH (đặc tả V1.1, mục 3.3) và giải thích khuyến nghị bằng lời.

Ảnh dùng để NHẬN RA TÊN mặt hàng trong danh mục của cửa hàng, không dùng để đếm hàng. Mô hình thị giác nhìn ảnh
(kể cả chữ trên nhãn) rồi đối chiếu với danh mục; app chỉ nhận các mã có trong danh mục, tối đa 3 ứng viên.
Độ chắc chắn thấp thì hỏi lại, không tự chọn; không khớp thì báo "không nhận ra".

Lưu ý: ảnh được gửi tới dịch vụ AI bên ngoài (có chi phí theo lượt, ảnh rời khỏi máy người dùng).
Chưa có số đo độ chính xác trên ảnh thật: không được nói "nhận diện được" khi chưa đo.
LLM không tự tính số: phần giải thích chỉ diễn đạt lại các con số app đã tính.
"""
import json

from . import tro_ly as tl

NGUONG_TU_TIN = 0.80           # từ mức này app đề xuất ứng viên đầu; vẫn cần người dùng chạm xác nhận
NGUONG_NHAN_RA = 0.40          # dưới mức này coi như không nhận ra
ANH_TOI_DA = 6_000_000         # ký tự base64 (~4,5 MB)

LOI_DAN = """Bạn giúp một cửa hàng nhận ra sản phẩm trong ảnh là MẶT HÀNG NÀO trong danh mục của họ.
Danh mục (mã: tên): {danh_muc}
Nhìn bao bì và đọc chữ trên nhãn. Chỉ chọn mã CÓ trong danh mục. Nếu sản phẩm không thuộc danh mục, hoặc ảnh không rõ,
trả về danh sách rỗng: tuyệt đối không đoán bừa. Bao bì cùng hãng khác vị thì hạ độ chắc chắn.
Trả về JSON: {{"ung_vien": [{{"ma": "...", "do_chac_chan": 0.0-1.0}}], "chu_tren_nhan": "chữ đọc được trên nhãn"}}
(tối đa 3 ứng viên, độ chắc chắn giảm dần)."""


def trang_thai():
    """(đã có khoá API chưa, tên mô hình). Không bao giờ trả về khoá."""
    key, mo_hinh = tl.doc_cau_hinh()
    return bool(key), mo_hinh


def loc_ung_vien(tra_loi, danh_muc):
    """Kiểm tra câu trả lời của mô hình: bỏ mã ngoài danh mục, sắp theo độ chắc chắn, áp ngưỡng."""
    ten = {m["ma"]: m["ten"] for m in danh_muc}
    uv = []
    for u in (tra_loi or {}).get("ung_vien") or []:
        try:
            p = min(max(float(u.get("do_chac_chan", 0)), 0.0), 1.0)
        except (TypeError, ValueError):
            continue
        if u.get("ma") in ten and p >= NGUONG_NHAN_RA and u["ma"] not in {x["ma"] for x in uv}:
            uv.append({"ma": u["ma"], "ten": ten[u["ma"]], "do_chac_chan": p})
    uv = sorted(uv, key=lambda x: -x["do_chac_chan"])[:3]
    return {"ung_vien": uv, "khong_nhan_ra": not uv, "can_hoi_lai": bool(uv) and uv[0]["do_chac_chan"] < NGUONG_TU_TIN,
            "chu_tren_nhan": str((tra_loi or {}).get("chu_tren_nhan") or "")[:200]}


def nhan_dien(anh_b64, mime, danh_muc, client=None, mo_hinh=None):
    """Trả về {"san_sang", "ung_vien", "khong_nhan_ra", "can_hoi_lai", "chu_tren_nhan"} hoặc {"san_sang": False, "loi"}."""
    if not danh_muc:
        return {"san_sang": True, "ung_vien": [], "khong_nhan_ra": True, "can_hoi_lai": False, "chu_tren_nhan": "",
                "loi": "Danh mục chưa có mặt hàng nào."}
    if len(anh_b64) > ANH_TOI_DA:
        return {"san_sang": True, "loi": "Ảnh quá lớn. Hãy chụp lại hoặc chọn ảnh nhỏ hơn."}
    if client is None:
        key, mo_hinh_cfg = tl.doc_cau_hinh()
        if not key:
            return {"san_sang": False, "loi": "Chưa cấu hình khoá API cho AI nên chưa nhận diện được ảnh. Hãy tìm mặt hàng bằng tay."}
        client, mo_hinh = tl.tao_client(key), mo_hinh or mo_hinh_cfg
    loi_dan = LOI_DAN.format(danh_muc="; ".join(f"{m['ma']}: {m['ten']}" for m in danh_muc))
    try:
        r = client.chat.completions.create(
            model=mo_hinh, max_completion_tokens=300,response_format={"type": "json_object"},
            messages=[{"role": "user", "content": [{"type": "text", "text": loi_dan},
                                                   {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{anh_b64}"}}]}])
        tra_loi = json.loads(r.choices[0].message.content or "{}")
    except Exception as e:                                   # noqa: BLE001
        return {"san_sang": True, "loi": tl.loi_than_thien(e)}
    return dict(loc_ung_vien(tra_loi, danh_muc), san_sang=True)


def giai_thich(so_lieu, client=None, mo_hinh=None):
    """Diễn đạt lại một khuyến nghị bằng lời dễ hiểu, chỉ từ các con số app đã tính."""
    if client is None:
        key, mo_hinh_cfg = tl.doc_cau_hinh()
        if not key:
            return {"san_sang": False, "loi": "Chưa cấu hình khoá API cho AI."}
        client, mo_hinh = tl.tao_client(key), mo_hinh or mo_hinh_cfg
    try:
        return {"san_sang": True, "van_ban": tl.phan_tich(client, mo_hinh, "khuyến nghị đặt hàng của một mặt hàng", so_lieu)}
    except Exception as e:                                   # noqa: BLE001
        return {"san_sang": True, "loi": tl.loi_than_thien(e)}
