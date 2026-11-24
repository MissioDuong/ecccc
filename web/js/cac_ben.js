// MÀN HÌNH CỦA CÁC BÊN CÒN LẠI:
//   ve_chu_hang      chủ hàng gửi kho: chỉ XEM phần hàng của mình
//   ve_quan_tri      bên bán dịch vụ: khách, hạn gói, nhắc và gia hạn (không có số liệu kinh doanh của khách)
//   ve_nha_cung_cap  cổng nhà cung cấp qua liên kết: xác nhận đơn và ngày giao, không cần tài khoản
import { goi, e, so, tien, ngay, thu, the_ba_cau, tt } from "./nen_tang.js";
import { mo_chi_tiet } from "./chi_tiet.js";

export async function ve_chu_hang(el) {
  const d = await goi("/tong-quan"), k = d.kpi;
  el.innerHTML = `<h1>Hàng của tôi</h1><p class="phu">Hôm nay ${ngay(d.hom_nay)}. Bạn chỉ thấy phần hàng mình gửi ở ${e(tt.toi.kho.ten)}. Muốn sửa số liệu hay đặt hàng, hãy báo chủ kho.</p>
    <div class="luoi kpi">
      <div class="the"><div class="so">${so(k.so_mat_hang)}</div><div class="nhan">Mặt hàng của tôi</div></div>
      <div class="the"><div class="so">${tien(k.gia_tri_ton)}</div><div class="nhan">Tiền vốn đang nằm trong kho</div></div>
      <div class="the"><div class="so" style="color:var(--cam)">${so(k.so_can_dat)}</div><div class="nhan">Mặt hàng nên nhập thêm</div></div>
      <div class="the"><div class="so">${tien(k.tien_co_the_mat)}</div><div class="nhan">Có thể mất vì hết hạn (ước tính)</div></div>
    </div>
    <h2>Từng mặt hàng</h2>
    <div class="luoi c2">${d.mat_hang.map((m) => the_ba_cau(m, { nut: m.co_du_lieu ? `<button class="nut phu2 nho" data-ct="${e(m.ma)}">Xem chi tiết</button>` : "" })).join("")
      || `<div class="the">Bạn chưa có mặt hàng nào trong kho này.</div>`}</div>`;
  el.querySelectorAll("[data-ct]").forEach((b) => (b.onclick = () => mo_chi_tiet(b.dataset.ct)));
}

const TT_GOI = { het_han: ["m-do", "Đã hết hạn"], sap_het: ["m-cam", "Sắp hết hạn"], con_han: ["m-xanh", "Còn hạn"] };

export async function ve_quan_tri(el) {
  const d = await goi("/quan-tri/khach"), ds = d.khach;
  const dem = (t) => ds.filter((k) => k.trang_thai === t).length;
  el.innerHTML = `<h1>Khách & gia hạn</h1><p class="phu">Hôm nay ${ngay(d.hom_nay)}. Ai đang dùng dịch vụ, gói nào, khi nào hết hạn. Bản đầu chưa có thanh toán: nhắc và gia hạn làm bằng tay.</p>
    <div class="luoi kpi">
      <div class="the"><div class="so">${ds.length}</div><div class="nhan">Khách đang có</div></div>
      <div class="the"><div class="so" style="color:var(--cam)">${dem("sap_het")}</div><div class="nhan">Hết hạn trong 14 ngày tới</div></div>
      <div class="the"><div class="so" style="color:var(--do)">${dem("het_han")}</div><div class="nhan">Đã hết hạn</div></div>
    </div>
    <h2>Danh sách khách (cần gia hạn xếp trước)</h2>
    <div class="the cuon" style="padding:.3rem .6rem"><table>
      <tr><th>Khách</th><th>Ngành</th><th>Gói</th><th>Hết hạn</th><th>Trạng thái</th><th class="so">Tài khoản</th><th class="so">Mặt hàng</th><th>Gia hạn</th></tr>
      ${ds.map((k) => `<tr data-kho="${e(k.ma_kho)}"><td><b>${e(k.ten)}</b><br><small>${e(k.chu)}</small></td><td>${e(k.nganh)}</td><td>${e(k.ten_goi)}</td>
        <td>${ngay(k.ngay_het_han)}<br><small>${k.con_ngay < 0 ? "quá " + -k.con_ngay + " ngày" : "còn " + k.con_ngay + " ngày"}</small></td>
        <td><span class="nhan-mau ${TT_GOI[k.trang_thai][0]}">${TT_GOI[k.trang_thai][1]}</span>${k.da_nhac ? `<br><small>Đã nhắc ${ngay(k.da_nhac)}</small>` : ""}</td>
        <td class="so">${k.so_tai_khoan}</td><td class="so">${k.so_mat_hang}</td>
        <td><div class="hang-nut"><select aria-label="Số tháng gia hạn cho ${e(k.ten)}" style="width:auto;min-height:36px"><option value="1">1 tháng</option><option value="3">3 tháng</option><option value="6">6 tháng</option><option value="12">12 tháng</option></select>
          <button class="nut nho" data-viec="gia_han">Gia hạn</button>${k.trang_thai !== "con_han" ? `<button class="nut phu2 nho" data-viec="nhac">Đã nhắc</button>` : ""}</div></td></tr>`).join("")}
    </table></div>
    <div class="bao tin" style="margin-top:1rem"><b>Quyền riêng tư:</b> màn hình này chỉ có thông tin gói dịch vụ và số lượng tài khoản, mặt hàng. Doanh số, tồn kho và giá của khách là dữ liệu nhạy cảm; quản trị không xem được nếu khách chưa cho phép.
      <br>Dữ liệu đang lưu ở: ${e(d.noi_luu)}.</div>`;
  el.querySelectorAll("[data-viec]").forEach((b) => (b.onclick = async () => {
    const tr = b.closest("tr"), ma = tr.dataset.kho;
    const ok = b.dataset.viec === "gia_han"
      ? await thu(() => goi(`/quan-tri/khach/${ma}/gia-han`, { method: "POST", body: { so_thang: tr.querySelector("select").value } }), "Đã gia hạn")
      : await thu(() => goi(`/quan-tri/khach/${ma}/da-nhac`, { method: "POST" }), "Đã ghi nhận đã nhắc khách");
    if (ok !== undefined) ve_quan_tri(el);
  }));
}

