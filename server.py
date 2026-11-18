"""
HỆ THỐNG BI & QUẢN TRỊ KINH DOANH SỐ 5 BƯỚC (MASTER PROMPT LOCALHOST SERVER)
Cơ chế: ZERO-DATA INITIALIZATION (Tẩy trắng dữ liệu cũ 100%) & SCHEMA-AGNOSTIC ENGINE (Đọc dữ liệu động 100%).
Vận hành nghiêm ngặt theo Pipeline 5 Bước Tuần Tự có Trạm Kiểm Soát Tương Tác (Human-in-the-loop Gatekeeping):
- BƯỚC 1: Tiếp Nhận & Xác Thực Bối Cảnh Doanh Nghiệp (Context Ingestion & Validation)
- BƯỚC 2: Nhập & Kiểm Định Dữ Liệu Thô (Raw Data Ingestion & Data Profiling)
- BƯỚC 3: Làm Sạch & Tiền Xử Lý Dữ Liệu (Data Cleaning & Preprocessing)
- BƯỚC 4: Ánh Xạ Động, Tạo Công Thức & Tính Chỉ Số BI (Dynamic Mapping, Feature Engineering & 4-Quadrant Matrix)
- BƯỚC 5: Dashboard Điều Hành & Kế Hoạch Hành Động (BI Dashboard & Actionable Playbook)
"""

import http.server
import socketserver
import os
import io
import json
import re
import urllib.request
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import pandas as pd
import numpy as np

try:
    from report_generator import generate_docx_report
except ImportError:
    generate_docx_report = None

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Gemini API Key từ Environment Variable hoặc .env
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    env_path = os.path.join(DIRECTORY, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    GEMINI_API_KEY = line.strip().split("=", 1)[1]

# =============================================================================
# 1. ZERO-DATA INITIALIZATION (TẨY TRẮNG DỮ LIỆU CŨ 100%)
# =============================================================================
QUAD_STAR = "🌟 Ngôi sao tăng trưởng"
QUAD_COW = "🐄 Bò sữa sinh lời"
QUAD_TRAP = "⚠️ Bẫy doanh thu ảo"
QUAD_BURNER = "🔥 Đốt tiền / Cần cắt lỗ"

ALERT_OPTIMAL = "🟢 Tối ưu"
ALERT_WARNING = "🟡 Cảnh báo"
ALERT_DANGER = "🔴 Nguy hiểm"

def get_clean_slate_state():
    """Trả về trạng thái trắng hoàn toàn (Clean Slate) tại Bước 1."""
    return {
        "is_clean_slate": True,
        "filename": None,
        "current_unlocked_step": 1,
        "updated_at": None,
        "step1": {
            "has_context": False,
            "is_confirmed": False,
            "raw_input": "",
            "uploaded_doc_name": None,
            "business_profile": None,
            "checkpoint_msg": None
        },
        "step2": {
            "has_data": False,
            "is_confirmed": False,
            "total_rows": 0,
            "total_cols": 0,
            "columns_profiling": [],
            "health_summary": None,
            "preview_columns": [],
            "preview_rows": [],
            "schema_detected": None,
            "checkpoint_msg": None
        },
        "step3": {
            "has_cleaned": False,
            "is_confirmed": False,
            "cleaning_options": {
                "missing_numeric": "median",
                "missing_cat": "unknown",
                "deduplicate": True,
                "standardize_format": True,
                "handle_outliers": "cap"
            },
            "summary": None,
            "stats_comparison": [],
            "preview_columns": [],
            "preview_rows": [],
            "checkpoint_msg": None
        },
        "step4": {
            "has_processed": False,
            "is_confirmed": False,
            "available_columns": [],
            "mapping_used": {},
            "custom_formulas": [],
            "feature_formulas": [],
            "quadrant_counts": {QUAD_STAR: 0, QUAD_COW: 0, QUAD_TRAP: 0, QUAD_BURNER: 0, "Star": 0, "Cash Cow": 0, "Volume Trap": 0, "Cash Burner": 0},
            "grouped_summaries": {},
            "available_dimensions": [],
            "preview_columns": [],
            "preview_rows": [],
            "checkpoint_msg": None
        },
        "step5": {
            "has_dashboard": False,
            "is_confirmed": False,
            "kpis": None,
            "quadrant_counts": {QUAD_STAR: 0, QUAD_COW: 0, QUAD_TRAP: 0, QUAD_BURNER: 0, "Star": 0, "Cash Cow": 0, "Volume Trap": 0, "Cash Burner": 0},
            "scorecard": [],
            "matrix_scatter": [],
            "scorecards_by_dim": {},
            "available_dimensions": [],
            "pivot_camp_chan": [],
            "pivot_cat_reg": [],
            "daily_activity_log": [],
            "playbook": {"highlights": [], "bottlenecks": [], "actions": []},
            "time_trend": {"labels": [], "revenue": [], "ad_spend": [], "net_profit": []},
            "cat_donut": {"labels": [], "revenue": [], "net_profit": []},
            "grouped_bar": {"labels": [], "revenue": [], "ad_spend": [], "net_profit": []}
        }
    }

CURRENT_PIPELINE = {
    "raw_df": None,
    "cleaned_df": None,
    "processed_df": None,
    "state": get_clean_slate_state()
}

def purge_all_state():
    """Xóa sạch mọi file lưu tạm trên ổ đĩa và làm mới hoàn toàn bộ nhớ."""
    global CURRENT_PIPELINE
    stale_files = [
        "pipeline_state_5step.json",
        "pipeline_state.json",
        "uploaded_state.json",
        "uploaded_dataset.csv",
        "raw_sales_data.csv",
        "bi_datawarehouse.db"
    ]
    for fname in stale_files:
        fpath = os.path.join(DIRECTORY, fname)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception:
                pass
    CURRENT_PIPELINE = {
        "raw_df": None,
        "cleaned_df": None,
        "processed_df": None,
        "state": get_clean_slate_state()
    }
    return CURRENT_PIPELINE["state"]

# =============================================================================
# 2. BƯỚC 1: PHÂN TÍCH & TỔNG HỢP BỐI CẢNH DOANH NGHIỆP (BUSINESS PROFILING)
# =============================================================================
def analyze_business_context(raw_text, doc_filename=None, doc_content=None, manual_override=None):
    """Phân tích văn bản mô tả hoặc tài liệu tải lên để trích xuất Hồ sơ Bối cảnh Doanh nghiệp."""
    if manual_override and isinstance(manual_override, dict):
        return {
            "company_overview": manual_override.get("company_overview", "").strip(),
            "primary_goal": manual_override.get("primary_goal", "").strip(),
            "key_questions": [q.strip() for q in manual_override.get("key_questions", []) if str(q).strip()],
            "data_constraints": manual_override.get("data_constraints", "").strip(),
            "source_summary": f"Cập nhật trực tiếp bởi người dùng" + (f" (Kèm tài liệu: {doc_filename})" if doc_filename else "")
        }

    combined_text = "\n".join(filter(None, [str(raw_text or "").strip(), str(doc_content or "").strip()])).strip()
    if not combined_text:
        return None

    # Thử phân tích cấu trúc qua Gemini API nếu có kết nối
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
            prompt = (
                "Bạn là Chuyên gia Phân tích Bối cảnh Doanh nghiệp (Business Intelligence Profiler).\n"
                "Hãy phân tích thông tin người dùng cung cấp dưới đây và trích xuất ra JSON thuần túy (không bọc markdown) với đúng 4 trường:\n"
                "{\n"
                '  "company_overview": "Tóm tắt ngành nghề, mô hình kinh doanh (B2B/B2C/E-commerce/F&B...), quy mô hoặc đặc thù vận hành",\n'
                '  "primary_goal": "Mục tiêu phân tích cốt lõi cần giải quyết",\n'
                '  "key_questions": ["Câu hỏi trọng tâm 1", "Câu hỏi trọng tâm 2", "Câu hỏi trọng tâm 3"],\n'
                '  "data_constraints": "Các giả định ban đầu, từ điển dữ liệu, mốc thời gian/khu vực hoặc ràng buộc đi kèm"\n'
                "}\n\n"
                f"Nội dung đầu vào:\n{combined_text}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                res_data = json.loads(res.read().decode("utf-8"))
                ai_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                ai_text = re.sub(r"^```(?:json)?\s*", "", ai_text)
                ai_text = re.sub(r"\s*```$", "", ai_text)
                parsed = json.loads(ai_text)
                if isinstance(parsed, dict) and parsed.get("company_overview"):
                    parsed["source_summary"] = f"Trích xuất từ mô tả văn bản" + (f" & file '{doc_filename}'" if doc_filename else "")
                    return parsed
        except Exception:
            pass

    # Fallback bóc tách ngữ nghĩa trực tiếp từ văn bản người dùng nhập (100% dựa trên nội dung thật)
    lines = [ln.strip() for ln in re.split(r'[\r\n]+', combined_text) if ln.strip()]
    overview_parts = []
    goal_parts = []
    questions = []
    constraint_parts = []

    for ln in lines:
        ln_clean = re.sub(r'^[-*•+>\d.)\s]+', '', ln).strip()
        ln_lower = ln_clean.lower()
        if '?' in ln_clean or any(k in ln_lower for k in ['câu hỏi', 'cau hoi', ' tại sao', 'như thế nào', 'kênh nào', 'sản phẩm nào', 'đâu là']):
            questions.append(ln_clean)
        elif any(k in ln_lower for k in ['mục tiêu', 'muc tieu', 'vấn đề', 'van de', 'giải quyết', 'tối ưu', 'toi uu', 'tăng trưởng', 'cắt lỗ', 'hoàn đơn']):
            goal_parts.append(ln_clean)
        elif any(k in ln_lower for k in ['dữ liệu', 'du lieu', 'ràng buộc', 'rang buoc', 'thời gian', 'khu vực', 'từ điển', 'cột', 'giả định', 'lưu ý']):
            constraint_parts.append(ln_clean)
        else:
            overview_parts.append(ln_clean)

    company_overview = " | ".join(overview_parts) if overview_parts else lines[0]
    primary_goal = " ".join(goal_parts) if goal_parts else (lines[1] if len(lines) > 1 else f"Phân tích hiệu quả hoạt động và tối ưu vận hành theo bối cảnh: {lines[0]}")
    if not questions:
        questions = [
            f"Hoạt động/nhóm nào đang đóng góp doanh thu và lợi nhuận ròng cao nhất?",
            f"Đâu là điểm nghẽn vận hành (chi phí cao, tỷ lệ hoàn/hủy lớn hoặc biên lợi nhuận âm) cần xử lý?",
            f"Giải pháp phân bổ nguồn lực và tối ưu chi phí cho mục tiêu: {primary_goal}?"
        ]
    data_constraints = " | ".join(constraint_parts) if constraint_parts else (f"Tài liệu đính kèm: {doc_filename}. Đối chiếu trực tiếp với cấu trúc file dữ liệu tải lên ở Bước 2." if doc_filename else "Đối chiếu trực tiếp với cấu trúc các cột dữ liệu thực tế người dùng tải lên tại Bước 2.")

    return {
        "company_overview": company_overview,
        "primary_goal": primary_goal,
        "key_questions": questions,
        "data_constraints": data_constraints,
        "source_summary": f"Trích xuất trực tiếp từ đầu vào người dùng" + (f" & tài liệu '{doc_filename}'" if doc_filename else "")
    }

# =============================================================================
# 3. SCHEMA-AGNOSTIC PARSER & NUMBER NORMALIZER (ĐỌC DỮ LIỆU ĐỘNG 100%)
# =============================================================================
def parse_flexible_number(val):
    """Chuyển đổi chuỗi số có ký hiệu tiền tệ/viết tắt ('135tr', '150k', '1,200,000 VNĐ', '$50') sang float."""
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float, np.number)):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() in ['nan', 'none', 'null', 'n/a', 'na', '-', '']:
        return np.nan

    s_lower = s.lower()
    multiplier = 1.0
    if any(u in s_lower for u in ['tỷ', 'ty', 'billion', 'bn']):
        multiplier = 1e9
    elif any(u in s_lower for u in ['triệu', 'trieu', 'tr', 'million', 'm']):
        if re.search(r'\d\s*(?:triệu|trieu|tr|m)\b', s_lower):
            multiplier = 1e6
    elif any(u in s_lower for u in ['nghìn', 'nghin', 'ngàn', 'ngan', 'k']):
        if re.search(r'\d\s*(?:nghìn|nghin|ngàn|ngan|k)\b', s_lower):
            multiplier = 1e3

    # Giữ lại chữ số, dấu trừ, dấu chấm, dấu phẩy
    num_part = re.sub(r'[^0-9.,-]', '', s_lower)
    if not num_part or num_part in ['-', '.', ',']:
        return np.nan

    # Xử lý dấu chấm / phẩy phân cách hàng nghìn
    if ',' in num_part and '.' in num_part:
        if num_part.rfind(',') > num_part.rfind('.'):
            num_part = num_part.replace('.', '').replace(',', '.')
        else:
            num_part = num_part.replace(',', '')
    elif ',' in num_part:
        parts = num_part.split(',')
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3 and multiplier == 1.0):
            num_part = num_part.replace(',', '')
        else:
            num_part = num_part.replace(',', '.')
    elif '.' in num_part:
        parts = num_part.split('.')
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3 and multiplier == 1.0):
            num_part = num_part.replace('.', '')

    try:
        return float(num_part) * multiplier
    except Exception:
        return np.nan

def has_formatting_noise(val):
    """Kiểm tra xem một ô số có chứa ký tự chữ, đơn vị tiền tệ hoặc khoảng trắng thừa không."""
    if pd.isna(val):
        return False
    if isinstance(val, (int, float, np.number)):
        return False
    s = str(val)
    if s != s.strip():
        return True
    s_clean = s.strip()
    if re.search(r'[a-zA-ZđĐ$₫%€£¥]', s_clean):
        return True
    return False

def detect_schema_columns(df):
    """
    Quét động 100% danh sách cột từ dòng tiêu đề đầu tiên của file mới.
    Tự động phân loại vào 3 nhóm: Date, Dimensions, Metrics dựa trên kiểu dữ liệu thực tế.
    """
    date_cols = []
    metric_cols = []
    dim_cols = []

    date_keywords = ['date', 'time', 'ngày', 'ngay', 'tháng', 'thang', 'year', 'năm', 'nam', 'quý', 'quy', 'period', 'created', 'timestamp', 'day', 'month']
    id_keywords = ['id', 'mã', 'ma_', '_id', 'code', 'sku', 'phone', 'sdt', 'điện thoại', 'email']

    for col in df.columns:
        col_str = str(col).strip()
        col_lower = col_str.lower()
        col_clean = col_lower.replace(' ', '_')

        non_null = df[col].dropna()
        non_empty = non_null[~non_null.astype(str).str.strip().str.lower().isin(['', 'nan', 'none', 'null', 'n/a', 'na'])]

        if len(non_empty) == 0:
            dim_cols.append(col)
            continue

        # 1. Kiểm tra cột ID / Mã định danh -> Luôn xếp vào Dimension
        is_id_col = any(col_clean == k or col_clean.endswith(f"_{k}") or col_clean.startswith(f"{k}_") for k in id_keywords)

        # 2. Kiểm tra cột Thời gian (Date/Time)
        is_date = False
        if any(k in col_lower for k in date_keywords) and not any(m in col_lower for m in ['revenue', 'doanh', 'cost', 'chi', 'price', 'giá', 'rate', 'tỷ lệ']):
            sample = non_empty.head(15).astype(str)
            parsed_dates = pd.to_datetime(sample, format='mixed', errors='coerce')
            if parsed_dates.notnull().mean() >= 0.5:
                is_date = True
        else:
            sample = non_empty.head(15).astype(str)
            if all(re.search(r'^\d{1,4}[-/\.]\d{1,2}(?:[-/\.]\d{1,4})?', s.strip()) for s in sample):
                parsed_dates = pd.to_datetime(sample, format='mixed', errors='coerce')
                if parsed_dates.notnull().mean() >= 0.7:
                    is_date = True

        if is_date:
            date_cols.append(col)
            continue

        # 3. Kiểm tra cột Số liệu (Numeric / Metrics)
        if not is_id_col:
            parsed_nums = non_empty.apply(parse_flexible_number)
            valid_ratio = parsed_nums.notnull().mean()
            if valid_ratio >= 0.6:
                metric_cols.append(col)
                continue

        # 4. Còn lại là Cột Phân loại / Chiều phân tích (Dimensions)
        dim_cols.append(col)

    # Gợi ý ghép nối cột thông minh (Dynamic Mapping Suggestions) - Mở rộng hỗ trợ tiếng Việt & tiếng Anh
    revenue_kw = [
        'revenue', 'doanh thu', 'doanh_thu', 'doanhso', 'doanh_so', 'gmv', 'sales', 'total_sales',
        'thành tiền', 'thanh_tien', 'total_amount', 'amount', 'tổng tiền', 'tong_tien',
        'doanhthu', 'tiền hàng', 'doanh thu thuần', 'net_sales', 'giá trị đơn', 'gia tri don'
    ]
    cost_kw = [
        'ad_spend', 'adspend', 'ads', 'quảng cáo', 'quang_cao', 'marketing_cost', 'marketing',
        'chi phí ads', 'chi_phi_ads', 'chi phí', 'chi_phi', 'chiphi', 'cost', 'spend',
        'ngân sách', 'ngan_sach', 'expense', 'chiết khấu', 'discount'
    ]
    cogs_kw = [
        'cogs', 'giá vốn', 'gia_von', 'giavon', 'cost_of_goods', 'vốn', 'chi phí hàng',
        'phi_nhap', 'tiền vốn', 'unit_cost', 'total_cost'
    ]
    profit_kw = [
        'profit', 'gross_profit', 'net_profit', 'loi_nhuan', 'lợi nhuận', 'lãi gộp', 'lai_gop',
        'lãi', 'margin', 'lợi nhuận sau thuế', 'loinhuan'
    ]
    qty_kw = [
        'orders', 'order', 'order_count', 'số đơn', 'so_don', 'sodon', 'đơn hàng', 'don_hang',
        'quantity', 'số lượng', 'so_luong', 'soluong', 'qty', 'sl', 'volume', 'sản lượng', 'units'
    ]
    traffic_kw = [
        'traffic', 'views', 'clicks', 'lượt truy cập', 'truy_cap', 'truy cập', 'lượt xem',
        'luot_xem', 'impressions', 'sessions', 'reach', 'khách truy cập', 'visits'
    ]
    return_kw = [
        'returned', 'return', 'returned_orders', 'returns', 'hoàn', 'hoan', 'đơn hoàn', 'don_hoan',
        'hủy', 'huy', 'cancel', 'cancelled', 'trả hàng', 'tra_hang', 'refund', 'hoan_hang'
    ]
    price_kw = [
        'unit_price', 'price', 'đơn giá', 'don_gia', 'dongia', 'giá bán', 'gia_ban', 'giá', 'gia'
    ]

    def match_metric(keywords, exclude=None):
        exclude = exclude or []
        for kw in keywords:
            for c in metric_cols:
                if c not in exclude and kw in str(c).lower().replace('_', ' '):
                    return c
                if c not in exclude and kw in str(c).lower():
                    return c
        return None

    best_rev = match_metric(revenue_kw)
    best_cost = match_metric(cost_kw, exclude=[best_rev])
    best_cogs = match_metric(cogs_kw, exclude=[best_rev, best_cost])
    best_profit = match_metric(profit_kw, exclude=[best_rev, best_cost, best_cogs])
    best_qty = match_metric(qty_kw, exclude=[best_rev, best_cost, best_cogs, best_profit])
    best_traffic = match_metric(traffic_kw, exclude=[best_rev, best_cost, best_cogs, best_profit, best_qty])
    best_return = match_metric(return_kw, exclude=[best_rev, best_cost, best_cogs, best_profit, best_qty, best_traffic])
    best_price = match_metric(price_kw, exclude=[best_rev, best_cost, best_cogs, best_profit, best_qty])

    # Nếu không có cột khớp từ khóa doanh thu nhưng có cột metric đầu tiên, gợi ý cột metric đầu tiên làm chỉ số chính
    if not best_rev and not best_price and len(metric_cols) > 0:
        best_rev = metric_cols[0]

    non_id_dims = [c for c in dim_cols if not any(k in str(c).lower() for k in id_keywords)]
    usable_dims = non_id_dims if non_id_dims else dim_cols

    def match_dim(keywords, exclude=None):
        exclude = exclude or []
        for kw in keywords:
            for c in usable_dims:
                if c not in exclude and kw in str(c).lower():
                    return c
        return None

    best_channel = match_dim(['channel', 'kênh', 'kenh', 'platform', 'sàn', 'san', 'nguồn', 'source'])
    best_campaign = match_dim(['campaign', 'chiến dịch', 'chien_dich', 'chiendich', 'chương trình', 'promo', 'hoạt động'], exclude=[best_channel])
    best_category = match_dim(['category', 'danh mục', 'danh_muc', 'product', 'sản phẩm', 'san_pham', 'nhóm hàng', 'item', 'mặt hàng', 'brand'], exclude=[best_channel, best_campaign])
    best_region = match_dim(['region', 'khu vực', 'khu_vuc', 'city', 'tỉnh', 'thành phố', 'chi nhánh', 'branch', 'store', 'location', 'miền'], exclude=[best_channel, best_campaign, best_category])

    # Fallback gán các chiều phân tích có sẵn trong file nếu tên cột hoàn toàn mới
    assigned_dims = [d for d in [best_channel, best_campaign, best_category, best_region] if d]
    remaining_dims = [d for d in usable_dims if d not in assigned_dims]
    if not best_channel and remaining_dims:
        best_channel = remaining_dims.pop(0)
    if not best_campaign and remaining_dims:
        best_campaign = remaining_dims.pop(0)
    if not best_category and remaining_dims:
        best_category = remaining_dims.pop(0)
    if not best_region and remaining_dims:
        best_region = remaining_dims.pop(0)

    return {
        "all_columns": list(df.columns),
        "date_cols": date_cols,
        "metric_cols": metric_cols,
        "dim_cols": dim_cols,
        "mapping": {
            "date": date_cols[0] if date_cols else None,
            "channel": best_channel,
            "campaign": best_campaign,
            "category": best_category,
            "region": best_region,
            "revenue": best_rev,
            "unit_price": best_price,
            "quantity": best_qty,
            "returned_orders": best_return,
            "traffic": best_traffic,
            "cost": best_cost,
            "cogs": best_cogs,
            "profit": best_profit
        }
    }

# =============================================================================
# 4. BƯỚC 2: KIỂM ĐỊNH DỮ LIỆU THÔ (RAW DATA PROFILING & HEALTH CHECK)
# =============================================================================
def profile_raw_data(df):
    detected = detect_schema_columns(df)
    total_rows = len(df)
    total_cols = len(df.columns)

    columns_profiling = []
    total_missing_cells = 0
    total_format_errors = 0
    total_logic_anomalies = 0

    col_types = {}
    col_p99 = {}
    for col in df.columns:
        if col in detected["date_cols"]:
            col_type = "Date (Thời gian)"
        elif col in detected["metric_cols"]:
            col_type = "Metric (Chỉ số định lượng)"
        else:
            col_type = "Dimension (Chiều phân tích)"
        col_types[col] = col_type

        series = df[col]
        is_blank = series.isna() | series.astype(str).str.strip().str.lower().isin(['', 'nan', 'none', 'null', 'n/a', 'na'])
        missing_count = int(is_blank.sum())
        total_missing_cells += missing_count

        format_err_count = 0
        anomaly_count = 0
        if col in detected["metric_cols"]:
            parsed_nums = series[~is_blank].apply(parse_flexible_number)
            valid_nums = parsed_nums.dropna()
            if len(valid_nums) > 10:
                q1 = valid_nums.quantile(0.25)
                q3 = valid_nums.quantile(0.75)
                iqr = q3 - q1
                p99 = valid_nums.quantile(0.99)
                upper_bound = max(p99, q3 + 3.0 * iqr) if iqr > 0 else p99
                col_p99[col] = upper_bound

            for raw_val in series[~is_blank]:
                if has_formatting_noise(raw_val):
                    format_err_count += 1
                num_v = parse_flexible_number(raw_val)
                if pd.isna(num_v):
                    format_err_count += 1
                else:
                    if num_v < 0:
                        anomaly_count += 1
                    elif col in col_p99 and col_p99[col] > 0 and num_v > col_p99[col]:
                        anomaly_count += 1

        elif col in detected["date_cols"]:
            for raw_val in series[~is_blank]:
                if pd.isna(pd.to_datetime(str(raw_val), format='mixed', errors='coerce')):
                    format_err_count += 1

        total_format_errors += format_err_count
        total_logic_anomalies += anomaly_count

        sample_vals = [str(x) for x in series[~is_blank].unique()[:4]]
        columns_profiling.append({
            "column": str(col),
            "type": col_type,
            "missing_count": missing_count,
            "missing_pct": round(missing_count / max(total_rows, 1) * 100, 1),
            "format_errors": format_err_count,
            "anomalies": anomaly_count,
            "samples": sample_vals
        })

    # Kiểm tra lỗi logic chéo giữa cột Đơn hoàn và cột Số đơn (Returned_Orders > Orders)
    qty_col = detected["mapping"].get("quantity")
    ret_col = detected["mapping"].get("returned_orders")
    row_logic_errors = set()
    if qty_col and ret_col and qty_col in df.columns and ret_col in df.columns:
        q_s = df[qty_col].apply(parse_flexible_number)
        r_s = df[ret_col].apply(parse_flexible_number)
        bad_mask = (r_s.notnull() & q_s.notnull() & (r_s > q_s))
        cross_err_count = int(bad_mask.sum())
        total_logic_anomalies += cross_err_count
        row_logic_errors = set(df.index[bad_mask].tolist())

    duplicate_rows_count = int(df.duplicated().sum())

    # Raw Data Preview (20 dòng đầu + các dòng có lỗi nổi bật)
    preview_rows = []
    for idx, row in df.head(20).iterrows():
        row_dict = {}
        for col in df.columns:
            val = row[col]
            val_str = "" if pd.isna(val) else str(val).strip()
            is_error = False
            error_type = None
            error_msg = None

            if val_str.lower() in ['', 'nan', 'none', 'null', 'n/a', 'na']:
                is_error = True
                error_type = "missing"
                error_msg = "Ô bị trống (Missing / Null)"
            elif col in detected["metric_cols"]:
                num = parse_flexible_number(val)
                if pd.isna(num):
                    is_error = True
                    error_type = "format"
                    error_msg = "Không phải định dạng số hợp lệ"
                elif num < 0:
                    is_error = True
                    error_type = "anomaly"
                    error_msg = f"Giá trị âm vô lý ({val_str})"
                elif col == ret_col and idx in row_logic_errors:
                    is_error = True
                    error_type = "anomaly"
                    error_msg = "Lỗi logic: Số đơn hoàn > Số đơn đặt"
                elif col in col_p99 and col_p99[col] > 0 and num > col_p99[col]:
                    is_error = True
                    error_type = "anomaly"
                    error_msg = f"Ngoại lai vượt ngưỡng P99 ({num:,.0f})"
                elif has_formatting_noise(val):
                    is_error = True
                    error_type = "format"
                    error_msg = "Chứa ký tự chữ/đơn vị tiền tệ hoặc khoảng trắng thừa"

            row_dict[str(col)] = {
                "val": val_str,
                "is_error": is_error,
                "error_type": error_type,
                "error_msg": error_msg
            }
        preview_rows.append(row_dict)

    total_cells = max(total_rows * total_cols, 1)
    error_penalty = ((total_missing_cells + total_format_errors + total_logic_anomalies) / total_cells) * 100 + (duplicate_rows_count / max(total_rows, 1)) * 100
    health_score = max(0.0, round(100.0 - error_penalty * 2.5, 1))
    health_status = "Tốt (Sẵn sàng làm sạch)" if health_score >= 85 else ("Cần làm sạch chuẩn BI" if health_score >= 55 else "Nhiều nhiễu & lỗi dữ liệu")

    return {
        "has_data": True,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "columns_profiling": columns_profiling,
        "health_summary": {
            "total_missing_cells": total_missing_cells,
            "duplicate_rows": duplicate_rows_count,
            "format_errors": total_format_errors,
            "logic_anomalies": total_logic_anomalies,
            "health_score": health_score,
            "health_status": health_status
        },
        "preview_columns": [str(c) for c in df.columns],
        "preview_rows": preview_rows,
        "schema_detected": detected
    }

