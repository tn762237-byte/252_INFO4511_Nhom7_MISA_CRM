# 🧾 Hệ thống Quản lý Khách hàng Công ty Cổ phần MISA

> Đề tài bài tập lớn học phần Lập trình Python – Nhóm 7  
> 🚀 Giao diện web: **Streamlit**  
> 💻 Giao diện dòng lệnh: **Python thuần**  
> 📁 Lưu trữ dữ liệu: **File JSON**  
> 🧩 Tổ chức chương trình: Theo **hàm và module**

---

## 📌 Mục tiêu đề tài

Xây dựng hệ thống quản lý khách hàng của Công ty Cổ phần MISA nhằm hỗ trợ lưu trữ, quản lý và tra cứu thông tin khách hàng một cách đơn giản, khoa học và thuận tiện. Chương trình cho phép người dùng thực hiện các chức năng chính như:

- Nhập thông tin khách hàng mới
- Xóa thông tin khách hàng
- Cập nhật thông tin khách hàng
- Tìm kiếm thông tin khách hàng
- Xem danh sách khách hàng

---

## 🧱 Cấu trúc thư mục

```text
252_INFO4511_Nhom7_MISA_CRM/
├── app.py                      # Giao diện web chính bằng Streamlit
├── main.py                     # Giao diện dòng lệnh Python thuần
├── config.toml                 # File cấu hình giao diện Streamlit
├── requirements.txt            # Danh sách thư viện cần cài đặt
├── README.md                   # Tài liệu mô tả và hướng dẫn sử dụng
│
├── data/
│   └── customers.json          # File lưu trữ dữ liệu khách hàng
│
└── modules/
    ├── customer_service.py     # Các hàm xử lý nghiệp vụ khách hàng
    └── storage.py              # Các hàm đọc / ghi dữ liệu JSON
```

---

## 🚀 Cách chạy web app

### Bước 1: Cài đặt thư viện

```bash
python -m pip install -r requirements.txt
```

### Bước 2: Chạy ứng dụng Streamlit

```bash
python -m streamlit run app.py
```

Sau khi chạy lệnh, hệ thống sẽ mở giao diện web trên trình duyệt. Người dùng có thể thao tác với các chức năng quản lý khách hàng thông qua menu chức năng.

---

## 💻 Cách chạy bản Python thuần

```bash
python main.py
```

Khi chạy bằng dòng lệnh, chương trình sẽ hiển thị menu chính:

```text
1. Nhập thông tin khách hàng mới
2. Xóa thông tin khách hàng
3. Cập nhật thông tin khách hàng
4. Tìm kiếm thông tin khách hàng
5. Xem danh sách khách hàng
0. Thoát
```

---

## 📂 Dữ liệu lưu trữ

Dữ liệu khách hàng được lưu trong file:

```text
data/customers.json
```

Định dạng lưu trữ là **JSON**. Mỗi khách hàng gồm các thông tin chính:

- `customer_id`: Mã khách hàng
- `customer_name`: Tên khách hàng
- `customer_type`: Loại khách hàng
- `phone`: Số điện thoại
- `email`: Email
- `address`: Địa chỉ
- `representative`: Người đại diện
- `tax_code`: Mã số thuế
- `product_service`: Sản phẩm cung cấp
- `service_package`: Gói dịch vụ
- `start_date`: Ngày bắt đầu
- `expiry_date`: Ngày hết hạn
- `balance`: Công nợ
- `notes`: Ghi chú
- `created_at`: Thời gian tạo
- `updated_at`: Thời gian cập nhật
- `is_deleted`: Trạng thái xóa mềm
- `deleted_at`: Thời gian xóa

---

## 🖥️ Giao diện người dùng

Hệ thống hỗ trợ hai hình thức sử dụng:

### Giao diện web Streamlit

Giao diện web được xây dựng bằng Streamlit, gồm các chức năng:

