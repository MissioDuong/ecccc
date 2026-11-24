// NGĂN CHI TIẾT một mặt hàng: 3 câu trả lời, rủi ro nói bằng lời, chọn "mức yên tâm" (CSL what-if),
// biểu đồ, và mục "Xem chi tiết" (công thức với số thật, bảng sai số dự báo, số ngày hàng về, lô hàng).
import { goi, e, so, tien, pt, ngay, mo_ngan, thu, the_ba_cau } from "./nen_tang.js";
import { bieu_do_ban, bieu_do_ton } from "./bieu_do.js";

const NGUON_LT = {
  mac_dinh: () => "Chưa có lần giao nào được ghi: đang dùng số bạn nhập cho nhà cung cấp.",
  co_ve_mac_dinh: (n) => `Mới có ${n} lần giao (dưới 5): trung bình được trộn với số bạn nhập; độ dao động vẫn dùng số bạn nhập vì ${n} lần là quá ít để tin.`,
  so_do: (n) => `Đo từ ${n} lần giao thực tế đã ghi.`,
};
const TEN_RANG_BUOC = { eoq: "lượng đặt tối ưu chi phí (EOQ)", han_dung: "trần hạn dùng", ngan_sach: "trần ngân sách" };

function cong_thuc(k, tp) {
  const dong = [
    `z = Φ⁻¹(${pt(k.csl)})                          = ${so(k.z, 2)}`,
    `Nhu cầu trong ${k.L} ngày chờ hàng (μ_L)        = ${so(k.mu_L, 1)}`,
    `Độ dao động trong lúc chờ (σ_L)              = ${so(k.sigma_L, 1)}`,
    `Hàng dự phòng  SS = z × σ_L                  = ${so(k.ss, 1)}`,
    `Mức báo đặt hàng  ROP = μ_L + SS             = ${so(k.rop, 1)}`,
    `Hàng khả dụng = tồn ${so(k.ton_kho)} + đang về ${so(k.hang_dang_ve)} − giữ chỗ ${so(k.giu_cho)} = ${so(k.kha_dung)}`,
    `   → ${k.nen_dat ? "khả dụng ≤ ROP: NÊN ĐẶT" : "khả dụng > ROP: chưa cần đặt"}`,
    ``,
    `EOQ = √(2 × ${so(k.nhu_cau_nam)}/năm × ${so(tp.chi_phi_dat_hang)} đ ÷ ${so(tp.ty_le_giu_hang_nam * tp.gia_von)} đ) = ${so(k.eoq)}`,
    `Trần hạn dùng = lượng bán được trong ${k.so_ngay_tran} ngày   = ${so(k.tran_han_dung)}`,
    k.tran_ngan_sach != null ? `Trần ngân sách                               = ${so(k.tran_ngan_sach)}` : null,
    `Q* = số nhỏ nhất, làm tròn theo quy cách ${so(tp.quy_cach)}    = ${so(k.q)}   (đang chặn bởi: ${TEN_RANG_BUOC[k.rang_buoc]})`,
    k.nen_dat ? `Số lượng đặt = ${k.so_don_vi_q} × Q*                       = ${so(k.so_luong_dat)}` : null,
  ];
  return dong.filter((x) => x != null).join("\n");
}

