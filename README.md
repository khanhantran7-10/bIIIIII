# Hệ Thống BI & Quản Trị Kinh Doanh Số 5 Bước (Vercel Ready)

Hệ thống Business Intelligence (BI) và Quản trị Kinh doanh số 5 bước tuần tự, hoạt động theo cơ chế **Zero-Data Clean Slate** và **Schema-Agnostic Engine** (tự động thích ứng mọi file dữ liệu).

---

## 📁 Cấu Trúc Thư Mục Dự Án (Chuẩn Vercel Deployment)

```
.
├── api/
│   └── index.py            # Serverless Python Function cho toàn bộ API (/api/*)
├── index.html              # Giao diện Frontend Single Page Application (SPA)
├── vercel.json             # Cấu hình định tuyến Vercel Rewrite (/api/(.*) -> api/index.py)
├── requirements.txt        # Thư viện Python phụ thuộc cho Vercel Build (pandas, openpyxl, ...)
├── .gitignore              # Loại bỏ file tạm, cache, .env trước khi push Git
├── server.py               # Server chạy kiểm thử trực tiếp trên máy cục bộ (localhost:8000)
└── README.md               # Hướng dẫn triển khai
```

---

## 🚀 Hướng Dẫn Xuất / Triển Khai Lên Vercel (2 Cách)

### Cách 1: Triển khai qua GitHub (Khuyên dùng)
1. Đẩy toàn bộ thư mục dự án lên một kho lưu trữ (Repository) trên **GitHub**.
2. Truy cập [vercel.com](https://vercel.com/) và đăng nhập tài khoản.
3. Bấm **"Add New..."** ➔ **"Project"** ➔ Chọn kho GitHub của bạn ➔ Bấm **"Import"**.
4. **Cấu hình Project Settings:**
   - **Framework Preset:** Chọn `Other`.
   - **Root Directory:** Để trống `./`.
   - **Environment Variables:**
     - Thêm biến `GEMINI_API_KEY` với giá trị API Key của bạn (từ Google AI Studio).
5. Bấm nút **"Deploy"**. Vercel sẽ tự động:
   - Cài đặt các thư viện trong `requirements.txt`.
   - Biên dịch `api/index.py` thành Serverless Function.
   - Triển khai `index.html` làm Frontend tĩnh.
   - Gán đường dẫn công khai (ví dụ: `https://your-bi-studio.vercel.app`).

---

### Cách 2: Triển khai trực tiếp qua Vercel CLI
1. Cài đặt Vercel CLI trên máy (nếu chưa có):
   ```bash
   npm install -g vercel
   ```
2. Mở terminal tại thư mục này và gõ lệnh:
   ```bash
   vercel
   ```
3. Đăng nhập và xác nhận các câu hỏi mặc định (`Y` ➔ `Enter`).
4. Khi muốn deploy lên môi trường Production chính thức:
   ```bash
   vercel --prod
   ```

---

## 💻 Cách Khởi Chạy Local (Trên máy tính cá nhân)

Chỉ cần chạy lệnh:
```bash
python server.py
```
Và mở trình duyệt tại: **[http://localhost:8000](http://localhost:8000)**.