export async function ve_nha_cung_cap(goc, ma_lien_ket) {
  goc.onclick = null;
  goc.innerHTML = `<div class="khung"><header class="dau"><span class="ten">SmartStock AI</span><span class="vai">Cổng nhà cung cấp</span><span class="gian"></span>
    <button id="ve_dau">Về trang đầu</button></header><main class="than" id="ncc" style="max-width:720px"><p class="phu">Đang tải đơn…</p></main></div>`;
  goc.querySelector("#ve_dau").onclick = () => { location.hash = ""; };
  const el = goc.querySelector("#ncc");
  let d;
  try { d = await goi("/ncc/" + encodeURIComponent(ma_lien_ket)); } catch (x) { el.innerHTML = `<div class="bao loi">${e(x.message)}</div>`; return; }
  const ve = () => {
    const cho = d.trang_thai === "da_dat" || d.trang_thai === "ncc_xac_nhan";
    el.innerHTML = `<h1>Đơn đặt hàng gửi ${e(d.ten_ncc)}</h1><p class="phu">Từ <b>${e(d.ten_khach)}</b>, đặt ngày ${ngay(d.ngay_dat)}. Bạn không cần tài khoản: liên kết này chỉ mở đúng một đơn.</p>
      <div class="the"><div class="dau-the"><h3>Hàng cần giao</h3><span class="nhan-mau ${d.trang_thai === "ncc_xac_nhan" || d.trang_thai === "da_ve" ? "m-xanh" : d.trang_thai === "huy" ? "m-do" : "m-cam"}">${e(d.ten_trang_thai)}</span></div>
        <table><tr><th>Mặt hàng</th><th class="so">Số lượng</th></tr>${d.dong.map((x) => `<tr><td>${e(x.ten)}</td><td class="so"><b>${so(x.so_luong)}</b> ${e(x.don_vi)}</td></tr>`).join("")}</table></div>
      ${cho ? `<div class="the" style="margin-top:.75rem"><h3>${d.trang_thai === "ncc_xac_nhan" ? "Đổi ngày giao (nếu cần)" : "Xác nhận đơn và báo ngày giao"}</h3>
        <form class="bieu-mau"><label class="o">Ngày giao được<input type="date" name="ngay_giao" value="${e(d.ngay_giao_du_kien)}" min="${e(d.ngay_dat)}" required></label>
          <label class="o">Lời nhắn (thiếu hàng, đổi mẫu…)<input name="ghi_chu" maxlength="300" value="${e(d.ghi_chu_ncc)}"></label>
          <div style="align-self:end"><button class="nut">${d.trang_thai === "ncc_xac_nhan" ? "Cập nhật" : "Xác nhận nhận đơn"}</button></div></form>
        <p class="phu">Ngày giao bạn báo giúp bên mua biết hàng về lúc nào, để không đặt trùng và không hết hàng.</p></div>`
        : `<div class="bao tin">${d.trang_thai === "da_ve" ? `Hàng đã được nhận ngày ${ngay(d.ngay_ve)}. Cảm ơn bạn.` : "Đơn này đã đóng, không cần làm gì thêm."}</div>`}`;
    const f = el.querySelector("form");
    if (f) f.onsubmit = async (ev) => {
      ev.preventDefault();
      const r = await thu(() => goi(`/ncc/${encodeURIComponent(ma_lien_ket)}/xac-nhan`, { method: "POST", body: { ngay_giao: f.ngay_giao.value, ghi_chu: f.ghi_chu.value } }), "Đã gửi xác nhận cho bên mua");
      if (r) { d = r; ve(); }
    };
  };
  ve();
}