export async function mo_chi_tiet(ma, { duoc_sua = false, sau_khi_luu = null } = {}) {
  const ngan = mo_ngan(`<p class="phu">Đang tính…</p>`);
  let csl = null;

  async function ve() {
    let d;
    try { d = await goi(`/mat-hang/${ma}/chi-tiet${csl ? "?csl=" + csl : ""}`); } catch (x) { ngan.innerHTML = `<div class="bao loi">${e(x.message)}</div>`; return; }
    const k = d.ket_qua, mh = d.mat_hang, dv = mh.don_vi;
    const dong = "";
    if (!k.co_du_lieu) { ngan.innerHTML = dong + the_ba_cau(k); return; }
    const khac = csl && Math.abs(csl - mh.muc_phuc_vu) > 1e-9;
    ngan.innerHTML = `${dong}
      ${the_ba_cau(k)}
      <h2>Rủi ro, nói bằng lời</h2>
      <div class="the"><p>${e(k.cau_rui_ro)}</p><p>${e(k.cau_du_bao)}</p>
        ${k.cau_het_han ? "" : `<p class="phu">Không thấy lô nào có nguy cơ hết hạn trước khi bán kịp.</p>`}</div>

      <h2>Mức yên tâm không hết hàng</h2>
      <p class="phu">Yên tâm hơn thì phải giữ nhiều hàng dự phòng hơn, tốn thêm vốn. Bấm để thử từng mức.</p>
      <div class="muc-yt">${d.what_if.map((w) => `<button data-csl="${w.csl}" class="${Math.abs(w.csl - k.csl) < 1e-9 ? "chon" : ""}">
        <b>${pt(w.csl)}</b><small>Trong 20 lần, khoảng ${w.trong_20_lan || "dưới 1"} lần hết hàng</small><br>
        Dự phòng <b style="display:inline;font-size:1rem">${so(w.ss)}</b> ${e(dv)}<br><small>Mức báo đặt hàng ${so(w.rop)} · giữ dự phòng tốn ${tien(w.chi_phi_giu_ss_nam)}/năm</small>
        ${w.mo_phong ? `<br><small>Thử trên mô phỏng: ${pt(w.mo_phong.csl_thuc_te)} chu kỳ không hết hàng · đáp ứng ${pt(w.mo_phong.fill_rate, 1)} lượng khách hỏi</small>` : ""}
      </button>`).join("")}</div>
      ${khac ? `<div class="bao tin">Đang xem thử mức ${pt(csl)} (mức đang lưu: ${pt(mh.muc_phuc_vu)}).
        ${duoc_sua ? `<button class="nut nho" id="luu_csl">Dùng mức ${pt(csl)} cho mặt hàng này</button>` : ""}</div>` : ""}

      <h2>Đã bán và dự báo</h2>
      <div class="the">${bieu_do_ban(d.bieu_do.lich_su, d.bieu_do.du_bao)}
        <p class="phu">Cách dự báo đang dùng: <b>${e(d.du_bao.ten_mo_hinh)}</b>. ${e(d.du_bao.ghi_chu || "")}</p></div>
      <h2>Tồn kho dự kiến nếu không đặt thêm</h2>
      <div class="the">${bieu_do_ton(d.bieu_do.ton, k.rop, k.ss)}</div>

      <h2>Xem chi tiết (cho người muốn kiểm tra)</h2>
      <details><summary>Công thức với số của mặt hàng này</summary><div class="cong-thuc">${e(cong_thuc(k, d.tham_so))}</div></details>
      <details><summary>Dự báo sai bao nhiêu? (bảng WAPE)</summary>
        ${d.du_bao.wape.length ? `<table><tr><th>Cách dự báo</th><th class="so">Sai số (WAPE)</th><th></th></tr>
          ${d.du_bao.wape.map((w) => `<tr><td>${e(w.ten)}</td><td class="so">${pt(w.wape, 1)}</td><td>${w.ma === d.du_bao.mo_hinh ? "✓ đang dùng" : ""}</td></tr>`).join("")}</table>
          <p class="phu">WAPE = tổng sai lệch ÷ tổng lượng bán, đo trên 30% dữ liệu cuối mà mô hình chưa được học. Càng thấp càng tốt. App dùng cách thấp nhất; AI không tốt hơn thì không dùng AI.</p>`
        : `<p class="phu">Chưa đủ dữ liệu để đo sai số ngoài mẫu (cần khoảng 240 ngày số bán). Đã có ${so(d.du_bao.so_ngay_do)} ngày.</p>`}</details>
      <details><summary>Mức yên tâm đo trên mô phỏng</summary>
        ${d.mo_phong ? `<p>Mục tiêu: <b>${pt(d.mo_phong.csl_muc_tieu)}</b> chu kỳ không hết hàng. Chạy thử ${d.mo_phong.so_lan} lần × ${d.mo_phong.so_ngay} ngày với nhu cầu và ngày giao ngẫu nhiên:</p>
          <ul><li>Chu kỳ không hết hàng (CSL thực tế): <b>${pt(d.mo_phong.csl_thuc_te, 1)}</b> trên ${d.mo_phong.so_chu_ky} chu kỳ</li>
          <li>Lượng khách hỏi được đáp ứng (fill rate): <b>${pt(d.mo_phong.fill_rate, 1)}</b></li></ul>
          <p class="phu">Hai chỉ số này khác nhau: một chu kỳ bị tính là hết hàng dù chỉ thiếu vài ${e(dv)}. Đây là mô phỏng quanh chính dự báo của app nên có thể đẹp hơn thực tế.</p>` : `<p class="phu">Chưa đo được.</p>`}</details>
      <details><summary>Số ngày hàng về của ${e(k.ten_ncc)}</summary>
        <p>Trung bình <b>${so(d.lead_time.tb, 1)} ngày</b>, dao động ±${so(d.lead_time.do_lech, 1)} ngày. ${e(NGUON_LT[d.lead_time.nguon](d.lead_time.so_lan))}</p></details>
      <details><summary>Các lô đang có và hàng đang về</summary>
        ${d.lo.length ? `<table><tr><th>Số lượng</th><th>Hạn dùng</th><th class="so">Còn</th></tr>${d.lo.map((b) => `<tr><td>${so(b.so_luong)} ${e(dv)}</td><td>${ngay(b.han_su_dung)}</td><td class="so">${b.con_ngay} ngày</td></tr>`).join("")}</table>` : `<p class="phu">Không còn lô nào trong sổ.</p>`}
        ${d.dang_ve.map((v) => `<p>Đang về: ${so(v.so_luong)} ${e(dv)}, dự kiến ${v.sau_ngay === 0 ? "hôm nay" : "sau " + v.sau_ngay + " ngày"}.</p>`).join("")}</details>
      <details><summary>Nhờ AI giải thích bằng lời</summary>
        <p class="phu">AI chỉ diễn đạt lại các con số app đã tính, không tự tính. Nội dung được gửi tới dịch vụ AI bên ngoài.</p>
        <button class="nut phu2 nho" id="ai_gt">Giải thích khuyến nghị này</button><div id="ai_kq" style="white-space:pre-wrap;margin:.6rem 0"></div></details>`;

    ngan.querySelectorAll("[data-csl]").forEach((b) => (b.onclick = () => { csl = Number(b.dataset.csl); ve(); }));
    const luu = ngan.querySelector("#luu_csl");
    if (luu) luu.onclick = async () => {
      if (await thu(() => goi(`/mat-hang/${ma}`, { method: "PUT", body: { muc_phuc_vu: csl } }), "Đã lưu mức yên tâm mới") !== undefined) { csl = null; await ve(); if (sau_khi_luu) sau_khi_luu(); }
    };
    ngan.querySelector("#ai_gt").onclick = async (ev) => {
      const o = ngan.querySelector("#ai_kq");
      ev.target.disabled = true; o.textContent = "Đang hỏi AI…";
      const r = await thu(() => goi("/ai/giai-thich", { method: "POST", body: { ma } }));
      o.textContent = r ? (r.van_ban || r.loi || "") : "";
      ev.target.disabled = false;
    };
  }
  await ve();
}
