@echo off
echo ================================================================================
echo  Cambodia Agricultural Intelligence - Starting All Services
echo ================================================================================
echo.

echo [1/2] Starting API Server (FastAPI)...
echo.
start "Cambodia Agri - API Server" cmd /k "cd /d D:\Projects\cambodia && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo Waiting for API to start...
timeout /t 8 /nobreak >nul
echo.

echo [2/2] Starting Streamlit UI...
echo.
start "Cambodia Agri - Streamlit UI" cmd /k "cd /d D:\Projects\cambodia && python -m streamlit run ui/streamlit_app.py"

echo.
echo ================================================================================
echo  Services Started Successfully!
echo ================================================================================
echo.
echo  API Server:  http://localhost:8000
echo  API Docs:    http://localhost:8000/docs
echo  Streamlit:   http://localhost:8501
echo.
echo  Status:      Press Ctrl+C in each window to stop
echo  Dashboard:   http://localhost:8501/Admin
echo  Trends:      http://localhost:8501/Market_Trends
echo.
echo ================================================================================
echo.
echo Opening Streamlit in browser in 10 seconds...
timeout /t 10 /nobreak >nul

start http://localhost:8501

echo.
echo All services running!
echo Press any key to exit this window...
pause >nul