# =============================================================================
# 5. BƯỚC 3: LÀM SẠCH & TIỀN XỬ LÝ DỮ LIỆU ĐỘNG (SCHEMA-AGNOSTIC CLEANING)
# =============================================================================
def clean_and_preprocess(raw_df, options=None):
    if options is None:
        options = {
            "missing_numeric": "median",
            "missing_cat": "unknown",
            "deduplicate": True,
            "standardize_format": True,
            "handle_outliers": "cap"
        }

    df = raw_df.copy()
    rows_before = len(df)
    detected = detect_schema_columns(df)
    metric_cols = detected["metric_cols"]
    date_cols = detected["date_cols"]

    # Thống kê mô tả TRƯỚC khi làm sạch
    stats_before = {}
    for col in metric_cols:
        s_raw = df[col].apply(parse_flexible_number).dropna()
        stats_before[col] = {
            "count": int(len(s_raw)),
            "mean": round(float(s_raw.mean()), 2) if len(s_raw) > 0 else 0.0,
            "median": round(float(s_raw.median()), 2) if len(s_raw) > 0 else 0.0,
            "min": round(float(s_raw.min()), 2) if len(s_raw) > 0 else 0.0,
            "max": round(float(s_raw.max()), 2) if len(s_raw) > 0 else 0.0,
            "std": round(float(s_raw.std()), 2) if len(s_raw) > 1 else 0.0,
        }

    # 1. Khử dòng trùng lặp 100%
    duplicates_removed = 0
    if options.get("deduplicate", True):
        dup_mask = df.duplicated()
        duplicates_removed = int(dup_mask.sum())
        df = df.drop_duplicates().reset_index(drop=True)

    cells_filled = 0
    outliers_treated = 0
    format_fixed = 0

    # 2. Xử lý từng cột theo đúng kiểu dữ liệu thực tế
    for col in list(df.columns):
        if col in metric_cols:
            # Đếm số ô sửa định dạng
            for v in df[col].dropna():
                if has_formatting_noise(v):
                    format_fixed += 1

            df[col] = df[col].apply(parse_flexible_number).astype(float)
            missing_count = int(df[col].isna().sum())
            if missing_count > 0:
                method = options.get("missing_numeric", "median")
                if method == "drop":
                    df = df.dropna(subset=[col]).reset_index(drop=True)
                else:
                    cells_filled += missing_count
                    if method == "zero":
                        df[col] = df[col].fillna(0.0)
                    elif method == "mean":
                        val = df[col].mean()
                        df[col] = df[col].fillna(0.0 if pd.isna(val) else round(float(val), 2))
                    else:  # median
                        val = df[col].median()
                        df[col] = df[col].fillna(0.0 if pd.isna(val) else round(float(val), 2))

            # Xử lý số âm vô lý & Ngoại lai P99
            outlier_mode = options.get("handle_outliers", "cap")
            if outlier_mode in ["cap", "drop"]:
                neg_mask = df[col] < 0
                if neg_mask.sum() > 0:
                    outliers_treated += int(neg_mask.sum())
                    if outlier_mode == "drop":
                        df = df.loc[~neg_mask].reset_index(drop=True)
                    else:
                        df.loc[neg_mask, col] = df.loc[neg_mask, col].abs()

                if len(df) > 10:
                    p99 = float(df[col].quantile(0.99))
                    q1 = float(df[col].quantile(0.25))
                    q3 = float(df[col].quantile(0.75))
                    iqr = q3 - q1
                    cap_limit = max(p99, q3 + 3.0 * iqr) if iqr > 0 else p99
                    if cap_limit > 0:
                        ext_mask = df[col] > cap_limit
                        if ext_mask.sum() > 0:
                            outliers_treated += int(ext_mask.sum())
                            if outlier_mode == "drop":
                                df = df.loc[~ext_mask].reset_index(drop=True)
                            else:
                                df.loc[ext_mask, col] = round(cap_limit, 2)

        elif col in date_cols:
            parsed_d = pd.to_datetime(df[col], format='mixed', errors='coerce')
            missing_d = int(parsed_d.isna().sum())
            if missing_d > 0:
                cells_filled += missing_d
                mode_d = parsed_d.dropna().mode()
                fill_d = mode_d[0].strftime("%Y-%m-%d") if len(mode_d) > 0 else datetime.now().strftime("%Y-%m-%d")
                df[col] = parsed_d.dt.strftime("%Y-%m-%d").fillna(fill_d)
            else:
                df[col] = parsed_d.dt.strftime("%Y-%m-%d")

        else:
            # Cột phân loại (Dimensions)
            df[col] = df[col].astype(str).str.strip()
            blank_mask = df[col].str.lower().isin(['', 'nan', 'none', 'null', 'n/a', 'na'])
            if blank_mask.sum() > 0:
                cells_filled += int(blank_mask.sum())
                if options.get("missing_cat") == "mode":
                    valid_vals = df.loc[~blank_mask, col]
                    mode_val = valid_vals.mode()
                    fill_val = mode_val[0] if len(mode_val) > 0 else "Chưa phân loại (Unknown)"
                else:
                    fill_val = "Chưa phân loại (Unknown)"
                df.loc[blank_mask, col] = fill_val

    # Ràng buộc logic chéo: Đơn hoàn không vượt quá Số đơn đặt
    qty_col = detected["mapping"].get("quantity")
    ret_col = detected["mapping"].get("returned_orders")
    if qty_col and ret_col and qty_col in df.columns and ret_col in df.columns:
        bad_logic = df[ret_col] > df[qty_col]
        if bad_logic.sum() > 0:
            outliers_treated += int(bad_logic.sum())
            if options.get("handle_outliers") == "drop":
                df = df.loc[~bad_logic].reset_index(drop=True)
            else:
                df.loc[bad_logic, ret_col] = df.loc[bad_logic, qty_col]

    rows_after = len(df)

    # Thống kê mô tả SAU khi làm sạch
    stats_comparison = []
    for col in metric_cols:
        s_after = df[col].dropna()
        sb = stats_before.get(col, {})
        stats_comparison.append({
            "column": str(col),
            "count_before": sb.get("count", 0),
            "count_after": int(len(s_after)),
            "mean_before": sb.get("mean", 0.0),
            "mean_after": round(float(s_after.mean()), 2) if len(s_after) > 0 else 0.0,
            "median_before": sb.get("median", 0.0),
            "median_after": round(float(s_after.median()), 2) if len(s_after) > 0 else 0.0,
            "min_before": sb.get("min", 0.0),
            "min_after": round(float(s_after.min()), 2) if len(s_after) > 0 else 0.0,
            "max_before": sb.get("max", 0.0),
            "max_after": round(float(s_after.max()), 2) if len(s_after) > 0 else 0.0,
            "std_before": sb.get("std", 0.0),
            "std_after": round(float(s_after.std()), 2) if len(s_after) > 1 else 0.0
        })

    preview_clean = json.loads(df.head(20).to_json(orient="records", date_format="iso"))

    return {
        "cleaned_df": df,
        "has_cleaned": True,
        "cleaning_options": options,
        "summary": {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "rows_dropped": rows_before - rows_after,
            "cells_filled": cells_filled,
            "duplicates_removed": duplicates_removed,
            "format_fixed": format_fixed,
            "outliers_treated": outliers_treated
        },
        "stats_comparison": stats_comparison,
        "preview_columns": [str(c) for c in df.columns],
        "preview_rows": preview_clean
    }

# =============================================================================
# 6. BƯỚC 4: ÁNH XẠ CỘT ĐỘNG, TỰ TẠO CÔNG THỨC & TÍNH CHỈ SỐ BI (100% REAL DATA)
# =============================================================================
def evaluate_custom_formulas(df, custom_formulas):
    """
    Cho phép người dùng tự tạo công thức cột mới ngay trên giao diện.
    Cú pháp hỗ trợ: [Tên_Cột_A] + [Tên_Cột_B], [Doanh_Thu] * 0.1, ([Doanh_Thu] - [Chi_Phí]) / [Số_Đơn]
    """
    applied_formulas = []
    if not custom_formulas or not isinstance(custom_formulas, list):
        return df, applied_formulas

    for item in custom_formulas:
        col_name = str(item.get("name", "")).strip()
        expr = str(item.get("formula", "")).strip()
        if not col_name or not expr:
            continue

        try:
            # Thay thế [Column_Name] bằng biến an toàn trong môi trường tính toán
            local_env = {"np": np, "pd": pd}
            col_idx = 0

            def repl_col(match):
                nonlocal col_idx
                c_ref = match.group(1).strip()
                if c_ref in df.columns:
                    var_name = f"_col_{col_idx}"
                    col_idx += 1
                    local_env[var_name] = pd.to_numeric(df[c_ref], errors='coerce').fillna(0.0)
                    return var_name
                return "0.0"

            safe_expr = re.sub(r'\[([^\]]+)\]', repl_col, expr)
            # Chỉ cho phép ký tự toán học và tên biến _col_
            if re.match(r'^[\d\s\+\-\*\/\(\)\._col]+$', safe_expr):
                res_series = eval(safe_expr, {"__builtins__": {}}, local_env)
                if isinstance(res_series, (pd.Series, np.ndarray)):
                    res_series = pd.Series(res_series, index=df.index).replace([np.inf, -np.inf], 0.0).fillna(0.0).round(2)
                    df[col_name] = res_series
                else:
                    df[col_name] = float(res_series)
                applied_formulas.append({
                    "code": col_name,
                    "name": f"Cột tùy chỉnh: {col_name}",
                    "formula": expr,
                    "desc": "Công thức do người dùng tự thiết lập trên giao diện."
                })
        except Exception as e:
            print(f"Lỗi tính công thức tùy chỉnh {col_name}: {e}")

    return df, applied_formulas

def classify_row_adaptive(r, scenario, med_rev, med_margin, med_orders, med_aov, has_returns, has_ad_spend, has_profit_or_cost):
    """Phân loại tự thích nghi vào 4 góc phần tư theo 3 kịch bản dữ liệu."""
    rev = float(r.get("_revenue", 0.0) or 0.0)
    np_val = float(r.get("net_profit", 0.0) or 0.0)
    margin = float(r.get("net_margin_percent", 0.0) or 0.0)
    ret = float(r.get("return_rate", 0.0) or 0.0)
    roas_val = float(r.get("roas", 0.0) or 0.0)
    cir_val = float(r.get("cir_percent", 0.0) or 0.0)
    aov_val = float(r.get("aov", 0.0) or 0.0)
    ord_val = float(r.get("_orders", 0.0) or 0.0)

    if scenario == "A":
        # Kịch bản A: Đầy đủ Doanh thu + Chi phí Ads + Giá vốn/Lợi nhuận
        if np_val < 0 or (rev < med_rev and margin < 5.0):
            return QUAD_BURNER
        if rev >= med_rev and (margin < 12.0 or (has_returns and ret >= 15.0) or cir_val > 25.0):
            return QUAD_TRAP
        if (margin >= 20.0 or roas_val >= 5.0) and (not has_returns or ret < 8.0):
            return QUAD_COW
        if rev >= med_rev and (margin >= 20.0 or roas_val >= 4.0):
            return QUAD_STAR
        if margin >= 15.0 or roas_val >= 3.0:
            return QUAD_COW
        return QUAD_TRAP

    elif scenario == "B":
        # Kịch bản B: Bán hàng / Phân phối có Doanh thu + Giá vốn/Lợi nhuận, KHÔNG Ads
        if np_val < 0:
            return QUAD_BURNER
        if rev >= med_rev and margin >= med_margin and margin > 0:
            return QUAD_STAR
        if rev < med_rev and margin >= med_margin and margin > 0:
            return QUAD_COW
        if rev >= med_rev and margin < med_margin:
            return QUAD_TRAP
        return QUAD_BURNER

    else:
        # Kịch bản C: Chỉ có Doanh thu & Số lượng/Đơn giá, KHÔNG Giá vốn/Ads
        if rev >= med_rev and (aov_val >= med_aov or ord_val >= med_orders):
            return QUAD_STAR
        elif rev < med_rev and aov_val >= med_aov:
            return QUAD_COW
        elif rev >= med_rev and aov_val < med_aov:
            return QUAD_TRAP
        else:
            return QUAD_BURNER

def determine_alert_adaptive(quad, net_p, ret_rate, has_profit_or_cost, has_returns):
    """Xác định mức cảnh báo 100% tiếng Việt: Tối ưu / Cảnh báo / Nguy hiểm."""
    if quad == QUAD_BURNER or (has_profit_or_cost and net_p < 0) or (has_returns and ret_rate > 15.0):
        return ALERT_DANGER
    elif quad == QUAD_TRAP:
        return ALERT_WARNING
    else:
        return ALERT_OPTIMAL

def engineer_features(clean_df, custom_mapping=None, custom_formulas=None):
    """
    Tính toán hệ thống chỉ số Unit Economics & Phễu chuyển đổi dựa 100% trên dữ liệu thật của người dùng.
    Hỗ trợ nhận diện cột mở rộng, ẩn cột rỗng và phân loại tự thích nghi 100% tiếng Việt.
    """
    df = clean_df.copy()

    # 1. Thực thi các công thức cột tùy chỉnh của người dùng trước
    df, user_formula_docs = evaluate_custom_formulas(df, custom_formulas)

    detected = detect_schema_columns(df)
    default_map = detected["mapping"]
    mapping = {}
    for k in ["date", "channel", "campaign", "category", "region", "revenue", "unit_price", "quantity", "returned_orders", "traffic", "cost", "cogs", "profit"]:
        if custom_mapping and k in custom_mapping:
            val = custom_mapping.get(k)
            mapping[k] = val if (val and val in df.columns) else None
        else:
            val = default_map.get(k)
            mapping[k] = val if (val and val in df.columns) else None

    rev_col = mapping.get("revenue")
    price_col = mapping.get("unit_price")
    qty_col = mapping.get("quantity")
    ret_col = mapping.get("returned_orders")
    traffic_col = mapping.get("traffic")
    cost_col = mapping.get("cost")
    cogs_col = mapping.get("cogs")
    profit_col = mapping.get("profit")

    # Helper trích xuất số an toàn (xử lý cả dấu phẩy/chấm/khoảng trắng)
    def clean_num_series(s):
        if s is None:
            return pd.Series(0.0, index=df.index)
        return pd.to_numeric(
            s.astype(str).str.replace(',', '', regex=False).str.strip(),
            errors='coerce'
        ).fillna(0.0)

    # 1. Orders / Quantity
    if qty_col and qty_col in df.columns:
        df["_orders"] = clean_num_series(df[qty_col])
    else:
        df["_orders"] = 1.0

    # 2. Revenue (Nếu không có Doanh thu nhưng có Đơn giá & Số lượng thì tự nhân)
    if rev_col and rev_col in df.columns:
        df["_revenue"] = clean_num_series(df[rev_col])
    elif price_col and price_col in df.columns:
        df["_revenue"] = clean_num_series(df[price_col]) * df["_orders"]
    else:
        df["_revenue"] = 0.0

    # 3. Ad Spend
    if cost_col and cost_col in df.columns:
        df["_ad_spend"] = clean_num_series(df[cost_col])
    else:
        df["_ad_spend"] = 0.0

    # 4. COGS
    if cogs_col and cogs_col in df.columns:
        df["_cogs"] = clean_num_series(df[cogs_col])
    else:
        df["_cogs"] = 0.0

    # 5. Existing Profit (nếu file đã có sẵn cột lợi nhuận)
    if profit_col and profit_col in df.columns:
        df["_existing_profit"] = clean_num_series(df[profit_col])
        has_existing_profit = True
    else:
        df["_existing_profit"] = None
        has_existing_profit = False

    # 6. Returned Orders
    if ret_col and ret_col in df.columns:
        df["_returned"] = clean_num_series(df[ret_col])
        df["_returned"] = np.minimum(df["_returned"], df["_orders"])
    else:
        status_col = next((c for c in df.columns if any(k in str(c).lower() for k in ['status', 'trạng thái', 'trang_thai', 'tình trạng'])), None)
        if status_col:
            df["_returned"] = df[status_col].astype(str).apply(
                lambda s: 1.0 if any(k in s.lower() for k in ['hủy', 'hoàn', 'trả', 'cancel', 'return', 'refund']) else 0.0
            ) * df["_orders"]
        else:
            df["_returned"] = 0.0

    # 7. Traffic
    if traffic_col and traffic_col in df.columns:
        df["_traffic"] = clean_num_series(df[traffic_col])
    else:
        df["_traffic"] = 0.0

    # Dynamic visibility flags
    has_traffic = bool(traffic_col is not None and df["_traffic"].sum() > 0)
    has_returns = bool((ret_col is not None or df["_returned"].sum() > 0) and df["_returned"].sum() > 0)
    has_ad_spend = bool(cost_col is not None and df["_ad_spend"].sum() > 0)
    has_cogs = bool(cogs_col is not None and df["_cogs"].sum() > 0)
    has_profit_or_cost = bool(has_existing_profit or has_cogs or has_ad_spend)

    # Tính toán các chỉ số phái sinh
    safe_orders = np.where(df["_orders"] > 0, df["_orders"], np.nan)
    safe_traffic = np.where(df["_traffic"] > 0, df["_traffic"], np.nan)
    safe_rev = np.where(df["_revenue"] > 0, df["_revenue"], np.nan)
    safe_spend = np.where(df["_ad_spend"] > 0, df["_ad_spend"], np.nan)

    df["cr_percent"] = np.where(df["_traffic"] > 0, (df["_orders"] / safe_traffic * 100.0).round(2), 0.0)
    df["net_orders"] = np.maximum(df["_orders"] - df["_returned"], 0.0).round(2)
    df["return_rate"] = np.where(df["_orders"] > 0, (df["_returned"] / safe_orders * 100.0).round(2), 0.0)
    df["net_realized_revenue"] = (df["_revenue"] * (1.0 - df["return_rate"] / 100.0)).round(2)

    df["aov"] = np.where(df["_orders"] > 0, (df["_revenue"] / safe_orders).round(2), 0.0)
    df["cpa"] = np.where(df["_orders"] > 0, (df["_ad_spend"] / safe_orders).round(2), 0.0)
    df["cir_percent"] = np.where(df["_revenue"] > 0, (df["_ad_spend"] / safe_rev * 100.0).round(2), 0.0)
    df["roas"] = np.where(df["_ad_spend"] > 0, (df["_revenue"] / safe_spend).round(2), 0.0)

    if has_existing_profit:
        df["gross_profit"] = df["_existing_profit"].round(2)
        df["net_profit"] = (df["_existing_profit"] - df["_ad_spend"]).round(2)
    else:
        df["gross_profit"] = (df["_revenue"] - df["_cogs"]).round(2)
        df["net_profit"] = (df["net_realized_revenue"] - df["_cogs"] - df["_ad_spend"]).round(2)

    df["net_margin_percent"] = np.where(df["_revenue"] > 0, (df["net_profit"] / safe_rev * 100.0).round(2), 0.0)

    # Xác định Kịch bản dữ liệu (Scenario A / B / C)
    if has_ad_spend and has_profit_or_cost:
        scenario = "A"
    elif has_profit_or_cost:
        scenario = "B"
    else:
        scenario = "C"

    med_rev = float(df["_revenue"].median()) if len(df) > 0 else 0.0
    med_margin = float(df["net_margin_percent"].median()) if len(df) > 0 else 0.0
    med_orders = float(df["_orders"].median()) if len(df) > 0 else 0.0
    med_aov = float(df["aov"].median()) if len(df) > 0 else 0.0

    # Phân nhóm tự thích nghi 100% tiếng Việt
    df["quadrant"] = df.apply(
        lambda r: classify_row_adaptive(r, scenario, med_rev, med_margin, med_orders, med_aov, has_returns, has_ad_spend, has_profit_or_cost),
        axis=1
    )
    df["alert"] = df.apply(
        lambda r: determine_alert_adaptive(r["quadrant"], r["net_profit"], r["return_rate"], has_profit_or_cost, has_returns),
        axis=1
    )

    # Gán các cột người dùng hiển thị 100% tiếng Việt chuẩn Quản trị Kinh doanh số
    vi_cols_added = []
    if has_traffic:
        df["Tỷ lệ chuyển đổi (%)"] = df["cr_percent"]
        vi_cols_added.append("Tỷ lệ chuyển đổi (%)")

    if has_returns:
        df["Đơn thành công"] = df["net_orders"]
        df["Tỷ lệ hoàn (%)"] = df["return_rate"]
        df["Doanh thu thực thu"] = df["net_realized_revenue"]
        vi_cols_added.extend(["Đơn thành công", "Tỷ lệ hoàn (%)", "Doanh thu thực thu"])

    df["Giá trị TB đơn (AOV)"] = df["aov"]
    vi_cols_added.append("Giá trị TB đơn (AOV)")

    if has_ad_spend:
        df["Chi phí/Đơn (CAC)"] = df["cpa"]
        df["Tỷ lệ chi phí Ads (CIR %)"] = df["cir_percent"]
        df["Hiệu quả Ads (ROAS)"] = df["roas"]
        vi_cols_added.extend(["Chi phí/Đơn (CAC)", "Tỷ lệ chi phí Ads (CIR %)", "Hiệu quả Ads (ROAS)"])

    if has_cogs:
        df["Lợi nhuận gộp"] = df["gross_profit"]
        vi_cols_added.append("Lợi nhuận gộp")

    if has_profit_or_cost:
        df["Lợi nhuận ròng"] = df["net_profit"]
        df["Biên lợi nhuận (%)"] = df["net_margin_percent"]
        vi_cols_added.extend(["Lợi nhuận ròng", "Biên lợi nhuận (%)"])

    df["Phân nhóm Ma trận"] = df["quadrant"]
    df["Mức cảnh báo"] = df["alert"]
    vi_cols_added.extend(["Phân nhóm Ma trận", "Mức cảnh báo"])

    # Chỉ hiển thị các cột gốc và cột tiếng Việt (ẩn triệt để các biến snake_case nội bộ)
    user_orig_cols = [c for c in clean_df.columns if not str(c).startswith('_')]
    display_cols = user_orig_cols + vi_cols_added

    # Tính bảng gộp nhóm (Group-by) cho dữ liệu giao dịch lẻ (Requirement 4)
    usable_dims = detected["dim_cols"]
    grouped_summaries = {}
    for d_col in usable_dims:
        if d_col in df.columns:
            try:
                g_df = df.groupby(d_col, dropna=False).agg(
                    rev=("_revenue", "sum"),
                    orders=("_orders", "sum"),
                    ret=("_returned", "sum"),
                    traffic=("_traffic", "sum"),
                    spend=("_ad_spend", "sum"),
                    cogs=("_cogs", "sum"),
                    net_p=("net_profit", "sum") if has_profit_or_cost else ("_revenue", "sum")
                ).reset_index()

                g_med_rev = float(g_df["rev"].median()) if len(g_df) > 0 else 0.0
                g_med_margin = float((g_df["net_p"] / np.where(g_df["rev"] > 0, g_df["rev"], np.nan) * 100.0).median()) if len(g_df) > 0 else 0.0
                g_med_orders = float(g_df["orders"].median()) if len(g_df) > 0 else 0.0
                g_med_aov = float((g_df["rev"] / np.where(g_df["orders"] > 0, g_df["orders"], np.nan)).median()) if len(g_df) > 0 else 0.0

                g_rows = []
                for _, gr in g_df.iterrows():
                    d_val = str(gr[d_col]).strip()
                    if not d_val or d_val.lower() in ['nan', 'none']:
                        d_val = "Chưa phân loại"
                    g_rev = float(gr["rev"])
                    g_ord = float(gr["orders"])
                    g_ret = float(gr["ret"])
                    g_trf = float(gr["traffic"])
                    g_spd = float(gr["spend"])
                    g_cog = float(gr["cogs"])
                    g_net = float(gr["net_p"])

                    g_ret_rate = round((g_ret / g_ord * 100.0), 1) if g_ord > 0 else 0.0
                    g_cr = round((g_ord / g_trf * 100.0), 2) if g_trf > 0 else 0.0
                    g_aov = round(g_rev / g_ord, 2) if g_ord > 0 else 0.0
                    g_cpa = round(g_spd / g_ord, 2) if g_ord > 0 else 0.0
                    g_cir = round((g_spd / g_rev * 100.0), 1) if g_rev > 0 else 0.0
                    g_roas = round((g_rev / g_spd), 2) if g_spd > 0 else 0.0
                    g_margin = round((g_net / g_rev * 100.0), 1) if g_rev > 0 else 0.0
                    g_net_rev = round(g_rev * (1.0 - g_ret_rate / 100.0), 2)

                    dummy_r = {
                        "_revenue": g_rev,
                        "net_profit": g_net,
                        "net_margin_percent": g_margin,
                        "return_rate": g_ret_rate,
                        "roas": g_roas,
                        "cir_percent": g_cir,
                        "aov": g_aov,
                        "_orders": g_ord
                    }
                    g_quad = classify_row_adaptive(dummy_r, scenario, g_med_rev, g_med_margin, g_med_orders, g_med_aov, has_returns, has_ad_spend, has_profit_or_cost)
                    g_alert = determine_alert_adaptive(g_quad, g_net, g_ret_rate, has_profit_or_cost, has_returns)

                    row_dict = {
                        str(d_col): d_val,
                        "Doanh thu": g_rev,
                        "Số đơn / Sản lượng": g_ord
                    }
                    if has_returns:
                        row_dict["Đơn thành công"] = max(g_ord - g_ret, 0.0)
                        row_dict["Tỷ lệ hoàn (%)"] = g_ret_rate
                        row_dict["Doanh thu thực thu"] = g_net_rev
                    if has_traffic:
                        row_dict["Tỷ lệ chuyển đổi (%)"] = g_cr
                    row_dict["Giá trị TB đơn (AOV)"] = g_aov
                    if has_ad_spend:
                        row_dict["Chi phí Ads"] = g_spd
                        row_dict["Chi phí/Đơn (CAC)"] = g_cpa
                        row_dict["Tỷ lệ chi phí Ads (CIR %)"] = g_cir
                        row_dict["Hiệu quả Ads (ROAS)"] = g_roas
                    if has_cogs:
                        row_dict["Giá vốn (COGS)"] = g_cog
                        row_dict["Lợi nhuận gộp"] = g_rev - g_cog
                    if has_profit_or_cost:
                        row_dict["Lợi nhuận ròng"] = g_net
                        row_dict["Biên lợi nhuận (%)"] = g_margin
                    row_dict["Phân nhóm Ma trận"] = g_quad
                    row_dict["Mức cảnh báo"] = g_alert
                    g_rows.append(row_dict)

                grouped_cols = list(g_rows[0].keys()) if g_rows else [str(d_col)]
                grouped_summaries[str(d_col)] = {
                    "dimension": str(d_col),
                    "columns": grouped_cols,
                    "rows": g_rows[:50]
                }
            except Exception as e:
                print(f"Lỗi gom nhóm theo chiều {d_col}: {e}")

    # Danh mục công thức hiển thị 100% tiếng Việt
    standard_formulas = []
    if has_traffic:
        standard_formulas.append({"code": "cr_percent", "name": "Tỷ lệ chuyển đổi (%)", "formula": "(Đơn hàng / Lượt truy cập) * 100", "desc": "Tỷ lệ khách truy cập chuyển đổi thành đơn hàng."})
    if has_returns:
        standard_formulas.append({"code": "net_orders", "name": "Đơn thành công", "formula": "Đơn hàng - Đơn hoàn/hủy", "desc": "Số đơn hàng thực giao thành công sau trừ hoàn/hủy."})
        standard_formulas.append({"code": "return_rate", "name": "Tỷ lệ hoàn (%)", "formula": "(Đơn hoàn / Tổng đơn) * 100", "desc": "Cảnh báo Nguy hiểm khi > 15%, Cảnh báo khi 8% - 15%."})
        standard_formulas.append({"code": "net_realized_revenue", "name": "Doanh thu thực thu", "formula": "Doanh thu * (1 - Tỷ lệ hoàn %)", "desc": "Doanh thu thực tế giữ lại sau khi trừ hoàn hàng."})
    standard_formulas.append({"code": "aov", "name": "Giá trị TB đơn (AOV)", "formula": "Doanh thu / Đơn hàng", "desc": "Quy mô doanh thu trung bình trên mỗi đơn hàng."})
    if has_ad_spend:
        standard_formulas.append({"code": "cpa", "name": "Chi phí/Đơn (CAC)", "formula": "Chi phí Ads / Đơn hàng", "desc": "Chi phí quảng cáo bỏ ra để có một đơn hàng."})
        standard_formulas.append({"code": "cir_percent", "name": "Tỷ lệ chi phí Ads (CIR %)", "formula": "(Chi phí Ads / Doanh thu) * 100", "desc": "Tỷ trọng chi phí quảng cáo trên tổng doanh thu."})
        standard_formulas.append({"code": "roas", "name": "Hiệu quả Ads (ROAS)", "formula": "Doanh thu / Chi phí Ads", "desc": "Doanh thu tạo ra trên mỗi 1 đồng chi phí quảng cáo."})
    if has_cogs:
        standard_formulas.append({"code": "gross_profit", "name": "Lợi nhuận gộp", "formula": "Doanh thu - Giá vốn (COGS)", "desc": "Lợi nhuận sau khi trừ giá vốn hàng bán."})
    if has_profit_or_cost:
        standard_formulas.append({"code": "net_profit", "name": "Lợi nhuận ròng", "formula": "Doanh thu thực thu - Giá vốn - Chi phí Ads", "desc": "Lợi nhuận thực thu cuối cùng sau mọi chi phí."})
        standard_formulas.append({"code": "net_margin_percent", "name": "Biên lợi nhuận (%)", "formula": "(Lợi nhuận ròng / Doanh thu) * 100", "desc": "Tỷ suất lợi nhuận ròng trên tổng doanh thu."})

    all_formulas = user_formula_docs + standard_formulas

    q_counts = {
        QUAD_STAR: int((df["quadrant"] == QUAD_STAR).sum()),
        QUAD_COW: int((df["quadrant"] == QUAD_COW).sum()),
        QUAD_TRAP: int((df["quadrant"] == QUAD_TRAP).sum()),
        QUAD_BURNER: int((df["quadrant"] == QUAD_BURNER).sum()),
        "Star": int((df["quadrant"] == QUAD_STAR).sum()),
        "Cash Cow": int((df["quadrant"] == QUAD_COW).sum()),
        "Volume Trap": int((df["quadrant"] == QUAD_TRAP).sum()),
        "Cash Burner": int((df["quadrant"] == QUAD_BURNER).sum())
    }

    preview_processed = json.loads(df[display_cols].head(25).to_json(orient="records", date_format="iso"))

    return {
        "processed_df": df,
        "has_processed": True,
        "scenario": scenario,
        "available_columns": [c for c in clean_df.columns if not str(c).startswith('_')],
        "available_dimensions": usable_dims,
        "grouped_summaries": grouped_summaries,
        "mapping_used": mapping,
        "custom_formulas": custom_formulas or [],
        "feature_formulas": all_formulas,
        "quadrant_counts": q_counts,
        "preview_columns": display_cols,
        "preview_rows": preview_processed
    }

