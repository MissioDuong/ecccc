# SMARTSTOCK AI - KIẾN TRÚC HỆ THỐNG & ĐẶC TẢ SẢN PHẨM (V1.1)

## Công cụ gợi ý nhập hàng bằng AI cho tiểu thương và SME bán hàng có hạn dùng, có mùa vụ

> **Trạng thái tài liệu:** bản cập nhật từ V1.0. Các mục đánh dấu **[cần xác nhận]** là giả định chưa kiểm chứng với khách hàng thật. Mọi con số về hiệu quả trong tài liệu này là **chỉ số cần đo**, không phải kết quả đã đạt.

### Những điểm thay đổi so với V1.0

| # | Thay đổi | Lý do |
|---|---|---|
| 1 | Đổi khách hàng mục tiêu từ "chuỗi 3–20 chi nhánh" sang "tiểu thương và SME 1–3 điểm bán", bắt đầu bằng bánh kẹo ở chợ truyền thống | Khớp với đề tài và với khách có thể thật sự dùng; chuỗi nhiều chi nhánh chuyển sang giai đoạn sau |
| 2 | Thêm mô-đun **dự báo nhu cầu theo mùa vụ** và nối vào công thức SS, ROP, EOQ | V1.0 chỉ dùng nhu cầu trung bình, thiếu phần "AI dự báo" |
| 3 | Bỏ các con số hiệu quả không có nguồn (giảm lãng phí, tăng lợi nhuận, ROI 13 lần); thay bằng bảng chỉ số cần đo | Tránh khẳng định không kiểm chứng được |
| 4 | Điều chỉnh khung giá theo khả năng chi trả của tiểu thương | Mức giá V1.0 hợp với chuỗi hơn là sạp nhỏ |
| 5 | Chia phạm vi thành 3 giai đoạn (MVP, mở rộng, nâng cao) | V1.0 có quá nhiều mô-đun cho một bản đầu |
| 6 | Sửa chi tiết kỹ thuật: tần suất quét, hàm giá giảm, ước lượng lead time, nguồn dữ liệu đầu vào | Xem mục 2 và 3 |
| 7 | Sửa tính năng chụp ảnh: **nhận diện mặt hàng** để tra tồn kho và khuyến nghị, không dùng để đếm hàng | Làm rõ đúng mục đích |
| 8 | Thêm CSL có thể chọn và đo thực tế, tách riêng với fill rate | Giúp người dùng hiểu đánh đổi giữa rủi ro hết hàng và chi phí giữ hàng |
| 9 | Thêm mục khoảng trống nghiên cứu và mục giới hạn | Cần cho bài thi và để trung thực về điều chưa làm |

---

## 1. TỔNG QUAN & ĐỊNH VỊ

### 1.1 Mục tiêu chính

> **Giúp tiểu thương biết mỗi ngày: còn bao nhiêu hàng, có cần đặt không, đặt bao nhiêu và muộn nhất ngày nào. Trước Tết và Trung thu, cho biết mỗi mặt hàng nên nhập bao nhiêu. Nhờ đó ít hết hàng, ít hàng hết hạn và ít tiền vốn nằm kho.**

AI chỉ là phương tiện: dự báo nhu cầu theo mùa vụ và độ bất định, rồi nối thẳng vào quyết định đặt hàng. Người dùng không cần hiểu mô hình để dùng kết quả.

### 1.2 Khách hàng mục tiêu (ICP)

* **Nhóm chính (giai đoạn 1):** chủ sạp hoặc cửa hàng bánh kẹo ở chợ truyền thống, đại lý nhỏ.
  * Quy mô: 1–3 điểm bán, vài chục đến vài trăm mặt hàng. **[cần xác nhận bằng khảo sát]**
  * Đặc điểm: nhập từ đại lý hoặc nhà phân phối, hàng về sau 1–3 ngày, bán tăng mạnh vào Tết và Trung thu, hàng có hạn dùng.
  * Thực tế dữ liệu: nhiều sạp chưa có máy POS; có thể chỉ ghi sổ tay hoặc Excel.
* **Nhóm mở rộng (giai đoạn 2):** SME bán hàng có hạn dùng hoặc có mùa vụ ở ngành khác (ví dụ thực phẩm khô, hoa, văn phòng phẩm theo mùa khai giảng, nước giải khát). Mỗi ngành thay bằng một **gói cấu hình ngành** (mục 3.4).
* **Nhóm sau cùng (giai đoạn 3):** chuỗi nhiều chi nhánh với hàng tươi sống, nhiều nhiệt độ bảo quản. Các tính năng V1.0 dành cho nhóm này (bản đồ kệ 2D, chuyển hàng giữa chi nhánh, giá giảm động) giữ ở mục 3.5 như hướng phát triển.

### 1.3 Vấn đề cần giải quyết

Người bán nhỏ phải tự đoán lượng nhập, nhất là trước mùa cao điểm:

1. **Nhập thiếu:** hết hàng đúng lúc đắt khách, mất doanh thu.
2. **Nhập thừa:** hàng tồn lâu, hết hạn (ví dụ bánh trung thu sau rằm), tiền vốn nằm kho.
3. **Quyết định theo cảm tính hoặc sổ tay:** không tính được hàng đang về, thời gian giao hàng thay đổi, hay độ biến động của doanh số.

### 1.4 Khác biệt so với phần mềm bán hàng và quản lý kho thông thường

| Tiêu chí | Phần mềm bán hàng/kho thông thường (nhìn chung) | SmartStock AI |
|---|---|---|
| Việc chính | Ghi nhập, bán, tồn; hoá đơn; báo cáo | **Quyết định nhập hàng**: bao nhiêu, khi nào |
| Cách báo cần nhập | Thường báo khi tồn dưới mức tối thiểu do người dùng tự đặt | Mức báo tính từ dự báo bán, số ngày hàng về, độ biến động, mức yên tâm chọn |
| Mùa vụ (Tết, Trung thu) | Không phải trọng tâm | Dự báo có đặc trưng mùa vụ |
| Hạn dùng | Quản lý lô và cảnh báo sắp hết hạn | Giới hạn lượng đặt theo hạn dùng, nên không nhập quá lượng bán kịp |
| Cách dùng | Thay thế sổ sách và máy bán hàng | **Đứng cạnh** phần mềm bán hàng: nhập được file doanh số xuất từ các phần mềm đó; hoặc ghi nhanh số bán cuối ngày |

*Lưu ý: bảng trên mô tả xu hướng chung. Trước khi dùng câu "chưa có ai làm", cần kiểm tra trực tiếp từng sản phẩm.*

**Câu định vị:** *Dành cho chủ sạp bánh kẹo ở chợ truyền thống phải tự đoán lượng nhập trước Tết và Trung thu, SmartStock AI là công cụ gợi ý nhập hàng. Khác với phần mềm bán hàng chỉ báo khi tồn dưới mức tự đặt, SmartStock AI dự báo nhu cầu theo mùa vụ và cho biết nên đặt bao nhiêu, muộn nhất ngày nào, có tính hạn dùng.*

### 1.5 Khoảng trống nghiên cứu

Trong các tài liệu đã khảo sát, các hạn chế sau lặp lại và là cơ sở cho đề tài. Đây là nhận định thận trọng, chưa phải khảo sát toàn diện.

| Khoảng trống | Cách SmartStock AI xử lý |
|---|---|
| Nhiều mô hình AI cho tồn kho cần dữ liệu lớn và sạch | Chạy được với 1–2 năm doanh số; kiểm tra dữ liệu và báo lỗi bằng tiếng Việt |
| Mô hình "hộp đen", người quản lý khó tin | Mỗi khuyến nghị kèm lý do ngắn; công thức đặt ở mục "Xem chi tiết" |
| Dự báo và quyết định tồn kho thường tách rời, sai số dự báo lan sang tồn kho | Nối dự báo vào EOQ, SS, ROP; đưa cả độ bất định (phương sai) vào SS |
| Dự báo một con số, bỏ qua độ bất định | Mô hình phương sai Var = a·d̂ + b·d̂², ước lượng ngoài mẫu |
| Hàng có hạn dùng và có mùa vụ ít được tính chung trong một công cụ nhỏ | Trần lượng đặt theo hạn dùng, FIFO, đặc trưng Tết và Trung thu |
| Ít công cụ thiết kế cho người bán nhỏ và không rành công nghệ ở thị trường Việt Nam | Giao diện theo 3 câu hỏi, thuật ngữ thường, nhận diện mặt hàng bằng ảnh |

Việc cần làm thêm: tìm nghiên cứu tiếng Việt về quản lý tồn kho của hộ kinh doanh để khẳng định khoảng trống chắc hơn.

### 1.6 Chỉ số thành công (cần đo, chưa có giá trị)

| Chỉ số | Cách đo |
|---|---|
| Số lần hết hàng | Mô phỏng và thử nghiệm thực tế |
| Lượng hàng hết hạn hoặc bị huỷ | Mô phỏng và thử nghiệm thực tế |
| Vốn nằm trong tồn kho | Giá trị tồn trung bình |
| CSL thực tế (tỷ lệ chu kỳ không hết hàng) | Mô phỏng, so với CSL mục tiêu |
| Fill rate (tỷ lệ nhu cầu được đáp ứng) | Mô phỏng và thực tế |
| Sai số dự báo (WAPE) so với trung bình đơn giản | Bảng WAPE trong app |

---

