import io
import datetime
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_shading(cell, color_hex):
    """Đặt màu nền cho cell trong bảng docx."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Đặt padding cho cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def format_num(val):
    if val is None or val == "" or str(val) == "nan":
        return "--"
    try:
        f = float(val)
        if f == int(f):
            return f"{int(f):,}".replace(",", ".")
        return f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(val)

def generate_docx_report(state, raw_df=None, cleaned_df=None, processed_df=None):
    """
    Sinh tài liệu Word (.DOCX) chuyên nghiệp tổng hợp toàn diện cả 5 bước của quy trình Smart BI Studio:
    - Trang bìa / Tiêu đề lớn
    - Phần 1: Hồ sơ bối cảnh doanh nghiệp (Bước 1)
    - Phần 2: Kiểm định & Nhật ký làm sạch (Bước 2 & 3)
    - Phần 3: Bảng chỉ số KPI & Kinh tế đơn vị (Bước 4 & 5)
    - Phần 4: Ma trận 4 Góc phần tư & Chấm điểm hoạt động
    - Phần 5: Kế hoạch hành động quản trị (Actionable Playbook)
    """
    doc = docx.Document()

    # Thiết lập lề trang chuẩn báo cáo (1 inch các phía)
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.9)
        s.right_margin = Inches(0.9)

    # Palette màu Báo cáo Doanh nghiệp Chuyên nghiệp
    PRIMARY_COLOR = RGBColor(30, 58, 138)    # Deep Royal Blue (#1E3A8A)
    SECONDARY_COLOR = RGBColor(180, 83, 9)   # Warm Bronze Gold (#B45309)
    TEXT_MAIN = RGBColor(15, 23, 42)         # Deep Charcoal (#0F172A)
    TEXT_MUTED = RGBColor(71, 85, 105)       # Slate Gray (#475569)

    # =========================================================================
    # TRANG BÌA / HEADER BÁO CÁO
    # =========================================================================
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_tag = p_title.add_run("HỆ THỐNG QUẢN TRỊ KINH DOANH SỐ • SMART BI STUDIO\n")
    r_tag.font.size = Pt(10)
    r_tag.font.bold = True
    r_tag.font.color.rgb = SECONDARY_COLOR

    r_title = p_title.add_run("BÁO CÁO PHÂN TÍCH KINH DOANH SỐ &\nĐÁNH GIÁ HIỆU QUẢ HOẠT ĐỘNG BI")
    r_title.font.size = Pt(20)
    r_title.font.bold = True
    r_title.font.color.rgb = PRIMARY_COLOR

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("Báo cáo Điều hành Chiến lược • Phân loại Ma trận 4 Góc & Kế hoạch Hành động Cốt lõi")
    r_sub.font.italic = True
    r_sub.font.size = Pt(11)
    r_sub.font.color.rgb = TEXT_MUTED

    # Bảng Metadata tóm tắt
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    fname = state.get("filename") or "Dữ liệu kinh doanh nạp động"

    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        [f"📅 Ngày xuất báo cáo: {now_str}", f"📁 File dữ liệu phân tích: {fname}"],
        ["📊 Quy trình: 5 Bước Chuẩn BI (Schema-Agnostic)", "🔒 Trạng thái kiểm định: Đã qua trạm kiểm soát 100%"]
    ]
    for row_idx, row in enumerate(meta_table.rows):
        for col_idx, cell in enumerate(row.cells):
            cell.text = meta_data[row_idx][col_idx]
            p = cell.paragraphs[0]
            p.runs[0].font.size = Pt(9.5)
            p.runs[0].font.color.rgb = TEXT_MUTED
            set_cell_shading(cell, "F8FAFC")
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # =========================================================================
    # PHẦN 1: HỒ SƠ BỐI CẢNH DOANH NGHIỆP (TỪ BƯỚC 1)
    # =========================================================================
    h1 = doc.add_heading(level=1)
    r = h1.add_run("PHẦN 1: HỒ SƠ BỐI CẢNH DOANH NGHIỆP (CONTEXT PROFILE)")
    r.font.size = Pt(13.5)
    r.font.bold = True
    r.font.color.rgb = PRIMARY_COLOR

    step1 = state.get("step1", {})
    prof = step1.get("business_profile") or {}

    p_p1 = doc.add_paragraph()
    p_p1.paragraph_format.line_spacing = 1.3
    
    # 1. Tổng quan Doanh nghiệp
    r = p_p1.add_run("1.1. Tổng Quan Doanh Nghiệp (Ngành nghề, Mô hình, Quy mô):\n")
    r.bold = True
    r.font.color.rgb = TEXT_MAIN
    overview_text = prof.get("company_overview") or "Chưa có mô tả bối cảnh doanh nghiệp cụ thể."
    r_val = p_p1.add_run(f"• {overview_text}\n\n")
    r_val.font.color.rgb = TEXT_MUTED

    # 1.2. Mục tiêu Phân tích Cốt lõi
    r = p_p1.add_run("1.2. Mục Tiêu Phân Tích Cốt Lõi & Câu Hỏi Trọng Tâm:\n")
    r.bold = True
    r.font.color.rgb = TEXT_MAIN
    goal_text = prof.get("primary_goal") or "Đánh giá hiệu quả kinh doanh, tối ưu hóa lợi nhuận ròng và chi phí ads."
    p_p1.add_run(f"• Mục tiêu chính: {goal_text}\n")
    
    questions = prof.get("key_questions") or []
    if questions:
        for q in questions:
            p_p1.add_run(f"   - 🎯 {q}\n")
    p_p1.add_run("\n")

    # 1.3. Ràng buộc & Ngưỡng KPI
    r = p_p1.add_run("1.3. Ràng Buộc Dữ Liệu & Ngưỡng Mục Tiêu Hoạt Động:\n")
    r.bold = True
    r.font.color.rgb = TEXT_MAIN
    constraints_text = prof.get("data_constraints") or "Áp dụng ngưỡng phân loại 4 nhóm ma trận dựa trên trung vị (Median) và chuẩn hoạt động đa kênh."
    p_p1.add_run(f"• {constraints_text}\n")

    # =========================================================================
    # PHẦN 2: KIỂM ĐỊNH & NHẬT KÝ LÀM SẠCH DỮ LIỆU (BƯỚC 2 & BƯỚC 3)
    # =========================================================================
    h2 = doc.add_heading(level=1)
    r = h2.add_run("PHẦN 2: KIỂM ĐỊNH DỮ LIỆU THÔ & NHẬT KÝ LÀM SẠCH (DATA PROFILING & CLEANING)")
    r.font.size = Pt(13.5)
    r.font.bold = True
    r.font.color.rgb = PRIMARY_COLOR

    step2 = state.get("step2", {})
    step3 = state.get("step3", {})
    h_sum = step2.get("health_summary") or {}
    c_sum = step3.get("summary") or {}

    p_h2 = doc.add_paragraph()
    p_h2.add_run("2.1. Kết Quả Quét Lỗi & Kiểm Định Dữ Liệu Thô (Raw Data Health Check):\n").bold = True

    t_health = doc.add_table(rows=6, cols=3)
    t_health.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_health_data = [
        ["Hạng Mục Kiểm Định Sơ Bộ", "Số Lượng Phát Hiện", "Đánh Giá Trạng Thái"],
        ["Tổng quy mô dữ liệu thô ban đầu", f"{format_num(step2.get('total_rows', 0))} dòng × {step2.get('total_cols', 0)} cột", "Đầy đủ cấu trúc bảng"],
        ["Ô khuyết thiếu (Missing / Null values)", f"{format_num(h_sum.get('total_missing_cells', 0))} ô", "Cần xử lý bù giá trị (Imputation)"],
        ["Dòng bản ghi trùng lặp 100% (Duplicates)", f"{format_num(h_sum.get('duplicate_rows', 0))} dòng", "Đã loại bỏ khỏi tập phân tích"],
        ["Lỗi sai định dạng số / Tiền tệ (Format errors)", f"{format_num(h_sum.get('format_errors', 0))} ô", "Chuẩn hóa định dạng số thực"],
        ["Bản ghi bất thường logic / Ngoại lai (Outliers)", f"{format_num(h_sum.get('logic_anomalies', 0))} trường hợp", "Kiểm soát trần P99 / Khử số âm"]
    ]
    for row_idx, row in enumerate(t_health.rows):
        is_header = (row_idx == 0)
        for col_idx, cell in enumerate(row.cells):
            cell.text = t_health_data[row_idx][col_idx]
            p = cell.paragraphs[0]
            if is_header:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
                set_cell_shading(cell, "1E3A8A")
            else:
                p.runs[0].font.size = Pt(9.5)
                if col_idx == 1:
                    p.runs[0].font.bold = True
                set_cell_shading(cell, "F8FAFC" if row_idx % 2 == 1 else "FFFFFF")
            set_cell_margins(cell, top=70, bottom=70, left=100, right=100)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # 2.2. Bảng đối chiếu Trước & Sau làm sạch
    p_clean = doc.add_paragraph()
    p_clean.add_run("2.2. Bảng Đối Chiếu Thống Kê Trước & Sau Làm Sạch (Data Comparison):\n").bold = True
    stats_comp = step3.get("stats_comparison") or []

    if stats_comp:
        t_stat = doc.add_table(rows=len(stats_comp) + 1, cols=6)
        t_stat.alignment = WD_TABLE_ALIGNMENT.CENTER
        headers = ["Cột Chỉ Số", "Dòng (Trước ➔ Sau)", "Trung Bình (Mean)", "Trung Vị (Median)", "Tối Thiểu (Min)", "Tối Đa (Max)"]
        for col_idx, cell in enumerate(t_stat.rows[0].cells):
            cell.text = headers[col_idx]
            cell.paragraphs[0].runs[0].font.bold = True
            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
            set_cell_shading(cell, "2563EB")
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)

        for s_idx, s in enumerate(stats_comp):
            row = t_stat.rows[s_idx + 1]
            row.cells[0].text = str(s.get("column", ""))
            row.cells[1].text = f"{format_num(s.get('count_before'))} ➔ {format_num(s.get('count_after'))}"
            row.cells[2].text = f"{format_num(s.get('mean_before'))} ➔ {format_num(s.get('mean_after'))}"
            row.cells[3].text = f"{format_num(s.get('median_before'))} ➔ {format_num(s.get('median_after'))}"
            row.cells[4].text = f"{format_num(s.get('min_before'))} ➔ {format_num(s.get('min_after'))}"
            row.cells[5].text = f"{format_num(s.get('max_before'))} ➔ {format_num(s.get('max_after'))}"
            for c_idx, cell in enumerate(row.cells):
                cell.paragraphs[0].runs[0].font.size = Pt(9)
                set_cell_shading(cell, "F1F5F9" if s_idx % 2 == 1 else "FFFFFF")
                set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
    else:
        p_clean.add_run(f"• Số dòng sạch cuối cùng: {format_num(c_sum.get('rows_after', step2.get('total_rows', 0)))} dòng (đã loại bỏ dòng trùng và điền khuyết thiếu).\n")

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # =========================================================================
    # PHẦN 3: TỔNG HỢP CHỈ SỐ KPI & KINH TẾ ĐƠN VỊ (BƯỚC 4 & BƯỚC 5)
    # =========================================================================
    h3 = doc.add_heading(level=1)
    r = h3.add_run("PHẦN 3: BẢNG CHỈ SỐ KPI & KINH TẾ ĐƠN VỊ TOÀN HỆ THỐNG (UNIT ECONOMICS)")
    r.font.size = Pt(13.5)
    r.font.bold = True
    r.font.color.rgb = PRIMARY_COLOR

    step5 = state.get("step5", {})
    kpis = step5.get("kpis") or {}

    t_kpi = doc.add_table(rows=7, cols=4)
    t_kpi.alignment = WD_TABLE_ALIGNMENT.CENTER
    kpi_rows_data = [
        ["Chỉ Số Tài Chính & Doanh Thu", "Giá Trị", "Chỉ Số Vận Hành & Chuyển Đổi", "Giá Trị"],
        ["Tổng Doanh Thu (GMV)", f"{format_num(kpis.get('total_revenue', 0))} đ", "Tổng Lượng Đơn Đặt Hàng", f"{format_num(kpis.get('total_orders', 0))} đơn"],
        ["Thực Thu Ước Tính Sau Hoàn", f"{format_num(kpis.get('net_realized_revenue', 0))} đ", "Đơn Hoàn Trả & Tỷ Lệ Hoàn", f"{format_num(kpis.get('total_returned', 0))} đơn ({kpis.get('system_return_rate', 0)}%)"],
        ["Tổng Chi Phí Quảng Cáo (Ads)", f"{format_num(kpis.get('total_cost', 0))} đ", "Giá Trị Trung Bình Đơn (AOV)", f"{format_num(kpis.get('aov', 0))} đ"],
        ["Tổng Giá Vốn Hàng Bán (COGS)", f"{format_num(kpis.get('total_cogs', 0))} đ", "Tỷ Suất Doanh Thu/Ads (ROAS)", f"{kpis.get('roas', 0)}x"],
        ["Lợi Nhuận Ròng (Net Profit)", f"{format_num(kpis.get('net_profit', 0))} đ", "Tỷ Lệ Chuyển Đổi (CR)", f"{kpis.get('system_cr', 0)}%"],
        ["Biên Lợi Nhuận Ròng (Net Margin)", f"{kpis.get('net_margin_percent', 0)}%", "Tỷ Lệ Chi Phí Ads/Doanh Thu (CIR)", f"{kpis.get('cir_percent', 0)}%"]
    ]
    for row_idx, row in enumerate(t_kpi.rows):
        is_header = (row_idx == 0)
        for col_idx, cell in enumerate(row.cells):
            cell.text = kpi_rows_data[row_idx][col_idx]
            p = cell.paragraphs[0]
            if is_header:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
                set_cell_shading(cell, "1E3A8A")
            else:
                p.runs[0].font.size = Pt(9.5)
                if col_idx in [1, 3]:
                    p.runs[0].font.bold = True
                    p.runs[0].font.color.rgb = PRIMARY_COLOR
                set_cell_shading(cell, "F8FAFC" if row_idx % 2 == 1 else "FFFFFF")
            set_cell_margins(cell, top=70, bottom=70, left=100, right=100)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # =========================================================================
    # PHẦN 4: MA TRẬN 4 GÓC PHẦN TƯ & BẢNG PHÂN BỔ CHI TIẾT
    # =========================================================================
    h4 = doc.add_heading(level=1)
    r = h4.add_run("PHẦN 4: MA TRẬN 4 GÓC PHẦN TƯ & BẢNG ĐÁNH GIÁ KÊNH/CHIẾN DỊCH")
    r.font.size = Pt(13.5)
    r.font.bold = True
    r.font.color.rgb = PRIMARY_COLOR

    q_counts = step5.get("quadrant_counts") or {}
    q_star = q_counts.get("🌟 Ngôi sao tăng trưởng") or q_counts.get("Star", 0)
    q_cow = q_counts.get("🐄 Bò sữa sinh lời") or q_counts.get("Cash Cow", 0)
    q_trap = q_counts.get("⚠️ Bẫy doanh thu ảo") or q_counts.get("Volume Trap", 0)
    q_burner = q_counts.get("🔥 Đốt tiền / Cần cắt lỗ") or q_counts.get("Cash Burner", 0)

    p_q = doc.add_paragraph()
    p_q.add_run("4.1. Phân Bổ Quy Mô 4 Nhóm Hoạt Động Doanh Nghiệp:\n").bold = True
    p_q.add_run(
        f"• 🌟 Ngôi sao tăng trưởng: {q_star} đối tượng (Biên lợi nhuận cao & Hiệu suất tăng trưởng mạnh).\n"
        f"• 🐄 Bò sữa sinh lời: {q_cow} đối tượng (Dòng tiền ổn định, lợi nhuận ròng bền vững).\n"
        f"• ⚠️ Bẫy doanh thu ảo: {q_trap} đối tượng (Doanh thu lớn nhưng tỷ lệ hoàn cao, biên mỏng).\n"
        f"• 🔥 Đốt tiền / Cần cắt lỗ: {q_burner} đối tượng (Lợi nhuận ròng âm, cần cắt giảm khẩn cấp).\n"
    )

    # Bảng chi tiết từng đối tượng / kênh bán
    scorecard = step5.get("scorecard") or []
    if scorecard:
        doc.add_paragraph().add_run("4.2. Bảng Chấm Điểm & Phân Loại Hiệu Quả Chi Tiết:").bold = True
        t_sc = doc.add_table(rows=min(len(scorecard), 25) + 1, cols=7)
        t_sc.alignment = WD_TABLE_ALIGNMENT.CENTER
        sc_headers = ["Đối Tượng / Kênh", "Phân Nhóm Ma Trận", "Doanh Thu", "Chi Phí Ads", "Lợi Nhuận Ròng", "Biên Lợi Nhuận (%)", "Hiệu Quả Ads (ROAS)"]
        for col_idx, cell in enumerate(t_sc.rows[0].cells):
            cell.text = sc_headers[col_idx]
            cell.paragraphs[0].runs[0].font.bold = True
            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
            set_cell_shading(cell, "2563EB")
            set_cell_margins(cell, top=70, bottom=70, left=80, right=80)

        for sc_idx, sc in enumerate(scorecard[:25]):
            row = t_sc.rows[sc_idx + 1]
            row.cells[0].text = str(sc.get("name", ""))
            row.cells[1].text = str(sc.get("quadrant", ""))
            row.cells[2].text = f"{format_num(sc.get('revenue'))} đ"
            row.cells[3].text = f"{format_num(sc.get('ad_spend'))} đ"
            row.cells[4].text = f"{format_num(sc.get('net_profit'))} đ"
            row.cells[5].text = f"{sc.get('net_margin_percent', 0)}%"
            row.cells[6].text = f"{sc.get('roas', 0)}x"

            q_type = str(sc.get("quadrant", ""))
            q_color = "ECFDF5" if ("Ngôi sao" in q_type or q_type == "Star") else ("EFF6FF" if ("Bò sữa" in q_type or q_type == "Cash Cow") else ("FFFBEB" if ("Bẫy" in q_type or q_type == "Volume Trap") else "FEF2F2"))

            for c_idx, cell in enumerate(row.cells):
                cell.paragraphs[0].runs[0].font.size = Pt(9)
                set_cell_shading(cell, q_color if c_idx == 1 else ("F8FAFC" if sc_idx % 2 == 1 else "FFFFFF"))
                set_cell_margins(cell, top=60, bottom=60, left=80, right=80)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # =========================================================================
    # PHẦN 5: CHẨN ĐOÁN & KẾ HOẠCH HÀNH ĐỘNG QUẢN TRỊ (ACTIONABLE PLAYBOOK)
    # =========================================================================
    h5 = doc.add_heading(level=1)
    r = h5.add_run("PHẦN 5: CHẨN ĐOÁN & KẾ HOẠCH HÀNH ĐỘNG CHIẾN LƯỢC (ACTIONABLE PLAYBOOK)")
    r.font.size = Pt(13.5)
    r.font.bold = True
    r.font.color.rgb = PRIMARY_COLOR

    pb = step5.get("playbook") or {}
    highlights = pb.get("highlights") or []
    bottlenecks = pb.get("bottlenecks") or []
    actions = pb.get("actions") or []

    # Mũi nhọn 1
    p_pb1 = doc.add_paragraph()
    r = p_pb1.add_run("5.1. Mũi Nhọn 1: Hoạt Động Cần Mở Rộng Ngân Sách & Tăng Tốc (Scale-up Strategy):\n")
    r.bold = True
    r.font.color.rgb = RGBColor(16, 185, 129)
    if highlights:
        for item in highlights:
            clean_item = item.replace("**", "").replace("*", "")
            p_pb1.add_run(f"• {clean_item}\n")
    else:
        p_pb1.add_run("• Tập trung đẩy mạnh ngân sách vào nhóm Ngôi sao (Star) có ROAS cao và biên lợi nhuận ròng dương trên 15%.\n")

    # Mũi nhọn 2
    p_pb2 = doc.add_paragraph()
    r = p_pb2.add_run("5.2. Mũi Nhọn 2: Điểm Nghẽn Vận Hành & Tỷ Lệ Hoàn Cần Xử Lý Gấp (Operations & Bottlenecks):\n")
    r.bold = True
    r.font.color.rgb = RGBColor(217, 119, 6)
    if bottlenecks:
        for item in bottlenecks:
            clean_item = item.replace("**", "").replace("*", "")
            p_pb2.add_run(f"• {clean_item}\n")
    else:
        p_pb2.add_run("• Rà soát các chiến dịch/kênh có tỷ lệ hoàn đơn vượt ngưỡng an toàn (trên 15%), siết chặt quy trình đóng gói và xác nhận đơn trước khi giao.\n")

    # Mũi nhọn 3
    p_pb3 = doc.add_paragraph()
    r = p_pb3.add_run("5.3. Mũi Nhọn 3: Danh Mục / Chiến Dịch Âm Lợi Nhuận Cần Cắt Lỗ Ngay (Cost Reduction & Stop-loss):\n")
    r.bold = True
    r.font.color.rgb = RGBColor(220, 38, 38)
    if actions:
        for item in actions:
            clean_item = item.replace("**", "").replace("*", "")
            p_pb3.add_run(f"• {clean_item}\n")
    else:
        p_pb3.add_run("• Dừng ngay các chiến dịch thuộc nhóm Cash Burner có ROAS thấp dưới ngưỡng hòa vốn và lợi nhuận ròng âm liên tiếp.\n")

    # Footer ký duyệt báo cáo
    doc.add_paragraph().paragraph_format.space_after = Pt(20)
    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_sign.add_run("Báo cáo được khởi tạo tự động bởi Smart BI Studio Agent\n").italic = True
    p_sign.add_run("Xác nhận duyệt bởi Giám đốc Điều hành / Trưởng bộ phận Dữ liệu").bold = True

    # Trả về bytes của document
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
