import json
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR  = Path("data")
DATA_FILE = DATA_DIR / "customers.json"


def ensure_data_file() -> None:
    """Tạo thư mục data và file customers.json nếu chưa tồn tại."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def load_customers() -> List[Dict[str, Any]]:
    """Đọc danh sách khách hàng từ file JSON. Trả về [] nếu file lỗi."""
    ensure_data_file()
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        print("⚠️  File customers.json bị lỗi định dạng. Hệ thống nạp danh sách rỗng.")
        return []


def save_customers(customers: List[Dict[str, Any]]) -> None:
    """Ghi danh sách khách hàng vào file JSON (indent=4, utf-8)."""
    ensure_data_file()
    DATA_FILE.write_text(
        json.dumps(customers, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )
