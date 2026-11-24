// HƯỚNG DẪN & SƠ ĐỒ: mọi thứ ở đây là sơ đồ bấm được. Bấm một ô → hiện cách dùng / giải thích chi tiết của ô đó.
//   1. Cách dùng theo từng bước   (theo vai trò đang đăng nhập)
//   2. Luồng giữa các bên         (4 bên + hệ thống)
//   3. App tính thế nào           (dữ liệu → dự báo → SS, ROP, Q* → khuyến nghị → người duyệt)
//   4. Sơ đồ mã nguồn             (các tầng và file; muốn sửa gì thì vào đâu)
import { e, tt } from "./nen_tang.js";

// ---------------------------------------------------------------- 1. cách dùng theo vai trò
const BUOC = {
  chu_kho: [
    { ten: "Thiết lập lần đầu", ngan: "Làm một lần", trang: "nhap", muc_dich: "Khai báo kho của bạn để app có thứ để tính. Chỉ làm một lần, sau đó sửa khi có thay đổi.",
      buoc: ["Mở <b>Nhập liệu › Chủ hàng</b>: thêm từng người gửi hàng trong kho (kể cả chính bạn).",
        "Mở <b>Nhập liệu › Nhà cung cấp</b>: thêm nơi bạn lấy hàng, hàng thường về sau mấy ngày, sớm muộn khoảng mấy ngày.",
        "Mở <b>Nhập liệu › Mặt hàng</b>: thêm từng mặt hàng với giá vốn, hạn dùng, của ai, nhập từ đâu.",
        "Có file doanh số cũ thì tải lên ở <b>Tải file doanh số</b>. Chưa có thì nhập <b>ước lượng bán mỗi ngày</b> (ít nhất, thường, nhiều nhất) trong biểu mẫu mặt hàng.",
        "Mở <b>Tồn kho theo lô</b>: đếm hàng đang có và thêm thành lô kèm hạn sử dụng."],
      luu_y: "Mặt hàng tạo tự động từ file sẽ mang giá và hạn dùng mặc định, có nhãn “cần sửa thông số”. Sửa ngay, nếu không lượng đặt gợi ý sẽ sai." },
    { ten: "Nhập liệu", ngan: "Mỗi tối, vài phút", trang: "nhap", muc_dich: "Giữ cho sổ bán và sổ tồn kho đúng. Đây là việc duy nhất phải làm đều mỗi ngày.",
      buoc: ["Mở <b>Nhập liệu › Số bán cuối ngày</b>, chọn đúng ngày.", "Gõ số đã bán của từng mặt hàng. Mặt hàng nào không ghi thì để trống, đừng gõ 0 nếu bạn không chắc.",
        "Hôm đó hết hàng giữa chừng thì đánh dấu <b>Hôm đó hết hàng</b>: app sẽ không hiểu nhầm là khách không hỏi mua.",
        "Bấm <b>Lưu</b>. App tự trừ tồn kho, lấy lô gần hết hạn trước.", "Thỉnh thoảng đếm lại hàng thật và sửa ở <b>Tồn kho theo lô</b> nếu lệch sổ."],
      luu_y: "Quên ghi từ 2 ngày trở lên, app sẽ cảnh báo trên từng mặt hàng vì tồn kho trong sổ có thể không còn đúng." },
    { ten: "Tình trạng kho", ngan: "Nhìn 10 giây", trang: "kho", muc_dich: "Biết ngay hôm nay kho có vấn đề gì trước khi đi vào từng mặt hàng.",
      buoc: ["Đọc 6 ô số: bao nhiêu tiền vốn nằm trong kho, mấy mặt hàng nên đặt, mấy mặt hàng đã hết hoặc dưới mức dự phòng, có thể mất bao nhiêu vì hết hạn.",
        "Xem dòng lịch mùa vụ (ví dụ “Tết còn 74 ngày”): dự báo đã tính mức bán tăng.", "Mục <b>Việc cần làm hôm nay</b> liệt kê các mặt hàng đỏ và cam, mỗi mặt hàng một thẻ 3 câu."],
      luu_y: "Màu đỏ: hết hàng hoặc dưới mức dự phòng. Màu cam: đã tới mức báo đặt hàng. Màu xanh: ổn." },
    { ten: "Tình trạng hàng", ngan: "Khi cần tra cứu", trang: "hang", muc_dich: "Tra từng mặt hàng: của ai, còn bao nhiêu, đang về bao nhiêu, bán được mấy ngày nữa.",
      buoc: ["Lọc theo màu hoặc theo chủ hàng ở đầu trang.", "Cột <b>Đủ bán</b> là số ngày dự kiến còn hàng nếu không nhập thêm.",
        "Cột <b>Sắp hết hạn</b> là lượng hàng thuộc các lô còn dưới 20% hạn dùng: nên bày ra trước hoặc bán kèm.", "Bấm vào một dòng để mở chi tiết mặt hàng đó."],
      luu_y: "Không nhớ tên mặt hàng? Dùng công cụ Chụp ảnh nhận diện." },
    { ten: "Khuyến nghị đặt hàng", ngan: "Quyết định", trang: "khuyen-nghi", muc_dich: "Trả lời ba câu cho mỗi mặt hàng: tình trạng bây giờ, việc nên làm, vì sao.",
      buoc: ["Đọc thẻ của từng mặt hàng trong mục <b>Nên đặt</b>: “Nên đặt 120 hộp, đặt chậm nhất ngày 18/01”.",
        "Bấm <b>Xem chi tiết và chọn mức yên tâm</b> để thử ba mức 90%, 95%, 99%: yên tâm hơn thì giữ nhiều hàng dự phòng hơn, tốn thêm bao nhiêu mỗi năm.",
        "Trong chi tiết có câu rủi ro nói bằng lời (“trong 20 lần khoảng 1 lần hết hàng”) và khoảng dự báo bán mỗi ngày.",
        "Muốn kiểm tra con số: mở <b>Xem chi tiết</b> để thấy công thức với số thật, bảng sai số dự báo và kết quả mô phỏng.",
        "Đồng ý thì bấm <b>Gộp thành đơn nháp theo nhà cung cấp</b>."],
      luu_y: "App chỉ gợi ý. Dự báo có thể sai, nhất là khi dữ liệu dưới một năm hoặc sổ tồn kho không đúng." },
    { ten: "Đơn hàng", ngan: "Đặt và nhận", trang: "don", muc_dich: "Biến gợi ý thành đơn thật, theo dõi hàng về và đo số ngày hàng về của từng nhà cung cấp.",
      buoc: ["Mục <b>Đơn nháp</b>: sửa số lượng nếu muốn, rồi bấm <b>Xác nhận đặt đơn này</b>. Từ lúc đó hàng được tính là đang về.",
        "Bấm <b>Chép tin nhắn gửi Zalo</b> và dán cho nhà cung cấp. Tin nhắn có sẵn liên kết để họ xác nhận và báo ngày giao.",
        "Khi nhà cung cấp xác nhận, đơn chuyển sang “Nhà cung cấp đã xác nhận” với ngày giao họ báo.",
        "Hàng về: chọn ngày về thật rồi bấm <b>Đã nhận đủ hàng</b>. App tạo lô tồn kho mới và ghi lại số ngày hàng về."],
      luu_y: "App không tự gửi đơn. Sau khoảng 5 lần giao, số ngày hàng về sẽ dùng số đo thật thay cho số bạn nhập." },
    { ten: "Chụp ảnh nhận diện", ngan: "Công cụ phụ", trang: "anh", muc_dich: "Không nhớ tên hay mã mặt hàng: chụp bao bì để app nhận ra rồi tra tồn kho và khuyến nghị.",
      buoc: ["Bấm chọn ảnh rồi chụp rõ nhãn sản phẩm.", "App đưa tối đa 3 ứng viên kèm độ chắc chắn. Chạm vào đúng mặt hàng để xác nhận.",
        "App chưa chắc thì sẽ hỏi lại; không khớp thì báo “không nhận ra” thay vì đoán.", "Sau khi chọn, thẻ 3 câu của mặt hàng hiện ra ngay bên dưới."],
      luu_y: "Ảnh chỉ để nhận ra tên, không đếm hàng. Ảnh được gửi tới dịch vụ AI bên ngoài và cần khoá API; chưa có khoá thì dùng ô tìm bằng tay." },
  ],
  chu_hang: [
    { ten: "Mở Hàng của tôi", ngan: "Bắt đầu", trang: "hang-cua-toi", muc_dich: "Xem phần hàng bạn gửi trong kho chung. Bạn không thấy hàng của người khác.",
      buoc: ["Đăng nhập bằng tài khoản chủ hàng.", "Bốn ô số ở trên cho biết: mấy mặt hàng, bao nhiêu vốn nằm kho, mấy mặt hàng nên nhập thêm, có thể mất bao nhiêu vì hết hạn."], luu_y: "" },
    { ten: "Đọc thẻ 3 câu", ngan: "Mỗi mặt hàng", trang: "hang-cua-toi", muc_dich: "Mỗi mặt hàng có một thẻ trả lời: tình trạng bây giờ, việc nên làm, vì sao.",
      buoc: ["Màu đỏ: đã hết hoặc dưới mức dự phòng. Màu cam: nên nhập thêm. Màu xanh: ổn.", "Dòng <b>Việc nên làm</b> cho biết nên nhập bao nhiêu và chậm nhất ngày nào.", "Ô vàng (nếu có) báo lượng hàng có thể hết hạn trước khi bán kịp."], luu_y: "" },
    { ten: "Xem chi tiết", ngan: "Khi muốn hiểu", trang: "hang-cua-toi", muc_dich: "Hiểu vì sao app gợi ý như vậy.",
      buoc: ["Bấm <b>Xem chi tiết</b> trên thẻ.", "Thử ba mức yên tâm 90%, 95%, 99% để thấy hàng dự phòng thay đổi thế nào.", "Xem biểu đồ đã bán, dự báo và tồn kho dự kiến."], luu_y: "Bạn chỉ xem thử mức yên tâm, không lưu được; người lưu là chủ kho." },
    { ten: "Báo chủ kho", ngan: "Ngoài app", trang: "hang-cua-toi", muc_dich: "Chủ hàng chỉ có quyền xem. Mọi thay đổi do chủ kho thực hiện.",
      buoc: ["Số tồn không đúng với thực tế: báo chủ kho kiểm và sửa sổ.", "Muốn nhập thêm theo gợi ý: báo chủ kho đưa vào đơn của nhà cung cấp."], luu_y: "" },
  ],
  quan_tri: [
    { ten: "Xem danh sách khách", ngan: "Mỗi ngày", trang: "khach", muc_dich: "Biết ai đang dùng dịch vụ, gói nào, bao giờ hết hạn.",
      buoc: ["Ba ô số trên cùng: tổng số khách, số khách hết hạn trong 14 ngày, số khách đã hết hạn.", "Bảng xếp khách cần gia hạn lên trước."], luu_y: "" },
    { ten: "Nhắc khách", ngan: "Thủ công", trang: "khach", muc_dich: "Bản đầu chưa có thanh toán tự động: nhắc khách qua Zalo hoặc điện thoại.",
      buoc: ["Liên hệ khách đang ở trạng thái “Sắp hết hạn” hoặc “Đã hết hạn”.", "Bấm <b>Đã nhắc</b> để ghi lại ngày nhắc, tránh nhắc trùng."], luu_y: "" },
    { ten: "Gia hạn", ngan: "Khi khách đồng ý", trang: "khach", muc_dich: "Kéo dài ngày hết hạn của gói.",
      buoc: ["Chọn số tháng (1, 3, 6 hoặc 12).", "Bấm <b>Gia hạn</b>. Gói còn hạn thì cộng tiếp vào ngày hết hạn cũ; đã hết hạn thì tính từ hôm nay."], luu_y: "" },
    { ten: "Tôn trọng dữ liệu khách", ngan: "Nguyên tắc", trang: "khach", muc_dich: "Doanh số, tồn kho và giá là dữ liệu nhạy cảm của tiểu thương.",
      buoc: ["Màn hình quản trị chỉ có thông tin gói và số lượng tài khoản, mặt hàng.", "Tài khoản quản trị bị chặn ở mọi đường dẫn đọc số liệu kinh doanh."], luu_y: "" },
  ],
};

