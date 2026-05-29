from datetime import date
from typing import Any, Dict, List, Optional
import pandas as pd
from modules.customer_service import (
    CUSTOMER_TYPES,
    PACKAGES,
    PRODUCTS,
    SERVICE_STATUS_ALL,
    active_customers,
    build_customer_record,
    customers_to_rows,
    enrich_customer,
    find_customer_by_id,
    generate_next_customer_id,
    normalize_keyword,
    normalize_spaces,
    parse_date,
    phone_is_valid,
    email_is_valid,
    tax_code_is_valid,
    search_customers,
    soft_delete_customer,
    validate_customer_record,
)
from modules.storage import load_customers, save_customers

# HIỂN THỊ DỮ LIỆU
def show_table(customers: List[Dict[str, Any]]) -> None:
    rows = customers_to_rows(customers)
    if not rows:
        print("Không có dữ liệu để hiển thị.")
        return
    try:
        from IPython.display import display
        display(pd.DataFrame(rows))
    except Exception:
        df = pd.DataFrame(rows)
        print(df.to_string(index=False))

def show_customer_detail(customer: Dict[str, Any]) -> None:
    c = enrich_customer(customer)
    fields = [
        ("Mã khách hàng",         c.get("customer_id", "")),
        ("Tên khách hàng",        c.get("customer_name", "")),
        ("Loại khách hàng",       c.get("customer_type", "")),
        ("Số điện thoại",         c.get("phone", "")),
        ("Email",                 c.get("email", "")),
        ("Địa chỉ",               c.get("address", "")),
        ("Người đại diện",        c.get("representative") or "—"),
        ("Mã số thuế",            c.get("tax_code") or "—"),
        ("Sản phẩm",              c.get("product_service", "")),
        ("Gói dịch vụ",           c.get("service_package", "")),
        ("Ngày bắt đầu",          c.get("start_date", "")),
        ("Ngày hết hạn",          c.get("expiry_date", "")),
        ("Trạng thái dịch vụ",    c.get("service_status", "")),
        ("Trạng thái thanh toán", c.get("payment_status", "")),
        ("Công nợ",               f"{float(c.get('balance', 0) or 0):,.0f} VND"),
        ("Ghi chú",               c.get("notes", "") or "—"),
        ("Tạo lúc",               c.get("created_at", "")),
        ("Cập nhật lúc",          c.get("updated_at", "")),
        ("Đã xóa",                c.get("is_deleted", False)),
        ("Xóa lúc",               c.get("deleted_at") or "—"),
    ]
    detail = pd.DataFrame(fields, columns=["Trường thông tin", "Giá trị"])
    try:
        from IPython.display import display
        display(detail)
    except Exception:
        print(detail.to_string(index=False))

def print_validation_errors(errors: List[str]) -> None:
    if errors:
        print("Dữ liệu chưa hợp lệ. Vui lòng kiểm tra:")
        for err in errors:
            print(f"  ⚠️  {err}")

# NHÓM HÀM NHẬP LIỆU CẢNH BÁO TỨC THỜI
def input_non_empty(label: str, max_length: Optional[int] = None) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if not value:
            print(f"⚠️  {label} không được để trống.")
            continue
        if max_length and len(value) > max_length:
            print(f"⚠️  {label} không được vượt quá {max_length} ký tự.")
            continue
        return value
