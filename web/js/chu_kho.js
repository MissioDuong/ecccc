// MÀN HÌNH CỦA CHỦ KHO (người dùng chính), theo đúng thứ tự công việc:
//   ① ve_nhap  ② ve_kho  ③ ve_hang  ④ ve_khuyen_nghi  ⑤ ve_don   + công cụ ve_anh (chụp ảnh nhận diện)
import { goi, e, so, tien, ngay, ngay_ngan, nhan_mau, bao, thu, mo_ngan, dong_ngan, the_ba_cau, doc_bieu_mau, tt } from "./nen_tang.js";
import { mo_chi_tiet } from "./chi_tiet.js";

const xem_chi_tiet = (el, ve_lai) => el.querySelectorAll("[data-ct]").forEach((b) => (b.onclick = () => mo_chi_tiet(b.dataset.ct, { duoc_sua: true, sau_khi_luu: ve_lai })));
const nut_ct = (m) => (m.co_du_lieu ? `<button class="nut phu2 nho" data-ct="${e(m.ma)}">Xem chi tiết và chọn mức yên tâm</button>` : "");
const dau_trang = (ten, mo_ta) => `<h1>${ten}</h1><p class="phu">${mo_ta}</p>`;
const luu_y_mau = (d) => (d.nganh.minh_hoa ? `<div class="bao canh">Ngành <b>${e(d.nganh.ten)}</b> là gói cấu hình minh hoạ: ngày sự kiện và tham số mặc định cần người trong ngành xác nhận.</div>` : "");

// ============================================================ ② TÌNH TRẠNG KHO
export async function ve_kho(el) {
  const d = await goi("/tong-quan"), k = d.kpi;
  const can_lam = d.mat_hang.filter((m) => m.mau === "do" || m.mau === "cam" || m.cau_het_han);
  el.innerHTML = `${dau_trang("Tình trạng kho", `Hôm nay ${ngay(d.hom_nay)}. Tổng quan cả kho và những việc cần làm trước.`)}
    ${luu_y_mau(d)}
    ${d.su_kien.map((s) => `<div class="bao tin">📅 <b>${e(s.ten)}</b> còn <b>${s.con_ngay} ngày</b> nữa: dự báo đã tính mức bán tăng theo mùa.</div>`).join("")}
    <div class="luoi kpi">
      <div class="the"><div class="so">${so(k.so_mat_hang)}</div><div class="nhan">Mặt hàng trong kho</div></div>
      <div class="the"><div class="so">${tien(k.gia_tri_ton)}</div><div class="nhan">Tiền vốn đang nằm trong kho</div></div>
      <div class="the"><div class="so" style="color:var(--cam)">${so(k.so_can_dat)}</div><div class="nhan">Mặt hàng nên đặt hôm nay${k.tien_can_dat ? " · " + tien(k.tien_can_dat) : ""}</div></div>
      <div class="the"><div class="so" style="color:var(--do)">${so(k.so_nguy_cap)}</div><div class="nhan">Đã hết hoặc dưới mức dự phòng</div></div>
      <div class="the"><div class="so">${so(k.so_sap_het_han)}</div><div class="nhan">Mặt hàng có lô sắp hết hạn</div></div>
      <div class="the"><div class="so">${tien(k.tien_co_the_mat)}</div><div class="nhan">Có thể mất vì hết hạn (ước tính)</div></div>
    </div>
    <h2>Việc cần làm hôm nay</h2>
    ${can_lam.length ? `<div class="luoi c2">${can_lam.map((m) => the_ba_cau(m, { nut: nut_ct(m) })).join("")}</div>
      <div class="hang-nut" style="margin-top:1rem"><a class="nut" href="#/khuyen-nghi">Sang bước ④: xem khuyến nghị đặt hàng →</a></div>`
      : `<div class="the">Hôm nay chưa có mặt hàng nào cần đặt hay cần xử lý. 👍</div>`}`;
  xem_chi_tiet(el, () => ve_kho(el));
}

// ============================================================ ③ TÌNH TRẠNG HÀNG
let loc_hang = { mau: "", chu: "" };
export async function ve_hang(el) {
  const d = await goi("/tong-quan");
  const chu = [...new Map(d.mat_hang.map((m) => [m.ma_chu_hang, m.ten_chu_hang])).entries()];
  const ds = d.mat_hang.filter((m) => (!loc_hang.mau || m.mau === loc_hang.mau) && (!loc_hang.chu || m.ma_chu_hang === loc_hang.chu));
  el.innerHTML = `${dau_trang("Tình trạng hàng", "Từng mặt hàng: của ai, còn bao nhiêu, đang về bao nhiêu, bán được mấy ngày nữa. Bấm một dòng để xem chi tiết.")}
    <div class="hang-nut"><div class="the-tab" style="margin:0">${[["", "Tất cả"], ["do", "Cần xử lý ngay"], ["cam", "Nên đặt"], ["xanh", "Ổn"]].map(([m, t]) =>
      `<button data-mau="${m}" class="${loc_hang.mau === m ? "chon" : ""}">${t}</button>`).join("")}</div>
      <select id="loc_chu" style="width:auto"><option value="">Mọi chủ hàng</option>${chu.map(([ma, ten]) => `<option value="${e(ma)}" ${loc_hang.chu === ma ? "selected" : ""}>${e(ten)}</option>`).join("")}</select></div>
    <div class="the cuon" style="margin-top:.75rem;padding:.3rem .6rem"><table>
      <tr><th>Mặt hàng</th><th>Của ai</th><th>Tình trạng</th><th class="so">Tồn</th><th class="so">Đang về</th><th class="so">Đủ bán</th><th class="so">Sắp hết hạn</th></tr>
      ${ds.map((m) => `<tr class="bam" data-ct="${e(m.ma)}" tabindex="0"><td><b>${e(m.ten)}</b></td><td>${e(m.ten_chu_hang)}</td><td>${nhan_mau(m.mau)}</td>
        <td class="so">${so(m.ton_kho)} ${e(m.don_vi)}</td><td class="so">${m.co_du_lieu && m.hang_dang_ve ? so(m.hang_dang_ve) : "–"}</td>
        <td class="so">${!m.co_du_lieu ? "–" : m.so_ngay_du_ban == null ? "lâu" : m.so_ngay_du_ban + " ngày"}</td>
        <td class="so">${m.luong_sap_het_han ? so(m.luong_sap_het_han) + " " + e(m.don_vi) : "–"}</td></tr>`).join("") || `<tr><td colspan="7" class="phu">Không có mặt hàng nào khớp bộ lọc.</td></tr>`}
    </table></div>
    <p class="phu">"Đủ bán" là số ngày dự kiến còn hàng nếu không nhập thêm. "Sắp hết hạn" là lượng hàng thuộc các lô còn dưới 20% hạn dùng.</p>`;
  el.querySelectorAll("[data-mau]").forEach((b) => (b.onclick = () => { loc_hang.mau = b.dataset.mau; ve_hang(el); }));
  el.querySelector("#loc_chu").onchange = (ev) => { loc_hang.chu = ev.target.value; ve_hang(el); };
  xem_chi_tiet(el, () => ve_hang(el));
}

// ============================================================ ④ KHUYẾN NGHỊ ĐẶT HÀNG
export async function ve_khuyen_nghi(el) {
  const d = await goi("/tong-quan");
  const nen = d.mat_hang.filter((m) => m.nen_dat), chua = d.mat_hang.filter((m) => !m.nen_dat);
  el.innerHTML = `${dau_trang("Khuyến nghị đặt hàng", "Đặt bao nhiêu, muộn nhất ngày nào, vì sao. App chỉ gợi ý; bạn xem, sửa rồi mới xác nhận.")}
    ${luu_y_mau(d)}
    <h2>Nên đặt (${nen.length})</h2>
    ${nen.length ? `<div class="luoi c2">${nen.map((m) => the_ba_cau(m, { nut: nut_ct(m) })).join("")}</div>
      <div class="the" style="margin-top:1rem"><b>Tổng tiền hàng theo gợi ý: ${tien(d.kpi.tien_can_dat)}</b>
        <p class="phu">Bước tiếp theo: gom các mặt hàng trên thành đơn nháp, mỗi nhà cung cấp một đơn. Bạn vẫn sửa được số lượng trước khi xác nhận.</p>
        <button class="nut" id="gop">Gộp thành đơn nháp theo nhà cung cấp →</button></div>`
      : `<div class="the">Hôm nay chưa có mặt hàng nào chạm mức báo đặt hàng.</div>`}
    <h2>Chưa cần đặt (${chua.length})</h2>
    <div class="luoi c2">${chua.map((m) => the_ba_cau(m, { nut: nut_ct(m) })).join("")}</div>`;
  xem_chi_tiet(el, () => ve_khuyen_nghi(el));
  const gop = el.querySelector("#gop");
  if (gop) gop.onclick = async () => {
    const r = await thu(() => goi("/don-hang/tao-nhap", { method: "POST" }));
    if (r) { bao(`Đã tạo ${r.so_don} đơn nháp`); location.hash = "#/don"; }
  };
}

// ============================================================ ⑤ ĐƠN HÀNG
const lien_ket_ncc = (d) => `${location.origin}/#/ncc/${d.ma_lien_ket}`;
async function chep(van_ban, thong_bao) {
  try { await navigator.clipboard.writeText(van_ban); bao(thong_bao); } catch { window.prompt("Hãy chép dòng dưới đây:", van_ban); }
}
function tin_nhan(d) {
  return `Chào anh/chị ${d.ten_ncc}, em là ${tt.toi.ten} (${tt.toi.kho.ten}). Em gửi đơn đặt hàng ngày ${ngay(d.ngay_dat)}:\n`
    + d.dong.map((x) => `- ${x.ten}: ${so(x.so_luong)} ${x.don_vi || ""}`).join("\n")
    + `\nAnh/chị xác nhận và báo ngày giao giúp em ở đây: ${lien_ket_ncc(d)}`;
}