// ---------------------------------------------------------------- 2. luồng giữa các bên
const LAN = [
  { ten: "① Quản trị", phu: "bên bán dịch vụ", nut: [
    ["Mở gói cho khách", "Tạo khách mới với một gói (dùng thử, cơ bản, nâng cao) và ngày hết hạn. Mỗi khách là một kho riêng; dữ liệu các kho tách hẳn nhau bằng mã kho."],
    ["Theo dõi hạn gói", "Dashboard xếp khách sắp hết hạn lên trước. Quản trị không đọc được doanh số hay tồn kho của khách."],
    ["Nhắc và gia hạn", "Nhắc thủ công rồi gia hạn theo số tháng. Bản đầu chưa làm thanh toán."]] },
  { ten: "② Chủ kho", phu: "người dùng chính", nut: [
    ["Nhập liệu", "Ghi số bán cuối ngày, tải file doanh số, cập nhật tồn kho theo lô. Mỗi mặt hàng ghi rõ của chủ hàng nào."],
    ["Xem tình trạng", "Tình trạng kho (tổng quan) và tình trạng từng mặt hàng với màu xanh, cam, đỏ."],
    ["Nhận khuyến nghị", "Mỗi mặt hàng: đặt bao nhiêu, muộn nhất ngày nào, vì sao. Thử mức yên tâm 90 / 95 / 99%."],
    ["Duyệt và đặt đơn", "Gộp theo nhà cung cấp thành đơn nháp, sửa số lượng, xác nhận. App không tự gửi đơn."],
    ["Nhận hàng", "Ghi ngày hàng về: tạo lô tồn kho mới và thêm một số đo “số ngày hàng về” cho nhà cung cấp."]] },
  { ten: "③ Chủ hàng", phu: "gửi hàng trong kho", nut: [
    ["Xem hàng của mình", "Chỉ thấy các mặt hàng mang tên mình: tồn kho, màu trạng thái, lô sắp hết hạn."],
    ["Xem gợi ý nhập thêm", "Đọc cùng khuyến nghị mà chủ kho thấy, nhưng chỉ ở chế độ xem."],
    ["Báo chủ kho", "Muốn sửa sổ hay nhập thêm thì báo chủ kho: việc này làm ngoài app."]] },
  { ten: "④ Nhà cung cấp", phu: "vào bằng liên kết", nut: [
    ["Nhận liên kết đơn", "Chủ kho gửi tin nhắn Zalo có liên kết. Mỗi liên kết chỉ mở đúng một đơn, không lộ giá vốn hay tồn kho của bên mua."],
    ["Xác nhận, báo ngày giao", "Nhà cung cấp chọn ngày giao được và để lại lời nhắn. Đơn chuyển sang “đã xác nhận”, ngày dự kiến hàng về được cập nhật."],
    ["Giao hàng", "Khi chủ kho ghi “đã nhận”, vòng lặp khép lại và quay về bước nhập liệu."]] },
];

