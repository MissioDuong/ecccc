# -*- coding: utf-8 -*-
"""
LƯU DỮ LIỆU của SmartStock AI: MongoDB (mặc định) hoặc một file JSON (khi MongoDB tắt, và trong kiểm thử).

Hai lớp có cùng 5 hàm: tim, tim_mot, them, sua, xoa. Bộ lọc chỉ là so sánh bằng trên các trường.
`PhamVi` bọc một kho dữ liệu và TỰ GẮN `ma_kho` vào mọi lệnh đọc / ghi: tầng dịch vụ chỉ làm việc qua PhamVi nên
khách này không đọc được dữ liệu của khách khác (đặc tả V1.1, mục 5).

Các bảng: khach, tai_khoan, phien, chu_hang, nha_cung_cap, mat_hang, doanh_so, lo_hang, don_hang.
Ngày lưu dạng chuỗi "YYYY-MM-DD".
"""
import copy
import json
import os
import threading

MONGO_MAC_DINH = "mongodb://127.0.0.1:27017/smartstock_ai"     # database RIÊNG; không đụng database của dự án khác
THU_MUC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _khop(doc, loc):
    return all(doc.get(k) == v for k, v in loc.items())


class KhoTep:
    """Lưu trong bộ nhớ; nếu có `duong_dan` thì ghi ra file JSON sau mỗi thay đổi."""

    def __init__(self, duong_dan=None):
        self.duong_dan, self.khoa, self.bang = duong_dan, threading.RLock(), {}
        if duong_dan and os.path.exists(duong_dan):
            with open(duong_dan, encoding="utf-8") as f:
                self.bang = json.load(f)

    def mo_ta(self):
        return f"file {self.duong_dan}" if self.duong_dan else "bộ nhớ tạm (mất khi tắt máy chủ)"

    def _luu(self):
        if self.duong_dan:
            os.makedirs(os.path.dirname(self.duong_dan), exist_ok=True)
            tam = self.duong_dan + ".tmp"
            with open(tam, "w", encoding="utf-8") as f:
                json.dump(self.bang, f, ensure_ascii=False)
            os.replace(tam, self.duong_dan)

    def tim(self, bang, **loc):
        with self.khoa:
            return [copy.deepcopy(d) for d in self.bang.get(bang, []) if _khop(d, loc)]

    def tim_mot(self, bang, **loc):
        ds = self.tim(bang, **loc)
        return ds[0] if ds else None

    def them(self, bang, doc):
        with self.khoa:
            self.bang.setdefault(bang, []).append(copy.deepcopy(doc))
            self._luu()

    def sua(self, bang, loc, gia_tri):
        with self.khoa:
            n = 0
            for d in self.bang.get(bang, []):
                if _khop(d, loc):
                    d.update(copy.deepcopy(gia_tri))
                    n += 1
            if n:
                self._luu()
            return n

    def xoa(self, bang, **loc):
        with self.khoa:
            cu = self.bang.get(bang, [])
            self.bang[bang] = [d for d in cu if not _khop(d, loc)]
            self._luu()
            return len(cu) - len(self.bang[bang])


class KhoMongo:
    def __init__(self, uri):
        import pymongo
        self.uri = uri
        self.client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=1500)
        self.client.admin.command("ping")
        self.db = self.client.get_default_database()

    def mo_ta(self):
        return f"MongoDB, database '{self.db.name}'"

    def tim(self, bang, **loc):
        return list(self.db[bang].find(loc, {"_id": 0}))

    def tim_mot(self, bang, **loc):
        return self.db[bang].find_one(loc, {"_id": 0})

    def them(self, bang, doc):
        self.db[bang].insert_one(copy.deepcopy(doc))

    def sua(self, bang, loc, gia_tri):
        return self.db[bang].update_many(loc, {"$set": gia_tri}).matched_count

    def xoa(self, bang, **loc):
        return self.db[bang].delete_many(loc).deleted_count


def mo_kho():
    """Chọn nơi lưu: SMARTSTOCK_THU_MUC (file JSON trong thư mục đó, dùng cho test / chạy thử) →
    MongoDB (SMARTSTOCK_MONGO_URI hoặc mặc định) → file du_lieu_cua_toi/smartstock.json khi MongoDB không chạy."""
    thu_muc = os.environ.get("SMARTSTOCK_THU_MUC")
    if thu_muc:
        return KhoTep(os.path.join(thu_muc, "smartstock.json"))
    try:
        return KhoMongo(os.environ.get("SMARTSTOCK_MONGO_URI", MONGO_MAC_DINH))
    except Exception:                                        # noqa: BLE001  (MongoDB tắt hoặc thiếu pymongo)
        return KhoTep(os.path.join(THU_MUC, "du_lieu_cua_toi", "smartstock.json"))


class PhamVi:
    """Cửa sổ nhìn vào dữ liệu của MỘT khách (ma_kho). Mọi lệnh đều bị ép kèm ma_kho."""

    def __init__(self, kho, ma_kho):
        if not ma_kho:
            raise ValueError("Thiếu mã kho")
        self.kho, self.ma_kho = kho, ma_kho

    def tim(self, bang, **loc):
        return self.kho.tim(bang, **dict(loc, ma_kho=self.ma_kho))

    def tim_mot(self, bang, **loc):
        return self.kho.tim_mot(bang, **dict(loc, ma_kho=self.ma_kho))

    def them(self, bang, doc):
        self.kho.them(bang, dict(doc, ma_kho=self.ma_kho))

    def sua(self, bang, loc, gia_tri):
        gia_tri = {k: v for k, v in gia_tri.items() if k != "ma_kho"}      # không cho chuyển bản ghi sang kho khác
        return self.kho.sua(bang, dict(loc, ma_kho=self.ma_kho), gia_tri)

    def xoa(self, bang, **loc):
        return self.kho.xoa(bang, **dict(loc, ma_kho=self.ma_kho))