export async function ve_don(el) {
  const ds = await goi("/don-hang");
  const nhap = ds.filter((d) => d.trang_thai === "nhap"), ve = ds.filter((d) => ["da_dat", "ncc_xac_nhan"].includes(d.trang_thai));
  const xong = ds.filter((d) => d.trang_thai === "da_ve" || d.trang_thai === "huy");
  const dong = (d, sua) => `<table><tr><th>Mặt hàng</th><th>Của ai</th><th class="so">Số lượng</th><th class="so">Thành tiền</th></tr>
    ${d.dong.map((x) => `<tr><td>${e(x.ten)}${sua && x.dat_muon_nhat ? `<br><small>Đặt chậm nhất ${ngay_ngan(x.dat_muon_nhat)}</small>` : ""}</td><td>${e(x.ten_chu_hang || "")}</td>
      <td class="so">${sua ? `<input class="ngan" type="number" min="0" inputmode="numeric" data-sl="${e(x.ma_mat_hang)}" value="${x.so_luong}" aria-label="Số lượng ${e(x.ten)}">` : so(x.so_luong)} ${e(x.don_vi || "")}</td>
      <td class="so">${tien(x.so_luong * x.don_gia)}</td></tr>`).join("")}
    <tr><td colspan="3"><b>Tổng</b></td><td class="so"><b>${tien(d.tong_tien)}</b></td></tr></table>`;
  el.innerHTML = `${dau_trang("Đơn hàng", "Đơn nháp → bạn xác nhận → nhà cung cấp báo ngày giao → nhận hàng. App không tự gửi đơn.")}
    <h2>Đơn nháp chờ bạn duyệt (${nhap.length})</h2>
    ${nhap.map((d) => `<div class="the" style="margin-bottom:.75rem" data-don="${e(d.ma)}"><h3>${e(d.ten_ncc)}</h3><div class="cuon">${dong(d, true)}</div>
      <div class="hang-nut" style="margin-top:.7rem"><button class="nut" data-viec="dat">Xác nhận đặt đơn này</button>
      <button class="nut phu2" data-viec="luu">Lưu số lượng đã sửa</button><button class="nut nguy" data-viec="huy">Bỏ đơn nháp</button></div></div>`).join("")
      || `<div class="the">Chưa có đơn nháp. Vào <a href="#/khuyen-nghi">Khuyến nghị đặt hàng</a> và bấm "Gộp thành đơn nháp".</div>`}
    <h2>Đang về (${ve.length})</h2>
    ${ve.map((d) => `<div class="the" style="margin-bottom:.75rem" data-don="${e(d.ma)}">
      <div class="dau-the"><h3>${e(d.ten_ncc)}</h3><span class="nhan-mau ${d.tre_hen ? "m-do" : d.trang_thai === "ncc_xac_nhan" ? "m-xanh" : "m-cam"}">${d.tre_hen ? "Trễ hẹn" : e(d.ten_trang_thai)}</span></div>
      <p>Đặt ngày ${ngay(d.ngay_dat)} · dự kiến giao <b>${ngay(d.ngay_giao_du_kien)}</b>${d.ghi_chu_ncc ? ` · Nhà cung cấp nhắn: "${e(d.ghi_chu_ncc)}"` : ""}</p>
      <div class="cuon">${dong(d, false)}</div>
      <div class="hang-nut" style="margin-top:.7rem">
        <button class="nut phu2 nho" data-viec="tin">Chép tin nhắn gửi Zalo</button><button class="nut phu2 nho" data-viec="lk">Chép liên kết cho nhà cung cấp</button>
        <a class="nut phu2 nho" style="text-decoration:none;display:inline-flex;align-items:center" href="#/ncc/${e(d.ma_lien_ket)}" target="_blank" rel="noopener">Xem như nhà cung cấp ↗</a></div>
      <div class="hang-nut" style="margin-top:.7rem"><label class="o">Hàng về ngày<input type="date" data-ngay-ve value="${e(tt.toi.hom_nay)}" min="${e(d.ngay_dat)}" max="${e(tt.toi.hom_nay)}" style="width:auto"></label>
        <button class="nut" data-viec="nhan">Đã nhận đủ hàng</button><button class="nut nguy" data-viec="huy">Huỷ đơn</button></div></div>`).join("") || `<div class="the phu">Không có đơn nào đang về.</div>`}
    <details><summary>Lịch sử (${xong.length}): nguồn số đo "số ngày hàng về"</summary><div class="cuon"><table>
      <tr><th>Nhà cung cấp</th><th>Trạng thái</th><th>Ngày đặt</th><th>Ngày về</th><th class="so">Mất</th></tr>
      ${xong.map((d) => `<tr><td>${e(d.ten_ncc)}</td><td>${e(d.ten_trang_thai)}</td><td>${ngay(d.ngay_dat)}</td><td>${ngay(d.ngay_ve)}</td>
        <td class="so">${d.ngay_ve ? Math.round((new Date(d.ngay_ve) - new Date(d.ngay_dat)) / 864e5) + " ngày" : "–"}</td></tr>`).join("")}</table></div></details>`;
  el.querySelectorAll("[data-viec]").forEach((b) => (b.onclick = async () => {
    const the = b.closest("[data-don]"), ma = the.dataset.don, d = ds.find((x) => x.ma === ma), viec = b.dataset.viec;
    const so_luong = Object.fromEntries([...the.querySelectorAll("[data-sl]")].map((i) => [i.dataset.sl, i.value]));
    if (viec === "tin") return chep(tin_nhan(d), "Đã chép tin nhắn. Dán vào Zalo để gửi.");
    if (viec === "lk") return chep(lien_ket_ncc(d), "Đã chép liên kết");
    let ok;
    if (viec === "luu") ok = await thu(() => goi(`/don-hang/${ma}`, { method: "PUT", body: { so_luong } }), "Đã lưu số lượng");
    if (viec === "dat") ok = await thu(async () => { await goi(`/don-hang/${ma}`, { method: "PUT", body: { so_luong } }); return goi(`/don-hang/${ma}/dat`, { method: "POST" }); }, "Đã xác nhận. Hàng được tính là đang về.");
    if (viec === "nhan") ok = await thu(() => goi(`/don-hang/${ma}/nhan`, { method: "POST", body: { ngay_ve: the.querySelector("[data-ngay-ve]").value } }), "Đã nhập kho và ghi ngày hàng về");
    if (viec === "huy" && window.confirm("Bỏ đơn này?")) ok = await thu(() => goi(`/don-hang/${ma}/huy`, { method: "POST" }), "Đã bỏ đơn");
    if (ok !== undefined) ve_don(el);
  }));
}

// ============================================================ ① NHẬP LIỆU
const TAB_NHAP = [["ban", "Số bán cuối ngày"], ["ton", "Tồn kho theo lô"], ["tep", "Tải file doanh số"], ["mh", "Mặt hàng"], ["ncc", "Nhà cung cấp"], ["ch", "Chủ hàng"]];
let tab_nhap = "ban", ngay_ban = null;

export async function ve_nhap(el) {
  el.innerHTML = `${dau_trang("Nhập liệu", "Khuyến nghị chỉ đúng khi số bán và tồn kho trong sổ đúng. Không có máy bán hàng vẫn dùng được: ghi nhanh cuối ngày là đủ.")}
    <div class="the-tab">${TAB_NHAP.map(([m, t]) => `<button data-tab="${m}" class="${tab_nhap === m ? "chon" : ""}">${t}</button>`).join("")}</div><div id="o_tab"></div>`;
  el.querySelectorAll("[data-tab]").forEach((b) => (b.onclick = () => { tab_nhap = b.dataset.tab; ve_nhap(el); }));
  const o = el.querySelector("#o_tab"), lai = () => ve_nhap(el);
  await { ban: tab_ban, ton: tab_ton, tep: tab_tep, mh: tab_mat_hang, ncc: tab_ncc, ch: tab_chu_hang }[tab_nhap](o, lai);
}

async function tab_ban(o, lai) {
  ngay_ban = ngay_ban || tt.toi.hom_nay;
  const d = await goi("/so-ban?ngay=" + ngay_ban);
  o.innerHTML = `<div class="the"><div class="hang-nut"><label class="o">Ngày bán<input type="date" id="ngay_ban" value="${e(ngay_ban)}" max="${e(tt.toi.hom_nay)}" style="width:auto"></label>
      <label class="hang-nut"><input type="checkbox" id="tru_ton" checked> Tự trừ tồn kho theo số bán (lấy lô gần hết hạn trước)</label></div>
    <div class="cuon"><table><tr><th>Mặt hàng</th><th class="so">Tồn trong sổ</th><th>Đã bán</th><th>Hôm đó hết hàng?</th></tr>
    ${d.dong.map((x) => `<tr data-ma="${e(x.ma)}"><td><b>${e(x.ten)}</b></td><td class="so">${so(x.ton_kho)} ${e(x.don_vi)}</td>
      <td><input class="ngan" type="number" min="0" inputmode="numeric" value="${x.so_luong ?? ""}" placeholder="chưa ghi" aria-label="Đã bán ${e(x.ten)}"> ${e(x.don_vi)}</td>
      <td><input type="checkbox" ${x.het_hang ? "checked" : ""} aria-label="${e(x.ten)} hết hàng hôm đó"></td></tr>`).join("") || `<tr><td colspan="4" class="phu">Chưa có mặt hàng. Thêm ở thẻ "Mặt hàng".</td></tr>`}</table></div>
    <div class="hang-nut" style="margin-top:.75rem"><button class="nut" id="luu_ban">Lưu số bán ngày ${ngay_ngan(ngay_ban)}</button></div>
    <p class="phu">Ô để trống = chưa ghi (app coi là thiếu số liệu, không coi là bán 0). Đánh dấu "hết hàng" để app không hiểu nhầm là khách không hỏi mua.</p></div>`;
  o.querySelector("#ngay_ban").onchange = (ev) => { ngay_ban = ev.target.value; lai(); };
  o.querySelector("#luu_ban").onclick = async () => {
    const dong = [...o.querySelectorAll("tr[data-ma]")].map((tr) => ({ ma: tr.dataset.ma, so_luong: tr.querySelector("input[type=number]").value, het_hang: tr.querySelector("input[type=checkbox]").checked }));
    const r = await thu(() => goi("/so-ban", { method: "POST", body: { ngay: ngay_ban, dong, tru_ton: o.querySelector("#tru_ton").checked } }));
    if (r) { bao(`Đã lưu ${r.so_dong} dòng. Khuyến nghị sẽ được tính lại.`); lai(); }
  };
}