## 2. LÕI TÍNH TOÁN SCM & AI

```
   [Doanh số theo ngày] + [Lead time thực tế] + [Hạn dùng theo lô] + [Lịch sự kiện mùa vụ]
                                   │
                                   ▼
                    [Mô hình dự báo nhu cầu (AI) + phương sai]
                                   │
                                   ▼
        [Tính CSL → z, SS, ROP, EOQ động có trần hạn dùng, ngày đặt muộn nhất]
                                   │
                                   ▼
            [Khuyến nghị hằng ngày: đặt bao nhiêu, muộn nhất ngày nào, vì sao]
                                   │
                                   ▼
                   [Người dùng xem, sửa, xác nhận (human-in-the-loop)]
```

### 2.1 Dự báo nhu cầu theo mùa vụ (mô-đun mới)

* Mô hình: Gradient Boosting trên đặc trưng lịch (thứ, tháng, ngày trong năm, số ngày tới Tết, số ngày tới Trung thu). Với ngành khác, sự kiện mùa vụ lấy từ gói cấu hình ngành.
* Đầu ra: dự báo nhu cầu theo ngày $\hat d_t$ và phương sai sai số $\widehat{Var}_t$.

$$
\widehat{Var}_t = a \cdot \hat d_t + b \cdot \hat d_t^{\,2}, \qquad \widehat{Var}_t \ge \hat d_t
$$

Hệ số $a, b$ ước lượng ngoài mẫu (học trên khoảng 70% đầu, kiểm tra trên 30% cuối khi đủ dữ liệu); sàn phương sai bằng phương sai Poisson để tránh coi nhu cầu quá ổn định.

* Đánh giá: so sánh WAPE của mô hình với trung bình đơn giản, hiển thị cho người dùng. Nếu mô hình không tốt hơn, app phải nói rõ và có thể quay về trung bình.
* Dữ liệu tối thiểu: cảnh báo khi dưới 365 ngày, từ chối khi dưới 60 ngày.
* **Hiệu chỉnh nhu cầu khi hết hàng:** ngày doanh số bằng 0 do hết hàng không được coi là không có nhu cầu. Cần cờ đánh dấu ngày hết hàng khi nhập dữ liệu, để loại hoặc điều chỉnh khi huấn luyện. **[chưa cài đặt trong code hiện tại]**

### 2.2 Mức phục vụ mục tiêu (CSL) và hệ số an toàn

CSL là xác suất không bị hết hàng trong một chu kỳ đặt hàng.

$$
z_{CSL} = \Phi^{-1}(\mathrm{CSL})
$$

* Giá trị tham khảo: CSL 90% → $z \approx 1{,}28$; 95% → $z \approx 1{,}645$; 98% → $z \approx 2{,}05$.
* Với tiểu thương: mặc định 95%, có **thanh trượt what-if 90% / 95% / 99%** cho từng mặt hàng, hiện ngay SS, ROP và chi phí giữ SS mỗi năm.
* Có thể gợi ý CSL theo nhóm ABC (nhóm A cao hơn, nhóm C thấp hơn) như tuỳ chọn nâng cao.
* **CSL thực tế** đo từ mô phỏng và hiển thị cạnh CSL mục tiêu. **Tách rõ với fill rate** (tỷ lệ nhu cầu được đáp ứng): hai chỉ số này khác nhau.

### 2.3 Tồn kho an toàn (SS)

SS tính trên dự báo trong thời gian hàng về, kể cả biến động của lead time:

$$
SS = z_{CSL} \sqrt{\sum_{t=1}^{L} \widehat{Var}_t + \left(\frac{\mu_L}{L}\right)^{2} \sigma_{LT}^{2}}, \qquad \mu_L = \sum_{t=1}^{L} \hat d_t
$$

Với $L$ là lead time trung bình (ngày) và $\sigma_{LT}$ là độ lệch chuẩn của lead time.

**Ước lượng lead time từng nhà cung cấp:**
* Ghi ngày đặt và ngày hàng về mỗi lần.
* Nếu có ít lần giao (ví dụ dưới 5 lần), **không** dùng độ lệch chuẩn vừa tính; dùng giá trị mặc định của ngành hoặc kết hợp giữa giá trị mặc định và số đo (co về mặc định).
* Hiển thị số lần giao đã dùng để ước lượng.

### 2.4 Điểm đặt hàng lại (ROP) và vị thế tồn kho

$$
ROP = \sum_{t=1}^{L} \hat d_t + SS, \qquad I_{\text{avail}} = I_{\text{on-hand}} + I_{\text{on-order}} - I_{\text{reserved}}
$$

Đặt hàng khi $I_{\text{avail}} \le ROP$. Số đơn vị Q cần đặt là số nguyên $n \ge 1$ nhỏ nhất sao cho $I_{\text{avail}} + n \cdot Q^* > ROP$.