- Nhập thông tin khách hàng
- Cập nhật thông tin khách hàng
- Tìm kiếm thông tin khách hàng
- Xóa thông tin khách hàng
- Xem danh sách thông tin khách hàng

### Giao diện dòng lệnh Python thuần

Giao diện dòng lệnh hiển thị menu chức năng, cho phép người dùng nhập lựa chọn và thao tác trực tiếp trên terminal.

---

## ⚙️ Chức năng chính

### 1. Nhập thông tin khách hàng

Chức năng này cho phép thêm mới khách hàng vào hệ thống. Mã khách hàng được sinh tự động theo dạng `KH001`, `KH002`, ... Người dùng nhập các thông tin như tên khách hàng, loại khách hàng, số điện thoại, email, địa chỉ, người đại diện, mã số thuế, sản phẩm cung cấp, gói dịch vụ, ngày bắt đầu, ngày hết hạn, công nợ và ghi chú.

### 2. Xóa thông tin khách hàng

Chức năng này cho phép xóa khách hàng theo mã khách hàng. Hệ thống sử dụng cơ chế **xóa mềm**, tức là khách hàng không bị xóa hoàn toàn khỏi file dữ liệu mà được đánh dấu bằng trường `is_deleted = True`.

### 3. Cập nhật thông tin khách hàng

Chức năng này cho phép chỉnh sửa thông tin của khách hàng đã có trong hệ thống. Người dùng nhập mã khách hàng cần cập nhật, hệ thống hiển thị thông tin hiện tại và cho phép chọn từng trường thông tin để chỉnh sửa.

### 4. Tìm kiếm thông tin khách hàng

Chức năng này hỗ trợ tìm kiếm khách hàng theo mã khách hàng, tên khách hàng, số điện thoại hoặc email. Ngoài ra, hệ thống có thể lọc khách hàng theo trạng thái dịch vụ và tùy chọn bao gồm cả khách hàng đã bị xóa mềm.

### 5. Xem danh sách khách hàng

Chức năng này hiển thị danh sách khách hàng hiện có trong hệ thống. Người dùng có thể xem tổng quan danh sách và xem chi tiết từng khách hàng khi cần.

---

## 🧩 Nguyên tắc tổ chức code

- `modules/customer_service.py`: chứa toàn bộ logic nghiệp vụ như sinh mã khách hàng, chuẩn hóa dữ liệu, kiểm tra dữ liệu, tính trạng thái dịch vụ, tính trạng thái thanh toán, thêm mới, tìm kiếm, cập nhật và xóa mềm khách hàng.
- `modules/storage.py`: chịu trách nhiệm đọc và ghi dữ liệu trong file `data/customers.json`.
- `app.py`: xây dựng giao diện web bằng Streamlit và gọi các hàm xử lý từ module.
- `main.py`: xây dựng giao diện dòng lệnh, nhập/xuất dữ liệu và gọi các hàm xử lý từ module.

---

## ✅ Quy tắc nghiệp vụ

- Mã khách hàng được sinh tự động theo dạng `KH001`, `KH002`, ...
- Loại khách hàng gồm: `Cá nhân` và `Doanh nghiệp`.
- Sản phẩm cung cấp gồm: `meInvoice`, `MISA SME`, `MISA AMIS`, `Bamboo`.
- Gói dịch vụ gồm: `Standard`, `Professional`, `Enterprise`.
- Tên khách hàng không được để trống.
- Số điện thoại phải gồm đúng 10 chữ số và bắt đầu bằng số `0`.
- Email không được để trống và phải đúng định dạng cơ bản.
- Mã số thuế phải gồm 10, 12 hoặc 13 chữ số.
- Khách hàng doanh nghiệp bắt buộc phải có người đại diện.
- Ngày hết hạn phải lớn hơn ngày bắt đầu.
- Địa chỉ không được vượt quá 250 ký tự.
- Ghi chú không được vượt quá 500 ký tự.
- Khi xóa khách hàng, hệ thống thực hiện xóa mềm bằng `is_deleted = True`.
- Không cho phép cập nhật khách hàng đã bị xóa mềm.
- Không cho phép xóa khách hàng khi dịch vụ đang `Hoạt động` hoặc `Sắp hết hạn`.
- Không cho phép xóa khách hàng còn công nợ.