async function tab_ton(o, lai) {
  const [lo, dm] = await Promise.all([goi("/lo-hang"), goi("/danh-muc")]);
  o.innerHTML = `<div class="the"><h3>Thêm lô hàng (hàng mới về, hoặc kiểm kho lần đầu)</h3>
      <form class="bieu-mau" id="f_lo"><label class="o">Mặt hàng<select name="ma_mat_hang">${dm.mat_hang.map((m) => `<option value="${e(m.ma)}">${e(m.ten)}</option>`).join("")}</select></label>
        <label class="o">Số lượng<input name="so_luong" type="number" min="0" step="any" required></label>
        <label class="o">Hạn sử dụng (để trống: tính từ hôm nay)<input name="han_su_dung" type="date"></label>
        <div style="align-self:end"><button class="nut">Thêm lô</button></div></form></div>
    <h2>Các lô đang có (${lo.length})</h2>
    <div class="the cuon" style="padding:.3rem .6rem"><table><tr><th>Mặt hàng</th><th>Hạn dùng</th><th class="so">Còn</th><th>Số lượng trong sổ</th><th></th></tr>
    ${lo.map((b) => `<tr data-lo="${e(b.ma)}"><td><b>${e(b.ten)}</b></td><td>${ngay(b.han_su_dung)}</td>
      <td class="so"><span class="nhan-mau ${b.con_ngay <= 0 ? "m-do" : b.con_ngay <= 7 ? "m-cam" : "m-xanh"}">${b.con_ngay <= 0 ? "quá hạn" : b.con_ngay + " ngày"}</span></td>
      <td><input class="ngan" type="number" min="0" step="any" value="${b.so_luong}" aria-label="Số lượng lô ${e(b.ten)}"> ${e(b.don_vi)}</td>
      <td><button class="nut phu2 nho">Lưu số đếm lại</button></td></tr>`).join("") || `<tr><td colspan="5" class="phu">Sổ tồn kho đang trống.</td></tr>`}</table></div>
    <p class="phu">Đếm lại thấy khác sổ thì sửa số rồi bấm lưu; nhập 0 để xoá lô (hàng hỏng, đã loại). Hàng nhận từ đơn ở bước ⑤ được tự thêm vào đây.</p>`;
  o.querySelector("#f_lo").onsubmit = async (ev) => {
    ev.preventDefault();
    if (await thu(() => goi("/lo-hang", { method: "POST", body: doc_bieu_mau(ev.target) }), "Đã thêm lô") !== undefined) lai();
  };
  o.querySelectorAll("tr[data-lo] button").forEach((b) => (b.onclick = async () => {
    const tr = b.closest("tr");
    if (await thu(() => goi(`/lo-hang/${tr.dataset.lo}`, { method: "PUT", body: { so_luong: tr.querySelector("input").value } }), "Đã cập nhật tồn kho") !== undefined) lai();
  }));
}

async function tab_tep(o, lai) {
  o.innerHTML = `<div class="the"><h3>Tải file doanh số (CSV hoặc Excel)</h3>
    <p>Dùng khi bạn có file xuất từ phần mềm bán hàng hoặc sổ Excel. Cần ít nhất 60 ngày; từ 1 năm trở lên thì app mới thấy được mùa Tết và Trung thu.</p>
    <div class="luoi c2"><div><b>Dạng dài</b> (mỗi dòng một mặt hàng một ngày)<div class="cong-thuc">ngay,mat_hang,so_luong_ban
2026-01-01,Kẹo dừa,18
2026-01-01,Bánh pía,10</div></div>
      <div><b>Dạng rộng</b> (mỗi cột một mặt hàng)<div class="cong-thuc">ngay,Kẹo dừa,Bánh pía
2026-01-01,18,10
2026-01-02,20,9</div></div></div>
    <p class="phu">Có thể thêm cột <code>het_hang</code> (ghi 1 hoặc x) ở dạng dài để đánh dấu ngày hết hàng. Mặt hàng trùng tên được cập nhật; tên mới được tạo thành mặt hàng mới.</p>
    <input type="file" id="tep" accept=".csv,.xlsx,.xls"><div id="kq_tep"></div></div>`;
  o.querySelector("#tep").onchange = async (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    const kq = o.querySelector("#kq_tep");
    kq.innerHTML = `<p class="phu">Đang đọc và kiểm tra file…</p>`;
    const byte = new Uint8Array(await f.arrayBuffer());
    let nhi_phan = "";
    for (let i = 0; i < byte.length; i += 8192) nhi_phan += String.fromCharCode(...byte.subarray(i, i + 8192));
    try {
      const r = await goi("/doanh-so/tai-len", { method: "POST", body: { ten_file: f.name, noi_dung_b64: btoa(nhi_phan) } });
      kq.innerHTML = `<div class="bao tin">Đã nhập <b>${so(r.so_ngay)} ngày</b> (${ngay(r.tu_ngay)} → ${ngay(r.den_ngay)}): cập nhật ${r.mat_hang_cap_nhat.length} mặt hàng, tạo mới ${r.mat_hang_moi.length}.</div>
        ${r.canh_bao.map((c) => `<div class="bao canh">${e(c)}</div>`).join("")}`;
    } catch (x) { kq.innerHTML = `<div class="bao loi"><b>File chưa nhập được.</b> ${e(x.message)}</div>`; }
  };
}

// ---------- danh mục: mặt hàng, nhà cung cấp, chủ hàng ----------
const o_nhap = (nhan, ten, gt, them = "") => `<label class="o">${nhan}<input name="${ten}" value="${e(gt ?? "")}" ${them}></label>`;

