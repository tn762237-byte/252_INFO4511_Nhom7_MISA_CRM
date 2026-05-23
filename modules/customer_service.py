"""
customer_service.py
===================
Module logic nghiệp vụ thuần (pure functions, không có I/O, không có framework).
Được dùng chung bởi CLI (main_cli.py) và Web UI (app.py).

Thay đổi so với phiên bản cũ:
- Bỏ trường `usage_duration_type`: tất cả dịch vụ đều CÓ THỜI HẠN (start_date + expiry_date bắt buộc).
- `email` trở thành bắt buộc (validate format + không được để trống).
- Bỏ toàn bộ logic kiểm tra trùng lặp (duplicate check).
- Trạng thái "Sắp hết hạn" (≤30 ngày) được giữ nhất quán ở mọi nơi.
- Thống nhất: validate ngày hết hạn phải STRICTLY lớn hơn ngày bắt đầu (app.py từng dùng >=, nay đồng nhất >).
- tax_code cho phép 10, 12 hoặc 13 chữ số — thông điệp lỗi khớp hoàn toàn.
- service_status và payment_status KHÔNG lưu vào JSON, chỉ tính khi cần qua enrich_customer().
- Soft delete chặn xóa khi dịch vụ "Hoạt động" HOẶC "Sắp hết hạn" hoặc còn công nợ.
"""

import re
import unicodedata
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# HẰNG SỐ NGHIỆP VỤ
# ---------------------------------------------------------------------------

PRODUCTS = ["meInvoice", "MISA SME", "MISA AMIS", "Bamboo"]
PACKAGES = ["Standard", "Professional", "Enterprise"]
CUSTOMER_TYPES = ["Cá nhân", "Doanh nghiệp"]
SERVICE_STATUS_ALL = ["Tất cả", "Hoạt động", "Sắp hết hạn", "Hết hạn", "Đã xóa"]


# ---------------------------------------------------------------------------
# NHÓM HÀM CHUẨN HÓA
# ---------------------------------------------------------------------------

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_spaces(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def remove_accents(text: Any) -> str:
    text = str(text or "")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D")


def normalize_keyword(text: Any) -> str:
    return remove_accents(normalize_spaces(text)).lower()


def digits_only(text: Any) -> str:
    return re.sub(r"\D", "", str(text or ""))


def parse_date(date_text: str) -> date:
    """Chuyển chuỗi YYYY-MM-DD sang kiểu date. Ném ValueError nếu sai."""
    return datetime.strptime(normalize_spaces(date_text), "%Y-%m-%d").date()


# ---------------------------------------------------------------------------
# NHÓM HÀM SINH MÃ KHÁCH HÀNG
# ---------------------------------------------------------------------------

def parse_customer_no(customer_id: str) -> int:
    match = re.search(r"KH(\d+)$", str(customer_id or "").upper())
    return int(match.group(1)) if match else 0


def generate_next_customer_id(customers: List[Dict[str, Any]]) -> str:
    """Sinh mã KH dựa trên số lớn nhất từng tồn tại, kể cả bản ghi đã xóa."""
    max_no = max((parse_customer_no(c.get("customer_id", "")) for c in customers), default=0)
    return f"KH{max_no + 1:03d}"


# ---------------------------------------------------------------------------
# NHÓM HÀM KIỂM TRA ĐỊNH DẠNG
# ---------------------------------------------------------------------------

def phone_is_valid(phone: Any) -> bool:
    """10 chữ số, bắt đầu bằng 0."""
    d = digits_only(phone)
    return len(d) == 10 and d.startswith("0")


def email_is_valid(email: Any) -> bool:
    """Email bắt buộc: không được trống và phải đúng định dạng."""
    email = normalize_spaces(email)
    if not email:
        return False
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}$", email))


def tax_code_is_valid(tax_code: Any) -> bool:
    """MST có thể trống (với cá nhân). Nếu nhập: 10, 12 hoặc 13 chữ số."""
    tax_code = normalize_spaces(tax_code)
    if not tax_code:
        return True
    return len(digits_only(tax_code)) in (10, 12, 13)


# ---------------------------------------------------------------------------
# NHÓM HÀM TÍNH TRẠNG THÁI
# ---------------------------------------------------------------------------

def calculate_service_status(expiry_date: str) -> str:
    """
    Tính trạng thái dịch vụ dựa trên ngày hết hạn (tất cả dịch vụ đều có thời hạn).

    - Ngày hết hạn đã qua          → "Hết hạn"
    - Còn ≤ 30 ngày                → "Sắp hết hạn"
    - Còn > 30 ngày                → "Hoạt động"
    - Ngày hết hạn không hợp lệ   → "Hết hạn"
    """
    try:
        exp = datetime.strptime(str(expiry_date), "%Y-%m-%d").date()
    except Exception:
        return "Hết hạn"

    today = date.today()
    days_left = (exp - today).days

    if days_left < 0:
        return "Hết hạn"
    if days_left <= 30:
        return "Sắp hết hạn"
    return "Hoạt động"


def calculate_payment_status(balance: float) -> str:
    """
    - balance == 0   → Đã thanh toán
    - balance > 0    → Chưa thanh toán  (khách còn nợ)
    - balance < 0    → Đã thanh toán (dư) (công ty nợ khách)
    """
    if balance == 0:
        return "Đã thanh toán"
    if balance > 0:
        return "Chưa thanh toán"
    return f"Đã thanh toán (Dư: {abs(balance):,.0f} VND)"


# ---------------------------------------------------------------------------
# NHÓM HÀM LÀM GIÀU DỮ LIỆU
# ---------------------------------------------------------------------------

