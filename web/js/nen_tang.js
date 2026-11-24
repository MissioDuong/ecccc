// NỀN TẢNG dùng chung của giao diện: gọi API, định dạng số / ngày, thông báo, ngăn kéo chi tiết.
// Mọi màn hình chỉ nói chuyện với máy chủ qua hàm goi(); không màn hình nào tự tính công thức tồn kho.

export const tt = { token: localStorage.getItem("ss_token"), toi: null };

export async function goi(duong, { method = "GET", body } = {}) {
  const r = await fetch("/api" + duong, {
    method,
    headers: { "Content-Type": "application/json", ...(tt.token ? { Authorization: "Bearer " + tt.token } : {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) {
    const loi = new Error(d.loi || d.detail || "Có lỗi xảy ra. Hãy thử lại.");
    loi.ma = r.status;
    throw loi;
  }
  return d;
}

export function dat_token(token) {
  tt.token = token;
  if (token) localStorage.setItem("ss_token", token); else localStorage.removeItem("ss_token");
}

// ---------- định dạng ----------
export const e = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export const so = (x, le = 0) => (x == null ? "–" : Number(x).toLocaleString("vi-VN", { maximumFractionDigits: le }));
export const tien = (x) => (x == null ? "–" : so(x) + " đ");
export const pt = (x, le = 0) => (x == null ? "–" : so(x * 100, le) + "%");
export const ngay = (s) => (s ? s.slice(8, 10) + "/" + s.slice(5, 7) + "/" + s.slice(0, 4) : "–");
export const ngay_ngan = (s) => (s ? s.slice(8, 10) + "/" + s.slice(5, 7) : "–");
export const TEN_MAU = { do: "Cần xử lý ngay", cam: "Nên đặt hàng", xanh: "Ổn", xam: "Chưa có số liệu" };
export const nhan_mau = (m) => `<span class="nhan-mau m-${m}">${TEN_MAU[m]}</span>`;

// ---------- thông báo ngắn ----------
export function bao(noi_dung, loi = false) {
  const el = document.createElement("div");
  if (loi) el.className = "loi";
  el.textContent = noi_dung;
  document.getElementById("thong_bao").append(el);
  setTimeout(() => el.remove(), loi ? 6000 : 3200);
}

/** Chạy một việc bất đồng bộ; lỗi thì hiện thông báo tiếng Việt thay vì im lặng. */
export async function thu(viec, thanh_cong) {
  try {
    const kq = await viec();
    if (thanh_cong) bao(thanh_cong);
    return kq;
  } catch (x) {
    bao(x.message, true);
    return undefined;
  }
}

// ---------- ngăn kéo (chi tiết mặt hàng, biểu mẫu) ----------
export function mo_ngan(html) {
  const lop = document.getElementById("lop_phu");
  lop.innerHTML = `<div class="ngan-keo" role="dialog" aria-modal="true"><div class="thanh-dong"><button class="nut phu2 nho" data-dong>Đóng ✕</button></div><div class="than-ngan">${html}</div></div>`;
  lop.onclick = (ev) => { if (ev.target === lop || ev.target.closest("[data-dong]")) dong_ngan(); };
  return lop.querySelector(".than-ngan");
}
export function dong_ngan() {
  document.getElementById("lop_phu").innerHTML = "";
}
document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") dong_ngan(); });

/** Thẻ "3 câu hỏi" của một mặt hàng: tình trạng bây giờ, việc nên làm, lý do. */
export function the_ba_cau(m, { nut = "" } = {}) {
  return `<div class="the vien-${m.mau}">
    <div class="dau-the"><div><h3>${e(m.ten)}</h3><small>${e(m.ten_chu_hang || "")}${m.ten_ncc ? " · nhập từ " + e(m.ten_ncc) : ""}</small></div>${nhan_mau(m.mau)}</div>
    <div class="ba-cau">
      <div><span class="hoi">Tình trạng</span><span>${e(m.cau_tinh_trang)}</span></div>
      <div><span class="hoi">Việc nên làm</span><span class="viec">${e(m.cau_viec)}</span></div>
      <div><span class="hoi">Vì sao</span><span>${e(m.cau_ly_do)}</span></div>
    </div>
    ${(m.canh_bao || []).map((c) => `<div class="bao canh">${e(c)}</div>`).join("")}
    ${m.cau_het_han ? `<div class="bao canh">${e(m.cau_het_han)}</div>` : ""}
    ${nut ? `<div class="hang-nut" style="margin-top:.7rem">${nut}</div>` : ""}
  </div>`;
}

export function doc_bieu_mau(form) {
  const d = {};
  for (const el of form.querySelectorAll("[name]")) d[el.name] = el.type === "checkbox" ? el.checked : el.value.trim();
  return d;
}