async function tab_mat_hang(o, lai) {
  const dm = await goi("/danh-muc");
  const ten = (ds, ma) => (ds.find((x) => x.ma === ma) || {}).ten || "?";
  o.innerHTML = `<div class="bao tin">Ngành: <b>${e(dm.nganh.ten)}</b> · sự kiện mùa vụ: ${dm.nganh.su_kien.map(e).join(", ")}. ${e(dm.nganh.rang_buoc)}</div>
    <div class="hang-nut"><button class="nut" id="them_mh">+ Thêm mặt hàng</button></div>
    <div class="the cuon" style="margin-top:.75rem;padding:.3rem .6rem"><table>
      <tr><th>Mặt hàng</th><th>Của ai</th><th>Nhập từ</th><th class="so">Giá vốn</th><th class="so">Hạn dùng</th><th class="so">Mức yên tâm</th><th></th></tr>
      ${dm.mat_hang.map((m) => `<tr><td><b>${e(m.ten)}</b>${m.can_bo_sung ? `<br><span class="nhan-mau m-cam">cần sửa thông số</span>` : ""}</td><td>${e(ten(dm.chu_hang, m.ma_chu_hang))}</td><td>${e(ten(dm.nha_cung_cap, m.ma_ncc))}</td>
        <td class="so">${tien(m.gia_von)}</td><td class="so">${so(m.han_dung_ngay)} ngày</td><td class="so">${so(m.muc_phuc_vu * 100)}%</td>
        <td><button class="nut phu2 nho" data-sua="${e(m.ma)}">Sửa</button></td></tr>`).join("") || `<tr><td colspan="7" class="phu">Chưa có mặt hàng nào.</td></tr>`}</table></div>`;
  const mo = (m) => {
    const md = dm.mac_dinh, ul = (m && m.uoc_luong) || ["", "", ""];
    const chon = (nhan, t, ds, gt) => `<label class="o">${nhan}<select name="${t}">${ds.map((x) => `<option value="${e(x.ma)}" ${x.ma === gt ? "selected" : ""}>${e(x.ten)}</option>`).join("")}</select></label>`;
    const ngan = mo_ngan(`<h2 style="margin-top:0">${m ? "Sửa mặt hàng" : "Thêm mặt hàng"}</h2><form id="f_mh">
      <h3>Thông tin cơ bản</h3><div class="bieu-mau">${o_nhap("Tên mặt hàng", "ten", m?.ten, "required")}${o_nhap("Đơn vị (gói, hộp, cái…)", "don_vi", m?.don_vi ?? "gói")}
        ${chon("Hàng này của ai", "ma_chu_hang", dm.chu_hang, m?.ma_chu_hang)}${chon("Nhập từ nhà cung cấp", "ma_ncc", dm.nha_cung_cap, m?.ma_ncc)}
        ${o_nhap("Giá vốn (đ)", "gia_von", m?.gia_von, 'type="number" min="1" required')}${o_nhap("Giá bán (đ)", "gia_ban", m?.gia_ban, 'type="number" min="0"')}
        ${o_nhap("Hạn dùng (ngày)", "han_dung_ngay", m?.han_dung_ngay ?? md.han_dung_ngay, 'type="number" min="1"')}${o_nhap("Quy cách (mua theo bội số)", "quy_cach", m?.quy_cach ?? 1, 'type="number" min="1"')}</div>
      <h3 style="margin-top:1rem">Chưa có số bán? Nhập ước lượng bán mỗi ngày</h3><div class="bieu-mau">
        ${o_nhap("Ngày ít nhất", "ul0", ul[0], 'type="number" min="0" step="any"')}${o_nhap("Ngày thường", "ul1", ul[1], 'type="number" min="0" step="any"')}${o_nhap("Ngày nhiều nhất", "ul2", ul[2], 'type="number" min="0" step="any"')}</div>
      <details><summary>Thông số nâng cao (có sẵn giá trị mặc định của ngành)</summary><div class="bieu-mau">
        ${o_nhap("Chi phí mỗi lần đặt hàng (đ): xe, công đi lấy", "chi_phi_dat_hang", m?.chi_phi_dat_hang ?? md.chi_phi_dat_hang, 'type="number" min="1"')}
        ${o_nhap("Tỷ lệ giữ hàng mỗi năm (0,25 = 25% giá vốn)", "ty_le_giu_hang_nam", m?.ty_le_giu_hang_nam ?? md.ty_le_giu_hang_nam, 'type="number" step="0.01" min="0.01" max="2"')}
        ${o_nhap("Mức yên tâm không hết hàng (0,5–0,999)", "muc_phuc_vu", m?.muc_phuc_vu ?? md.muc_phuc_vu, 'type="number" step="0.001" min="0.5" max="0.999"')}
        ${o_nhap("Hệ số hạn dùng (0,5–0,85): chỉ nhập lượng bán kịp trong phần này của hạn", "alpha", m?.alpha ?? 0.6, 'type="number" step="0.05" min="0.5" max="0.85"')}
        ${o_nhap("Ngân sách tối đa mỗi lần đặt (đ, để trống nếu không giới hạn)", "ngan_sach", m?.ngan_sach, 'type="number" min="0"')}
        ${o_nhap("Hàng khách đã đặt giữ", "giu_cho", m?.giu_cho ?? 0, 'type="number" min="0" step="any"')}</div></details>
      <div class="hang-nut" style="margin-top:1rem"><button class="nut">Lưu</button>${m ? `<button type="button" class="nut nguy" id="xoa_mh">Xoá mặt hàng</button>` : ""}</div></form>`);
    ngan.querySelector("#f_mh").onsubmit = async (ev) => {
      ev.preventDefault();
      const d = doc_bieu_mau(ev.target);
      d.uoc_luong = d.ul0 || d.ul1 || d.ul2 ? [d.ul0, d.ul1, d.ul2] : null;
      ["ul0", "ul1", "ul2"].forEach((k) => delete d[k]);
      const r = await thu(() => goi(m ? `/mat-hang/${m.ma}` : "/mat-hang", { method: m ? "PUT" : "POST", body: d }), "Đã lưu mặt hàng");
      if (r) { dong_ngan(); lai(); }
    };
    const xoa = ngan.querySelector("#xoa_mh");
    if (xoa) xoa.onclick = async () => {
      if (!window.confirm(`Xoá "${m.ten}" cùng toàn bộ số bán và tồn kho của nó? Không khôi phục được.`)) return;
      if (await thu(() => goi(`/mat-hang/${m.ma}`, { method: "DELETE" }), "Đã xoá") !== undefined) { dong_ngan(); lai(); }
    };
  };
  o.querySelector("#them_mh").onclick = () => (dm.chu_hang.length && dm.nha_cung_cap.length ? mo(null) : bao("Hãy thêm ít nhất một chủ hàng và một nhà cung cấp trước.", true));
  o.querySelectorAll("[data-sua]").forEach((b) => (b.onclick = () => mo(dm.mat_hang.find((m) => m.ma === b.dataset.sua))));
}