# =============================================================================
# 7. BƯỚC 5: BI DASHBOARD, SCORECARD, CROSS-PIVOT & ACTIONABLE PLAYBOOK
# =============================================================================
def aggregate_by_dimension(df, dim_col):
    if not dim_col or dim_col not in df.columns:
        return [], [], {QUAD_STAR: 0, QUAD_COW: 0, QUAD_TRAP: 0, QUAD_BURNER: 0, "Star": 0, "Cash Cow": 0, "Volume Trap": 0, "Cash Burner": 0}

    grouped = df.groupby(dim_col, dropna=False).agg(
        rev=("_revenue", "sum"),
        net_rev=("net_realized_revenue", "sum"),
        orders=("_orders", "sum"),
        returned=("_returned", "sum"),
        traffic=("_traffic", "sum"),
        spend=("_ad_spend", "sum"),
        cogs=("_cogs", "sum"),
        gross_p=("gross_profit", "sum"),
        net_p=("net_profit", "sum")
    ).reset_index()

    median_dim_rev = float(grouped["rev"].median()) if len(grouped) > 0 else 0.0
    median_dim_orders = float(grouped["orders"].median()) if len(grouped) > 0 else 0.0
    has_ad_spend = float(grouped["spend"].sum()) > 0
    has_cost = (has_ad_spend or float(grouped["cogs"].sum()) > 0 or "Lợi nhuận ròng" in df.columns)
    has_returns = float(grouped["returned"].sum()) > 0
    has_profit_or_cost = has_cost or (df["net_profit"].abs().sum() > 0)

    if has_ad_spend and has_profit_or_cost:
        scenario = "A"
    elif has_profit_or_cost:
        scenario = "B"
    else:
        scenario = "C"

    median_dim_margin = float((grouped["net_p"] / np.where(grouped["rev"] > 0, grouped["rev"], np.nan) * 100.0).median()) if len(grouped) > 0 else 0.0
    median_dim_aov = float((grouped["rev"] / np.where(grouped["orders"] > 0, grouped["orders"], np.nan)).median()) if len(grouped) > 0 else 0.0

    items = []
    scatter = []
    q_counts = {
        QUAD_STAR: 0, QUAD_COW: 0, QUAD_TRAP: 0, QUAD_BURNER: 0,
        "Star": 0, "Cash Cow": 0, "Volume Trap": 0, "Cash Burner": 0
    }

    for _, row in grouped.iterrows():
        name = str(row[dim_col]).strip()
        if not name or name.lower() in ['nan', 'none']:
            name = "Chưa phân loại"

        rev = float(row["rev"])
        net_r = float(row["net_rev"])
        orders = float(row["orders"])
        returned = float(row["returned"])
        traffic = float(row["traffic"])
        spend = float(row["spend"])
        cogs = float(row["cogs"])
        net_p = float(row["net_p"])

        cr = round((orders / traffic * 100.0), 2) if traffic > 0 else 0.0
        ret_rate = round((returned / orders * 100.0), 1) if orders > 0 else 0.0
        net_o = max(orders - returned, 0.0)
        i_aov = round(rev / orders, 2) if orders > 0 else 0.0
        i_cpa = round(spend / orders, 2) if orders > 0 else 0.0
        i_cir = round((spend / rev * 100.0), 1) if rev > 0 else 0.0
        i_margin = round((net_p / rev * 100.0), 1) if rev > 0 else 0.0
        i_roas = round((rev / spend), 2) if spend > 0 else 0.0

        dummy_r = {
            "_revenue": rev,
            "net_profit": net_p,
            "net_margin_percent": i_margin,
            "return_rate": ret_rate,
            "roas": i_roas,
            "cir_percent": i_cir,
            "aov": i_aov,
            "_orders": orders
        }
        quad = classify_row_adaptive(dummy_r, scenario, median_dim_rev, median_dim_margin, median_dim_orders, median_dim_aov, has_returns, has_ad_spend, has_profit_or_cost)
        alert_str = determine_alert_adaptive(quad, net_p, ret_rate, has_profit_or_cost, has_returns)

        q_counts[quad] = q_counts.get(quad, 0) + 1
        if quad == QUAD_STAR: q_counts["Star"] = q_counts.get("Star", 0) + 1
        elif quad == QUAD_COW: q_counts["Cash Cow"] = q_counts.get("Cash Cow", 0) + 1
        elif quad == QUAD_TRAP: q_counts["Volume Trap"] = q_counts.get("Volume Trap", 0) + 1
        elif quad == QUAD_BURNER: q_counts["Cash Burner"] = q_counts.get("Cash Burner", 0) + 1

        items.append({
            "name": name,
            "quadrant": quad,
            "alert": alert_str,
            "revenue": rev,
            "net_realized_revenue": net_r,
            "orders": orders,
            "returned_orders": returned,
            "return_rate": ret_rate,
            "net_orders": net_o,
            "traffic": traffic,
            "cr_percent": cr,
            "aov": i_aov,
            "ad_spend": spend,
            "cpa": i_cpa,
            "cir_percent": i_cir,
            "roas": i_roas,
            "cogs": cogs,
            "net_profit": net_p,
            "net_margin_percent": i_margin
        })

        scatter.append({
            "name": name,
            "quadrant": quad,
            "revenue": rev,
            "x": i_roas if has_ad_spend else round(i_aov / 1000.0, 1),
            "y": i_margin if has_profit_or_cost else round(rev / 1000000.0, 2),
            "r": max(min(int(np.sqrt(rev) / 250), 30), 6) if rev > 0 else 6
        })

    items.sort(key=lambda x: x["revenue"], reverse=True)
    return items, scatter, q_counts

def compute_cross_pivot(df, row_dim, col_dim):
    if not row_dim or not col_dim or row_dim not in df.columns or col_dim not in df.columns:
        return []
    if row_dim == col_dim:
        p = df.groupby([row_dim], dropna=False).agg(
            rev=("_revenue", "sum"),
            net_rev=("net_realized_revenue", "sum"),
            orders=("_orders", "sum"),
            returned=("_returned", "sum"),
            spend=("_ad_spend", "sum"),
            net_p=("net_profit", "sum")
        ).reset_index()
        p["_col_dim"] = "Tất cả"
        col_key = "_col_dim"
    else:
        p = df.groupby([row_dim, col_dim], dropna=False).agg(
            rev=("_revenue", "sum"),
            net_rev=("net_realized_revenue", "sum"),
            orders=("_orders", "sum"),
            returned=("_returned", "sum"),
            spend=("_ad_spend", "sum"),
            net_p=("net_profit", "sum")
        ).reset_index()
        col_key = col_dim

    res = []
    for _, r in p.sort_values(by="rev", ascending=False).head(25).iterrows():
        orders = float(r["orders"])
        rev = float(r["rev"])
        spend = float(r["spend"])
        net_p = float(r["net_p"])
        ret_rate = round((float(r["returned"]) / orders * 100.0), 1) if orders > 0 else 0.0
        roas = round((rev / spend), 2) if spend > 0 else 0.0
        margin = round((net_p / rev * 100.0), 1) if rev > 0 else 0.0

        if ret_rate > 15.0 or net_p < 0:
            alert = "RED"
        elif ret_rate >= 8.0 or (spend > 0 and margin < 10.0):
            alert = "YELLOW"
        else:
            alert = "GREEN"

        res.append({
            "row_dim": str(r[row_dim]),
            "col_dim": str(r[col_key]),
            "revenue": round(rev, 2),
            "net_revenue": round(float(r["net_rev"]), 2),
            "orders": round(orders, 2),
            "return_rate": ret_rate,
            "ad_spend": round(spend, 2),
            "net_profit": round(net_p, 2),
            "net_margin": margin,
            "roas": roas,
            "alert": alert
        })
    return res

def generate_step5_dashboard(processed_df, mapping, business_context=None, filters=None):
    df = processed_df.copy()

    # Áp dụng bộ lọc động (Filters) nếu người dùng chọn trên Dashboard
    if filters and isinstance(filters, dict):
        for col, val in filters.items():
            if val and val != "ALL" and col in df.columns:
                df = df[df[col].astype(str) == str(val)].copy()

    total_revenue = float(df["_revenue"].sum())
    net_realized_revenue = float(df["net_realized_revenue"].sum())
    total_orders = float(df["_orders"].sum())
    total_returned = float(df["_returned"].sum())
    total_traffic = float(df["_traffic"].sum())
    total_ad_spend = float(df["_ad_spend"].sum())
    total_cogs = float(df["_cogs"].sum())
    gross_profit = float(df["gross_profit"].sum())
    net_profit = float(df["net_profit"].sum())

    net_orders = max(total_orders - total_returned, 0.0)
    system_return_rate = round((total_returned / total_orders * 100.0), 1) if total_orders > 0 else 0.0
    system_cr = round((total_orders / total_traffic * 100.0), 2) if total_traffic > 0 else 0.0
    aov = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    cpa = round(total_ad_spend / total_orders, 2) if total_orders > 0 else 0.0
    cir_percent = round((total_ad_spend / total_revenue * 100.0), 1) if total_revenue > 0 else 0.0
    net_margin_percent = round((net_profit / total_revenue * 100.0), 1) if total_revenue > 0 else 0.0
    roas = round((total_revenue / total_ad_spend), 2) if total_ad_spend > 0 else 0.0

    if system_return_rate > 15.0 or (net_profit < 0 and total_revenue > 0) or (total_traffic > 0 and system_cr < 2.0):
        system_alert = ALERT_DANGER
    elif system_return_rate >= 8.0 or cir_percent > 30.0 or ((total_ad_spend > 0 or total_cogs > 0) and net_margin_percent < 10.0):
        system_alert = ALERT_WARNING
    else:
        system_alert = ALERT_OPTIMAL

    # Tìm tất cả các cột Dimension có trong file để người dùng tự do chuyển đổi góc nhìn
    detected = detect_schema_columns(df[[c for c in df.columns if not str(c).startswith('_')]])
    available_dims = detected["dim_cols"]

    chan_col = mapping.get("channel") or (available_dims[0] if len(available_dims) > 0 else None)
    camp_col = mapping.get("campaign") or (available_dims[1] if len(available_dims) > 1 else chan_col)
    cat_col = mapping.get("category") or (available_dims[2] if len(available_dims) > 2 else chan_col)
    reg_col = mapping.get("region") or (available_dims[3] if len(available_dims) > 3 else camp_col)
    date_col = mapping.get("date")

    scorecards_by_dim = {}
    scatters_by_dim = {}
    quads_by_dim = {}
    for d_col in available_dims:
        sc, scat, qc = aggregate_by_dimension(df, d_col)
        scorecards_by_dim[str(d_col)] = sc
        scatters_by_dim[str(d_col)] = scat
        quads_by_dim[str(d_col)] = qc

    primary_dim = camp_col or chan_col or (available_dims[0] if available_dims else None)
    primary_scorecard = scorecards_by_dim.get(str(primary_dim), [])
    primary_scatter = scatters_by_dim.get(str(primary_dim), [])
    primary_quadrants = quads_by_dim.get(str(primary_dim), {QUAD_STAR: 0, QUAD_COW: 0, QUAD_TRAP: 0, QUAD_BURNER: 0, "Star": 0, "Cash Cow": 0, "Volume Trap": 0, "Cash Burner": 0})

    # Pivot 1 & Pivot 2 dựa trên các chiều thật của file
    pivot_camp_chan = compute_cross_pivot(df, camp_col or primary_dim, chan_col or primary_dim)
    pivot_cat_reg = compute_cross_pivot(df, cat_col or primary_dim, reg_col or primary_dim)

    # Xu hướng theo thời gian & Nhật ký hoạt động
    daily_activity_log = []
    time_trend = {"labels": [], "revenue": [], "ad_spend": [], "net_profit": []}
    if date_col and date_col in df.columns:
        try:
            d_grouped = df.groupby(date_col, dropna=True).agg(
                rev=("_revenue", "sum"),
                orders=("_orders", "sum"),
                spend=("_ad_spend", "sum"),
                net_p=("net_profit", "sum")
            ).reset_index().sort_values(by=date_col)
            for _, r in d_grouped.tail(30).iterrows():
                d_rev = round(float(r["rev"]), 2)
                d_spend = round(float(r["spend"]), 2)
                d_net = round(float(r["net_p"]), 2)
                d_cir = round((d_spend / d_rev * 100.0), 1) if d_rev > 0 else 0.0
                daily_activity_log.append({
                    "date": str(r[date_col]),
                    "revenue": d_rev,
                    "orders": round(float(r["orders"]), 2),
                    "spend": d_spend,
                    "net_profit": d_net,
                    "cir": d_cir,
                    "anomaly": "Cảnh báo: Lỗ ròng / Chi phí vượt thu" if d_net < 0 else ("CIR cao (>30%)" if d_cir > 30 else "Ổn định")
                })
                time_trend["labels"].append(str(r[date_col]))
                time_trend["revenue"].append(d_rev)
                time_trend["ad_spend"].append(d_spend)
                time_trend["net_profit"].append(d_net)
        except Exception:
            pass

    if not time_trend["labels"] and primary_scorecard:
        for item in primary_scorecard[:10]:
            time_trend["labels"].append(item["name"])
            time_trend["revenue"].append(item["revenue"])
            time_trend["ad_spend"].append(item["ad_spend"])
            time_trend["net_profit"].append(item["net_profit"])

    # Biểu đồ Grouped Bar & Donut
    bar_source = scorecards_by_dim.get(str(chan_col), primary_scorecard)[:8]
    grouped_bar = {
        "dim_name": str(chan_col or primary_dim or "Nhóm"),
        "labels": [x["name"] for x in bar_source],
        "revenue": [x["revenue"] for x in bar_source],
        "ad_spend": [x["ad_spend"] for x in bar_source],
        "net_profit": [x["net_profit"] for x in bar_source]
    }

    donut_source = scorecards_by_dim.get(str(cat_col), primary_scorecard)[:7]
    cat_donut = {
        "dim_name": str(cat_col or primary_dim or "Danh mục"),
        "labels": [x["name"] for x in donut_source],
        "revenue": [x["revenue"] for x in donut_source],
        "net_profit": [max(x["net_profit"], 0) for x in donut_source]
    }

    # Chẩn đoán Nguyên nhân gốc rễ & Actionable Playbook (Đối chiếu trực tiếp với Bối cảnh Bước 1)
    ctx_goal = (business_context or {}).get("primary_goal", "Tối ưu hiệu suất kinh doanh")
    ctx_overview = (business_context or {}).get("company_overview", "Doanh nghiệp")

    stars = [s for s in primary_scorecard if s["quadrant"] in [QUAD_STAR, "Star"]]
    cows = [s for s in primary_scorecard if s["quadrant"] in [QUAD_COW, "Cash Cow"]]
    traps = [s for s in primary_scorecard if s["quadrant"] in [QUAD_TRAP, "Volume Trap"]]
    burners = [s for s in primary_scorecard if s["quadrant"] in [QUAD_BURNER, "Cash Burner"]]

    playbook_highlights = []
    playbook_bottlenecks = []
    playbook_actions = []

    if stars:
        top_s = stars[0]
        playbook_highlights.append(
            f"**🌟 Ngôi sao tăng trưởng ({top_s['name']}):** Đóng góp **{top_s['revenue']:,.0f} đ** doanh thu (Biên ròng: **{top_s['net_margin_percent']}%**, AOV: **{top_s['aov']:,.0f} đ**). Đây là động lực chính để giải quyết mục tiêu: *{ctx_goal}*."
        )
    if cows:
        top_c = sorted(cows, key=lambda x: (x["roas"], x["net_profit"]), reverse=True)[0]
        playbook_highlights.append(
            f"**🐄 Bò sữa sinh lời ({top_c['name']}):** Vận hành rất an toàn với tỷ lệ hoàn chỉ **{top_c['return_rate']}%**, lợi nhuận ròng đạt **{top_c['net_profit']:,.0f} đ**" + (f" và ROAS đạt **{top_c['roas']}x**." if top_c['roas'] > 0 else ".")
        )
    if not playbook_highlights and primary_scorecard:
        top_any = primary_scorecard[0]
        playbook_highlights.append(
            f"**Nhóm dẫn đầu quy mô ({top_any['name']}):** Đạt doanh thu **{top_any['revenue']:,.0f} đ** với **{top_any['orders']:,.0f}** đơn hàng."
        )

    if traps:
        worst_t = sorted(traps, key=lambda x: (x["return_rate"], x["cir_percent"]), reverse=True)[0]
        playbook_bottlenecks.append(
            f"**⚠️ Bẫy doanh thu ảo ({worst_t['name']}):** Doanh thu gộp đạt **{worst_t['revenue']:,.0f} đ** nhưng tỷ lệ hoàn hàng là **{worst_t['return_rate']}%** (CIR: **{worst_t['cir_percent']}%**), làm thất thoát **{worst_t['revenue'] - worst_t['net_realized_revenue']:,.0f} đ** doanh thu thực thu."
        )
    if burners:
        worst_b = sorted(burners, key=lambda x: x["net_profit"])[0]
        playbook_bottlenecks.append(
            f"**🔥 Điểm nghẽn Đốt tiền ({worst_b['name']}):** Lợi nhuận ròng đang âm (**{worst_b['net_profit']:,.0f} đ**), ROAS chỉ đạt **{worst_b['roas']}x** và CAC lên tới **{worst_b['cpa']:,.0f} đ**/đơn."
        )
    if not playbook_bottlenecks:
        playbook_bottlenecks.append(
            f"Hệ thống chưa ghi nhận nhóm hoạt động nào âm lợi nhuận ròng hoặc vượt ngưỡng hoàn đơn 15%. Tổng tỷ lệ hoàn toàn hệ thống đang ở mức an toàn **{system_return_rate}%**."
        )

    # Đề xuất hành động cụ thể bám sát Bước 1
    if burners:
        playbook_actions.append(
            f"**Quyết định Cắt lỗ (Cut & Optimize):** Cắt giảm ngân sách quảng cáo hoặc tạm dừng các hoạt động thuộc nhóm *🔥 Đốt tiền / Cần cắt lỗ* (đứng đầu là **{burners[0]['name']}** đang lỗ **{burners[0]['net_profit']:,.0f} đ**), tái cấu trúc gói sản phẩm để đẩy AOV vượt mức chi phí CAC (**{burners[0]['cpa']:,.0f} đ**)."
        )
    if traps:
        playbook_actions.append(
            f"**Khắc phục Điểm nghẽn Vận hành:** Rà soát ngay quy trình đóng gói, chất lượng sản phẩm và chính sách giao hàng tại nhóm *⚠️ Bẫy doanh thu ảo* (đứng đầu là **{traps[0]['name']}**) để kéo tỷ lệ hoàn từ **{traps[0]['return_rate']}%** xuống dưới ngưỡng an toàn 8%."
        )
    if stars or cows:
        target_name = stars[0]["name"] if stars else cows[0]["name"]
        playbook_actions.append(
            f"**Mở rộng Quy mô (Scale-up):** Dồn nguồn lực và ngân sách từ các nhóm kém hiệu quả sang **{target_name}** nhằm tối đa hóa lợi nhuận ròng theo định hướng của *{ctx_overview}*."
        )

    # Danh sách giá trị duy nhất cho bộ lọc trên Dashboard
    filter_options = {}
    for d_col in available_dims[:4]:
        filter_options[str(d_col)] = [str(x) for x in df[d_col].dropna().unique()[:30]]

    return {
        "has_dashboard": True,
        "primary_dimension": str(primary_dim) if primary_dim else None,
        "available_dimensions": [str(d) for d in available_dims],
        "filter_options": filter_options,
        "pivot_meta": {
            "p1_row": str(camp_col or primary_dim or ""),
            "p1_col": str(chan_col or primary_dim or ""),
            "p2_row": str(cat_col or primary_dim or ""),
            "p2_col": str(reg_col or primary_dim or "")
        },
        "kpis": {
            "total_revenue": round(total_revenue, 2),
            "net_realized_revenue": round(net_realized_revenue, 2),
            "total_orders": round(total_orders, 2),
            "net_orders": round(net_orders, 2),
            "total_returned": round(total_returned, 2),
            "system_return_rate": system_return_rate,
            "total_traffic": round(total_traffic, 2),
            "system_cr": system_cr,
            "aov": aov,
            "total_cost": round(total_ad_spend, 2),
            "total_cogs": round(total_cogs, 2),
            "cpa": cpa,
            "cir_percent": cir_percent,
            "gross_profit": round(gross_profit, 2),
            "net_profit": round(net_profit, 2),
            "net_margin_percent": net_margin_percent,
            "roas": roas,
            "system_alert": system_alert
        },
        "quadrant_counts": primary_quadrants,
        "scorecard": primary_scorecard,
        "matrix_scatter": primary_scatter,
        "scorecards_by_dim": scorecards_by_dim,
        "scatters_by_dim": scatters_by_dim,
        "quads_by_dim": quads_by_dim,
        "pivot_camp_chan": pivot_camp_chan,
        "pivot_cat_reg": pivot_cat_reg,
        "daily_activity_log": daily_activity_log,
        "playbook": {
            "highlights": playbook_highlights,
            "bottlenecks": playbook_bottlenecks,
            "actions": playbook_actions
        },
        "time_trend": time_trend,
        "cat_donut": cat_donut,
        "grouped_bar": grouped_bar
    }