// ---------------------------------------------------------------- 3. app tính thế nào
const TINH = [
  ["Dữ liệu vào", "4 nguồn", "<b>Doanh số theo ngày</b> (ghi tay hoặc file), <b>số ngày hàng về</b> của từng nhà cung cấp (đo từ đơn đã nhận), <b>hạn dùng theo lô</b>, và <b>lịch sự kiện mùa vụ</b> của ngành (bánh kẹo: Tết, Trung thu). Ngày hết hàng được đánh dấu để không bị hiểu là bán 0."],
  ["Dự báo nhu cầu", "AI + độ bất định", "So sánh ba cách trên 30% dữ liệu cuối mà mô hình chưa học: Gradient Boosting trên đặc trưng lịch, thống kê mùa vụ, và trung bình đơn giản. Dùng cách có sai số (WAPE) thấp nhất và nói rõ đang dùng cách nào. Cùng lúc ước lượng độ dao động: Var = a·d̂ + b·d̂², không thấp hơn mức Poisson. Dưới 60 ngày số liệu: dùng ước lượng của người bán trộn với số đã đo."],
  ["Mức yên tâm → z", "CSL", "Mức yên tâm (CSL) là xác suất không hết hàng trong một chu kỳ đặt hàng. z = Φ⁻¹(CSL): 90% → 1,28; 95% → 1,645; 99% → 2,33. Mặc định 95%, đổi được cho từng mặt hàng."],
  ["Hàng dự phòng (SS)", "", "SS = z × √( tổng độ dao động nhu cầu trong lúc chờ hàng + (nhu cầu mỗi ngày)² × độ dao động của số ngày hàng về ). Hàng về càng thất thường, dự phòng càng lớn."],
  ["Mức báo đặt hàng (ROP)", "", "ROP = nhu cầu dự báo trong lúc chờ hàng + SS. So với <b>hàng khả dụng</b> = tồn thực + hàng đang về − hàng khách đã đặt giữ. Khả dụng ≤ ROP thì nên đặt."],
  ["Lượng đặt Q*", "có trần", "Q* = số nhỏ nhất trong ba số: EOQ = √(2·D·S/H) (cân bằng chi phí đặt và chi phí giữ), <b>trần hạn dùng</b> (chỉ nhập lượng bán kịp trong 60% hạn dùng), và <b>trần ngân sách</b> nếu bạn nhập. Làm tròn theo quy cách đóng gói."],
  ["Ngày đặt muộn nhất", "", "Dự phóng tồn kho thực từng ngày nếu không đặt thêm (bán lô gần hết hạn trước, loại hàng quá hạn), tìm ngày tồn kho chạm mức dự phòng, rồi lùi lại số ngày hàng về."],
  ["Khuyến nghị bằng lời", "3 câu", "Con số được đổi thành ba câu: tình trạng, việc nên làm, lý do; kèm rủi ro nói bằng lời (“trong 20 lần khoảng 1 lần hết hàng”) và số tiền có thể mất vì hết hạn. Thuật ngữ kỹ thuật chỉ xuất hiện trong mục “Xem chi tiết”."],
  ["Người duyệt", "bạn quyết định", "Người dùng xem, sửa số lượng rồi mới xác nhận đơn. Sau khi nhận hàng, ngày về thật quay lại làm dữ liệu vào cho lần tính sau."],
];