/** Bảng + biểu mẫu chung cho hai danh mục đơn giản: nhà cung cấp và chủ hàng. */
function danh_muc_don(o, lai, { ds, duong, ten_goi, cot, o_nhap_them }) {
  o.innerHTML = `<div class="hang-nut"><button class="nut" id="them">+ Thêm ${ten_goi}</button></div>
    <div class="the cuon" style="margin-top:.75rem;padding:.3rem .6rem"><table><tr><th>Tên</th>${cot.map((c) => `<th>${c[0]}</th>`).join("")}<th></th></tr>
    ${ds.map((x) => `<tr><td><b>${e(x.ten)}</b></td>${cot.map((c) => `<td>${c[1](x)}</td>`).join("")}<td><button class="nut phu2 nho" data-sua="${e(x.ma)}">Sửa</button></td></tr>`).join("") || `<tr><td colspan="9" class="phu">Chưa có ${ten_goi} nào.</td></tr>`}</table></div>`;
  const mo = (x) => {
    const ngan = mo_ngan(`<h2 style="margin-top:0">${x ? "Sửa" : "Thêm"} ${ten_goi}</h2><form><div class="bieu-mau">${o_nhap("Tên", "ten", x?.ten, "required")}${o_nhap_them(x)}</div>
      <div class="hang-nut" style="margin-top:1rem"><button class="nut">Lưu</button>${x ? `<button type="button" class="nut nguy" id="xoa">Xoá</button>` : ""}</div></form>`);
    ngan.querySelector("form").onsubmit = async (ev) => {
      ev.preventDefault();
      if (await thu(() => goi(x ? `/${duong}/${x.ma}` : `/${duong}`, { method: x ? "PUT" : "POST", body: doc_bieu_mau(ev.target) }), "Đã lưu")) { dong_ngan(); lai(); }
    };
    const xoa = ngan.querySelector("#xoa");
    if (xoa) xoa.onclick = async () => {
      if (window.confirm(`Xoá "${x.ten}"?`) && (await thu(() => goi(`/${duong}/${x.ma}`, { method: "DELETE" }), "Đã xoá")) !== undefined) { dong_ngan(); lai(); }
    };
  };
  o.querySelector("#them").onclick = () => mo(null);
  o.querySelectorAll("[data-sua]").forEach((b) => (b.onclick = () => mo(ds.find((x) => x.ma === b.dataset.sua))));
}

async function tab_ncc(o, lai) {
  const dm = await goi("/danh-muc");
  danh_muc_don(o, lai, { ds: dm.nha_cung_cap, duong: "nha-cung-cap", ten_goi: "nhà cung cấp",
    cot: [["Số ngày hàng về (bạn nhập)", (x) => `${so(x.lead_time_ngay, 1)} ± ${so(x.do_lech_lead_time, 1)} ngày`],
      ["App đang dùng", (x) => `${so(x.do_duoc.tb, 1)} ± ${so(x.do_duoc.do_lech, 1)} ngày<br><small>${x.do_duoc.so_lan ? "từ " + x.do_duoc.so_lan + " lần giao đã ghi" : "chưa có lần giao nào"}</small>`],
      ["Liên hệ", (x) => e(x.lien_he)]],
    o_nhap_them: (x) => o_nhap("Số ngày hàng về (thường)", "lead_time_ngay", x?.lead_time_ngay ?? dm.mac_dinh.lead_time_ngay, 'type="number" step="0.5" min="0.5" required')
      + o_nhap("Sớm muộn khoảng mấy ngày (±)", "do_lech_lead_time", x?.do_lech_lead_time ?? dm.mac_dinh.do_lech_lead_time, 'type="number" step="0.1" min="0"') + o_nhap("Liên hệ (Zalo, điện thoại)", "lien_he", x?.lien_he) });
  o.insertAdjacentHTML("beforeend", `<p class="phu">Mỗi lần bạn bấm "Đã nhận đủ hàng" ở bước ⑤, app ghi lại số ngày hàng về thật. Dưới 5 lần giao thì app chưa tin số đo và trộn với số bạn nhập.</p>`);
}

async function tab_chu_hang(o, lai) {
  const dm = await goi("/danh-muc");
  danh_muc_don(o, lai, { ds: dm.chu_hang, duong: "chu-hang", ten_goi: "chủ hàng",
    cot: [["Số mặt hàng gửi kho", (x) => so(dm.mat_hang.filter((m) => m.ma_chu_hang === x.ma).length)], ["Điện thoại", (x) => e(x.dien_thoai)]],
    o_nhap_them: (x) => o_nhap("Điện thoại", "dien_thoai", x?.dien_thoai) });
  o.insertAdjacentHTML("beforeend", `<p class="phu">Kho giữ hàng cho nhiều người thì mỗi mặt hàng phải ghi rõ của ai. Chủ hàng đăng nhập chỉ thấy phần hàng của mình.</p>`);
}

