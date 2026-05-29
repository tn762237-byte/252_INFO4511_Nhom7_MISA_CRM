from __future__ import annotations
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
    email_is_valid,
    enrich_customer,
    find_customer_by_id,
    generate_next_customer_id,
    parse_date,
    phone_is_valid,
    search_customers,
    soft_delete_customer,
    tax_code_is_valid,
    validate_customer_record,
)
from modules.storage import load_customers, save_customers

# CẤU HÌNH TRANG
st.set_page_config(page_title="Quản lý khách hàng MISA", layout="wide")
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] { font-family: 'Be Vietnam Pro', sans-serif; }

        .main-title {
            background: linear-gradient(90deg, #0052cc 0%, #0078d4 100%);
            color: white;
            padding: 20px 28px;
            border-radius: 14px;
            text-align: center;
            font-size: 26px;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(0,82,204,0.18);
        }
        .section-title {
            color: #0052cc;
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 18px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e8f0fe;
        }
        .detail-box {
            background: #f8fbff;
            border: 1px solid #d6e4f5;
            border-radius: 12px;
            padding: 20px 24px;
            margin: 12px 0 18px 0;
        }
        .note-box {
            background: #fff7e6;
            border: 1px solid #ffd591;
            border-radius: 10px;
            padding: 12px 16px;
            margin-top: 16px;
            font-size: 13.5px;
        }
        .small-muted {
            color: #64748b;
            font-size: 13px;
            line-height: 1.5;
        }
        .field-required::after { content: " *"; color: #e53e3e; }

        div.stButton > button:first-child {
            border-radius: 9px;
            font-weight: 600;
            transition: all .15s;
        }
        div.stButton > button[kind="primary"] {
            background: #0052cc;
            border-color: #0052cc;
        }
        div.stButton > button[kind="primary"]:hover {
            background: #003d99;
            border-color: #003d99;
        }

        /* Sidebar */
        [data-testid="stSidebar"] { background: #f0f4ff; }
        [data-testid="stSidebar"] .stRadio label { font-weight: 500; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🏢 QUẢN LÝ KHÁCH HÀNG MISA</div>', unsafe_allow_html=True)

# ─── Flash messages toàn cục ─────────────────────────────────────────────────
if "flash_success" in st.session_state:
    st.success(st.session_state.pop("flash_success"))
if "flash_error" in st.session_state:
    st.error(st.session_state.pop("flash_error"))

customers: List[Dict[str, Any]] = load_customers()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def safe_date(value: Any, default: date) -> date:
    try:
        return parse_date(str(value)) if value else default
    except Exception:
        return default


def show_error_once(errors: List[str], message: str | None) -> None:
    """Ghi nhận lỗi và hiển thị ngay, tránh trùng."""
    if message and message not in errors:
        errors.append(message)
        st.error(message)


def render_customer_detail(customer: Dict[str, Any]) -> None:
    if not customer:
        st.info("Chưa có khách hàng để hiển thị.")
        return
    c = enrich_customer(customer)
    st.markdown('<div class="detail-box">', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        for lbl, key in [
            ("Mã khách hàng",   "customer_id"),
            ("Tên khách hàng",  "customer_name"),
            ("Loại khách hàng", "customer_type"),
            ("Số điện thoại",   "phone"),
            ("Email",           "email"),
            ("Địa chỉ",         "address"),
            ("Người đại diện",  "representative"),
            ("Mã số thuế",      "tax_code"),
        ]:
            st.write(f"**{lbl}:** {c.get(key) or '—'}")
    with right:
        for lbl, key in [
            ("Sản phẩm",               "product_service"),
            ("Gói dịch vụ",            "service_package"),
            ("Ngày bắt đầu",           "start_date"),
            ("Ngày hết hạn",           "expiry_date"),
            ("Trạng thái dịch vụ",     "service_status"),
            ("Trạng thái thanh toán",  "payment_status"),
        ]:
            st.write(f"**{lbl}:** {c.get(key) or '—'}")
        st.write(f"**Công nợ:** {float(c.get('balance', 0) or 0):,.0f} VND")
    if c.get("notes"):
        st.write(f"**Ghi chú:** {c['notes']}")
    st.markdown(
        f"<div class='small-muted'>Tạo: {c.get('created_at','')} &nbsp;|&nbsp; "
        f"Cập nhật: {c.get('updated_at','')} &nbsp;|&nbsp; "
        f"Xóa: {c.get('deleted_at') or '—'}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🔷 MISA")
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
    st.divider()
    active_count = len(active_customers(customers))
    st.metric("Khách hàng đang hoạt động", active_count)

# NHẬP THÔNG TIN KHÁCH HÀNG
if menu == "Nhập thông tin khách hàng":
    st.markdown('<div class="section-title">Nhập thông tin khách hàng</div>', unsafe_allow_html=True)

    # Dùng form_version để reset tất cả widget sau khi lưu thành công
    fv = st.session_state.get("add_form_version", 0)
    new_id = generate_next_customer_id(customers)
    live_errors: List[str] = []
    st.info(f"Mã khách hàng được sinh tự động: **{new_id}**")

    #  Thông tin định dạng
    st.subheader("1. Thông tin định danh và liên hệ")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Mã khách hàng", value=new_id, disabled=True, key=f"add_id_{fv}")
    with c2:
        customer_name = st.text_input(
            "Tên khách hàng *", placeholder="Nhập tên khách hàng", key=f"add_name_{fv}"
        )
        if customer_name and len(customer_name.strip()) < 2:
            show_error_once(live_errors, "Tên khách hàng phải có ít nhất 2 ký tự.")
    with c3:
        customer_type = st.selectbox("Loại khách hàng *", CUSTOMER_TYPES, key=f"add_type_{fv}")

    c4, c5, c6 = st.columns(3)
    with c4:
        phone = st.text_input(
            "Số điện thoại *", placeholder="Ví dụ: 0912345678", max_chars=10, key=f"add_phone_{fv}"
        )
        if phone and not phone_is_valid(phone):
            show_error_once(live_errors, "Số điện thoại phải gồm đúng 10 chữ số và bắt đầu bằng số 0.")
    with c5:
        email = st.text_input(
            "Email *", placeholder="Ví dụ: abc@gmail.com", key=f"add_email_{fv}"
        )
        if email and not email_is_valid(email):
            show_error_once(live_errors, "Email không đúng định dạng (ví dụ: abc@gmail.com).")
    with c6:
        address = st.text_input(
            "Địa chỉ *", placeholder="Nhập địa chỉ", max_chars=250, key=f"add_addr_{fv}"
        )
        if address and len(address.strip()) < 5:
            show_error_once(live_errors, "Địa chỉ cần có ít nhất 5 ký tự.")

    c7, c8, c9 = st.columns(3)
    with c7:
        representative = st.text_input(
            "Người đại diện" + (" *" if customer_type == "Doanh nghiệp" else ""),
            placeholder="Bắt buộc nếu là Doanh nghiệp",
            key=f"add_rep_{fv}",
        )
        if customer_type == "Doanh nghiệp" and not representative.strip():
            st.warning("Khách hàng Doanh nghiệp bắt buộc nhập người đại diện.")
    with c8:
        tax_code = st.text_input(
            "Mã số thuế *",
            placeholder="10, 12 hoặc 13 chữ số",
            key=f"add_tax_{fv}",
        )

        if tax_code and not tax_code_is_valid(tax_code):
            show_error_once(live_errors, "Mã số thuế phải gồm 10, 12 hoặc 13 chữ số.")
    with c9:
        st.markdown(
            "<div class='small-muted' style='margin-top:32px'>Mã số thuế là bắt buộc với mọi loại khách hàng.</div>",
            unsafe_allow_html=True,
        )
    # Thông tin dịch vụ
    st.subheader("2. Thông tin dịch vụ")
    d1, d2 = st.columns(2)
    with d1:
        product_service = st.selectbox("Sản phẩm cung cấp *", PRODUCTS, key=f"add_prod_{fv}")
    with d2:
        service_package = st.selectbox("Gói dịch vụ *", PACKAGES, key=f"add_pkg_{fv}")

    t1, t2, t3 = st.columns(3)
    with t1:
        start_date = st.date_input("Ngày bắt đầu *", value=date.today(), key=f"add_start_{fv}")
    with t2:
        expiry_date = st.date_input(
            "Ngày hết hạn *",
            value=date.today() + timedelta(days=365),
            key=f"add_expiry_{fv}",
        )
    with t3:
        if expiry_date <= start_date:
            show_error_once(live_errors, "Ngày hết hạn phải lớn hơn ngày bắt đầu.")
        else:
            days_left = (expiry_date - date.today()).days
            st.success(f"✓ Hợp lệ · còn {days_left} ngày")

    # Thông tin tài chính
    st.subheader("3. Thông tin tài chính")

    f1, f2 = st.columns([1, 2])
    with f1:
        balance = st.number_input(
            "Công nợ (VND)", min_value=0, value=0, step=10_000, format="%d", key=f"add_bal_{fv}"
        )
    with f2:
        notes = st.text_area("Ghi chú", max_chars=500, placeholder="Ghi chú tùy chọn", key=f"add_notes_{fv}")

    save_clicked = st.button("💾 Lưu khách hàng", type="primary")
    msg_area = st.empty()

    if "add_success_msg" in st.session_state:
        msg_area.success(st.session_state.pop("add_success_msg"))

    if save_clicked:
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
        # Bắt buộc mã số thuế ở mọi loại KH
        if not tax_code.strip():
            st.error("Mã số thuế không được để trống.")
        else:
            backend_errors = validate_customer_record(record, customers)
            if live_errors:
                st.error("Vui lòng sửa các lỗi đang hiển thị trước khi lưu.")
            elif backend_errors:
                for err in backend_errors:
                    st.error(err)
            else:
                customers.append(record)
                save_customers(customers)
                st.session_state["add_success_msg"] = (
                    f"✅ Thêm khách hàng **{new_id}** thành công! Dữ liệu đã được lưu."
                )
                st.session_state["add_form_version"] = fv + 1
                st.rerun()

# CẬP NHẬT THÔNG TIN KHÁCH HÀNG
elif menu == "Cập nhật thông tin khách hàng":
    st.markdown('<div class="section-title">Cập nhật thông tin khách hàng</div>', unsafe_allow_html=True)

    active_list = [enrich_customer(c) for c in active_customers(customers)]
    if not active_list:
        st.info("Chưa có khách hàng đang hoạt động để cập nhật.")
        st.stop()

    st.caption("Nhập mã khách hàng cần cập nhật. Bảng bên dưới để tham khảo mã.")
    st.dataframe(
        pd.DataFrame(customers_to_rows(active_list)),
        use_container_width=True,
        hide_index=True,
    )

    selected_id = st.text_input(
        "Mã khách hàng cần cập nhật *",
        placeholder="Ví dụ: KH001",
        key="upd_id_input",
    ).strip().upper()

    if not selected_id:
        st.info("Vui lòng nhập mã khách hàng để tiếp tục.")
        st.stop()

    current = find_customer_by_id(customers, selected_id)
    if not current:
        st.error("Không tìm thấy khách hàng với mã đã nhập.")
        st.stop()
    if current.get("is_deleted"):
        st.warning("Khách hàng này đã bị xóa mềm, không thể cập nhật.")
        st.stop()

    c = enrich_customer(current)
    render_customer_detail(c)

    st.subheader("Chỉnh sửa thông tin")
    upd_errors: List[str] = []

    # Thông tin định danh
    u1, u2, u3 = st.columns(3)
    with u1:
        st.text_input("Mã khách hàng", value=c["customer_id"], disabled=True, key=f"upd_id_{selected_id}")
    with u2:
        customer_name = st.text_input(
            "Tên khách hàng *", value=c.get("customer_name", ""), key=f"upd_name_{selected_id}"
        )
        if customer_name and len(customer_name.strip()) < 2:
            show_error_once(upd_errors, "Tên khách hàng phải có ít nhất 2 ký tự.")
    with u3:
        customer_type = st.selectbox(
            "Loại khách hàng *",
            CUSTOMER_TYPES,
            index=CUSTOMER_TYPES.index(c["customer_type"]) if c.get("customer_type") in CUSTOMER_TYPES else 0,
            key=f"upd_type_{selected_id}",
        )

    u4, u5, u6 = st.columns(3)
    with u4:
        phone = st.text_input(
            "Số điện thoại *", value=c.get("phone", ""), max_chars=10, key=f"upd_phone_{selected_id}"
        )
        if phone and not phone_is_valid(phone):
            show_error_once(upd_errors, "Số điện thoại phải gồm đúng 10 chữ số và bắt đầu bằng số 0.")
    with u5:
        email = st.text_input(
            "Email *", value=c.get("email", ""), key=f"upd_email_{selected_id}"
        )
        if not email:
            show_error_once(upd_errors, "Email không được để trống.")
        elif not email_is_valid(email):
            show_error_once(upd_errors, "Email không đúng định dạng.")
    with u6:
        address = st.text_input(
            "Địa chỉ *", value=c.get("address", ""), max_chars=250, key=f"upd_addr_{selected_id}"
        )
        if address and len(address.strip()) < 5:
            show_error_once(upd_errors, "Địa chỉ cần có ít nhất 5 ký tự.")

    u7, u8, u9 = st.columns(3)
    with u7:
        representative = st.text_input(
            "Người đại diện" + (" *" if customer_type == "Doanh nghiệp" else ""),
            value=c.get("representative") or "",
            key=f"upd_rep_{selected_id}",
        )
        if customer_type == "Doanh nghiệp" and not representative.strip():
            st.warning("Khách hàng Doanh nghiệp bắt buộc nhập người đại diện.")
    with u8:
        tax_code = st.text_input(
            "Mã số thuế *",
            value=c.get("tax_code") or "",
            key=f"upd_tax_{selected_id}",
        )
        if not tax_code.strip():
            show_error_once(upd_errors, "Mã số thuế không được để trống.")
        elif not tax_code_is_valid(tax_code):
            show_error_once(upd_errors, "Mã số thuế phải gồm 10, 12 hoặc 13 chữ số.")
    with u9:
        st.markdown(
            "<div class='small-muted' style='margin-top:32px'>Mã khách hàng bị khóa để bảo đảm truy vết.</div>",
            unsafe_allow_html=True,
        )

    # Thông tin dịch vụ
    st.subheader("Thông tin dịch vụ")

    p1, p2 = st.columns(2)
    with p1:
        product_service = st.selectbox(
            "Sản phẩm cung cấp *",
            PRODUCTS,
            index=PRODUCTS.index(c["product_service"]) if c.get("product_service") in PRODUCTS else 0,
            key=f"upd_prod_{selected_id}",
        )
    with p2:
        service_package = st.selectbox(
            "Gói dịch vụ *",
            PACKAGES,
            index=PACKAGES.index(c["service_package"]) if c.get("service_package") in PACKAGES else 0,
            key=f"upd_pkg_{selected_id}",
        )

    p3, p4, p5 = st.columns(3)
    with p3:
        start_date = st.date_input(
            "Ngày bắt đầu *",
            value=safe_date(c.get("start_date"), date.today()),
            key=f"upd_start_{selected_id}",
        )
    with p4:
        expiry_date = st.date_input(
            "Ngày hết hạn *",
            value=safe_date(c.get("expiry_date"), date.today() + timedelta(days=365)),
            key=f"upd_expiry_{selected_id}",
        )
    with p5:
        if expiry_date <= start_date:
            show_error_once(upd_errors, "Ngày hết hạn phải lớn hơn ngày bắt đầu.")
        else:
            days_left = (expiry_date - date.today()).days
            st.success(f"✓ Còn {days_left} ngày")

    # ── Thông tin tài chính ───────────────────────────────────────────────
    st.subheader("Thông tin tài chính")

    b1, b2 = st.columns([1, 2])
    with b1:
        balance = st.number_input(
            "Công nợ (VND)",
            min_value=0,
            value=int(float(c.get("balance", 0) or 0)),
            step=10_000,
            format="%d",
            key=f"upd_bal_{selected_id}",
        )
    with b2:
        notes = st.text_area(
            "Ghi chú", value=c.get("notes", ""), max_chars=500, key=f"upd_notes_{selected_id}"
        )

    if st.button("✏️ Cập nhật khách hàng", type="primary"):
        if not tax_code.strip():
            st.error("Mã số thuế không được để trống.")
        else:
            updated = build_customer_record(
                customer_id=current["customer_id"],
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
            backend_errors = validate_customer_record(updated, customers, current_id=current["customer_id"])
            if upd_errors:
                st.error("Vui lòng sửa các lỗi đang hiển thị trước khi cập nhật.")
            elif backend_errors:
                for err in backend_errors:
                    st.error(err)
            else:
                current.update(updated)
                save_customers(customers)
                st.session_state["flash_success"] = (
                    f"✅ Cập nhật khách hàng **{selected_id}** thành công!"
                )
                st.rerun()

# TÌM KIẾM THÔNG TIN KHÁCH HÀNG

elif menu == "Tìm kiếm thông tin khách hàng":
    st.markdown('<div class="section-title">Tìm kiếm thông tin khách hàng</div>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns([3, 1, 1])
    with f1:
        keyword = st.text_input("Từ khóa", placeholder="Nhập mã KH, tên, SĐT hoặc email")
    with f2:
        status_filter = st.selectbox("Trạng thái", SERVICE_STATUS_ALL)
    with f3:
        include_deleted = st.checkbox("Bao gồm đã xóa")

    if st.button("🔍 Tìm kiếm", type="primary"):
        results, message = search_customers(customers, keyword, status_filter, include_deleted)
        if message and not results:
            st.warning(message) if "Tìm thấy" in message else st.info(message)
        else:
            st.markdown(f"#### Kết quả: {len(results)} bản ghi")
            st.dataframe(
                pd.DataFrame(customers_to_rows(results)),
                use_container_width=True,
                hide_index=True,
            )
            chosen = st.selectbox(
                "Xem chi tiết",
                [f"{c['customer_id']} – {c['customer_name']}" for c in results],
            )
            chosen_id = chosen.split(" – ")[0]
            render_customer_detail(find_customer_by_id(results, chosen_id) or results[0])

# 4. XÓA THÔNG TIN KHÁCH HÀNG

elif menu == "Xóa thông tin khách hàng":
    st.markdown('<div class="section-title">Xóa thông tin khách hàng</div>', unsafe_allow_html=True)

    active_list = [enrich_customer(c) for c in active_customers(customers)]
    if not active_list:
        st.info("Không có khách hàng đang hoạt động để xóa.")
        st.stop()

    st.caption("Nhập mã khách hàng cần xóa. Bảng bên dưới để tham khảo.")
    st.dataframe(
        pd.DataFrame(customers_to_rows(active_list)),
        use_container_width=True,
        hide_index=True,
    )

    delete_id = st.text_input(
        "Mã khách hàng cần xóa *",
        placeholder="Ví dụ: KH001",
        key="del_id_input",
    ).strip().upper()

    if not delete_id:
        st.info("Vui lòng nhập mã khách hàng để thực hiện xóa mềm.")
        st.stop()

    selected_customer = find_customer_by_id(active_list, delete_id)
    if not selected_customer:
        gone = find_customer_by_id(customers, delete_id)
        if gone and gone.get("is_deleted"):
            st.warning("Khách hàng này đã bị xóa trước đó.")
        else:
            st.error("Không tìm thấy khách hàng đang hoạt động với mã đã nhập.")
        st.stop()

    render_customer_detail(selected_customer)

    st.warning(
        "⚠️ Hệ thống dùng **xóa mềm**. Khách hàng đang Hoạt động, Sắp hết hạn hoặc còn công nợ sẽ không được xóa."
    )
    confirm = st.checkbox("Tôi xác nhận muốn xóa khách hàng này")

    if st.button("🗑️ Xóa khách hàng", type="primary"):
        if not confirm:
            st.error("Vui lòng tick xác nhận trước khi xóa.")
        else:
            ok, msg = soft_delete_customer(customers, delete_id)
            if ok:
                save_customers(customers)
                st.session_state["flash_success"] = msg
                st.rerun()
            else:
                st.error(msg)

# 5. XEM DANH SÁCH THÔNG TIN KHÁCH HÀNG

elif menu == "Xem danh sách thông tin khách hàng":
    st.markdown('<div class="section-title">Danh sách khách hàng</div>', unsafe_allow_html=True)

    active_list = [enrich_customer(c) for c in active_customers(customers)]
    if not active_list:
        st.info('Chưa có khách hàng. Dùng "Nhập thông tin khách hàng" để thêm.')
        st.stop()

    # Thống kê nhanh
    hoat_dong   = sum(1 for c in active_list if c.get("service_status") == "Hoạt động")
    sap_het_han = sum(1 for c in active_list if c.get("service_status") == "Sắp hết hạn")
    het_han     = sum(1 for c in active_list if c.get("service_status") == "Hết hạn")
    co_no       = sum(1 for c in active_list if float(c.get("balance", 0) or 0) > 0)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tổng khách hàng",  len(active_list))
    m2.metric("Đang hoạt động",   hoat_dong)
    m3.metric("Sắp hết hạn",      sap_het_han,
              delta=f"-{sap_het_han}" if sap_het_han else None, delta_color="inverse")
    m4.metric("Có công nợ",       co_no,
              delta=f"-{co_no}" if co_no else None, delta_color="inverse")

    st.divider()

    # Bảng có checkbox chọn để xem chi tiết
    rows = customers_to_rows(active_list)
    valid_ids = {str(r.get("Mã KH", "")) for r in rows}

    _sel_key   = "view_selected_id"
    _ver_key   = "view_table_ver"

    prev_sel = st.session_state.get(_sel_key)
    if prev_sel not in valid_ids:
        prev_sel = None
        st.session_state[_sel_key] = None

    table_data = [{"Chọn": str(r.get("Mã KH", "")) == prev_sel, **r} for r in rows]
    tver = st.session_state.get(_ver_key, 0)

    edited = st.data_editor(
        pd.DataFrame(table_data),
        use_container_width=True,
        hide_index=True,
        disabled=[col for col in pd.DataFrame(table_data).columns if col != "Chọn"],
        column_config={
            "Chọn": st.column_config.CheckboxColumn("Chọn", help="Tick để xem chi tiết", default=False)
        },
        key=f"view_table_{tver}",
    )

    sel_rows = edited[edited["Chọn"] == True]
    sel_ids  = [str(v) for v in sel_rows["Mã KH"].tolist()]

    if not sel_ids:
        if prev_sel is not None:
            st.session_state[_sel_key] = None
            st.session_state[_ver_key] = tver + 1
            st.rerun()
        st.info("Tick chọn một khách hàng trong bảng để xem chi tiết.")
    else:
        # Luôn hiển thị KH mới nhất được tick
        if prev_sel in sel_ids and len(sel_ids) > 1:
            new_sel = [i for i in sel_ids if i != prev_sel][-1]
        else:
            new_sel = sel_ids[-1]

        if new_sel != prev_sel or len(sel_ids) > 1:
            st.session_state[_sel_key] = new_sel
            st.session_state[_ver_key] = tver + 1
            st.rerun()

        sel_customer = find_customer_by_id(active_list, new_sel)
        st.markdown("### Thông tin chi tiết")
        render_customer_detail(sel_customer or active_list[0])

    st.markdown(
        '<div class="note-box">📌 Chỉ hiển thị khách hàng chưa bị xóa mềm. '
        'Dùng chức năng <b>Tìm kiếm</b> với tùy chọn "Bao gồm đã xóa" để tra cứu lịch sử.</div>',
        unsafe_allow_html=True,
    )
