"""
app.py
======
Giao diện web Streamlit quản lý khách hàng MISA.
Chạy: streamlit run app.py

Mọi logic nghiệp vụ đều gọi từ modules/customer_service.py.
File này chỉ chịu trách nhiệm về UI và trạng thái session.
"""

from datetime import date, timedelta
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

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
    search_customers,
    soft_delete_customer,
    validate_customer_record,
    phone_is_valid,
    email_is_valid,
    tax_code_is_valid,
)
from modules.storage import load_customers, save_customers


# ---------------------------------------------------------------------------
# CẤU HÌNH TRANG
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Quản lý khách hàng MISA", layout="wide")

st.markdown(
    """
    <style>
        .main-title {
            background: linear-gradient(90deg, #0052cc, #0078d4);
            color: white;
            padding: 18px 24px;
            border-radius: 12px;
            text-align: center;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 18px;
        }
        .section-title {
            color: #0052cc;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 16px;
        }
        .note-box {
            background: #fff7e6;
            border: 1px solid #ffd591;
            border-radius: 10px;
            padding: 12px 16px;
            margin-top: 16px;
        }
        .detail-box {
            background: #f8fbff;
            border: 1px solid #d6e4f5;
            border-radius: 12px;
            padding: 18px 20px;
            margin-top: 14px;
        }
        .small-muted { color: #64748b; font-size: 13px; }
        div.stButton > button:first-child { border-radius: 9px; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">QUẢN LÝ KHÁCH HÀNG MISA</div>', unsafe_allow_html=True)

# Flash messages toàn cục (dùng cho Cập nhật / Xóa)
if "flash_success" in st.session_state:
    st.success(st.session_state.pop("flash_success"))
if "flash_error" in st.session_state:
    st.error(st.session_state.pop("flash_error"))

customers: List[Dict[str, Any]] = load_customers()


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def safe_date(value: Any, default: date | None = None) -> date:
    """Chuyển chuỗi YYYY-MM-DD sang date; dùng cho st.date_input."""
    if default is None:
        default = date.today()
    try:
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            return date.fromisoformat(value)
    except Exception:
        pass
    return default


def render_customer_detail(customer: Dict[str, Any]) -> None:
    if not customer:
        st.info("Chưa có khách hàng để hiển thị chi tiết.")
        return
    c = enrich_customer(customer)
    st.markdown('<div class="detail-box">', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        st.write(f"**Mã khách hàng:** {c.get('customer_id', '')}")
        st.write(f"**Tên khách hàng:** {c.get('customer_name', '')}")
        st.write(f"**Loại khách hàng:** {c.get('customer_type', '')}")
        st.write(f"**Số điện thoại:** {c.get('phone', '')}")
        st.write(f"**Email:** {c.get('email', '')}")
        st.write(f"**Địa chỉ:** {c.get('address', '')}")
        st.write(f"**Người đại diện:** {c.get('representative') or '—'}")
        st.write(f"**Mã số thuế:** {c.get('tax_code') or '—'}")
    with right:
        st.write(f"**Sản phẩm:** {c.get('product_service', '')}")
        st.write(f"**Gói dịch vụ:** {c.get('service_package', '')}")
        st.write(f"**Ngày bắt đầu:** {c.get('start_date', '')}")
        st.write(f"**Ngày hết hạn:** {c.get('expiry_date', '')}")
        st.write(f"**Trạng thái dịch vụ:** {c.get('service_status', '')}")
        st.write(f"**Trạng thái thanh toán:** {c.get('payment_status', '')}")
        st.write(f"**Công nợ:** {float(c.get('balance', 0) or 0):,.0f} VND")
    st.write(f"**Ghi chú:** {c.get('notes', '') or '—'}")
    st.write(
        f"**Tạo lúc:** {c.get('created_at', '')} | "
        f"**Cập nhật:** {c.get('updated_at', '')} | "
        f"**Xóa lúc:** {c.get('deleted_at') or '—'}"
    )
    st.markdown("</div>", unsafe_allow_html=True)


def show_error_once(live_errors: List[str], message: str) -> None:
    """Hiển thị lỗi tức thời và ghi nhận để chặn lưu."""
    if message not in live_errors:
        live_errors.append(message)
    st.error(message)


# ---------------------------------------------------------------------------
# QUẢN LÝ FORM THÊM MỚI
# ---------------------------------------------------------------------------

ADD_FORM_KEYS = [
    "add_customer_name", "add_customer_type", "add_phone", "add_email",
    "add_address", "add_representative", "add_tax_code", "add_product",
    "add_package", "add_start_date", "add_expiry_date", "add_balance", "add_notes",
]


def reset_add_form_if_needed() -> None:
    if st.session_state.pop("reset_add_form", False):
        for key in ADD_FORM_KEYS:
            st.session_state.pop(key, None)


# ---------------------------------------------------------------------------
# SIDEBAR MENU
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## MISA")
    st.markdown("### Menu chức năng")
    menu = st.radio(
        "Chọn chức năng",
        [
            "Nhập thông tin khách hàng",
            "Cập nhật thông tin khách hàng",
            "Tìm kiếm thông tin khách hàng",
            "Xóa thông tin khách hàng",
            "Xem danh sách thông tin khách hàng",
        ],
        label_visibility="collapsed",
    )

reset_add_form_if_needed()


# ===========================================================================
# 1. NHẬP THÔNG TIN KHÁCH HÀNG
# ===========================================================================

if menu == "Nhập thông tin khách hàng":
    st.markdown('<div class="section-title">Nhập thông tin khách hàng</div>', unsafe_allow_html=True)

    new_id = generate_next_customer_id(customers)
    st.info(f"Mã khách hàng được sinh tự động: **{new_id}**")
    live_errors: List[str] = []

    st.subheader("1. Thông tin định danh và liên hệ")

    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        customer_name = st.text_input("Tên khách hàng *", placeholder="Nhập tên khách hàng", key="add_customer_name")
        if customer_name and len(customer_name.strip()) < 2:
            show_error_once(live_errors, "Tên khách hàng phải có ít nhất 2 ký tự.")
    with r1c2:
        customer_type = st.selectbox("Loại khách hàng *", CUSTOMER_TYPES, key="add_customer_type")
    with r1c3:
        phone = st.text_input("Số điện thoại *", placeholder="Ví dụ: 0912345678", max_chars=10, key="add_phone")
        if phone and not phone_is_valid(phone):
            show_error_once(live_errors, "Số điện thoại phải gồm đúng 10 chữ số và bắt đầu bằng số 0.")

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        # Email bắt buộc
        email = st.text_input("Email *", placeholder="Ví dụ: abc@gmail.com", key="add_email")
        if email and not email_is_valid(email):
            show_error_once(live_errors, "Email không đúng định dạng (ví dụ: abc@gmail.com).")
    with r2c2:
        address = st.text_input("Địa chỉ *", placeholder="Nhập địa chỉ", max_chars=250, key="add_address")
        if address and len(address.strip()) < 5:
            show_error_once(live_errors, "Địa chỉ cần có ít nhất 5 ký tự.")
    with r2c3:
        representative = st.text_input(
            "Người đại diện",
            placeholder="Bắt buộc nếu là Doanh nghiệp",
            key="add_representative",
        )
        if customer_type == "Doanh nghiệp" and not representative.strip():
            st.warning("Khách hàng Doanh nghiệp bắt buộc nhập người đại diện.")

    r3c1, r3c2, r3c3 = st.columns(3)
    with r3c1:
        tax_code = st.text_input(
            "Mã số thuế",
            placeholder="10, 12 hoặc 13 chữ số",
            key="add_tax_code",
        )
        if tax_code and not tax_code_is_valid(tax_code):
            show_error_once(live_errors, "Mã số thuế phải gồm 10, 12 hoặc 13 chữ số.")
        if customer_type == "Doanh nghiệp" and not tax_code.strip():
            st.warning("Khách hàng Doanh nghiệp bắt buộc nhập mã số thuế.")
    with r3c2:
        st.markdown(
            "<div class='small-muted'>Với khách hàng Cá nhân, người đại diện và mã số thuế có thể để trống.</div>",
            unsafe_allow_html=True,
        )

    st.subheader("2. Thông tin dịch vụ")

    d1, d2 = st.columns(2)
    with d1:
        product_service = st.selectbox("Sản phẩm cung cấp *", PRODUCTS, key="add_product")
    with d2:
        service_package = st.selectbox("Gói dịch vụ *", PACKAGES, key="add_package")

    t1, t2, t3 = st.columns(3)
    with t1:
        start_date = st.date_input("Ngày bắt đầu *", value=date.today(), key="add_start_date")
    with t2:
        expiry_date = st.date_input(
            "Ngày hết hạn *",
            value=date.today() + timedelta(days=365),
            key="add_expiry_date",
        )
    with t3:
        if expiry_date <= start_date:
            show_error_once(live_errors, "Ngày hết hạn phải lớn hơn ngày bắt đầu.")
        else:
            days_left = (expiry_date - date.today()).days
            st.success(f"Hợp lệ · còn {days_left} ngày")

    st.subheader("3. Thông tin tài chính")

    f1, f2 = st.columns([1, 2])
    with f1:
        balance = st.number_input(
            "Công nợ (VND)", min_value=0, value=0, step=10000, format="%d", key="add_balance"
        )
    with f2:
        notes = st.text_area("Ghi chú", max_chars=500, key="add_notes")

    save_clicked = st.button("Lưu khách hàng", type="primary")
    add_message_area = st.empty()

    if "add_flash_success" in st.session_state:
        add_message_area.success(st.session_state.pop("add_flash_success"))

    if save_clicked:
        # Xóa lỗi "Email trống" tạm thời khi người dùng chưa chạm vào trường
        # rồi mới bấm Lưu — validate_customer_record sẽ bắt đầy đủ
        record = build_customer_record(
            customer_id=new_id,
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
        if live_errors:
            st.error("Vui lòng sửa các lỗi đang hiển thị trước khi lưu.")
        elif errors:
            for err in errors:
                st.error(err)
        else:
            customers.append(record)
            save_customers(customers)
            st.session_state["add_flash_success"] = (
                f"Thêm khách hàng {new_id} thành công! Dữ liệu đã được lưu."
            )
            st.session_state["reset_add_form"] = True
            st.rerun()


# ===========================================================================
# 2. CẬP NHẬT THÔNG TIN KHÁCH HÀNG
# ===========================================================================

elif menu == "Cập nhật thông tin khách hàng":
    st.markdown('<div class="section-title">Cập nhật thông tin khách hàng</div>', unsafe_allow_html=True)

    active_list = [enrich_customer(c) for c in active_customers(customers)]
    if not active_list:
        st.info("Chưa có khách hàng đang hoạt động để cập nhật.")
    else:
        selected = st.selectbox(
            "Chọn khách hàng cần cập nhật",
            [f"{c['customer_id']} - {c['customer_name']}" for c in active_list],
        )
        selected_id = selected.split(" - ")[0]
        current     = find_customer_by_id(customers, selected_id)

        if current:
            c = enrich_customer(current)
            render_customer_detail(c)

            st.subheader("Chỉnh sửa thông tin")
            update_live_errors: List[str] = []

            u1, u2, u3 = st.columns(3)
            with u1:
                st.text_input("Mã khách hàng", value=c.get("customer_id", ""), disabled=True, key=f"upd_id_{selected_id}")
            with u2:
                customer_name = st.text_input("Tên khách hàng *", value=c.get("customer_name", ""), key=f"upd_name_{selected_id}")
                if customer_name and len(customer_name.strip()) < 2:
                    show_error_once(update_live_errors, "Tên khách hàng phải có ít nhất 2 ký tự.")
            with u3:
                customer_type = st.selectbox(
                    "Loại khách hàng *",
                    CUSTOMER_TYPES,
                    index=CUSTOMER_TYPES.index(c.get("customer_type", "Cá nhân"))
                          if c.get("customer_type") in CUSTOMER_TYPES else 0,
                    key=f"upd_type_{selected_id}",
                )

            u4, u5, u6 = st.columns(3)
            with u4:
                phone = st.text_input("Số điện thoại *", value=c.get("phone", ""), max_chars=10, key=f"upd_phone_{selected_id}")
                if phone and not phone_is_valid(phone):
                    show_error_once(update_live_errors, "Số điện thoại phải gồm đúng 10 chữ số và bắt đầu bằng số 0.")
            with u5:
                email = st.text_input("Email *", value=c.get("email", ""), key=f"upd_email_{selected_id}")
                if not email:
                    show_error_once(update_live_errors, "Email không được để trống.")
                elif not email_is_valid(email):
                    show_error_once(update_live_errors, "Email không đúng định dạng.")
            with u6:
                address = st.text_input("Địa chỉ *", value=c.get("address", ""), max_chars=250, key=f"upd_addr_{selected_id}")
                if address and len(address.strip()) < 5:
                    show_error_once(update_live_errors, "Địa chỉ cần có ít nhất 5 ký tự.")

            u7, u8, u9 = st.columns(3)
            with u7:
                representative = st.text_input("Người đại diện", value=c.get("representative") or "", key=f"upd_rep_{selected_id}")
                if customer_type == "Doanh nghiệp" and not representative.strip():
                    st.warning("Khách hàng Doanh nghiệp bắt buộc nhập người đại diện.")
            with u8:
                tax_code = st.text_input("Mã số thuế", value=c.get("tax_code") or "", key=f"upd_tax_{selected_id}")
                if tax_code and not tax_code_is_valid(tax_code):
                    show_error_once(update_live_errors, "Mã số thuế phải gồm 10, 12 hoặc 13 chữ số.")
                if customer_type == "Doanh nghiệp" and not tax_code.strip():
                    st.warning("Khách hàng Doanh nghiệp bắt buộc nhập mã số thuế.")
            with u9:
                st.markdown(
                    "<div class='small-muted'>Mã khách hàng được khóa để bảo đảm truy vết dữ liệu.</div>",
                    unsafe_allow_html=True,
                )

            st.subheader("Thông tin dịch vụ")

            p1, p2 = st.columns(2)
            with p1:
                product_service = st.selectbox(
                    "Sản phẩm cung cấp *",
                    PRODUCTS,
                    index=PRODUCTS.index(c.get("product_service")) if c.get("product_service") in PRODUCTS else 0,
                    key=f"upd_prod_{selected_id}",
                )
            with p2:
                service_package = st.selectbox(
                    "Gói dịch vụ *",
                    PACKAGES,
                    index=PACKAGES.index(c.get("service_package")) if c.get("service_package") in PACKAGES else 0,
                    key=f"upd_pkg_{selected_id}",
                )

            old_start  = safe_date(c.get("start_date", ""),  date.today())
            old_expiry = safe_date(c.get("expiry_date", ""), date.today() + timedelta(days=365))

            p3, p4, p5 = st.columns(3)
            with p3:
                start_date = st.date_input("Ngày bắt đầu *", value=old_start, key=f"upd_start_{selected_id}")
            with p4:
                expiry_date = st.date_input("Ngày hết hạn *", value=old_expiry, key=f"upd_expiry_{selected_id}")
            with p5:
                if expiry_date <= start_date:
                    show_error_once(update_live_errors, "Ngày hết hạn phải lớn hơn ngày bắt đầu.")
                else:
                    days_left = (expiry_date - date.today()).days
                    st.success(f"Hợp lệ · còn {days_left} ngày")

            st.subheader("Thông tin tài chính")

            b1, b2 = st.columns([1, 2])
            with b1:
                balance = st.number_input(
                    "Công nợ (VND)",
                    min_value=0,
                    value=int(float(c.get("balance", 0) or 0)),
                    step=10000,
                    format="%d",
                    key=f"upd_bal_{selected_id}",
                )
            with b2:
                notes = st.text_area("Ghi chú", value=c.get("notes", ""), max_chars=500, key=f"upd_notes_{selected_id}")

            if st.button("Cập nhật khách hàng", type="primary"):
                updated_record = build_customer_record(
                    customer_id=current.get("customer_id", ""),
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
                    created_at=current.get("created_at"),
                    is_deleted=current.get("is_deleted", False),
                    deleted_at=current.get("deleted_at"),
                )
                errors = validate_customer_record(updated_record, customers, current_id=current.get("customer_id"))
                if update_live_errors:
                    st.error("Vui lòng sửa các lỗi đang hiển thị trước khi cập nhật.")
                elif errors:
                    for err in errors:
                        st.error(err)
                else:
                    current.update(updated_record)
                    save_customers(customers)
                    st.session_state["flash_success"] = "Cập nhật khách hàng thành công!"
                    st.rerun()


# ===========================================================================
# 3. TÌM KIẾM THÔNG TIN KHÁCH HÀNG
# ===========================================================================

elif menu == "Tìm kiếm thông tin khách hàng":
    st.markdown('<div class="section-title">Tìm kiếm thông tin khách hàng</div>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns([3, 1, 1])
    with f1:
        keyword = st.text_input("Từ khóa", placeholder="Nhập mã KH, tên, SĐT hoặc email")
    with f2:
        status_filter = st.selectbox("Trạng thái", SERVICE_STATUS_ALL)
    with f3:
        include_deleted = st.checkbox("Bao gồm đã xóa")

    if st.button("Tìm kiếm", type="primary"):
        results, message = search_customers(customers, keyword, status_filter, include_deleted)
        if message and not results:
            if "Tìm thấy" in message:
                st.warning(message)
            else:
                st.info(message)
        else:
            st.markdown(f"#### Kết quả tìm kiếm: {len(results)} bản ghi")
            st.dataframe(
                pd.DataFrame(customers_to_rows(results)),
                use_container_width=True,
                hide_index=True,
            )
            chosen = st.selectbox(
                "Xem chi tiết kết quả",
                [f"{c['customer_id']} - {c['customer_name']}" for c in results],
            )
            chosen_id = chosen.split(" - ")[0]
            render_customer_detail(find_customer_by_id(results, chosen_id) or results[0])


# ===========================================================================
# 4. XÓA THÔNG TIN KHÁCH HÀNG
# ===========================================================================

elif menu == "Xóa thông tin khách hàng":
    st.markdown('<div class="section-title">Xóa thông tin khách hàng</div>', unsafe_allow_html=True)

    active_list = [enrich_customer(c) for c in active_customers(customers)]
    if not active_list:
        st.info("Không có khách hàng đang hoạt động để xóa.")
    else:
        selected = st.selectbox(
            "Chọn khách hàng cần xóa",
            [f"{c['customer_id']} - {c['customer_name']}" for c in active_list],
        )
        selected_id      = selected.split(" - ")[0]
        selected_customer = find_customer_by_id(customers, selected_id)
        if selected_customer:
            render_customer_detail(enrich_customer(selected_customer))

        st.warning(
            "Hệ thống sử dụng cơ chế xóa mềm. "
            "Khách hàng đang Hoạt động / Sắp hết hạn hoặc còn công nợ sẽ không được xóa."
        )
        confirm = st.checkbox("Tôi xác nhận muốn xóa khách hàng này")

        if st.button("Xóa khách hàng", type="primary"):
            if not confirm:
                st.error("Vui lòng tick xác nhận trước khi xóa.")
            else:
                ok, msg = soft_delete_customer(customers, selected_id)
                if ok:
                    save_customers(customers)
                    st.session_state["flash_success"] = msg
                    st.rerun()
                else:
                    st.error(msg)


# ===========================================================================
# 5. XEM DANH SÁCH THÔNG TIN KHÁCH HÀNG
# ===========================================================================

elif menu == "Xem danh sách thông tin khách hàng":
    st.markdown('<div class="section-title">Xem danh sách thông tin khách hàng</div>', unsafe_allow_html=True)

    active_list = [enrich_customer(c) for c in active_customers(customers)]
    if not active_list:
        st.info('Không có khách hàng. Vui lòng sử dụng chức năng "Nhập thông tin khách hàng" để thêm dữ liệu.')
    else:
        # Thống kê nhanh
        hoat_dong   = sum(1 for c in active_list if c.get("service_status") == "Hoạt động")
        sap_het_han = sum(1 for c in active_list if c.get("service_status") == "Sắp hết hạn")
        het_han     = sum(1 for c in active_list if c.get("service_status") == "Hết hạn")
        co_no       = sum(1 for c in active_list if float(c.get("balance", 0) or 0) > 0)

        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Tổng khách hàng", len(active_list))
        col_b.metric("Đang hoạt động",  hoat_dong)
        col_c.metric("Sắp hết hạn",     sap_het_han, delta=f"-{sap_het_han}" if sap_het_han else None, delta_color="inverse")
        col_d.metric("Có công nợ",       co_no,      delta=f"-{co_no}" if co_no else None, delta_color="inverse")

        st.divider()
        st.dataframe(
            pd.DataFrame(customers_to_rows(active_list)),
            use_container_width=True,
            hide_index=True,
        )

        chosen = st.selectbox(
            "Xem chi tiết khách hàng",
            [f"{c['customer_id']} - {c['customer_name']}" for c in active_list],
        )
        chosen_id = chosen.split(" - ")[0]
        render_customer_detail(find_customer_by_id(active_list, chosen_id) or active_list[0])

    st.markdown(
        '<div class="note-box">Chỉ hiển thị khách hàng chưa bị xóa mềm. '
        'Dùng chức năng Tìm kiếm với tùy chọn "Bao gồm đã xóa" để tra cứu lịch sử.</div>',
        unsafe_allow_html=True,
    )