// ============================================================ CÔNG CỤ: CHỤP ẢNH NHẬN DIỆN
function thu_nho_anh(tep, canh = 1024) {
  return new Promise((xong, hong) => {
    const anh = new Image();
    anh.onload = () => {
      const ty = Math.min(1, canh / Math.max(anh.width, anh.height)), c = document.createElement("canvas");
      c.width = Math.round(anh.width * ty); c.height = Math.round(anh.height * ty);
      c.getContext("2d").drawImage(anh, 0, 0, c.width, c.height);
      URL.revokeObjectURL(anh.src);
      xong(c.toDataURL("image/jpeg", 0.82));
    };
    anh.onerror = () => hong(new Error("Không mở được ảnh này."));
    anh.src = URL.createObjectURL(tep);
  });
}

export async function ve_anh(el) {
  const [d, ai] = await Promise.all([goi("/tong-quan"), goi("/ai/trang-thai")]);
  el.innerHTML = `${dau_trang("Chụp ảnh nhận diện", "Không nhớ tên mặt hàng? Chụp bao bì, app nhận ra đó là mặt hàng nào rồi cho biết tồn kho và có nên đặt không. Ảnh chỉ để nhận ra tên, không dùng để đếm hàng.")}
    ${ai.san_sang ? `<div class="bao tin">AI đã sẵn sàng (${e(ai.mo_hinh)}). Ảnh được gửi tới dịch vụ AI bên ngoài, mỗi lượt có chi phí. Độ chính xác chưa được đo trên ảnh thật: luôn kiểm tra lại tên trước khi xác nhận.</div>`
      : `<div class="bao canh"><b>Chưa cấu hình khoá API cho AI</b> nên chưa nhận diện được bằng ảnh. Bạn vẫn tìm mặt hàng bằng tay ở ô bên dưới.</div>`}
    <div class="luoi c2"><div class="the"><h3>1. Chụp hoặc chọn ảnh bao bì</h3>
        <input type="file" id="anh" accept="image/*" capture="environment" ${ai.san_sang ? "" : "disabled"}><div id="xem_anh" style="margin-top:.6rem"></div></div>
      <div class="the"><h3>Hoặc tìm bằng tay</h3><input id="tim" type="search" placeholder="Gõ vài chữ trong tên mặt hàng" aria-label="Tìm mặt hàng"><div id="kq_tim" class="hang-nut" style="margin-top:.6rem"></div></div></div>
    <div id="ung_vien"></div><div id="ket_qua" style="margin-top:1rem"></div>`;
  const kq = el.querySelector("#ket_qua"), uv = el.querySelector("#ung_vien");
  const chon = (ma) => {
    const m = d.mat_hang.find((x) => x.ma === ma);
    kq.innerHTML = `<h2>3. Kết quả</h2>${the_ba_cau(m, { nut: nut_ct(m) })}<p class="phu">Tồn kho ${so(m.ton_kho)} ${e(m.don_vi)}${m.co_du_lieu && m.hang_dang_ve ? ", đang về " + so(m.hang_dang_ve) : ""}. Con số lấy từ sổ tồn kho đã lưu: sổ sai thì gợi ý sai.</p>`;
    xem_chi_tiet(kq, () => {});
    kq.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };
  const nut_mh = (m, phu = "") => `<button class="nut phu2 nho" data-chon="${e(m.ma)}">${e(m.ten)}${phu}</button>`;
  const gan = (o) => o.querySelectorAll("[data-chon]").forEach((b) => (b.onclick = () => chon(b.dataset.chon)));
  el.querySelector("#tim").oninput = (ev) => {
    const q = ev.target.value.trim().toLowerCase(), o = el.querySelector("#kq_tim");
    o.innerHTML = q ? d.mat_hang.filter((m) => m.ten.toLowerCase().includes(q)).slice(0, 8).map((m) => nut_mh(m)).join("") || `<span class="phu">Không có mặt hàng nào chứa "${e(q)}".</span>` : "";
    gan(o);
  };
  el.querySelector("#anh").onchange = async (ev) => {
    const tep = ev.target.files[0];
    if (!tep) return;
    kq.innerHTML = ""; uv.innerHTML = `<p class="phu">Đang nhận diện…</p>`;
    try {
      const url = await thu_nho_anh(tep);
      el.querySelector("#xem_anh").innerHTML = `<img class="anh-xem" src="${url}" alt="Ảnh vừa chụp">`;
      const r = await goi("/nhan-dien", { method: "POST", body: { anh_b64: url.split(",")[1], mime: "image/jpeg" } });
      if (r.loi) { uv.innerHTML = `<div class="bao loi">${e(r.loi)}</div>`; return; }
      uv.innerHTML = r.khong_nhan_ra
        ? `<div class="bao canh"><b>Không nhận ra mặt hàng này trong danh mục.</b> Có thể là hàng chưa đăng ký hoặc ảnh chưa rõ nhãn. Hãy chụp lại gần nhãn hơn, hoặc tìm bằng tay.${r.chu_tren_nhan ? ` Chữ đọc được trên nhãn: "${e(r.chu_tren_nhan)}".` : ""}</div>`
        : `<h2>2. ${r.can_hoi_lai ? "App chưa chắc. Bạn chọn giúp đúng mặt hàng" : "Có phải mặt hàng này không? Chạm để xác nhận"}</h2>
           <div class="hang-nut">${r.ung_vien.map((u) => nut_mh(u, ` · chắc ${so(u.do_chac_chan * 100)}%`)).join("")}</div>
           <p class="phu">Bao bì cùng hãng khác vị rất dễ nhầm. Không đúng mặt hàng nào thì tìm bằng tay.</p>`;
      gan(uv);
    } catch (x) { uv.innerHTML = `<div class="bao loi">${e(x.message)}</div>`; }
  };
}
