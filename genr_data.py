"""
generate_test_data.py
=====================
Script tự động tạo 15 khách hàng mẫu vào hệ thống để phục vụ kiểm thử (Testing).
Chạy lệnh: python generate_test_data.py
"""

from datetime import date, timedelta
from modules.storage import load_customers, save_customers
from modules.customer_service import generate_next_customer_id


def generate_mock_data():
    # Tải danh sách khách hàng hiện tại từ file lưu trữ (JSON)
    customers = load_customers()

    # Định nghĩa ngày hôm nay để tính toán ngày bắt đầu và ngày hết hạn cho các kịch bản test
    today = date.today()

    # Danh sách dữ liệu thô của 15 khách hàng phục vụ kiểm thử đầy đủ các case nghiệp vụ
    mock_inputs = [
        # --- NHÓM 1: TRẠNG THÁI "HOẠT ĐỘNG" ---
        {
            "customer_name": "Nguyễn Văn A", "customer_type": "Cá nhân", "phone": "0912345678",
            "email": "vana@gmail.com", "tax_code": "", "product_service": "meInvoice", "service_package": "Standard",
            "start_date": today - timedelta(days=30), "expiry_date": today + timedelta(days=335), "amount_due": 1000000,
            "balance": 0
        },
        {
            "customer_name": "Công ty Công nghệ ABC", "customer_type": "Doanh nghiệp", "phone": "0243123456",
            "email": "contact@abc.com", "tax_code": "0101234567", "product_service": "MISA AMIS",
            "service_package": "Enterprise",
            "start_date": today - timedelta(days=10), "expiry_date": today + timedelta(days=355),
            "amount_due": 15000000, "balance": 0
        },
        {
            "customer_name": "Trần Thị B", "customer_type": "Cá nhân", "phone": "0987654321",
            "email": "thib@gmail.com", "tax_code": "", "product_service": "Bamboo", "service_package": "Professional",
            "start_date": today - timedelta(days=5), "expiry_date": today + timedelta(days=175), "amount_due": 2000000,
            "balance": 0
        },

        # --- NHÓM 2: TRẠNG THÁI "SẮP HẾT HẠN" (Thời hạn còn lại <= 30 ngày) ---
        {
            "customer_name": "Lê Văn C", "customer_type": "Cá nhân", "phone": "0905556667",
            "email": "vanc@gmail.com", "tax_code": "", "product_service": "MISA SME", "service_package": "Standard",
            "start_date": today - timedelta(days=340), "expiry_date": today + timedelta(days=25), "amount_due": 3000000,
            "balance": 0
        },
        {
            "customer_name": "Tập đoàn Đại Nam", "customer_type": "Doanh nghiệp", "phone": "0283999888",
            "email": "info@dainam.vn", "tax_code": "0301234567-001", "product_service": "MISA AMIS",
            "service_package": "Enterprise",
            "start_date": today - timedelta(days=350), "expiry_date": today + timedelta(days=15),
            "amount_due": 25000000, "balance": 0
        },
        {
            "customer_name": "Phạm Minh Hoàng", "customer_type": "Cá nhân", "phone": "0934112233",
            "email": "hoangpm@gmail.com", "tax_code": "", "product_service": "meInvoice",
            "service_package": "Professional",
            "start_date": today - timedelta(days=80), "expiry_date": today + timedelta(days=10), "amount_due": 1200000,
            "balance": 0
        },

        # --- NHÓM 3: TRẠNG THÁI "HẾT HẠN" (Ngày hết hạn trước ngày hôm nay) ---
        {
            "customer_name": "Hoàng Thị D", "customer_type": "Cá nhân", "phone": "0911223344",
            "email": "thid@gmail.com", "tax_code": "", "product_service": "Bamboo", "service_package": "Standard",
            "start_date": today - timedelta(days=400), "expiry_date": today - timedelta(days=35), "amount_due": 1000000,
            "balance": 0
        },
        {
            "customer_name": "Công ty TNHH Sao Mai", "customer_type": "Doanh nghiệp", "phone": "02363777888",
            "email": "saomai@gmail.com", "tax_code": "0401234567", "product_service": "MISA SME",
            "service_package": "Professional",
            "start_date": today - timedelta(days=370), "expiry_date": today - timedelta(days=5), "amount_due": 5000000,
            "balance": 0
        },

        # --- NHÓM 4: CÓ CÔNG NỢ (balance > 0) ĐỂ TEST CHỨC NĂNG CHẶN XÓA HOẶC LỌC THỐNG KÊ ---
        {
            "customer_name": "Vũ Đầu Tư Khách Hàng Nợ 1", "customer_type": "Cá nhân", "phone": "0966778899",
            "email": "no1@gmail.com", "tax_code": "", "product_service": "MISA SME", "service_package": "Standard",
            "start_date": today - timedelta(days=20), "expiry_date": today + timedelta(days=345), "amount_due": 4000000,
            "balance": 1500000
        },
        {
            "customer_name": "Tổng Công ty Phát triển Hạ tầng", "customer_type": "Doanh nghiệp", "phone": "0243555444",
            "email": "hatang@vnn.vn", "tax_code": "0109876543", "product_service": "MISA AMIS",
            "service_package": "Enterprise",
            "start_date": today - timedelta(days=100), "expiry_date": today + timedelta(days=265),
            "amount_due": 50000000, "balance": 20000000
        },
        {
            "customer_name": "Nguyễn Thị Thùy Chi", "customer_type": "Cá nhân", "phone": "0909090909",
            "email": "chi.thuy@gmail.com", "tax_code": "", "product_service": "meInvoice",
            "service_package": "Professional",
            "start_date": today - timedelta(days=350), "expiry_date": today + timedelta(days=15), "amount_due": 2000000,
            "balance": 500000
        },

        # --- NHÓM 5: KHÁCH HÀNG ĐÃ BỊ XÓA MỀM (is_deleted = True) ĐỂ TEST KHÔNG HIỂN THỊ TRÊN CÁC DANH SÁCH CHÍNH ---
        {
            "customer_name": "Khách Hàng Đã Xóa 1", "customer_type": "Cá nhân", "phone": "0988111222",
            "email": "del1@gmail.com", "tax_code": "", "product_service": "meInvoice", "service_package": "Standard",
            "start_date": today - timedelta(days=500), "expiry_date": today - timedelta(days=135),
            "amount_due": 1000000, "balance": 0, "is_deleted": True
        },
        {
            "customer_name": "Công ty Cổ phần Thất Bại", "customer_type": "Doanh nghiệp", "phone": "0243000000",
            "email": "closed@failure.com", "tax_code": "0100000000", "product_service": "MISA SME",
            "service_package": "Standard",
            "start_date": today - timedelta(days=450), "expiry_date": today - timedelta(days=85), "amount_due": 3000000,
            "balance": 0, "is_deleted": True
        },

        # --- NHÓM 6: CÁC TRƯỜNG HỢP KHÁC ĐỂ LÀM DÀY DỮ LIỆU (14 và 15) ---
        {
            "customer_name": "Đặng Hoàng Long", "customer_type": "Cá nhân", "phone": "0977223344",
            "email": "longdh@gmail.com", "tax_code": "", "product_service": "Bamboo", "service_package": "Enterprise",
            "start_date": today - timedelta(days=15), "expiry_date": today + timedelta(days=715), "amount_due": 6000000,
            "balance": 0
        },
        {
            "customer_name": "Hộ kinh doanh cá thể Toàn Phát", "customer_type": "Doanh nghiệp", "phone": "0283111222",
            "email": "toanphat@gmail.com", "tax_code": "0309998887", "product_service": "meInvoice",
            "service_package": "Professional",
            "start_date": today - timedelta(days=60), "expiry_date": today + timedelta(days=305), "amount_due": 2200000,
            "balance": 0
        }
    ]

    print(f"🔄 Bắt đầu sinh 15 khách hàng kiểm thử...")
    count = 0

    for data in mock_inputs:
        # Tự động sinh ID tăng dần dạng KH0001, KH0002... dựa vào tập dữ liệu hiện tại
        next_id = generate_next_customer_id(customers)

        # Tạo cấu trúc record hoàn chỉnh phù hợp với kiến trúc lưu trữ của hệ thống
        record = {
            "customer_id": next_id,
            "customer_name": data["customer_name"],
            "customer_type": data["customer_type"],
            "phone": data["phone"],
            "email": data["email"],
            "tax_code": data["tax_code"],
            "product_service": data["product_service"],
            "service_package": data["service_package"],
            "start_date": data["start_date"].strftime("%Y-%m-%d"),
            "expiry_date": data["expiry_date"].strftime("%Y-%m-%d"),
            "amount_due": float(data["amount_due"]),
            "balance": float(data["balance"]),
            "is_deleted": data.get("is_deleted", False)  # Nếu không có thì mặc định False (Chưa bị xóa)
        }

        customers.append(record)
        print(
            f"  ✅ Đã thêm: {record['customer_id']} - {record['customer_name']} ({record['product_service']} - {record['service_package']})")
        count += 1

    # Lưu toàn bộ dữ liệu mẫu vào file JSON cơ sở dữ liệu
    save_customers(customers)
    print(f"🎉 Hoàn thành! Đã nạp thành công {count} khách hàng vào hệ thống.")


if __name__ == "__main__":
    generate_mock_data()