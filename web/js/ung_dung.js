// ĐIỂM VÀO giao diện: đăng nhập theo vai trò, khung trang, menu theo đúng trình tự công việc, định tuyến bằng #/trang.
//   #/ncc/<liên kết>  → cổng nhà cung cấp (không cần đăng nhập)
//   chưa đăng nhập    → trang chọn tài khoản, xếp các bên theo trình tự ① Quản trị → ② Chủ kho → ③ Chủ hàng → ④ Nhà cung cấp
//   đã đăng nhập      → MENU[vai trò] quyết định có những màn hình nào
import { tt, goi, dat_token, e, ngay, thu } from "./nen_tang.js";
import * as chu_kho from "./chu_kho.js";
import * as cac_ben from "./cac_ben.js";
import * as huong_dan from "./huong_dan.js";

// Mỗi mục: [mã trang, tên, số bước trong luồng (nếu có), hàm vẽ]
export const MENU = {
  chu_kho: [
    { nhom: "Làm hằng ngày, theo thứ tự", muc: [
      ["nhap", "Nhập liệu", 1, chu_kho.ve_nhap],
      ["kho", "Tình trạng kho", 2, chu_kho.ve_kho],
      ["hang", "Tình trạng hàng", 3, chu_kho.ve_hang],
      ["khuyen-nghi", "Khuyến nghị đặt hàng", 4, chu_kho.ve_khuyen_nghi],
      ["don", "Đơn hàng", 5, chu_kho.ve_don],
    ] },
    { nhom: "Công cụ", muc: [["anh", "Chụp ảnh nhận diện", "📷", chu_kho.ve_anh]] },
    { nhom: "Trợ giúp", muc: [["huong-dan", "Hướng dẫn & sơ đồ", "?", huong_dan.ve]] },
  ],
  chu_hang: [
    { nhom: "Hàng gửi kho", muc: [["hang-cua-toi", "Hàng của tôi", 1, cac_ben.ve_chu_hang]] },
    { nhom: "Trợ giúp", muc: [["huong-dan", "Hướng dẫn & sơ đồ", "?", huong_dan.ve]] },
  ],
  quan_tri: [
    { nhom: "Vận hành dịch vụ", muc: [["khach", "Khách & gia hạn", 1, cac_ben.ve_quan_tri]] },
    { nhom: "Trợ giúp", muc: [["huong-dan", "Hướng dẫn & sơ đồ", "?", huong_dan.ve]] },
  ],
};
const TRANG_DAU = { chu_kho: "kho", chu_hang: "hang-cua-toi", quan_tri: "khach" };
const goc = document.getElementById("goc");

export function di_toi(trang) {
  location.hash = "#/" + trang;
}

async function ve() {
  const [, trang, tham_so] = location.hash.split("/");
  if (trang === "ncc" && tham_so) return cac_ben.ve_nha_cung_cap(goc, tham_so);
  if (tt.token && !tt.toi) {
    try { tt.toi = await goi("/toi"); } catch { dat_token(null); }
  }
  if (!tt.toi) return ve_dang_nhap();
  const menu = MENU[tt.toi.vai_tro];
  const muc = menu.flatMap((n) => n.muc).find((m) => m[0] === trang);
  if (!muc) return di_toi(TRANG_DAU[tt.toi.vai_tro]);
  const kho = tt.toi.kho;
  goc.innerHTML = `<div class="khung">
    <header class="dau"><span class="ten">SmartStock AI</span><span class="vai">${e(tt.toi.ten_vai_tro)}</span><span class="gian"></span>
      <span class="ai">${e(tt.toi.ten)}${kho ? `<br><small>${e(kho.ten)}</small>` : ""}</span><button id="dang_xuat">Đổi tài khoản</button></header>
    <div class="giua"><nav class="menu" aria-label="Màn hình">${menu.map((n) => `<span class="nhan-nhom">${e(n.nhom)}</span>` + n.muc.map((m) =>
      `<a href="#/${m[0]}" class="${m[0] === trang ? "chon" : ""}"><span class="buoc">${m[2]}</span>${e(m[1])}</a>`).join("")).join("")}</nav>
    <main class="than" id="than">
      ${kho && kho.con_ngay <= 14 ? `<div class="bao ${kho.con_ngay < 0 ? "loi" : "canh"}">Gói ${e(kho.ten_goi)} ${kho.con_ngay < 0 ? "đã hết hạn" : "sẽ hết hạn"} ngày ${ngay(kho.ngay_het_han)}. Hãy liên hệ nhóm vận hành để gia hạn.</div>` : ""}
      <div id="noi_dung"><p class="phu">Đang tải…</p></div></main></div></div>`;
  document.getElementById("dang_xuat").onclick = async () => {
    await thu(() => goi("/dang-xuat", { method: "POST" }));
    dat_token(null); tt.toi = null; location.hash = ""; ve();
  };
  const noi_dung = document.getElementById("noi_dung");
  try {
    await muc[3](noi_dung);
  } catch (x) {
    if (x.ma === 401) { dat_token(null); tt.toi = null; return ve(); }
    noi_dung.innerHTML = `<div class="bao loi">${e(x.message)}</div>`;
  }
}