# =============================================================================
# 8. GEMINI AI AGENT ĐA VAI TRÒ
# =============================================================================
def call_gemini_api(prompt, pipeline_state):
    step1 = pipeline_state.get("step1", {})
    prof = step1.get("business_profile") or {}
    step2 = pipeline_state.get("step2", {})
    step3 = pipeline_state.get("step3", {})
    step5 = pipeline_state.get("step5", {})
    kpis = step5.get("kpis") or {}
    playbook = step5.get("playbook") or {}
    quadrants = step5.get("quadrant_counts") or {}
    filename = pipeline_state.get("filename") or "Chưa tải file dữ liệu"

    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
            system_prompt = (
                "Bạn là Hệ thống AI Agent Đa Vai Trò chuyên sâu về Business Intelligence (BI), Kỹ thuật Dữ liệu (Data Engineering) và Quản trị Kinh doanh số.\n"
                f"- Trạng thái mở khóa hiện tại: Bước {pipeline_state.get('current_unlocked_step', 1)}/5\n"
                f"- Bối cảnh Bước 1: Tổng quan='{prof.get('company_overview', 'Chưa nhập')}', Mục tiêu='{prof.get('primary_goal', 'Chưa nhập')}', Câu hỏi='{prof.get('key_questions', [])}'\n"
                f"- File dữ liệu Bước 2: '{filename}' ({step2.get('total_rows', 0)} dòng, {step2.get('total_cols', 0)} cột, Health={step2.get('health_summary', {})})\n"
                f"- Kết quả Làm sạch Bước 3: {step3.get('summary', {})}\n"
                f"- KPI Bước 5: GMV={kpis.get('total_revenue', 0):,.0f}, Thực thu={kpis.get('net_realized_revenue', 0):,.0f}, Net Profit={kpis.get('net_profit', 0):,.0f} (Biên ròng {kpis.get('net_margin_percent', 0)}%), Return Rate={kpis.get('system_return_rate', 0)}%, ROAS={kpis.get('roas', 0)}x, AOV={kpis.get('aov', 0):,.0f}\n"
                f"- Ma trận 4 góc: {quadrants}\n"
                f"- Playbook: Điểm sáng={playbook.get('highlights')}, Điểm nghẽn={playbook.get('bottlenecks')}, Hành động={playbook.get('actions')}\n\n"
                "Hãy trả lời ngắn gọn, sắc bén, bám sát 100% số liệu thật của người dùng (không bịa số liệu).\n"
                f"Câu hỏi của người dùng: {prompt}"
            )
            payload = {
                "contents": [{"parts": [{"text": system_prompt}]}],
                "generationConfig": {"temperature": 0.25, "maxOutputTokens": 550}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12) as res:
                res_data = json.loads(res.read().decode("utf-8"))
                text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return f"✨ **[AI Agent BI & Quản Trị Kinh Doanh Số]:**\n\n{text}"
        except Exception:
            pass

    if not step1.get("has_context"):
        return "⚠️ Hiện tại hệ thống đang ở **Bước 1 (Clean Slate)**. Bạn vui lòng nhập mô tả bối cảnh doanh nghiệp hoặc tải tài liệu bối cảnh lên trước khi phân tích."
    if not step2.get("has_data"):
        return f"✅ Bối cảnh doanh nghiệp (**{prof.get('primary_goal', '')}**) đã được ghi nhận. Hãy xác nhận Bước 1 và tải file dữ liệu thật lên ở **Bước 2**!"
    if not kpis:
        return f"📊 File **{filename}** ({step2.get('total_rows', 0)} dòng) đang ở Bước {pipeline_state.get('current_unlocked_step')}. Hãy xác nhận tuần tự qua các Trạm kiểm soát để mở khóa toàn bộ chỉ số!"

    return (
        f"🤖 **[Phân tích trực tiếp từ file '{filename}']:**\n"
        f"- **Tổng quy mô doanh thu (GMV):** {kpis.get('total_revenue', 0):,.0f} | **Thực thu sau hoàn:** {kpis.get('net_realized_revenue', 0):,.0f}\n"
        f"- **Lợi nhuận ròng:** {kpis.get('net_profit', 0):,.0f} (Biên ròng: **{kpis.get('net_margin_percent', 0)}%**)\n"
        f"- **Chất lượng vận hành:** Tỷ lệ hoàn **{kpis.get('system_return_rate', 0)}%**, AOV **{kpis.get('aov', 0):,.0f}**, ROAS **{kpis.get('roas', 0)}x**\n"
        f"- **Ma trận 4 nhóm:** Star: {quadrants.get('Star',0)}, Cash Cow: {quadrants.get('Cash Cow',0)}, Volume Trap: {quadrants.get('Volume Trap',0)}, Cash Burner: {quadrants.get('Cash Burner',0)}."
    )