def input_customer_type() -> str:
    while True:
        print("Loại khách hàng:")
        print(" 1. Cá nhân")
        print(" 2. Doanh nghiệp")

        value = input("Chọn loại khách hàng
        if value == "1":
            return "Cá nhân"

        if value == "2":
            return "Doanh nghiệp"

        for item in CUSTOMER_TYPES:
            if normalize_keyword(value) == normalize_keyword(item):
                return item

        print("⚠️ Lựa chọn không hợp lệ. Vui lòng nhập 1, 2, Cá nhân hoặc Doanh nghiệp.")

def input_phone() -> str:
    while True:
        phone = input("Số điện thoại: ").strip()
        if phone_is_valid(phone):
            return phone
        print("⚠️  Số điện thoại phải gồm đúng 10 chữ số và bắt đầu bằng số 0.")

def input_email() -> str:
    while True:
        email = input("Email: ").strip()
        if email_is_valid(email):
            return email
        print("⚠️  Email không được để trống và phải đúng định dạng (ví dụ: abc@gmail.com).")

def input_tax_code() -> str:
    """Mã số thuế bắt buộc với mọi loại khách hàng."""
    while True:
        tax_code = input("Mã số thuế *: ").strip()
        if not tax_code:
            print("⚠️  Mã số thuế không được để trống.")
            continue
        if not tax_code_is_valid(tax_code):
            print("⚠️  Mã số thuế phải gồm 10, 12 hoặc 13 chữ số.")
            continue
        return tax_code

def input_representative(required: bool = False) -> str:
    while True:
        value = input("Người đại diện: ").strip()
        if required and not value:
            print("⚠️  Khách hàng Doanh nghiệp bắt buộc nhập người đại diện.")
            continue
        return value

def input_choice_from_list(label: str, choices: List[str]) -> str:
    while True:
        print(f"{label}:")
        for i, item in enumerate(choices, start=1):
            print(f"  {i}. {item}")
        value = input(f"Chọn {label.lower()} (số thứ tự hoặc tên): ").strip()
        if value.isdigit() and 1 <= int(value) <= len(choices):
            return choices[int(value) - 1]
        for item in choices:
            if normalize_keyword(value) == normalize_keyword(item):
                return item
        print(f"⚠️  {label} không hợp lệ.")

def input_date_required(label: str) -> date:
    while True:
        value = input(f"{label} (YYYY-MM-DD, ví dụ 2026-05-21): ").strip()
        try:
            return parse_date(value)
        except Exception:
            print("⚠️  Ngày không hợp lệ. Vui lòng nhập đúng định dạng YYYY-MM-DD.")

def input_date_range() -> tuple:
    """Nhập ngày bắt đầu và ngày hết hạn, đảm bảo hết hạn > bắt đầu."""
    while True:
        start  = input_date_required("Ngày bắt đầu")
        expiry = input_date_required("Ngày hết hạn")
        if expiry <= start:
            print("⚠️  Ngày hết hạn phải lớn hơn ngày bắt đầu. Vui lòng nhập lại.")
            continue
        return start, expiry

def input_float_non_negative(label: str, default: float = 0) -> float:
    while True:
        value = input(f"{label} (Enter để bỏ qua, mặc định {default:,.0f}): ").strip()
        if value == "":
            return default
        try:
            f = float(value)
            if f < 0:
                print("⚠️  Giá trị không được âm.")
                continue
            return f
        except ValueError:
            print("⚠️  Vui lòng nhập số hợp lệ.")

def input_notes() -> str:
    while True:
        notes = input("Ghi chú: ").strip()
        if len(notes) <= 500:
            return notes
        print("⚠️  Ghi chú không được vượt quá 500 ký tự.")

# CÁC THAO TÁC NGHIỆP VỤ
def add_customer() -> None:
    print("\n" + "─" * 60)
    print("NHẬP THÔNG TIN KHÁCH HÀNG MỚI")
    print("─" * 60)

    customers = load_customers()
    next_id   = generate_next_customer_id(customers)
    print(f"Mã khách hàng được sinh tự động: {next_id}")

    customer_name = input_non_empty("Tên khách hàng")
    customer_type = input_customer_type()
    phone         = input_phone()
    email         = input_email()
    address       = input_non_empty("Địa chỉ", max_length=250)

    # Người đại diện: bắt buộc với Doanh nghiệp
    if customer_type == "Doanh nghiệp":
        representative = input_representative(required=True)
    else:
        representative = input_representative(required=False)

    # Mã số thuế: bắt buộc với mọi loại khách hàng
    tax_code = input_tax_code()
    product_service         = input_choice_from_list("Sản phẩm cung cấp", PRODUCTS)
    service_package         = input_choice_from_list("Gói dịch vụ", PACKAGES)
    start_date, expiry_date = input_date_range()
    balance                 = input_float_non_negative("Công nợ (VND)")
    notes                   = input_notes()

    record = build_customer_record(
        customer_id=next_id,
        customer_name=customer_name,
        customer_type=customer_type,
        phone=phone,
        email=email,
        address=address,
        representative=representative,
        tax_code=tax_code,
        product_service=product_service,
        service_package=service_package,
        start_date_value=start_date,
        expiry_date_value=expiry_date,
        balance=balance,
        notes=notes,
    )
    errors = validate_customer_record(record, customers)
    if errors:
        print_validation_errors(errors)
        return

    customers.append(record)
    save_customers(customers)
    print(f"\n✅  Thêm khách hàng thành công! Mã: {next_id}")
    show_customer_detail(record)

def delete_customer() -> None:
    print("\n" + "─" * 60)
    print("XÓA THÔNG TIN KHÁCH HÀNG")
    print("─" * 60)

    customers   = load_customers()
    customer_id = input("Nhập mã khách hàng cần xóa (ví dụ KH001): ").strip()
    ok, msg     = soft_delete_customer(customers, customer_id)

    if ok:
        save_customers(customers)
        print(f"✅  {msg}")
    else:
        print(f"⚠️  {msg}")

def update_customer_cli() -> None:
    print("\n" + "─" * 60)
    print("CẬP NHẬT THÔNG TIN KHÁCH HÀNG")
    print("─" * 60)

    customers   = load_customers()
    customer_id = input("Nhập mã khách hàng cần cập nhật (ví dụ KH001): ").strip()
    old         = find_customer_by_id(customers, customer_id)

    if old is None:
        print("⚠️  Không tìm thấy khách hàng.")
        return
    if old.get("is_deleted"):
        print("⚠️  Không thể cập nhật khách hàng đã xóa.")
        return

    print("\nThông tin hiện tại:")
    show_customer_detail(old)

    field_labels: Dict[str, str] = {
        "customer_name":   "Tên khách hàng",
        "customer_type":   "Loại khách hàng",
        "phone":           "Số điện thoại",
        "email":           "Email",
        "address":         "Địa chỉ",
        "representative":  "Người đại diện",
        "tax_code":        "Mã số thuế",
        "product_service": "Sản phẩm cung cấp",
        "service_package": "Gói dịch vụ",
        "start_date":      "Ngày bắt đầu",
        "expiry_date":     "Ngày hết hạn",
        "balance":         "Công nợ",
        "notes":           "Ghi chú",
    }
    allowed_fields = list(field_labels.keys())
    label_to_field = {normalize_keyword(v): k for k, v in field_labels.items()}

    print("\nCác trường có thể cập nhật:")
    for i, field in enumerate(allowed_fields, start=1):
        print(f"  {i:2}. {field_labels[field]}")

    fields_to_update: Dict[str, Any] = {}

    while True:
        raw = input("\nNhập số thứ tự hoặc tên trường (Enter để kết thúc): ").strip()
        if raw == "":
            break

        if raw.isdigit() and 1 <= int(raw) <= len(allowed_fields):
            field = allowed_fields[int(raw) - 1]
        else:
            field = label_to_field.get(normalize_keyword(raw), raw)

        if field not in allowed_fields:
            print("⚠️  Trường không hợp lệ.")
            continue

        label = field_labels[field]
        print(f"Giá trị hiện tại — {label}: {old.get(field, '')}")

        if field == "customer_name":
            value = input_non_empty("Tên khách hàng")
        elif field == "customer_type":
            value = input_customer_type()
            # Nếu đổi sang Doanh nghiệp và chưa có đại diện thì bắt nhập ngay
            if value == "Doanh nghiệp":
                if not fields_to_update.get("representative", old.get("representative")):
                    fields_to_update["representative"] = input_representative(required=True)
        elif field == "phone":
            value = input_phone()
        elif field == "email":
            value = input_email()
        elif field == "address":
            value = input_non_empty("Địa chỉ", max_length=250)
        elif field == "representative":
            required = (
                fields_to_update.get("customer_type", old.get("customer_type")) == "Doanh nghiệp"
            )
            value = input_representative(required=required)
        elif field == "tax_code":
            # Mã số thuế bắt buộc với mọi loại KH
            value = input_tax_code()
        elif field == "product_service":
            value = input_choice_from_list("Sản phẩm cung cấp", PRODUCTS)
        elif field == "service_package":
            value = input_choice_from_list("Gói dịch vụ", PACKAGES)
        elif field in ("start_date", "expiry_date"):
            value_date = input_date_required(label)
            value      = value_date.strftime("%Y-%m-%d")
        elif field == "balance":
            value = input_float_non_negative("Công nợ (VND)")
        elif field == "notes":
            value = input_notes()
        else:
            value = input(f"{label}: ").strip()

        fields_to_update[field] = value
        print(f"✔  Ghi nhận: {label} = {value}")

    if not fields_to_update:
        print("Không có thay đổi nào được ghi nhận.")
        return

    print("\nTóm tắt thay đổi trước khi lưu:")
    for k, v in fields_to_update.items():
        print(f"  {field_labels.get(k, k)}: {old.get(k, '')}  →  {v}")

    confirm = input("Xác nhận lưu? [Y/N]: ").strip().lower()
    if confirm != "y":
        print("Đã hủy thao tác.")
        return

    merged = dict(old)
    merged.update(fields_to_update)

    try:
        start_value  = parse_date(merged.get("start_date", ""))
        expiry_value = parse_date(merged.get("expiry_date", ""))
    except Exception:
        print("⚠️  Ngày bắt đầu hoặc ngày hết hạn không hợp lệ sau khi hợp nhất dữ liệu.")
        return

    updated_record = build_customer_record(
        customer_id=old.get("customer_id", ""),
        customer_name=merged.get("customer_name", ""),
        customer_type=merged.get("customer_type", ""),
        phone=merged.get("phone", ""),
        email=merged.get("email", ""),
        address=merged.get("address", ""),
        representative=merged.get("representative") or "",
        tax_code=merged.get("tax_code") or "",
        product_service=merged.get("product_service", ""),
        service_package=merged.get("service_package", ""),
        start_date_value=start_value,
        expiry_date_value=expiry_value,
        balance=float(merged.get("balance", 0) or 0),
        notes=merged.get("notes", ""),
        created_at=old.get("created_at"),
        is_deleted=old.get("is_deleted", False),
        deleted_at=old.get("deleted_at"),
    )
    errors = validate_customer_record(updated_record, customers, current_id=old.get("customer_id"))
    if errors:
        print_validation_errors(errors)
        return

    for idx, c in enumerate(customers):
        if c.get("customer_id") == old.get("customer_id"):
            customers[idx] = updated_record
            break

    save_customers(customers)
    print("\n✅  Cập nhật thành công!")
    show_customer_detail(updated_record)

def search_customers_cli() -> None:
    print("\n" + "─" * 60)
    print("TÌM KIẾM THÔNG TIN KHÁCH HÀNG")
    print("─" * 60)

    customers = load_customers()
    keyword   = input("Từ khóa (mã KH, tên, SĐT, email): ").strip()

    print("Lọc theo trạng thái:")
    for i, s in enumerate(SERVICE_STATUS_ALL, start=1):
        print(f"  {i}. {s}")
    raw_filter = input("Chọn trạng thái (Enter = Tất cả): ").strip()
    if raw_filter.isdigit() and 1 <= int(raw_filter) <= len(SERVICE_STATUS_ALL):
        status_filter = SERVICE_STATUS_ALL[int(raw_filter) - 1]
    else:
        status_filter = "Tất cả"

    include_deleted = input("Bao gồm khách hàng đã xóa? [Y/N]: ").strip().lower() == "y"

    results, message = search_customers(customers, keyword, status_filter, include_deleted)
    if message:
        print(f"  {message}")
        return

    print(f"\nKết quả tìm kiếm: {len(results)} bản ghi")
    show_table(results)

    view_detail = input("Xem chi tiết khách hàng? Nhập mã KH (Enter để bỏ qua): ").strip()
    if view_detail:
        found = find_customer_by_id(results, view_detail)
        if found:
            show_customer_detail(found)
        else:
            print("⚠️  Mã không nằm trong kết quả tìm kiếm.")

def list_customers_cli() -> None:
    print("\n" + "─" * 60)
    print("XEM DANH SÁCH KHÁCH HÀNG")
    print("─" * 60)

    customers = load_customers()
    result    = [enrich_customer(c) for c in active_customers(customers)]

    print(f"Tổng bản ghi trong file: {len(customers)}")
    print(f"Khách hàng chưa xóa:     {len(result)}")
    show_table(result)

    if result:
        view_detail = input("Xem chi tiết? Nhập mã KH (Enter để bỏ qua): ").strip()
        if view_detail:
            found = find_customer_by_id(result, view_detail)
            if found:
                show_customer_detail(found)
            else:
                print("⚠️  Không tìm thấy mã trong danh sách đang hiển thị.")

# MENU CHÍNH
def print_menu() -> None:
    print("\n" + "═" * 65)
    print("     CHƯƠNG TRÌNH QUẢN LÝ KHÁCH HÀNG MISA")
    print("═" * 65)
    print("  1. Nhập thông tin khách hàng mới")
    print("  2. Xóa thông tin khách hàng")
    print("  3. Cập nhật thông tin khách hàng")
    print("  4. Tìm kiếm thông tin khách hàng")
    print("  5. Xem danh sách khách hàng")
    print("  0. Thoát")
    print("═" * 65)

def main_menu() -> None:
    while True:
        print_menu()
        choice = input("Chọn chức năng: ").strip()

        if choice == "1":
            add_customer()
        elif choice == "2":
            delete_customer()
        elif choice == "3":
            update_customer_cli()
        elif choice == "4":
            search_customers_cli()
        elif choice == "5":
            list_customers_cli()
        elif choice == "0":
            print("Kết thúc chương trình.")
            break
        else:
            print("⚠️  Lựa chọn không hợp lệ.")

if __name__ == "__main__":
    main_menu()
    