---

## 📊 Trạng thái dịch vụ và thanh toán

Hệ thống tự động tính trạng thái dịch vụ dựa trên ngày hết hạn:

| Trạng thái | Ý nghĩa |
|---|---|
| `Hoạt động` | Dịch vụ còn hạn trên 30 ngày |
| `Sắp hết hạn` | Dịch vụ còn hạn từ 0 đến 30 ngày |
| `Hết hạn` | Dịch vụ đã quá hạn |
| `Đã xóa` | Khách hàng đã bị xóa mềm |

Hệ thống cũng tự động tính trạng thái thanh toán dựa trên công nợ:

| Trạng thái | Ý nghĩa |
|---|---|
| `Đã thanh toán` | Công nợ bằng 0 |
| `Chưa thanh toán` | Công nợ lớn hơn 0 |

---

## 🌟 Tính năng nổi bật

| Tính năng | Mô tả |
|---|---|
| Modular hóa | Code được chia thành các module rõ ràng, dễ bảo trì và mở rộng |
| Lưu trữ JSON | Dữ liệu được ghi/đọc từ file JSON, giúp lưu lại thông tin sau khi tắt chương trình |
| Web UI tiện lợi | Giao diện Streamlit trực quan, dễ thao tác |
| Python thuần | Có thể chạy chương trình trực tiếp bằng terminal |
| Sinh mã tự động | Mã khách hàng được sinh tự động, hạn chế trùng lặp |
| Kiểm tra dữ liệu | Hệ thống kiểm tra số điện thoại, email, mã số thuế, ngày tháng và độ dài dữ liệu |
| Xóa mềm | Dữ liệu khách hàng không bị mất hoàn toàn, giúp đảm bảo khả năng truy vết |
| Tìm kiếm linh hoạt | Có thể tìm kiếm theo mã, tên, số điện thoại hoặc email |
| Lọc trạng thái | Hỗ trợ lọc khách hàng theo trạng thái dịch vụ |

---

## 📎 Tài liệu bổ sung

Các tài liệu có thể kèm theo trong bài báo cáo:

- Tệp chương trình
- Báo cáo bài tập lớn
- Slide thuyết trình nhóm

---

## 🔮 Định hướng phát triển

Trong tương lai, hệ thống có thể được phát triển thêm các chức năng sau:

- Xuất dữ liệu khách hàng ra file Excel
- Kết nối cơ sở dữ liệu SQLite hoặc MySQL
- Thêm chức năng đăng nhập và phân quyền người dùng
- Thống kê số lượng khách hàng theo trạng thái dịch vụ
- Thống kê công nợ khách hàng
- Khôi phục khách hàng đã bị xóa mềm
- Triển khai chương trình lên Streamlit Community Cloud

---

## 👥 Nhóm thực hiện

**Nhóm 7**  
Học phần: **Lập trình Python**  
Đề tài: **Xây dựng chương trình quản lý khách hàng của Công ty Cổ phần MISA**
Trưởng nhóm: **Nguyễn Thu Hà** 

| STT | Họ và tên | Mã sinh viên |
|---|---|---|---|
| 1 | Lê Quốc Đạt | 24D400018 |
| 2 | Nguyễn Thành Đạt | 24D400074 |
| 3 | Phạm Anh Đức | 24D400019 |
| 4 | Đỗ Lưu Hà | 24D400075 |
| 5 | Nguyễn Thu Hà | 24D400076 |

---

## 📎 Ghi chú

Đây là sản phẩm phục vụ mục đích học tập và nghiên cứu trong học phần Lập trình Python. Chương trình không phải là phần mềm chính thức của Công ty Cổ phần MISA và không sử dụng cho mục đích thương mại.