# =============================================================================
# 9. HTTP SERVER HANDLER
# =============================================================================
class BIServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()
            with open(os.path.join(DIRECTORY, "index.html"), "rb") as f:
                self.wfile.write(f.read())
            return

        elif parsed.path in ["/api/status", "/api/pipeline"]:
            self.send_json(200, CURRENT_PIPELINE["state"])
            return

        elif parsed.path == "/api/export-clean":
            fmt = query.get("format", ["csv"])[0].lower()
            df_exp = CURRENT_PIPELINE.get("processed_df")
            if df_exp is None:
                df_exp = CURRENT_PIPELINE.get("cleaned_df")

            if df_exp is None or len(df_exp) == 0:
                self.send_json(400, {"status": "error", "message": "Chưa có dữ liệu sạch để xuất. Vui lòng thực hiện quy trình trước."})
                return

            exp_cols = [c for c in df_exp.columns if not str(c).startswith('_')]
            clean_export_df = df_exp[exp_cols]

            if fmt == "xlsx":
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    clean_export_df.to_excel(writer, index=False, sheet_name="Clean_BI_Data")
                xlsx_bytes = buf.getvalue()
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                self.send_header('Content-Disposition', 'attachment; filename="Cleaned_BI_Data.xlsx"')
                self.end_headers()
                self.wfile.write(xlsx_bytes)
                return
            else:
                csv_data = clean_export_df.to_csv(index=False, encoding="utf-8-sig")
                self.send_response(200)
                self.send_header('Content-Type', 'text/csv; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="Cleaned_BI_Data.csv"')
                self.end_headers()
                self.wfile.write(csv_data.encode('utf-8-sig'))
                return

        elif parsed.path == "/api/export-docx":
            state = CURRENT_PIPELINE.get("state", {})
            raw_df = CURRENT_PIPELINE.get("raw_df")
            cleaned_df = CURRENT_PIPELINE.get("cleaned_df")
            processed_df = CURRENT_PIPELINE.get("processed_df")

            try:
                from report_generator import generate_docx_report
                docx_bytes = generate_docx_report(state, raw_df, cleaned_df, processed_df)
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                self.send_header('Content-Disposition', 'attachment; filename="Bao_Cao_Quan_Tri_BI_Doanh_Nghiep.docx"')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(docx_bytes)
                return
            except Exception as e:
                self.send_json(500, {"status": "error", "message": f"Lỗi tạo báo cáo Word: {str(e)}"})
                return

        return super().do_GET()

    def do_POST(self):
        global CURRENT_PIPELINE
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        raw_bytes = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            body = raw_bytes.decode('utf-8')
        except Exception:
            body = raw_bytes.decode('utf-8', errors='replace')

        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {"prompt": body}

        state = CURRENT_PIPELINE["state"]

        # ---------------------------------------------------------------------
        # HARD RESET: TẨY TRẮNG DỮ LIỆU & LÀM MỚI PHIÊN 100%
        # ---------------------------------------------------------------------
        if parsed.path in ["/api/hard-reset", "/api/reset"]:
            fresh_state = purge_all_state()
            self.send_json(200, {
                "status": "success",
                "message": "Đã tẩy trắng toàn bộ dữ liệu cũ và khởi tạo phiên làm việc mới tại Bước 1!",
                "data": fresh_state
            })
            return

        # ---------------------------------------------------------------------
        # BƯỚC 1: PHÂN TÍCH & XÁC THỰC BỐI CẢNH DOANH NGHIỆP
        # ---------------------------------------------------------------------
        elif parsed.path in ["/api/step1-analyze", "/api/step1-save-context"]:
            raw_text = data.get("raw_text", "")
            doc_filename = data.get("doc_filename")
            doc_content = data.get("doc_content", "")
            manual_override = data.get("business_profile")

            profile = analyze_business_context(raw_text, doc_filename=doc_filename, doc_content=doc_content, manual_override=manual_override)
            if not profile:
                self.send_json(400, {"status": "error", "message": "Vui lòng nhập mô tả bối cảnh doanh nghiệp hoặc tải lên tài liệu nội bộ."})
                return

            state["is_clean_slate"] = False
            state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            state["step1"] = {
                "has_context": True,
                "is_confirmed": False,
                "raw_input": raw_text,
                "uploaded_doc_name": doc_filename,
                "business_profile": profile,
                "checkpoint_msg": (
                    "⚠️ [TRẠM KIỂM SOÁT BƯỚC 1]: Tôi đã tiếp nhận và tổng hợp hồ sơ bối cảnh doanh nghiệp của bạn như trên. "
                    "👉 Bạn hãy kiểm tra xem thông tin đã chính xác và đủ ý chưa? "
                    "Nếu ĐÃ ĐÚNG, vui lòng bấm 'Xác nhận' hoặc gõ 'Xác nhận' để mở khóa Bước 2 (Đánh giá chất lượng dữ liệu thô)."
                )
            }
            # Khi đổi bối cảnh và chưa xác nhận, khóa lại các bước sau nếu chưa xác nhận
            state["current_unlocked_step"] = 1
            self.send_json(200, {"status": "success", "message": "Đã phân tích và trích xuất Hồ sơ Bối cảnh Doanh nghiệp.", "data": state})
            return

        elif parsed.path == "/api/step1-confirm":
            if not state["step1"].get("has_context") or not state["step1"].get("business_profile"):
                self.send_json(400, {"status": "error", "message": "Bạn chưa nhập bối cảnh doanh nghiệp ở Bước 1."})
                return

            state["step1"]["is_confirmed"] = True
            state["current_unlocked_step"] = max(state.get("current_unlocked_step", 1), 2)
            state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Nếu đã có dữ liệu ở các bước sau, cập nhật lại Playbook Bước 5 theo bối cảnh mới
            if CURRENT_PIPELINE.get("processed_df") is not None:
                state["step5"] = generate_step5_dashboard(
                    CURRENT_PIPELINE["processed_df"],
                    state["step4"].get("mapping_used", {}),
                    business_context=state["step1"]["business_profile"]
                )

            self.send_json(200, {"status": "success", "message": "Đã xác nhận Bước 1! Mở khóa Bước 2: Nhập & Kiểm định dữ liệu thô.", "data": state})
            return

        # ---------------------------------------------------------------------
        # BƯỚC 2: TẢI FILE DỮ LIỆU THÔ & KIỂM ĐỊNH CHẤT LƯỢNG
        # ---------------------------------------------------------------------
        elif parsed.path in ["/api/step2-upload", "/api/upload"]:
            if not state["step1"].get("is_confirmed"):
                self.send_json(400, {"status": "error", "message": "Vui lòng hoàn thành và xác nhận Trạm kiểm soát Bước 1 trước khi tải dữ liệu!"})
                return

            filename = data.get("filename", "uploaded_data.csv")
            rows = data.get("rows", [])
            if not rows or not isinstance(rows, list):
                self.send_json(400, {"status": "error", "message": "File tải lên không có dòng dữ liệu nào."})
                return

            raw_df = pd.DataFrame(rows)
            # Xóa các cột hoàn toàn trống do lỗi dư cột trong Excel/CSV
            raw_df = raw_df.loc[:, ~raw_df.columns.astype(str).str.startswith('Unnamed:')]
            if len(raw_df.columns) == 0 or len(raw_df) == 0:
                self.send_json(400, {"status": "error", "message": "Không tìm thấy cột dữ liệu hợp lệ trong file."})
                return

            CURRENT_PIPELINE["raw_df"] = raw_df
            CURRENT_PIPELINE["cleaned_df"] = None
            CURRENT_PIPELINE["processed_df"] = None

            step2_report = profile_raw_data(raw_df)
            step2_report["is_confirmed"] = False
            step2_report["checkpoint_msg"] = (
                "⚠️ [TRẠM KIỂM SOÁT BƯỚC 2]: Tôi đã hoàn tất kiểm định chất lượng dữ liệu thô và phát hiện các vấn đề nêu trên. "
                "👉 Bạn có đồng ý chuyển sang Bước 3 để tiến hành làm sạch dữ liệu theo các đề xuất xử lý không?"
            )

            state["filename"] = filename
            state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            state["current_unlocked_step"] = 2
            state["step2"] = step2_report
            # Reset bước 3, 4, 5 khi nạp file mới
            state["step3"] = get_clean_slate_state()["step3"]
            state["step4"] = get_clean_slate_state()["step4"]
            state["step5"] = get_clean_slate_state()["step5"]

            self.send_json(200, {"status": "success", "message": f"Đã đọc và kiểm định {len(raw_df)} dòng, {len(raw_df.columns)} cột từ file '{filename}'.", "data": state})
            return

        elif parsed.path == "/api/step2-confirm":
            if CURRENT_PIPELINE.get("raw_df") is None or not state["step2"].get("has_data"):
                self.send_json(400, {"status": "error", "message": "Vui lòng tải lên file dữ liệu thô tại Bước 2 trước khi xác nhận."})
                return

            state["step2"]["is_confirmed"] = True
            state["current_unlocked_step"] = max(state.get("current_unlocked_step", 2), 3)

            # Thực thi làm sạch mặc định chuẩn BI để hiển thị sẵn bảng đối chiếu ở Bước 3
            step3_res = clean_and_preprocess(CURRENT_PIPELINE["raw_df"], options=state["step3"].get("cleaning_options"))
            CURRENT_PIPELINE["cleaned_df"] = step3_res.pop("cleaned_df")
            step3_res["is_confirmed"] = False
            step3_res["checkpoint_msg"] = (
                "⚠️ [TRẠM KIỂM SOÁT BƯỚC 3]: Dữ liệu đã được làm sạch và chuẩn hóa. Bạn hãy kiểm tra Bảng đối chiếu thống kê Trước & Sau khi làm sạch. "
                "👉 Bấm 'Xác nhận' để khóa tập dữ liệu sạch và chuyển sang Bước 4 (Tính toán chỉ số & Đánh giá hoạt động)."
            )
            state["step3"] = step3_res
            state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.send_json(200, {"status": "success", "message": "Đã xác nhận Bước 2! Mở khóa Bước 3: Làm sạch & Tiền xử lý dữ liệu.", "data": state})
            return

        # ---------------------------------------------------------------------
        # BƯỚC 3: LÀM SẠCH & TIỀN XỬ LÝ DỮ LIỆU
        # ---------------------------------------------------------------------
        elif parsed.path in ["/api/step3-clean", "/api/clean"]:
            if CURRENT_PIPELINE.get("raw_df") is None:
                self.send_json(400, {"status": "error", "message": "Chưa có dữ liệu thô để làm sạch."})
                return

            clean_options = data.get("options") or {
                "missing_numeric": "median",
                "missing_cat": "unknown",
                "deduplicate": True,
                "standardize_format": True,
                "handle_outliers": "cap"
            }
            step3_res = clean_and_preprocess(CURRENT_PIPELINE["raw_df"], options=clean_options)
            CURRENT_PIPELINE["cleaned_df"] = step3_res.pop("cleaned_df")
            step3_res["is_confirmed"] = False
            step3_res["checkpoint_msg"] = (
                "⚠️ [TRẠM KIỂM SOÁT BƯỚC 3]: Dữ liệu đã được làm sạch và chuẩn hóa. Bạn hãy kiểm tra Bảng đối chiếu thống kê Trước & Sau khi làm sạch. "
                "👉 Bấm 'Xác nhận' để khóa tập dữ liệu sạch và chuyển sang Bước 4."
            )
            state["step3"] = step3_res
            state["current_unlocked_step"] = 3
            state["step4"]["is_confirmed"] = False
            state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.send_json(200, {"status": "success", "message": "Đã áp dụng cấu hình làm sạch và cập nhật Bảng đối chiếu Trước - Sau.", "data": state})
            return

        elif parsed.path == "/api/step3-confirm":
            if CURRENT_PIPELINE.get("cleaned_df") is None or not state["step3"].get("has_cleaned"):
                self.send_json(400, {"status": "error", "message": "Vui lòng thực hiện làm sạch dữ liệu ở Bước 3 trước khi xác nhận."})
                return

            state["step3"]["is_confirmed"] = True
            state["current_unlocked_step"] = max(state.get("current_unlocked_step", 3), 4)

            # Tính toán khởi tạo Bước 4 trên tập dữ liệu sạch
            step4_res = engineer_features(
                CURRENT_PIPELINE["cleaned_df"],
                custom_mapping=state["step4"].get("mapping_used") or None,
                custom_formulas=state["step4"].get("custom_formulas") or []
            )
            CURRENT_PIPELINE["processed_df"] = step4_res.pop("processed_df")
            step4_res["is_confirmed"] = False
            step4_res["checkpoint_msg"] = (
                "⚠️ [TRẠM KIỂM SOÁT BƯỚC 4]: Hệ thống đã tính toán xong bộ chỉ số Unit Economics và phân nhóm Ma trận 4 góc phần tư. "
                "👉 Bạn có muốn điều chỉnh ghép nối cột hay thêm công thức cột mới nào không? Nếu đã chuẩn, hãy xác nhận để xuất Dashboard ở Bước 5."
            )
            state["step4"] = step4_res
            state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.send_json(200, {"status": "success", "message": "Đã khóa tập dữ liệu sạch! Mở khóa Bước 4: Ánh xạ cột động & Tính toán chỉ số BI.", "data": state})
            return

        # ---------------------------------------------------------------------
        # BƯỚC 4: ÁNH XẠ CỘT ĐỘNG, TẠO CÔNG THỨC MỚI & MA TRẬN 4 GÓC
        # ---------------------------------------------------------------------
        elif parsed.path in ["/api/step4-process", "/api/mapping"]:
            if CURRENT_PIPELINE.get("cleaned_df") is None:
                self.send_json(400, {"status": "error", "message": "Chưa có dữ liệu sạch từ Bước 3."})
                return

            custom_mapping = data.get("mapping", state["step4"].get("mapping_used"))
            custom_formulas = data.get("custom_formulas", state["step4"].get("custom_formulas", []))

            step4_res = engineer_features(
                CURRENT_PIPELINE["cleaned_df"],
                custom_mapping=custom_mapping,
                custom_formulas=custom_formulas
            )
            CURRENT_PIPELINE["processed_df"] = step4_res.pop("processed_df")
            step4_res["is_confirmed"] = False
            step4_res["checkpoint_msg"] = (
                "⚠️ [TRẠM KIỂM SOÁT BƯỚC 4]: Đã cập nhật ánh xạ cột và tính toán lại toàn bộ chỉ số Unit Economics & Ma trận 4 góc. "
                "👉 Bấm 'Xác nhận' để xuất Dashboard & Kế hoạch Hành động ở Bước 5."
            )
            state["step4"] = step4_res
            state["current_unlocked_step"] = 4
            state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.send_json(200, {"status": "success", "message": "Đã cập nhật ghép nối cột động và tính lại các chỉ số BI.", "data": state})
            return

        elif parsed.path == "/api/step4-confirm":
            if CURRENT_PIPELINE.get("processed_df") is None or not state["step4"].get("has_processed"):
                self.send_json(400, {"status": "error", "message": "Vui lòng hoàn tất tính toán chỉ số tại Bước 4 trước khi xác nhận."})
                return

            state["step4"]["is_confirmed"] = True
            state["current_unlocked_step"] = 5

            step5_res = generate_step5_dashboard(
                CURRENT_PIPELINE["processed_df"],
                state["step4"].get("mapping_used", {}),
                business_context=state["step1"].get("business_profile")
            )
            step5_res["is_confirmed"] = True
            state["step5"] = step5_res
            state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.send_json(200, {"status": "success", "message": "Đã xác nhận Bước 4! Mở khóa Bước 5: BI Dashboard & Actionable Playbook.", "data": state})
            return

        # ---------------------------------------------------------------------
        # BƯỚC 5: LỌC ĐỘNG & ĐỔI CHIỀU PHÂN TÍCH CHÉO (DYNAMIC FILTER & PIVOT)
        # ---------------------------------------------------------------------
        elif parsed.path == "/api/step5-filter":
            if CURRENT_PIPELINE.get("processed_df") is None:
                self.send_json(400, {"status": "error", "message": "Chưa có dữ liệu ở Bước 5."})
                return

            filters = data.get("filters", {})
            custom_pivot = data.get("pivot", {})
            step5_res = generate_step5_dashboard(
                CURRENT_PIPELINE["processed_df"],
                state["step4"].get("mapping_used", {}),
                business_context=state["step1"].get("business_profile"),
                filters=filters
            )
            if custom_pivot.get("row_dim") and custom_pivot.get("col_dim"):
                df_filtered = CURRENT_PIPELINE["processed_df"].copy()
                for col, val in (filters or {}).items():
                    if val and val != "ALL" and col in df_filtered.columns:
                        df_filtered = df_filtered[df_filtered[col].astype(str) == str(val)]
                step5_res["pivot_camp_chan"] = compute_cross_pivot(df_filtered, custom_pivot["row_dim"], custom_pivot["col_dim"])
                step5_res["pivot_meta"]["p1_row"] = custom_pivot["row_dim"]
                step5_res["pivot_meta"]["p1_col"] = custom_pivot["col_dim"]

            state["step5"] = step5_res
            self.send_json(200, {"status": "success", "data": state})
            return

        # ---------------------------------------------------------------------
        # AI CHAT & GATEKEEPING COMMANDS ("Xác nhận", "Tiếp tục")
        # ---------------------------------------------------------------------
        elif parsed.path == "/api/chat":
            prompt = str(data.get("prompt", "")).strip()
            reply = call_gemini_api(prompt, state)
            self.send_json(200, {"status": "success", "response": reply, "data": state})
            return

        self.send_json(404, {"status": "error", "message": "Endpoint không tồn tại"})

def run():
    os.chdir(DIRECTORY)
    # Tẩy trắng hoàn toàn dữ liệu cũ ngay khi khởi động server
    purge_all_state()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), BIServerHandler) as httpd:
        httpd.daemon_threads = True
        print(f"🚀 Hệ thống BI 5 Bước (Zero-Data Clean Slate & Schema-Agnostic) đang chạy tại: http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    run()