// ---------------------------------------------------------------- 4. sơ đồ mã nguồn
const TANG = [
  { ten: "web/  ·  giao diện chạy trong trình duyệt", phu: "HTML + CSS + JavaScript thuần, không cần bước build", tep: [
    ["index.html · kieu.css", "Trang duy nhất và toàn bộ kiểu dáng (màu, thẻ, bảng, sơ đồ). Sửa màu hay cỡ chữ: vào các biến đầu file kieu.css."],
    ["js/ung_dung.js", "Điểm vào: trang đăng nhập xếp theo các bên, khung trang, MENU theo vai trò, định tuyến #/trang. Thêm một màn hình: thêm một dòng vào MENU."],
    ["js/nen_tang.js", "Dùng chung: goi() gọi API kèm token, định dạng số / tiền / ngày, thông báo, ngăn kéo, thẻ 3 câu hỏi."],
    ["js/chu_kho.js", "Sáu màn hình của chủ kho: nhập liệu (6 thẻ con), tình trạng kho, tình trạng hàng, khuyến nghị, đơn hàng, chụp ảnh."],
    ["js/chi_tiet.js", "Ngăn chi tiết một mặt hàng: chọn mức yên tâm, biểu đồ, công thức với số thật, bảng WAPE, mô phỏng."],
    ["js/cac_ben.js", "Màn hình của chủ hàng, của quản trị, và cổng nhà cung cấp."],
    ["js/bieu_do.js", "Hai biểu đồ SVG vẽ tay: đã bán + dự báo, và tồn kho dự kiến."],
    ["js/huong_dan.js", "Chính trang này: nội dung hướng dẫn và các sơ đồ đều là dữ liệu ở đầu file."]] },
  { ten: "may_chu/  ·  máy chủ API (FastAPI)", phu: "mỗi yêu cầu: token → tài khoản → phạm vi một kho → dịch vụ → JSON", tep: [
    ["ung_dung.py", "Khai báo đường dẫn /api/..., kiểm tra vai trò (chủ kho, chủ hàng, quản trị), phục vụ thư mục web/. Không chứa công thức."],
    ["xac_thuc.py", "Tài khoản demo và phiên đăng nhập. Chuyển sang đăng nhập thật (Google, Zalo…): chỉ thay hàm dang_nhap."],
    ["dich_vu.py", "Nghiệp vụ: danh mục, sổ bán, lô hàng, tính khuyến nghị cho từng mặt hàng, câu chữ hiển thị, đơn hàng, quản trị."],
    ["kho_du_lieu.py", "Lưu dữ liệu (MongoDB hoặc file JSON) và lớp PhamVi tự gắn mã kho vào mọi lệnh: khách này không đọc được dữ liệu khách khác."],
    ["du_lieu_mau.py", "Dữ liệu mẫu mô phỏng cho ba khách và các tài khoản demo."]] },
  { ten: "tro_ly_ai/  ·  phần dùng AI bên ngoài", phu: "cần khoá API; AI không tự tính số", tep: [
    ["nhan_dien.py", "Nhận diện mặt hàng bằng ảnh (đối chiếu với danh mục, tối đa 3 ứng viên, có ngưỡng “không nhận ra”) và giải thích khuyến nghị bằng lời."],
    ["tro_ly.py", "Đọc khoá API và mô hình, tạo kết nối, đổi lỗi API thành câu tiếng Việt. Dùng chung với bản phân tích cũ."]] },
  { ten: "tinh_toan/  ·  lõi tính toán", phu: "numpy / pandas / scikit-learn, không phụ thuộc web, kiểm thử được riêng", tep: [
    ["du_bao_ai.py", "Dự báo theo mùa vụ: Gradient Boosting, so sánh WAPE ngoài mẫu với mô hình mùa vụ và trung bình, ước lượng phương sai."],
    ["khuyen_nghi.py", "SS, ROP, Q* có trần hạn dùng và ngân sách, ngày đặt muộn nhất, what-if mức yên tâm, đo CSL thực tế và fill rate bằng mô phỏng, ước lượng số ngày hàng về."],
    ["nganh.py", "Gói cấu hình ngành: lịch sự kiện, tham số mặc định, ràng buộc. Thêm ngành mới: thêm một mục vào GOI."],
    ["loi.py", "Lõi gốc: đọc và kiểm tra file doanh số, mô hình thống kê mùa vụ (Tết, Trung thu), mô phỏng tồn kho từng ngày."],
    ["nhieu_mat_hang.py · so_ghi.py", "Phần của bản phân tích cũ (nhập gộp nhiều mặt hàng, ràng buộc vốn và sức chứa, sổ kiểm kho); bản web dùng lại bộ sinh nhu cầu ngẫu nhiên."]] },
  { ten: "Nơi lưu dữ liệu", phu: "MongoDB database smartstock_ai · hoặc file du_lieu_cua_toi/smartstock.json khi MongoDB tắt", tep: [
    ["khach · tai_khoan · phien", "Khách của dịch vụ (gói, hạn), tài khoản và phiên đăng nhập."],
    ["chu_hang · nha_cung_cap · mat_hang", "Danh mục của từng kho; mỗi mặt hàng ghi rõ của chủ hàng nào."],
    ["doanh_so · lo_hang · don_hang", "Số bán theo ngày, tồn kho theo lô có hạn dùng, đơn hàng và ngày hàng về."]] },
];
const MUI_TANG = ["gọi /api/... kèm token", "gọi hàm", "gọi hàm tính", "đọc / ghi qua PhamVi (luôn kèm mã kho)"];