Ghi chú vận hành: tồn kho tổng (vị thế) tăng ngay khi đặt, còn tồn kho thực chỉ tăng sau khi hàng về.

**Ngày đặt muộn nhất:** dự phóng tồn kho thực nếu không đặt thêm, tìm ngày tồn kho chạm SS, rồi trừ đi lead time.

### 2.5 Lượng đặt hợp lý (EOQ động, có trần theo hạn dùng và ngân sách)

$$
D_{\text{annual}} = \frac{365}{30} \sum_{t=1}^{30} \hat d_t, \qquad EOQ_{\text{standard}} = \sqrt{\frac{2 \cdot D_{\text{annual}} \cdot S}{H}}
$$

$$
Q^* = \min\left(EOQ_{\text{standard}}, \; \alpha \cdot \bar d \cdot T_{\text{shelf}}, \; Q_{\text{cash}}\right)
$$

* $S$: chi phí đặt hàng mỗi lần. $H$: chi phí giữ hàng mỗi đơn vị mỗi năm (tính theo tỷ lệ giữ hàng nhân giá vốn).
* $\alpha$: hệ số hạn dùng. App hiện tại dùng 0,6; cho phép cấu hình trong khoảng 0,5 đến 0,85 tuỳ mặt hàng.
* $Q_{\text{cash}}$: lượng tối đa theo ngân sách người dùng nhập (tuỳ chọn).
* Ràng buộc thực tế chưa có trong code: số lượng đặt tối thiểu (MOQ), chiết khấu số lượng, quy cách đóng gói. **[roadmap]**

### 2.6 Quy trình khuyến nghị (có người duyệt)

1. **Kiểm tra theo ngày:** mỗi ngày (và khi người dùng cập nhật tồn kho) hệ thống so $I_{\text{avail}}$ với ROP. Quét mỗi 15 phút như V1.0 là không cần thiết với tiểu thương.
2. **Tạo khuyến nghị:** mặt hàng chạm ROP được đưa vào danh sách "nên đặt", kèm số lượng $Q^*$, ngày đặt muộn nhất và lý do ngắn.
3. **Gộp theo nhà cung cấp:** các mặt hàng cùng nhà cung cấp được gom vào một đơn nháp để đạt MOQ và tiết kiệm vận chuyển (giai đoạn 2).
4. **Người dùng xem, sửa, xác nhận.** Hệ thống không tự gửi đơn trong giai đoạn 1.
5. **Gửi đơn:** giai đoạn 2, gửi qua Zalo hoặc email; khi nhà cung cấp xác nhận thì ghi ngày hàng về để cập nhật lead time.

---

## 3. CÁC MÔ-ĐUN VÀ GIAI ĐOẠN TRIỂN KHAI

### 3.1 Tổng quan theo giai đoạn

| Giai đoạn | Mô-đun | Mục tiêu |
|---|---|---|
| **1. MVP** | Lưu dữ liệu; tài khoản; nhập liệu; tình trạng hàng và kho; khuyến nghị đặt hàng; CSL và SS what-if; nhận diện mặt hàng bằng ảnh | Dùng được cho một tiểu thương; chứng minh lõi EOQ + dự báo |
| **2. Mở rộng** | Gói cấu hình ngành; gộp đơn theo nhà cung cấp; cổng nhà cung cấp; dashboard quản trị và gia hạn; bên mua hàng | Mở sang ngành khác; vận hành như dịch vụ |
| **3. Nâng cao** | Bản đồ kệ 2D và FEFO; chuyển hàng giữa chi nhánh; giá giảm động; nhật ký kiểm toán có ảnh; hỏi đáp BI bằng ngôn ngữ tự nhiên | Dành cho cửa hàng nhiều chi nhánh |

### 3.2 Mô-đun 1: Nhập liệu và chuẩn hoá dữ liệu (giai đoạn 1)

* **Nhiều cách nhập, để người không có POS vẫn dùng được:**
  * Ghi nhanh số bán từng mặt hàng cuối ngày (mất vài phút).
  * Tải file CSV hoặc Excel doanh số (dạng dài hoặc dạng rộng); nhập được file xuất từ phần mềm bán hàng.
  * Ảnh phiếu giao hàng hoặc hoá đơn đọc bằng mô hình thị giác. **[giai đoạn 2]**
* **Kiểm tra và báo lỗi bằng tiếng Việt:** thiếu cột, ngày sai, số âm, tên mặt hàng không khớp; điền ngày thiếu bằng 0 kèm cảnh báo.
* **Chuẩn hoá tên mặt hàng:** gom các cách gọi khác nhau về một mã. **[giai đoạn 2]**
* **Dữ liệu cần theo từng mặt hàng:** giá vốn, giá bán, hạn dùng, chi phí đặt hàng, tỷ lệ giữ hàng, lead time và độ lệch, mức phục vụ.
* Phân loại ABC-XYZ động như tuỳ chọn nâng cao.

### 3.3 Mô-đun 2: Chụp ảnh nhận diện mặt hàng, tra tồn kho và khuyến nghị (giai đoạn 1)

**Mục đích:** người dùng không phải nhớ chính xác tên hoặc mã mặt hàng. Họ chụp ảnh sản phẩm, app nhận ra đó là mặt hàng nào, tra tồn kho và đưa khuyến nghị đặt hàng. Ảnh dùng để **nhận ra tên mặt hàng**, không dùng để đếm số hàng trong kho.

**Luồng sử dụng:**

1. Chụp ảnh sản phẩm (bao bì, nhãn).
2. App đối chiếu với danh mục mặt hàng của cửa hàng, trả về tối đa 3 ứng viên kèm độ chắc chắn.
3. Người dùng chạm xác nhận (hoặc chọn ứng viên khác, hoặc tìm tay). Độ chắc chắn thấp thì app hỏi lại, không tự chọn.
4. App tra **tồn kho và hàng đang về** của mặt hàng trong sổ tồn kho đã lưu.
5. App tính và hiện thẻ kết quả: mặt hàng, tồn kho, hàng đang về, trạng thái, **nên đặt bao nhiêu**, **đặt muộn nhất vào ngày nào**, lời giải thích ngắn.

**Điều kiện:** danh mục mặt hàng kèm ảnh mẫu (vài ảnh mỗi mặt hàng, nhiều góc); sổ tồn kho được lưu và cập nhật (phụ thuộc mô-đun lưu dữ liệu). Khi chưa có sổ lưu, người dùng nhập tồn kho tay sau khi ảnh đã nhận ra mặt hàng.

**Hướng kỹ thuật (đề xuất, chưa thử):** (a) mô hình thị giác nhìn ảnh rồi đối chiếu với danh mục, kể cả đọc chữ trên nhãn; hoặc (b) so khớp ảnh với ảnh mẫu đã đăng ký. Chọn sau khi thử trên ảnh thật.

**Giới hạn:** bao bì gần giống nhau (cùng hãng, khác vị) dễ nhầm; hàng bán rời không nhãn rất khó nhận; mặt hàng chưa đăng ký phải báo "không nhận ra" thay vì đoán; khuyến nghị chỉ đúng khi sổ tồn kho đúng; mỗi ảnh gọi dịch vụ bên ngoài (có chi phí và ảnh rời khỏi máy người dùng).

**Cách đo (đề xuất):** khoảng 10 ảnh thật mỗi mặt hàng (khác góc, khác ánh sáng) cộng vài ảnh hàng ngoài danh mục; đo tỷ lệ đúng ở ứng viên đầu tiên và trong 3 ứng viên, tỷ lệ nhầm khi app tự tin, tỷ lệ báo "không nhận ra" đúng với hàng lạ. Chỉ nói "nhận diện được" sau khi có số đo.

**Mở rộng về sau:** đếm số lượng hàng từ ảnh để đối chiếu sổ tồn kho là bài toán khác và khó hơn nhiều, nằm ngoài phạm vi hiện tại.

### 3.4 Mô-đun 3: Gói cấu hình ngành (giai đoạn 2)

Lõi EOQ, SS, ROP, FIFO giữ nguyên; mỗi ngành chỉ thay một gói gồm:

| Phần | Nội dung | Ví dụ |
|---|---|---|
| Lịch sự kiện | Ngày mùa vụ, sinh ra đặc trưng "số ngày tới sự kiện" | Bánh kẹo: Tết, Trung thu. Hoa: 8/3, 20/10. Văn phòng phẩm: khai giảng |
| Tham số mặc định | Hạn dùng, lead time, chi phí đặt, tỷ lệ giữ hàng, CSL | Hoa tươi có hạn dùng rất ngắn |
| Ràng buộc đặc thù | Quy tắc thêm | MOQ, chiết khấu số lượng |

Giữ bánh kẹo làm ngành chính được chứng minh sâu; thêm **một** ngành thứ hai làm minh hoạ, ghi rõ dữ liệu mô phỏng nếu chưa có dữ liệu thật. Bảng ngày Tết và Trung thu cho các năm xa (trước 2023 và sau 2027) cần đối chiếu lại trước khi dùng.

### 3.5 Mô-đun nâng cao (giai đoạn 3, từ V1.0, rút gọn)

* **Bản đồ kệ 2D và FEFO:** tô màu theo phần trăm hạn dùng còn lại (xanh trên 50%, vàng 20–50%, đỏ dưới 20%) để đưa hàng sắp hết hạn ra trước.
* **Chuyển hàng giữa chi nhánh:** chỉ chuyển khi chi phí vận chuyển thấp hơn thiệt hại dự kiến nếu giảm giá hoặc huỷ.

$$
\text{Chuyển hàng nếu: } C_{\text{transit}} < \Delta \text{Loss}_{\text{markdown}}
$$

* **Giá giảm động cho hàng sắp hết hạn:** chọn giá $p$ trong khoảng cho phép để tối đa số tiền thu hồi ròng.

$$
\max_{p_{\min} \le p \le p_0} \; \left[ p \cdot Q(p, t) - C_{\text{disposal}} \cdot \max\left(0, \; I_{\text{batch}} - Q(p, t)\right) \right]
$$

  * $p_0$: giá hiện hành; $p_{\min}$: giá sàn (không thấp hơn mức thu hồi tối thiểu và biên lợi nhuận mục tiêu do chủ cửa hàng đặt). Giá vốn đã chi nên không nằm trong hàm mục tiêu, nhưng phải có giá sàn để tránh bán dưới mức chấp nhận được.
  * $Q(p, t)$ cần ước lượng từ dữ liệu; khi chưa đủ dữ liệu thì dùng các mức giảm giá bậc thang cố định.
* **Nhật ký kiểm toán:** mọi điều chỉnh tồn kho ghi lý do, thời gian, người thực hiện, có ảnh xác minh.
* **Hỏi đáp BI bằng ngôn ngữ tự nhiên:** hỏi bằng tiếng Việt về số liệu vận hành; số liệu phải lấy từ công cụ tính, không để mô hình tự tính nhẩm.

---

## 4. GIAO DIỆN & HÀNH TRÌNH NGƯỜI DÙNG

### 4.1 Nguyên tắc giao diện cho người không rành công nghệ

**Màn hình đầu tiên chỉ trả lời 3 câu hỏi cho mỗi mặt hàng:**

1. **Tình trạng bây giờ:** màu xanh, cam, đỏ kèm một câu, ví dụ "Còn đủ bán khoảng 5 ngày".
2. **Việc nên làm:** ví dụ "Nên đặt 120 hộp, đặt chậm nhất ngày 18/01".
3. **Lý do trong một dòng:** ví dụ "Tết sắp tới, hàng về mất 2–3 ngày".

**Thêm 3 thông tin có tiền hoặc rủi ro cụ thể:**

* Hàng nào sắp hết hạn và số tiền có thể mất.
* Nếu không đặt thì khả năng hết hàng là bao nhiêu, nói bằng lời ("trong 20 lần chỉ khoảng 1 lần hết hàng") thay vì "CSL 95%".
* Dự báo bán vài ngày tới dưới dạng khoảng ("khoảng 18–26 hộp mỗi ngày"), kèm câu "dự báo có thể sai".

**Đổi thuật ngữ sang tiếng thường:**

| Thuật ngữ kỹ thuật | Tên hiển thị cho tiểu thương |
|---|---|
| ROP | Mức báo đặt hàng |
| SS (tồn kho an toàn) | Hàng dự phòng |
| EOQ | Lượng đặt hợp lý mỗi lần |
| CSL | Mức yên tâm không hết hàng |
| Lead time | Số ngày hàng về |

Công thức, bảng WAPE, tham số mô hình và biểu đồ mô phỏng đặt trong mục "Xem chi tiết" dành cho người muốn kiểm tra.

### 4.2 Danh sách màn hình

| Màn hình | Ai dùng | Nội dung |
|---|---|---|
| Tạo tài khoản và đăng nhập | Mọi người | Dùng dịch vụ đăng nhập có sẵn, không tự lưu mật khẩu |
| Nhập liệu | Người dùng chính | Ghi nhanh số bán, tải file, nhập tồn kho và hàng đang về, nhập thông số mặt hàng |
| Tình trạng kho | Người dùng chính | Tổng quan: số mặt hàng, giá trị tồn, hàng sắp hết, hàng sắp hết hạn |
| Tình trạng hàng | Người dùng chính | Từng mặt hàng: tồn, đang về, hạn dùng, màu trạng thái, ngày bán hết dự kiến |
| **Khuyến nghị đặt hàng** | Người dùng chính | Đặt bao nhiêu, muộn nhất ngày nào, vì sao; thanh trượt mức yên tâm |
| Chụp ảnh nhận diện | Người dùng chính | Mục 3.3 |
| Bên mua hàng | Bên mua hàng | Xem phần hàng của mình trong kho (xem mục 5) **[cần xác nhận]** |
| Dashboard quản trị | Quản trị | Theo dõi bên mua dịch vụ, ngày hết hạn gói, ngày cần gia hạn |

### 4.3 Các giao diện triển khai

