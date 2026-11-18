"""
BI PIPELINE WORKFLOW RUNNER (ORCHESTRATOR)
Công cụ điều phối và thực thi từng bước (Step-by-Step) quy trình Business Intelligence.
"""

import os
import sys
import time
import argparse
from datetime import datetime

# Import các bước từ module pipeline
from templates.bi_pipeline_template import (
    step1_data_collection,
    step2_data_cleaning,
    step3_data_warehousing,
    step4_analysis_and_modeling,
    step5_visualization,
    step6_actionable_insights
)

STEPS = [
    {"num": 1, "name": "Thu thập dữ liệu", "desc": "Trích xuất và tổng hợp dữ liệu thô từ nhiều nguồn"},
    {"num": 2, "name": "Làm sạch & Xử lý", "desc": "Khử trùng lặp, xử lý missing values, lọc outliers"},
    {"num": 3, "name": "Kho dữ liệu (DW)", "desc": "Nạp dữ liệu vào kho SQLite/DuckDB theo mô hình Star Schema"},
    {"num": 4, "name": "Phân tích & Mô hình", "desc": "Tính toán KPIs, phân tích Pareto 80/20 và phân khúc RFM"},
    {"num": 5, "name": "Trực quan hóa", "desc": "Tạo Dashboard tương tác HTML/Chart.js trên Localhost"},
    {"num": 6, "name": "Quyết định & Hành động", "desc": "Tạo báo cáo khuyến nghị chiến lược theo khung SCQA"}
]

def print_banner():
    print("\n" + "=" * 70)
    print("      🚀 HỆ THỐNG ĐIỀU PHỐI QUY TRÌNH BI TOÀN DIỆN (BI WORKFLOW)")
    print("=" * 70)

def print_step_header(step_info):
    print("\n" + "-" * 70)
    print(f"  👉 GIAI ĐOẠN {step_info['num']}: {step_info['name'].upper()}")
    print(f"  📌 Mô tả: {step_info['desc']}")
    print("-" * 70)

def execute_step(step_num, context):
    step_info = STEPS[step_num - 1]
    print_step_header(step_info)
    start_time = time.time()
    
    if step_num == 1:
        raw_file = step1_data_collection("raw_sales_data.csv")
        context["raw_file"] = raw_file
        print(f"  ✅ [Bước 1 Hoàn tất] File dữ liệu thô đã lưu tại: {raw_file}")
        
    elif step_num == 2:
        raw_file = context.get("raw_file", "raw_sales_data.csv")
        cleaned_rows = step2_data_cleaning(raw_file)
        context["cleaned_rows"] = cleaned_rows
        print(f"  ✅ [Bước 2 Hoàn tất] Đã xử lý & làm sạch {len(cleaned_rows)} bản ghi.")
        
    elif step_num == 3:
        cleaned_rows = context.get("cleaned_rows")
        if not cleaned_rows:
            raw_file = context.get("raw_file", "raw_sales_data.csv")
            cleaned_rows = step2_data_cleaning(raw_file)
        step3_data_warehousing(cleaned_rows, "bi_datawarehouse.db")
        context["db_path"] = "bi_datawarehouse.db"
        print("  ✅ [Bước 3 Hoàn tất] Dữ liệu đã sẵn sàng trong kho: bi_datawarehouse.db")
        
    elif step_num == 4:
        db_path = context.get("db_path", "bi_datawarehouse.db")
        results = step4_analysis_and_modeling(db_path)
        context["results"] = results
        kpis = results["kpis"]
        print(f"  ✅ [Bước 4 Hoàn tất] Doanh thu: {kpis['total_revenue']:,.0f} đ | Đơn hàng: {kpis['total_orders']}")
        
    elif step_num == 5:
        results = context.get("results")
        if not results:
            results = step4_analysis_and_modeling("bi_datawarehouse.db")
        step5_visualization(results, "bi_dashboard.html")
        context["dashboard_file"] = "bi_dashboard.html"
        print("  ✅ [Bước 5 Hoàn tất] Dashboard sẵn sàng: bi_dashboard.html (Mở tại http://localhost:8000)")
        
    elif step_num == 6:
        results = context.get("results")
        if not results:
            results = step4_analysis_and_modeling("bi_datawarehouse.db")
        report_file = "ACTIONABLE_INSIGHTS.md"
        step6_actionable_insights(results, report_file)
        context["report_file"] = report_file
        print(f"  ✅ [Bước 6 Hoàn tất] Báo cáo chiến lược đã tạo: {report_file}")
        
    elapsed = time.time() - start_time
    print(f"  ⏱ Thời gian xử lý: {elapsed:.2f} giây")

def run_interactive():
    print_banner()
    print("Chế độ: TỪNG BƯỚC MỘT (Interactive Step-by-Step)\n")
    context = {}
    
    for i in range(1, 7):
        execute_step(i, context)
        if i < 6:
            input(f"\n[Bấm phím ENTER để tiếp tục chuyển sang Bước {i+1}...] ")
            
    print("\n" + "=" * 70)
    print("  🎉 TẤT CẢ 6 BƯỚC ĐÃ ĐƯỢC THỰC THI THÀNH CÔNG THEO ĐÚNG TIẾN ĐỘ!")
    print("=" * 70)

def run_auto():
    print_banner()
    print("Chế độ: TỰ ĐỘNG TUẦN TỰ (Sequential Auto-Execution)\n")
    context = {}
    for i in range(1, 7):
        execute_step(i, context)
        time.sleep(0.5)
    print("\n" + "=" * 70)
    print("  🎉 QUY TRÌNH TỰ ĐỘNG ĐÃ HOÀN TẤT THÀNH CÔNG!")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BI Workflow Runner")
    parser.add_argument("--auto", action="store_true", help="Chạy tự động toàn bộ quy trình")
    parser.add_argument("--step", type=int, choices=range(1, 7), help="Chạy riêng một bước cụ thể (1 đến 6)")
    args = parser.parse_args()
    
    if args.step:
        print_banner()
        context = {}
        execute_step(args.step, context)
    elif args.auto:
        run_auto()
    else:
        # Mặc định chạy chế độ tự động nếu không có terminal input
        run_auto()

