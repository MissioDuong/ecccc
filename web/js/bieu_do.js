// BIỂU ĐỒ SVG vẽ tay (không dùng thư viện ngoài): đã bán + dự báo có khoảng, và tồn kho dự kiến có mức báo đặt hàng.
import { ngay_ngan, so } from "./nen_tang.js";

const R = 640, C = 230, LE = { t: 14, p: 14, d: 26, tr: 44 };

function thang(n, max) {
  const x = (i) => LE.tr + (i * (R - LE.tr - LE.p)) / Math.max(1, n - 1);
  const y = (v) => C - LE.d - (v / (max || 1)) * (C - LE.t - LE.d);
  return { x, y };
}
const duong = (ds, x, y) => ds.map((v, i) => (v == null ? null : `${x(i).toFixed(1)},${y(v).toFixed(1)}`));
function net(diem) {
  let d = "", moi = true;
  for (const p of diem) { if (p == null) { moi = true; continue; } d += (moi ? "M" : "L") + p + " "; moi = false; }
  return d;
}
function truc(nhan_ngay, max, x, y) {
  const muc = [0, 0.5, 1].map((k) => max * k);
  const buoc = Math.max(1, Math.ceil(nhan_ngay.length / 6));
  return muc.map((v) => `<line x1="${LE.tr}" x2="${R - LE.p}" y1="${y(v)}" y2="${y(v)}" stroke="#dfd9cc"/><text x="${LE.tr - 6}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="#667085">${so(v)}</text>`).join("")
    + nhan_ngay.map((s, i) => (i % buoc ? "" : `<text x="${x(i)}" y="${C - 8}" text-anchor="middle" font-size="11" fill="#667085">${ngay_ngan(s)}</text>`)).join("");
}

/** Đã bán 60 ngày gần đây (xám) + dự báo 30 ngày tới (xanh) kèm khoảng "có thể sai". */
export function bieu_do_ban(lich_su, du_bao) {
  const n1 = lich_su.length, n = n1 + du_bao.length;
  const max = Math.max(1, ...lich_su.map((r) => r.ban || 0), ...du_bao.map((r) => r.cao)) * 1.08;
  const { x, y } = thang(n, max);
  const thuc = duong(lich_su.map((r) => r.ban).concat(du_bao.map(() => null)), x, y);
  const db = duong(lich_su.map(() => null).concat(du_bao.map((r) => r.d)), x, y);
  const tren = du_bao.map((r, i) => `${x(n1 + i).toFixed(1)},${y(r.cao).toFixed(1)}`);
  const duoi = du_bao.map((r, i) => `${x(n1 + i).toFixed(1)},${y(r.thap).toFixed(1)}`).reverse();
  return `<svg class="bd" viewBox="0 0 ${R} ${C}" role="img" aria-label="Đã bán và dự báo">
    ${truc(lich_su.concat(du_bao).map((r) => r.ngay), max, x, y)}
    <polygon points="${tren.concat(duoi).join(" ")}" fill="#2f6f6a" opacity=".16"/>
    <path d="${net(thuc)}" fill="none" stroke="#8a8f99" stroke-width="1.6"/>
    <path d="${net(db)}" fill="none" stroke="#2f6f6a" stroke-width="2.4"/>
    <line x1="${x(n1 - 0.5)}" x2="${x(n1 - 0.5)}" y1="${LE.t}" y2="${C - LE.d}" stroke="#b86e14" stroke-dasharray="4 4"/>
    <text x="${x(n1 - 0.5) + 5}" y="${LE.t + 10}" font-size="11" fill="#b86e14">hôm nay</text>
  </svg>
  <div class="chu-giai"><span><i style="background:#8a8f99"></i>Đã bán</span><span><i style="background:#2f6f6a"></i>Dự báo</span><span><i style="background:#2f6f6a;opacity:.3;height:.6rem"></i>Khoảng có thể dao động</span></div>`;
}

/** Tồn kho dự kiến nếu KHÔNG đặt thêm, so với mức báo đặt hàng (ROP) và hàng dự phòng (SS). */
export function bieu_do_ton(ton, rop, ss) {
  const max = Math.max(rop, ...ton.map((r) => r.ton)) * 1.12 || 1;
  const { x, y } = thang(ton.length, max);
  const ngang = (v, mau, nhan) => `<line x1="${LE.tr}" x2="${R - LE.p}" y1="${y(v)}" y2="${y(v)}" stroke="${mau}" stroke-width="1.6" stroke-dasharray="6 4"/>
    <text x="${R - LE.p - 4}" y="${y(v) - 5}" text-anchor="end" font-size="11" fill="${mau}">${nhan}: ${so(v)}</text>`;
  return `<svg class="bd" viewBox="0 0 ${R} ${C}" role="img" aria-label="Tồn kho dự kiến">
    ${truc(ton.map((r) => r.ngay), max, x, y)}
    ${ngang(rop, "#b86e14", "Mức báo đặt hàng")}${ngang(ss, "#b0443b", "Hàng dự phòng")}
    <path d="${net(duong(ton.map((r) => r.ton), x, y))}" fill="none" stroke="#2f6f6a" stroke-width="2.4"/>
  </svg>
  <div class="chu-giai"><span><i style="background:#2f6f6a"></i>Tồn kho nếu không đặt thêm</span></div>`;
}