def enrich_customer(customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tính service_status và payment_status tại runtime (không lưu vào JSON).
    Trả về bản sao — không thay đổi dict gốc.
    """
    c = dict(customer)
    if c.get("is_deleted", False):
        c["service_status"] = "Đã xóa"
    else:
        c["service_status"] = calculate_service_status(c.get("expiry_date", ""))
    c["payment_status"] = calculate_payment_status(float(c.get("balance", 0) or 0))
    return c


# ---------------------------------------------------------------------------
# NHÓM HÀM LỌC DANH SÁCH
# ---------------------------------------------------------------------------

def active_customers(customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Trả về danh sách chưa bị xóa mềm."""
    return [c for c in customers if not c.get("is_deleted", False)]


# ---------------------------------------------------------------------------
# XÂY DỰNG BẢN GHI
# ---------------------------------------------------------------------------

def build_customer_record(
    customer_id: str,
    customer_name: str,
    customer_type: str,
    phone: str,
    email: str,
    address: str,
    representative: str,
    tax_code: str,
    product_service: str,
    service_package: str,
    start_date_value: Optional[date],
    expiry_date_value: Optional[date],
    balance: float,
    notes: str,
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None,
    is_deleted: bool = False,
    deleted_at: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Tạo dict khách hàng theo Data Schema chuẩn.
    service_status và payment_status KHÔNG được lưu vào dict — tính runtime qua enrich_customer().
    """
    customer_id    = normalize_spaces(customer_id).upper()
    customer_name  = normalize_spaces(customer_name)
    customer_type  = normalize_spaces(customer_type)
    phone          = digits_only(phone)
    email          = normalize_spaces(email).lower()
    address        = normalize_spaces(address)
    representative = normalize_spaces(representative) or None
    tax_code       = digits_only(tax_code) or None
    notes          = normalize_spaces(notes)
    balance        = float(balance or 0)

    # Cá nhân: không cần representative / tax_code dù người dùng tình cờ nhập
    if customer_type == "Cá nhân":
        representative = representative or None
        tax_code       = tax_code or None

    start_date_str  = start_date_value.strftime("%Y-%m-%d") if isinstance(start_date_value, date) else ""
    expiry_date_str = expiry_date_value.strftime("%Y-%m-%d") if isinstance(expiry_date_value, date) else ""

    current_time = now_str()
    return {
        "customer_id":    customer_id,
        "customer_name":  customer_name,
        "customer_type":  customer_type,
        "phone":          phone,
        "email":          email,
        "address":        address,
        "representative": representative,
        "tax_code":       tax_code,
        "product_service": product_service,
        "service_package": service_package,
        "start_date":     start_date_str,
        "expiry_date":    expiry_date_str,
        "balance":        balance,
        "notes":          notes,
        "created_at":     created_at or current_time,
        "updated_at":     updated_at or current_time,
        "is_deleted":     is_deleted,
        "deleted_at":     deleted_at,
    }


# ---------------------------------------------------------------------------
# VALIDATE
# ---------------------------------------------------------------------------

def validate_customer_record(
    customer: Dict[str, Any],
    customers: List[Dict[str, Any]],
    current_id: Optional[str] = None,
) -> List[str]:
    """
    Kiểm tra toàn bộ ràng buộc trước khi thêm / cập nhật.
    Trả về danh sách lỗi; danh sách rỗng = hợp lệ.
    """
    errors: List[str] = []

    # --- Trường bắt buộc ---
    required_fields: Dict[str, str] = {
        "customer_id":      "Mã khách hàng",
        "customer_name":    "Tên khách hàng",
        "customer_type":    "Loại khách hàng",
        "phone":            "Số điện thoại",
        "email":            "Email",
        "address":          "Địa chỉ",
        "product_service":  "Sản phẩm cung cấp",
        "service_package":  "Gói dịch vụ",
        "start_date":       "Ngày bắt đầu",
        "expiry_date":      "Ngày hết hạn",
    }
    for key, label in required_fields.items():
        if not customer.get(key):
            errors.append(f"{label} không được để trống.")

    # --- Enum ---
    if customer.get("customer_type") not in CUSTOMER_TYPES:
        errors.append("Loại khách hàng chỉ được chọn: Cá nhân hoặc Doanh nghiệp.")

    if customer.get("product_service") not in PRODUCTS:
        errors.append(f"Sản phẩm cung cấp không hợp lệ. Chọn một trong: {', '.join(PRODUCTS)}.")

    if customer.get("service_package") not in PACKAGES:
        errors.append(f"Gói dịch vụ không hợp lệ. Chọn một trong: {', '.join(PACKAGES)}.")

    # --- Định dạng liên hệ ---
    if not phone_is_valid(customer.get("phone", "")):
        errors.append("Số điện thoại phải gồm đúng 10 chữ số và bắt đầu bằng số 0.")

    if not email_is_valid(customer.get("email", "")):
        errors.append("Email không được để trống và phải đúng định dạng (ví dụ: abc@gmail.com).")

    if not tax_code_is_valid(customer.get("tax_code", "")):
        errors.append("Mã số thuế phải gồm 10, 12 hoặc 13 chữ số.")

    # --- Ràng buộc theo loại khách hàng ---
    if customer.get("customer_type") == "Doanh nghiệp":
        if not customer.get("representative"):
            errors.append("Khách hàng Doanh nghiệp bắt buộc nhập người đại diện.")
        if not customer.get("tax_code"):
            errors.append("Khách hàng Doanh nghiệp bắt buộc nhập mã số thuế.")

    # --- Ngày tháng ---
    if customer.get("start_date") and customer.get("expiry_date"):
        try:
            start  = parse_date(customer["start_date"])
            expiry = parse_date(customer["expiry_date"])
            if expiry <= start:
                errors.append("Ngày hết hạn phải lớn hơn ngày bắt đầu.")
        except Exception:
            errors.append("Ngày bắt đầu hoặc ngày hết hạn không đúng định dạng YYYY-MM-DD.")

    # --- Giới hạn độ dài ---
    if len(str(customer.get("address", "") or "")) > 250:
        errors.append("Địa chỉ không được vượt quá 250 ký tự.")

    if len(str(customer.get("notes", "") or "")) > 500:
        errors.append("Ghi chú không được vượt quá 500 ký tự.")

    return errors


# ---------------------------------------------------------------------------
# TÌM KIẾM
# ---------------------------------------------------------------------------

def find_customer_by_id(
    customers: List[Dict[str, Any]], customer_id: str
) -> Optional[Dict[str, Any]]:
    customer_id = normalize_spaces(customer_id).upper()
    for c in customers:
        if c.get("customer_id") == customer_id:
            return c
    return None


def search_customers(
    customers: List[Dict[str, Any]],
    keyword: str,
    status_filter: str = "Tất cả",
    include_deleted: bool = False,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Tìm theo từ khóa (mã KH, tên, SĐT, email), sau đó lọc theo trạng thái.

    Trả về (danh sách kết quả, thông báo lỗi).
    Thông báo lỗi rỗng = tìm thấy kết quả.
    """
    raw_keyword = normalize_spaces(keyword)
    key         = normalize_keyword(raw_keyword)
    phone_key   = digits_only(raw_keyword)

    if not key and not phone_key:
        return [], "Vui lòng nhập từ khóa tìm kiếm."

    is_email_keyword = "@" in raw_keyword or (
        "." in raw_keyword and not raw_keyword.replace(".", "").isdigit()
    )

    keyword_results: List[Dict[str, Any]] = []
    for customer in customers:
        c = enrich_customer(customer)
        if not include_deleted and c.get("is_deleted"):
            continue
        matched = (
            key in normalize_keyword(c.get("customer_id", ""))
            or key in normalize_keyword(c.get("customer_name", ""))
            or (bool(phone_key) and phone_key in digits_only(c.get("phone", "")))
            or (is_email_keyword and key in normalize_keyword(c.get("email", "")))
        )
        if matched:
            keyword_results.append(c)

    if not keyword_results:
        return [], "Không tìm thấy khách hàng phù hợp với từ khóa đã nhập."

    if status_filter == "Tất cả":
        final_results = keyword_results
    else:
        final_results = [c for c in keyword_results if c.get("service_status") == status_filter]

    if not final_results:
        return [], (
            f"Tìm thấy {len(keyword_results)} khách hàng khớp từ khóa, "
            f"nhưng không có khách hàng nào ở trạng thái '{status_filter}'."
        )

    return final_results, ""


# ---------------------------------------------------------------------------
# XÓA MỀM
# ---------------------------------------------------------------------------

def soft_delete_customer(
    customers: List[Dict[str, Any]], customer_id: str
) -> Tuple[bool, str]:
    """
    Xóa mềm khách hàng.

    Điều kiện chặn xóa:
    - Không tìm thấy / đã xóa trước đó.
    - Dịch vụ đang "Hoạt động" hoặc "Sắp hết hạn" (vẫn còn hiệu lực).
    - Còn công nợ (balance != 0).
    """
    customer = find_customer_by_id(customers, customer_id)
    if not customer:
        return False, "Không tìm thấy khách hàng."
    if customer.get("is_deleted"):
        return False, "Khách hàng này đã bị xóa trước đó."

    c = enrich_customer(customer)
    status = c.get("service_status", "")
    if status in ("Hoạt động", "Sắp hết hạn"):
        return False, (
            f"Không thể xóa khách hàng khi dịch vụ đang '{status}'. "
            "Vui lòng chờ hết hạn hoặc cập nhật trạng thái trước."
        )

    balance = float(c.get("balance", 0) or 0)
    if balance != 0:
        return False, (
            f"Không thể xóa vì khách hàng còn công nợ: {balance:,.0f} VND. "
            "Vui lòng xử lý tất toán trước khi xóa."
        )

    customer["is_deleted"]  = True
    customer["deleted_at"]  = now_str()
    customer["updated_at"]  = now_str()
    return True, (
        f"Đã xóa khách hàng {customer.get('customer_id')} - {customer.get('customer_name')}."
    )


# ---------------------------------------------------------------------------
# XUẤT DỮ LIỆU BẢNG
# ---------------------------------------------------------------------------

def customers_to_rows(customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Chuyển danh sách dict sang list of dict dạng bảng để hiển thị.
    Bao gồm cả cột Thời gian còn lại để người dùng nắm nhanh tình trạng.
    """
    rows: List[Dict[str, Any]] = []
    today = date.today()

    for idx, customer in enumerate(customers, start=1):
        c = enrich_customer(customer)

        # Tính số ngày còn lại
        try:
            exp        = parse_date(c.get("expiry_date", ""))
            days_left  = (exp - today).days
            days_label = f"{days_left} ngày" if days_left >= 0 else "Đã hết hạn"
        except Exception:
            days_label = "—"

        rows.append({
            "STT":            idx,
            "Mã KH":          c.get("customer_id", ""),
            "Tên khách hàng": c.get("customer_name", ""),
            "Loại KH":        c.get("customer_type", ""),
            "SĐT":            c.get("phone", ""),
            "Email":          c.get("email", ""),
            "Sản phẩm":       c.get("product_service", ""),
            "Gói DV":         c.get("service_package", ""),
            "Ngày bắt đầu":   c.get("start_date", ""),
            "Ngày hết hạn":   c.get("expiry_date", ""),
            "Còn lại":        days_label,
            "Trạng thái":     c.get("service_status", ""),
            "Công nợ":        f"{float(c.get('balance', 0) or 0):,.0f} VND",
            "Đã xóa":         bool(c.get("is_deleted", False)),
        })
    return rows
