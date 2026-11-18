@echo off
chcp 65001 > nul
cls
echo ================================================================
echo           HỆ THỐNG ĐIỀU PHỐI BI PIPELINE WORKFLOW
echo ================================================================
echo Chọn chế độ thực thi:
echo  [1] Chạy TỰ ĐỘNG toàn bộ 6 bước từ đầu đến cuối
echo  [2] Chạy Bước 1: Thu thập dữ liệu (Data Collection)
echo  [3] Chạy Bước 2: Làm sạch dữ liệu (Data Cleaning)
echo  [4] Chạy Bước 3: Nạp vào Kho dữ liệu (Data Warehouse)
echo  [5] Chạy Bước 4: Phân tích & Mô hình hóa (Analysis & Modeling)
echo  [6] Chạy Bước 5: Trực quan hóa & Dashboard (Visualization)
echo  [7] Chạy Bước 6: Đề xuất Quyết định & Hành động (Actionable Insights)
echo  [0] Thoát
echo ================================================================
set /p opt="Vui lòng nhập lựa chọn của bạn (0-7): "

if "%opt%"=="1" python workflow_runner.py --auto
if "%opt%"=="2" python workflow_runner.py --step 1
if "%opt%"=="3" python workflow_runner.py --step 2
if "%opt%"=="4" python workflow_runner.py --step 3
if "%opt%"=="5" python workflow_runner.py --step 4
if "%opt%"=="6" python workflow_runner.py --step 5
if "%opt%"=="7" python workflow_runner.py --step 6
if "%opt%"=="0" exit

echo.
pause