// ---------------------------------------------------------------- vẽ
const TAB = [["dung", "Cách dùng theo từng bước"], ["ben", "Luồng giữa các bên"], ["tinh", "App tính thế nào"], ["ma", "Sơ đồ mã nguồn"]];
const tt_hd = { tab: "dung", dung: 0, ben: "0-0", tinh: 0, ma: "0-0" };

const o_sd = (stt, ten, phu, chon, khoa) => `<button class="nut-sd ${chon ? "chon" : ""}" data-chon="${khoa}" aria-pressed="${chon}">${stt !== "" ? `<span class="stt">${stt}</span>` : ""}<b>${e(ten)}</b><small class="phu">${e(phu)}</small></button>`;
const noi = (ds) => ds.join(`<span class="mui" aria-hidden="true">→</span>`);

function ve_dung() {
  const ds = BUOC[tt.toi.vai_tro], b = ds[tt_hd.dung];
  const stt = (i) => (tt.toi.vai_tro === "chu_kho" ? (i === 0 ? "Chuẩn bị" : i === 6 ? "Công cụ" : "Bước " + i) : "Bước " + (i + 1));
  return `<p class="phu">Bấm vào từng ô theo thứ tự từ trái sang phải để xem cách dùng chi tiết.</p>
    <div class="so-do">${noi(ds.map((x, i) => o_sd(stt(i), x.ten, x.ngan, i === tt_hd.dung, i)))}</div>
    <div class="the chi-dan" style="margin-top:1rem"><h2 style="margin-top:0">${stt(tt_hd.dung)}: ${e(b.ten)}</h2><p>${e(b.muc_dich)}</p>
      <h3 style="margin-top:.8rem">Làm thế nào</h3><ol>${b.buoc.map((x) => `<li>${x}</li>`).join("")}</ol>
      ${b.luu_y ? `<div class="bao canh"><b>Lưu ý:</b> ${e(b.luu_y)}</div>` : ""}
      <div class="hang-nut" style="margin-top:.8rem"><a class="nut" href="#/${b.trang}">Mở màn hình này →</a>
        ${tt_hd.dung < ds.length - 1 ? `<button class="nut phu2" data-chon="${tt_hd.dung + 1}">Xem bước kế tiếp</button>` : ""}</div></div>`;
}

function ve_ben() {
  const [i, j] = tt_hd.ben.split("-").map(Number), n = LAN[i].nut[j];
  return `<p class="phu">Mỗi hàng là một bên, đọc từ trái sang phải. Bấm một ô để xem bên đó làm gì ở bước đó.</p>
    <div class="the">${LAN.map((l, a) => `<div class="lan"><div class="ten-lan">${e(l.ten)}<small class="phu">${e(l.phu)}</small></div>
      <div class="so-do">${noi(l.nut.map((x, b) => o_sd("", x[0], "", a === i && b === j, `${a}-${b}`)))}</div></div>`).join("")}</div>
    <div class="the chi-dan" style="margin-top:1rem"><h3>${e(LAN[i].ten)} · ${e(n[0])}</h3><p>${e(n[1])}</p></div>
    <div class="bao tin"><b>Các bên nối với nhau thế nào:</b> quản trị mở gói → chủ kho nhập liệu và nhận khuyến nghị → chủ hàng xem phần của mình →
      chủ kho đặt đơn và gửi liên kết → nhà cung cấp xác nhận ngày giao → chủ kho nhận hàng → số ngày hàng về thật quay lại làm khuyến nghị lần sau chính xác hơn.</div>`;
}

function ve_tinh() {
  const b = TINH[tt_hd.tinh];
  return `<p class="phu">Đường đi của con số, từ dữ liệu bạn nhập tới câu “nên đặt bao nhiêu”. Bấm một ô để xem công thức và ý nghĩa.</p>
    <div class="so-do">${noi(TINH.map((x, i) => o_sd(i + 1, x[0], x[1], i === tt_hd.tinh, i)))}</div>
    <div class="the chi-dan" style="margin-top:1rem"><h3>${tt_hd.tinh + 1}. ${e(b[0])}</h3><p>${b[2]}</p></div>
    <div class="bao canh"><b>Giới hạn cần biết:</b> dữ liệu mẫu là mô phỏng; chưa xử lý số lượng đặt tối thiểu, chiết khấu số lượng, nhiều nhà cung cấp cho một mặt hàng;
      độ chính xác nhận diện ảnh chưa được đo. Mọi con số hiệu quả phải đo lại bằng dữ liệu thật.</div>`;
}