| Giao diện | Dành cho | Giai đoạn |
|---|---|---|
| Ứng dụng web (di động trước) | Tiểu thương, người trông hàng | 1 |
| Dashboard quản trị | Nhóm vận hành dịch vụ | 2 |
| Cổng nhà cung cấp (liên kết, không cần cài đặt) | Nhà cung cấp xác nhận đơn, giá, ngày giao | 2 |
| Trang giới thiệu và dùng thử | Khách tiềm năng | 2 |

---

## 5. VAI TRÒ, QUYỀN & DỮ LIỆU NHIỀU NGƯỜI DÙNG

| Vai trò | Là ai | Thấy và làm được gì |
|---|---|---|
| Quản trị (bên bán dịch vụ) | Nhóm vận hành app | Dashboard: ai đang dùng dịch vụ, ngày hết hạn, ngày gia hạn; không xem số liệu kinh doanh chi tiết của khách nếu không được cho phép |
| Người dùng chính | Tiểu thương, chủ kho | Nhập liệu, xem tình trạng kho và hàng, nhận khuyến nghị |
| Bên mua hàng | Khách có hàng gửi trong kho **[cần xác nhận]** | Chỉ xem phần hàng của mình |
| Nhà cung cấp | Đại lý, nhà phân phối | Qua liên kết: xác nhận đơn và ngày giao, không cần tài khoản (giai đoạn 2) |

**Mô hình dữ liệu:**

* Mỗi bản ghi (doanh số, tồn kho, lệnh đặt, ngày hàng về) gắn một **mã người dùng**; người này không đọc được dữ liệu của người khác.
* Nếu một kho giữ hàng cho nhiều chủ hàng, kho phải ghi rõ **hàng này của ai**.
* Đăng nhập dùng dịch vụ xác thực có sẵn, không tự viết hệ thống mật khẩu.

**Câu hỏi cần chốt:** "bên mua hàng" là khách mua hàng từ tiểu thương rồi gửi hàng lại ở kho, hay là chính các tiểu thương gửi hàng vào một kho dịch vụ? Nếu app chỉ phục vụ một tiểu thương, bỏ vai trò này khỏi giai đoạn 1.

**Gia hạn dịch vụ:** giai đoạn đầu chỉ là danh sách khách kèm ngày hết hạn và nhắc thủ công; không làm thanh toán trong bản đầu.

---

## 6. MÔ HÌNH THƯƠNG MẠI (GIẢ THUYẾT, CẦN KIỂM CHỨNG)

Mức giá dưới đây là giả thuyết để kiểm chứng bằng khảo sát và dùng thử, không phải kết luận. Nguyên tắc: giá cho tiểu thương phải ngang hoặc thấp hơn phần mềm bán hàng thông dụng, vì app đứng cạnh chứ không thay chúng.

| Gói | Dành cho | Nội dung | Giá giả thuyết |
|---|---|---|---|
| Dùng thử | Mọi người | Tải một file doanh số, nhận báo cáo chẩn đoán miễn phí | Miễn phí, có giới hạn thời gian |
| Cơ bản | Tiểu thương 1 điểm bán | Nhập liệu, tình trạng hàng, khuyến nghị đặt hàng, CSL what-if | Khoảng 150.000đ đến 200.000đ mỗi tháng **[cần xác nhận]** |
| Nâng cao | Cửa hàng nhiều mặt hàng, SME | Gộp đơn theo nhà cung cấp, cổng nhà cung cấp, nhiều ngành, nhiều người dùng | Khoảng 300.000đ đến 400.000đ mỗi tháng **[cần xác nhận]** |
| Doanh nghiệp | Chuỗi nhiều chi nhánh | Giai đoạn 3: kệ 2D, chuyển hàng, giá giảm động, tích hợp riêng | Báo giá riêng |

**Cách tiếp cận thị trường:**

1. **Chẩn đoán miễn phí:** khách đưa khoảng 90 ngày doanh số và tồn kho (CSV hoặc Excel); app chạy và cho biết ước tính hàng hết hạn và hàng hết sạch nếu theo khuyến nghị so với cách đang làm. Báo cáo ghi rõ đây là ước tính.
2. **Thử nghiệm 30 ngày trên một điểm bán**, so sánh trước và sau.
3. **Hợp tác với đại lý và nhà phân phối** để tiếp cận nhiều tiểu thương cùng lúc.

---

## 7. ĐO HIỆU QUẢ VÀ KIỂM CHỨNG

V1.0 đưa các con số lợi ích và ROI cụ thể không có nguồn. V1.1 bỏ chúng. Hiệu quả được báo cáo từ hai nguồn:

1. **Mô phỏng nội bộ:** so ba chính sách (kinh nghiệm, EOQ cổ điển, AI + EOQ động) trên cùng nhiễu nhu cầu và lead time; nhiều lần chạy; báo chi phí, hết hàng, hết hạn, CSL thực tế, fill rate. Dữ liệu mô phỏng có cấu trúc lịch giống đặc trưng đầu vào của mô hình, nên lợi thế của AI có thể bị đánh giá cao hơn thực tế.
2. **Thử nghiệm thực tế:** trên một hoặc vài điểm bán, so với giai đoạn trước.

**Công thức lợi ích ròng** (điền số đo được, không điền số giả định):

$$
\text{Lợi ích ròng} = \text{Tiết kiệm (giảm hao hụt + giảm mất doanh thu do hết hàng)} - \text{Phí phần mềm}
$$

$$
\text{ROI ròng} = \frac{\text{Lợi ích ròng}}{\text{Phí phần mềm}}
$$

Lưu ý: ROI ròng tính trên lợi ích đã trừ phí. Không dùng tỷ lệ giữa tiết kiệm gộp và phí rồi gọi là lợi ích ròng.

**Bảng cần điền sau khi đo:**

| Chỉ số | Cách làm cũ (đo được) | SmartStock AI (đo được) | Nguồn số liệu |
|---|---|---|---|
| Hàng hết hạn hoặc huỷ | chưa đo | chưa đo | mô phỏng / thử nghiệm |
| Số lần hết hàng | chưa đo | chưa đo | mô phỏng / thử nghiệm |
| Vốn tồn kho trung bình | chưa đo | chưa đo | mô phỏng / thử nghiệm |
| CSL thực tế so với mục tiêu | chưa đo | chưa đo | mô phỏng |

---

## 8. GIỚI HẠN & RỦI RO

* **Dữ liệu mô phỏng:** dữ liệu hiện có là mô phỏng; tham số giá và hạn dùng là giả định minh hoạ. Cần dữ liệu thật của ít nhất một quầy hàng để kiểm chứng.
* **Mô hình dự báo:** AI không luôn tốt hơn phương pháp đơn giản; app phải báo WAPE và quay về trung bình khi AI không tốt hơn.
* **Nhận diện ảnh:** chưa có số đo độ chính xác; ảnh gửi ra dịch vụ bên ngoài nên cần thông báo và có chi phí theo lượt.
* **Sổ tồn kho:** khuyến nghị chỉ đúng khi tồn kho nhập đúng; app hiện chưa lưu dữ liệu giữa các lần chạy.
* **Ngày mùa vụ:** bảng ngày Tết và Trung thu ở các năm xa cần đối chiếu; ngày của ngành khác phải do ngành đó cung cấp.
* **Chưa xử lý:** MOQ, chiết khấu số lượng, nhiều nhà cung cấp cho cùng mặt hàng, hàng thay thế.
* **Quyền riêng tư:** dữ liệu kinh doanh là dữ liệu nhạy cảm đối với tiểu thương; cần chính sách xuất và xoá dữ liệu, cách ly dữ liệu giữa người dùng.
* **Chatbot:** nếu dùng dịch vụ AI bên ngoài, nội dung hội thoại và kết quả công cụ được gửi đi; khoá API không được đưa lên kho mã nguồn; cần quyết định ai trả chi phí gọi API khi có nhiều người dùng.
* **Phạm vi:** làm quá nhiều tính năng làm loãng trọng tâm; ưu tiên chiều sâu ở EOQ, SS, CSL và khuyến nghị đặt hàng.

---

## 9. LỘ TRÌNH ĐỀ XUẤT

1. **CSL và SS:** hiển thị CSL, thanh trượt what-if, đo CSL thực tế. *Qua bước khi:* kiểm thử z đúng, SS không giảm khi CSL tăng, có số đo từ mô phỏng.
2. **Lưu dữ liệu, rồi tài khoản:** cơ sở dữ liệu cho doanh số, tham số, tồn kho, lệnh đặt; đăng nhập bằng dịch vụ có sẵn. *Qua bước khi:* người dùng A không thấy dữ liệu của B.
3. **Tình trạng hàng, tình trạng kho, khuyến nghị đặt hàng** trên giao diện thuật ngữ thường. *Qua bước khi:* một người không rành công nghệ làm theo được mà không cần hướng dẫn.
4. **Chụp ảnh nhận diện mặt hàng.** *Qua bước khi:* có tỷ lệ nhận đúng đo trên ảnh thật và app báo "không nhận ra" đúng với hàng lạ.
5. **Gói cấu hình ngành** và ngành thứ hai minh hoạ. *Qua bước khi:* kết quả bánh kẹo không đổi sau khi tách cấu hình; ngành thứ hai chạy hết luồng và có bảng WAPE.
6. **Dashboard quản trị, gia hạn, bên mua hàng, cổng nhà cung cấp.**
7. **Giai đoạn 3** theo nhu cầu thật của khách.
