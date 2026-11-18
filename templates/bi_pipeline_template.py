"""
BI PIPELINE TEMPLATE: Mẫu triển khai toàn diện quy trình BI 6 bước bằng Python.
(Tương thích 100% với Python Standard Library & SQLite - Không yêu cầu cài thêm thư viện)

Quy trình:
1. Thu thập dữ liệu (Data Collection - ERP/CRM/Sales simulation)
2. Làm sạch & Xử lý (Data Cleaning & Processing: deduplication, missing values, outlier filter)
3. Kho dữ liệu (Data Warehousing - SQLite Star Schema: Facts & Dimensions)
4. Phân tích & Mô hình hóa (Analysis: KPIs, Pareto 80/20, Phân khúc RFM)
5. Trực quan hóa (Interactive Dashboard HTML / Chart.js)
6. Ra quyết định & Hành động (Actionable Insights Generator)
"""

import os
import csv
import json
import sqlite3
import random
from datetime import datetime, timedelta
from collections import defaultdict

def step1_data_collection(filename="raw_sales_data.csv"):
    print("[Bước 1] Thu thập dữ liệu (Data Collection)...")
    random.seed(42)
    n_records = 200
    
    products = [
        {"name": "Laptop Pro 14", "price": 25000000},
        {"name": "Bàn phím Cơ", "price": 1500000},
        {"name": "Chuột Wireless", "price": 600000},
        {"name": "Màn hình 27 inch", "price": 5500000},
        {"name": "Tai nghe Gaming", "price": 1200000}
    ]
    channels = ["Website", "Facebook", "Shopee", "Showroom", ""]
    statuses = ["Hoàn tất", "Đã giao", "Đang xử lý", "Hủy", ""]
    
    rows = []
    base_date = datetime.now()
    for i in range(1, n_records + 1):
        prod = random.choice(products)
        days_ago = int(random.expovariate(1/30))
        order_date = (base_date - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        cust_id = f"KH_{random.randint(100, 140)}"
        channel = random.choice(channels)
        qty = random.choices([1, 2, 3, 4, 100], weights=[70, 20, 6, 3, 1])[0] # 100 là outlier
        status = random.choices(statuses, weights=[60, 20, 10, 8, 2])[0]
        
        rows.append({
            "order_id": f"ORD_{1000 + i}",
            "order_date": order_date,
            "customer_id": cust_id,
            "product_name": prod["name"],
            "unit_price": prod["price"],
            "quantity": qty,
            "channel": channel,
            "status": status
        })
        
    # Thêm 5 bản ghi trùng lặp để mô phỏng dữ liệu thô từ hệ thống
    for dup in rows[:5]:
        rows.append(dup.copy())
        
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        
    print(f" -> Đã trích xuất {len(rows)} bản ghi vào file: {filename}")
    return filename

def step2_data_cleaning(raw_filename):
    print("\n[Bước 2] Làm sạch và xử lý dữ liệu (Data Cleaning & Processing)...")
    cleaned_rows = []
    seen_orders = set()
    
    with open(raw_filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            order_id = r["order_id"]
            
            # 1. Khử trùng lặp (Deduplication)
            if order_id in seen_orders:
                continue
            seen_orders.add(order_id)
            
            # 2. Xử lý thiếu dữ liệu (Missing Values)
            channel = r["channel"].strip() if r["channel"].strip() else "Chưa xác định"
            status = r["status"].strip() if r["status"].strip() else "Đang xử lý"
            
            # 3. Chuẩn hóa số liệu
            qty = int(r["quantity"])
            unit_price = float(r["unit_price"])
            
            # 4. Lọc giá trị ngoại lai bất thường (Outliers: số lượng nhập nhầm > 20)
            if qty > 20 or qty <= 0:
                continue
                
            total_amount = qty * unit_price
            
            cleaned_rows.append({
                "order_id": order_id,
                "order_date": r["order_date"],
                "customer_id": r["customer_id"],
                "product_name": r["product_name"],
                "unit_price": unit_price,
                "quantity": qty,
                "total_amount": total_amount,
                "channel": channel,
                "status": status
            })
            
    print(f" -> Làm sạch hoàn tất: Lưu giữ {len(cleaned_rows)} bản ghi chuẩn hóa.")
    return cleaned_rows

def step3_data_warehousing(cleaned_rows, db_path="bi_datawarehouse.db"):
    print(f"\n[Bước 3] Lưu trữ vào Kho dữ liệu (Data Warehousing: {db_path})...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Tạo mô hình Star Schema: Dim & Fact
    cur.execute("DROP TABLE IF EXISTS dim_customer")
    cur.execute("CREATE TABLE dim_customer (customer_id TEXT PRIMARY KEY)")
    
    cur.execute("DROP TABLE IF EXISTS dim_product")
    cur.execute("CREATE TABLE dim_product (product_name TEXT PRIMARY KEY, unit_price REAL)")
    
    cur.execute("DROP TABLE IF EXISTS fact_orders")
    cur.execute("""
        CREATE TABLE fact_orders (
            order_id TEXT PRIMARY KEY,
            order_date TEXT,
            customer_id TEXT,
            product_name TEXT,
            channel TEXT,
            quantity INTEGER,
            total_amount REAL,
            status TEXT,
            FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
            FOREIGN KEY (product_name) REFERENCES dim_product(product_name)
        )
    """)
    
    customers = set()
    products = {}
    for r in cleaned_rows:
        customers.add(r["customer_id"])
        products[r["product_name"]] = r["unit_price"]
        
    cur.executemany("INSERT INTO dim_customer VALUES (?)", [(c,) for c in customers])
    cur.executemany("INSERT INTO dim_product VALUES (?, ?)", [(p, pr) for p, pr in products.items()])
    
    cur.executemany("""
        INSERT INTO fact_orders VALUES (
            :order_id, :order_date, :customer_id, :product_name, :channel, :quantity, :total_amount, :status
        )
    """, cleaned_rows)
    
    conn.commit()
    conn.close()
    print(" -> Star Schema đã tạo thành công trong SQLite DW: dim_customer, dim_product, fact_orders.")

def step4_analysis_and_modeling(db_path="bi_datawarehouse.db"):
    print("\n[Bước 4] Phân tích và mô hình hóa dữ liệu (Data Analysis & Modeling)...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. KPIs cốt lõi
    cur.execute("""
        SELECT 
            COUNT(*) as total_orders,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as aov,
            COUNT(DISTINCT customer_id) as total_customers
        FROM fact_orders
        WHERE status IN ('Hoàn tất', 'Đã giao')
    """)
    total_orders, total_revenue, aov, total_customers = cur.fetchone()
    
    # 2. Phân tích doanh số theo Kênh (Channel Performance)
    cur.execute("""
        SELECT channel, SUM(total_amount) as revenue
        FROM fact_orders
        WHERE status IN ('Hoàn tất', 'Đã giao')
        GROUP BY channel
        ORDER BY revenue DESC
    """)
    channel_perf = {row[0]: row[1] for row in cur.fetchall()}
    
    # 3. Phân tích Pareto sản phẩm (80/20)
    cur.execute("""
        SELECT product_name, SUM(total_amount) as revenue, SUM(quantity) as units
        FROM fact_orders
        WHERE status IN ('Hoàn tất', 'Đã giao')
        GROUP BY product_name
        ORDER BY revenue DESC
    """)
    products = []
    cum = 0.0
    for p_name, rev, units in cur.fetchall():
        share = (rev / total_revenue) * 100
        cum += share
        products.append({
            "product_name": p_name,
            "revenue": rev,
            "units": units,
            "share": share,
            "cum_share": cum
        })
        
    # 4. Phân khúc khách hàng RFM cơ bản
    cur.execute("""
        SELECT 
            customer_id,
            COUNT(order_id) as frequency,
            SUM(total_amount) as monetary,
            MAX(order_date) as last_order
        FROM fact_orders
        WHERE status IN ('Hoàn tất', 'Đã giao')
        GROUP BY customer_id
    """)
    
    segments = defaultdict(int)
    for cid, freq, mon, last_date in cur.fetchall():
        # Đơn giản hóa phân khúc
        if mon >= (total_revenue / total_customers) * 1.5:
            segments["VIP (Doanh thu cao)"] += 1
        elif freq >= 2:
            segments["Khách hàng Thân thiết"] += 1
        else:
            segments["Khách hàng Tiềm năng"] += 1
            
    conn.close()
    
    results = {
        "kpis": {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "aov": aov,
            "total_customers": total_customers
        },
        "channel_perf": channel_perf,
        "product_perf": products,
        "segments": dict(segments)
    }
    print(" -> Hoàn tất phân tích KPIs, cơ cấu kênh, sản phẩm Pareto & RFM.")
    return results

def step5_visualization(results, output_html="bi_dashboard.html"):
    print(f"\n[Bước 5] Trực quan hóa dữ liệu (Data Visualization -> {output_html})...")
    kpis = results["kpis"]
    channels = results["channel_perf"]
    products = results["product_perf"]
    segments = results["segments"]
    
    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>BI Executive Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
        .header {{ margin-bottom: 24px; }}
        .header h1 {{ margin: 0; font-size: 26px; color: #0f172a; }}
        .header p {{ margin: 6px 0 0; color: #64748b; font-size: 14px; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .kpi-card {{ background: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); border-left: 5px solid #2563eb; }}
        .kpi-title {{ font-size: 13px; color: #64748b; text-transform: uppercase; font-weight: 600; }}
        .kpi-value {{ font-size: 26px; font-weight: 700; color: #0f172a; margin-top: 6px; }}
        .chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
        .chart-card {{ background: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
        .chart-card h3 {{ margin-top: 0; font-size: 16px; color: #334155; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f1f5f9; color: #475569; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 BÁO CÁO KINH DOANH ĐIỀU HÀNH (EXECUTIVE BI DASHBOARD)</h1>
        <p>Quy trình BI tự động hóa bởi Antigravity BI Agent | Dữ liệu từ kho SQLite Data Warehouse</p>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card" style="border-left-color: #2563eb;">
            <div class="kpi-title">Tổng Doanh Thu</div>
            <div class="kpi-value">{kpis['total_revenue']:,.0f} đ</div>
        </div>
        <div class="kpi-card" style="border-left-color: #10b981;">
            <div class="kpi-title">Đơn Thành Công</div>
            <div class="kpi-value">{kpis['total_orders']} đơn</div>
        </div>
        <div class="kpi-card" style="border-left-color: #f59e0b;">
            <div class="kpi-title">Giá Trị TB Đơn (AOV)</div>
            <div class="kpi-value">{kpis['aov']:,.0f} đ</div>
        </div>
        <div class="kpi-card" style="border-left-color: #8b5cf6;">
            <div class="kpi-title">Khách Hàng Phát Sinh Đơn</div>
            <div class="kpi-value">{kpis['total_customers']} khách</div>
        </div>
    </div>

    <div class="chart-grid">
        <div class="chart-card">
            <h3>Doanh Thu Theo Kênh Bán Hàng</h3>
            <canvas id="channelChart"></canvas>
        </div>
        <div class="chart-card">
            <h3>Phân Khúc Khách Hàng (RFM)</h3>
            <canvas id="segmentChart"></canvas>
        </div>
    </div>

    <div class="chart-card">
        <h3>Bảng Xếp Hạng & Tỷ Trọng Sản Phẩm (Pareto 80/20)</h3>
        <table>
            <thead>
                <tr>
                    <th>Sản phẩm</th>
                    <th>Số lượng bán</th>
                    <th>Doanh thu (VNĐ)</th>
                    <th>Tỷ trọng (%)</th>
                    <th>Tích lũy (%)</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f"<tr><td><b>{p['product_name']}</b></td><td>{p['units']}</td><td>{p['revenue']:,.0f} đ</td><td>{p['share']:.1f}%</td><td>{p['cum_share']:.1f}%</td></tr>" for p in products)}
            </tbody>
        </table>
    </div>

    <script>
        new Chart(document.getElementById('channelChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(list(channels.keys()))},
                datasets: [{{
                    label: 'Doanh thu (VNĐ)',
                    data: {json.dumps(list(channels.values()))},
                    backgroundColor: '#3b82f6'
                }}]
            }},
            options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }} }}
        }});

        new Chart(document.getElementById('segmentChart'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(list(segments.keys()))},
                datasets: [{{
                    data: {json.dumps(list(segments.values()))},
                    backgroundColor: ['#10b981', '#3b82f6', '#f59e0b']
                }}]
            }},
            options: {{ responsive: true }}
        }});
    </script>
</body>
</html>"""
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f" -> Đã xuất file Dashboard HTML trực quan: {output_html}")

def step6_actionable_insights(results, output_md="ACTIONABLE_INSIGHTS.md"):
    print(f"\n[Bước 6] Ra quyết định & Hành động (Actionable Insights -> {output_md})...")
    kpis = results["kpis"]
    top_p = results["product_perf"][0]
    best_c = max(results["channel_perf"].items(), key=lambda x: x[1])
    
    content = f"""# BÁO CÁO QUYẾT ĐỊNH & HÀNH ĐỘNG CHIẾN LƯỢC (ACTIONABLE INSIGHTS)

**Người lập:** BI Agent (Hệ thống Antigravity BI)  
**Ngày lập:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  

---

## 1. THỰC TRẠNG KINH DOANH (SITUATION)
- **Tổng doanh số đạt được:** {kpis['total_revenue']:,.0f} VNĐ ({kpis['total_orders']} đơn hàng giao dịch thành công).
- **Giá trị trung bình mỗi đơn (AOV):** {kpis['aov']:,.0f} VNĐ.
- **Kênh bán hàng hiệu quả nhất:** `{best_c[0]}` đóng góp doanh số cao nhất ({best_c[1]:,.0f} VNĐ).
- **Sản phẩm ngôi sao (Hero Product):** `{top_p['product_name']}` chiếm **{top_p['share']:.1f}%** tổng doanh thu toàn doanh nghiệp.

---

## 2. PHÁT HIỆN VẤN ĐỀ & CƠ HỘI (COMPLICATIONS & FINDINGS)
1. **Phụ thuộc doanh thu vào dòng `{top_p['product_name']}`:** Do chiếm tỷ trọng áp đảo ({top_p['share']:.1f}%), bất kỳ biến động về giá nhập hoặc đứt gãy nguồn cung sản phẩm này sẽ ảnh hưởng trực tiếp đến kết quả kinh doanh.
2. **Khai thác kênh `{best_c[0]}`:** Kênh này có lượng chuyển đổi vượt trội, cần tiếp tục đẩy mạnh nguồn lực để mở rộng thị phần.
3. **Phân nhóm khách hàng:** Cần có chương trình chăm sóc riêng cho các nhóm VIP để tối ưu hóa Giá trị trọn đời khách hàng (LTV).

---

## 3. ĐỀ XUẤT HÀNH ĐỘNG CỤ THỂ (ACTIONABLE RECOMMENDATIONS)

### ⚡ Nhóm hành động tức thời (Quick Wins - 1 đến 2 tuần)
- **Thiết lập Combo sản phẩm:** Bán kèm `{top_p['product_name']}` với các phụ kiện (chuột, bàn phím, tai nghe) để đẩy doanh số phụ kiện và tăng AOV thêm 10-15%.
- **Chăm sóc nhóm khách hàng VIP:** Bộ phận CSKH liên hệ trực tiếp gửi thiệp cảm ơn và đặc quyền bảo hành ưu tiên.

### 🎯 Nhóm hành động trung hạn (1 đến 3 tháng)
- **Đầu tư ngân sách cho kênh `{best_c[0]}`:** Tăng 15-20% ngân sách quảng cáo cho kênh này để tối ưu chi phí thu hút khách hàng mới (CAC).
- **Đa dạng hóa danh mục sản phẩm:** Mở rộng thêm 1-2 mẫu ở phân khúc phổ thông để giảm rủi ro phụ thuộc vào một sản phẩm chủ lực duy nhất.

---

## 4. DỰ BÁO TÁC ĐỘNG VÀ ĐO LƯỜNG (IMPACT & KPI MONITORING)
- **Mục tiêu 30 ngày sau triển khai:**
  - Nâng chỉ số AOV từ **{kpis['aov']:,.0f} đ** lên trên **{kpis['aov']*1.12:,.0f} đ** (+12%).
  - Tăng tỷ lệ khách hàng mua lại lần 2 (Repeat Purchase Rate) thêm 8%.
"""
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(content)
    print(f" -> Đã xuất Báo cáo Khuyến nghị Hành động: {output_md}")

if __name__ == "__main__":
    print("=" * 65)
    print("   BẮT ĐẦU CHẠY TOÀN BỘ QUY TRÌNH BI 6 BƯỚC VỚI BI AGENT")
    print("=" * 65)
    raw_file = step1_data_collection()
    cleaned = step2_data_cleaning(raw_file)
    step3_data_warehousing(cleaned)
    analysis = step4_analysis_and_modeling()
    step5_visualization(analysis)
    step6_actionable_insights(analysis)
    print("\n" + "=" * 65)
    print("   HOÀN THÀNH TOÀN DIỆN QUY TRÌNH BI 6 BƯỚC!")
    print("=" * 65)