// ---------- trang đăng nhập: bố cục theo trình tự các bên ----------
const CAC_BEN = [
  { vai: "quan_tri", ten: "Quản trị dịch vụ", la_ai: "Nhóm vận hành SmartStock (bên bán dịch vụ)",
    lam: ["Xem ai đang dùng dịch vụ, gói nào", "Theo dõi ngày hết hạn, nhắc và gia hạn", "Không xem số liệu kinh doanh của khách"] },
  { vai: "chu_kho", ten: "Chủ kho / tiểu thương", la_ai: "Người dùng chính: nhập liệu và quyết định đặt hàng",
    lam: ["Ghi số bán, tồn kho, hàng đang về", "Xem tình trạng kho và từng mặt hàng", "Nhận khuyến nghị: đặt bao nhiêu, muộn nhất ngày nào", "Gộp đơn theo nhà cung cấp, nhận hàng"] },
  { vai: "chu_hang", ten: "Chủ hàng gửi kho", la_ai: "Tiểu thương gửi hàng trong kho chung",
    lam: ["Chỉ xem phần hàng của mình", "Biết hàng nào sắp hết, sắp hết hạn", "Xem khuyến nghị nhập thêm"] },
  { vai: "ncc", ten: "Nhà cung cấp", la_ai: "Đại lý, nhà phân phối: vào bằng liên kết của từng đơn",
    lam: ["Không cần tài khoản, không cần cài đặt", "Xem đơn, xác nhận và báo ngày giao", "Ngày giao giúp app đo số ngày hàng về"] },
];

async function ve_dang_nhap() {
  goc.innerHTML = `<div class="dn"><p class="phu">Đang tải…</p></div>`;
  let d;
  try { d = await goi("/tai-khoan-demo"); } catch (x) { goc.innerHTML = `<div class="dn"><div class="bao loi">${e(x.message)}</div></div>`; return; }
  goc.innerHTML = `<div class="dn">
    <div class="dn-dau"><h1>SmartStock AI</h1>
      <p>Mỗi ngày cho biết: còn bao nhiêu hàng, có cần đặt không, đặt bao nhiêu và muộn nhất ngày nào.</p>
      <p class="phu">Chọn một tài khoản mẫu để vào. Bốn bên dưới đây xếp theo đúng trình tự công việc đi qua hệ thống.</p></div>
    <div class="cac-ben">${CAC_BEN.map((b, i) => `<section class="the ben">
      <div class="hang-nut"><span class="stt">${i + 1}</span><h3>${e(b.ten)}</h3></div>
      <small>${e(b.la_ai)}</small><ul>${b.lam.map((x) => `<li>${e(x)}</li>`).join("")}</ul>
      <div class="tk">${b.vai === "ncc"
        ? (d.lien_ket_ncc_demo ? `<button class="nut phu2" data-ncc="${e(d.lien_ket_ncc_demo)}">Mở đơn mẫu<small>Đơn của Chợ đầu mối Bình Tây</small></button>` : `<small>Liên kết được tạo khi chủ kho xác nhận một đơn.</small>`)
        : d.tai_khoan.filter((t) => t.vai_tro === b.vai).map((t) => `<button class="nut" data-tk="${e(t.ma)}">${e(t.ten)}<small>${e(t.ten_kho || "Toàn dịch vụ")}</small></button>`).join("")}</div>
    </section>`).join("")}</div>
    <div class="bao tin" style="margin-top:1.2rem">Đây là bản dùng thử với <b>tài khoản mẫu, không có mật khẩu</b>. Toàn bộ dữ liệu mẫu là <b>mô phỏng</b>; giá, hạn dùng và doanh số chỉ để minh hoạ.
      Dữ liệu đang lưu ở: ${e(d.noi_luu)}.</div></div>`;
  goc.onclick = async (ev) => {
    const tk = ev.target.closest("[data-tk]"), ncc = ev.target.closest("[data-ncc]");
    if (ncc) { goc.onclick = null; location.hash = "#/ncc/" + ncc.dataset.ncc; }
    if (!tk) return;
    const kq = await thu(() => goi("/dang-nhap", { method: "POST", body: { ma: tk.dataset.tk } }));
    if (!kq) return;
    goc.onclick = null;
    dat_token(kq.token); tt.toi = kq.tai_khoan;
    const dich = "#/" + TRANG_DAU[tt.toi.vai_tro];
    if (location.hash === dich) ve(); else location.hash = dich;
  };
}

window.addEventListener("hashchange", ve);
ve();