function ve_ma() {
  const [i, j] = tt_hd.ma.split("-").map(Number), t = TANG[i].tep[j];
  return `<p class="phu">Mã nguồn chia thành các tầng, tầng trên chỉ gọi tầng ngay dưới. Bấm một file để biết nó làm gì và khi nào cần sửa nó.</p>
    ${TANG.map((g, a) => `<div class="tang"><div class="ten-tang"><span>${e(g.ten)}</span><small class="phu">${e(g.phu)}</small></div>
      <div class="tep">${g.tep.map((x, b) => `<button data-chon="${a}-${b}" class="${a === i && b === j ? "chon" : ""}">${e(x[0])}</button>`).join("")}</div></div>
      ${a < TANG.length - 1 ? `<div class="mui-xuong">↓ <small class="phu">${MUI_TANG[a]}</small></div>` : ""}`).join("")}
    <div class="the chi-dan" style="margin-top:1rem"><h3>${e(t[0])}</h3><p>${e(t[1])}</p></div>
    <div class="bao tin">Quy tắc phụ thuộc: <b>web → may_chu → tro_ly_ai → tinh_toan</b>. Lõi tính toán không biết gì về web hay AI nên kiểm thử được bằng <code>python -m pytest tests -q</code>.
      Chi tiết cho người phát triển nằm trong file AGENTS.md của dự án.</div>`;
}

export async function ve(el) {
  el.innerHTML = `<h1>Hướng dẫn & sơ đồ</h1><p class="phu">Bạn đang xem với vai trò <b>${e(tt.toi.ten_vai_tro)}</b>.</p>
    <div class="the-tab">${TAB.map(([m, t]) => `<button data-tab="${m}" class="${tt_hd.tab === m ? "chon" : ""}">${t}</button>`).join("")}</div>
    <div id="o_hd">${{ dung: ve_dung, ben: ve_ben, tinh: ve_tinh, ma: ve_ma }[tt_hd.tab]()}</div>`;
  el.querySelectorAll("[data-tab]").forEach((b) => (b.onclick = () => { tt_hd.tab = b.dataset.tab; ve(el); }));
  el.querySelectorAll("#o_hd [data-chon]").forEach((b) => (b.onclick = () => {
    const v = b.dataset.chon;
    tt_hd[tt_hd.tab] = v.includes("-") ? v : Number(v);
    ve(el);
  }));
}
