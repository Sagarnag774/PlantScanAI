# 🚀 PlantScan AI: Step-by-Step Execution Guide

This guide provides simple, step-by-step instructions for running **PlantScan AI** on Windows (PowerShell, Command Prompt, or file explorer).

---

## ⚡ Quick Start (1-Click Executable Scripts)

For convenience on Windows, pre-configured batch scripts are provided in the root directory:

| Action | Script File | Description |
| :--- | :--- | :--- |
| **Start Backend API** | `run_backend.bat` | Double-click or run `.\run_backend.bat` to launch the FastAPI server at `http://localhost:8000` |
| **Run Unit Test Suite** | `run_tests.bat` | Double-click or run `.\run_tests.bat` to run all 16 automated Pytest tests |
| **Test Image Predictor** | `run_predictor.bat` | Run `.\run_predictor.bat <image_path> <crop_name>` to test disease prediction |

---

## 📋 Manual Step-by-Step Instructions

### Step 1: Open Terminal & Navigate to Project Directory

Open **PowerShell** or **Command Prompt (CMD)**:

```powershell
cd "d:\Sagarnag\major project\pgpt\PlantScanAI"
```

---

### Step 2: Python Environment Execution Options

Dependencies are installed inside `.venv`. You do **not** need to activate the environment if you run python directly via `.venv`:

#### Option A: Direct Execution (Easiest in PowerShell)
```powershell
# Run using virtual environment python executable
.\.venv\Scripts\python.exe --version
```

#### Option B: Activate Virtual Environment in PowerShell
If PowerShell blocks activation due to `Restricted` ExecutionPolicy:
```powershell
# 1. Temporarily allow scripts for this terminal session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 2. Activate environment
.\.venv\Scripts\Activate.ps1
```

---

### Step 3: Run the Automated Unit Test Suite

Run the 16 automated backend test cases:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -v
```

#### Expected Result:
- 16 passed tests in ~0.2s

---

### Step 4: Start the Production FastAPI Server

Start the REST API server:

```powershell
.\.venv\Scripts\python.exe -m backend.main
```

#### Access Web Interfaces:
- 🌐 **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 📖 **ReDoc Interface**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- 💚 **Health Status**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### Step 5: Test Model Predictor CLI

Test disease prediction on any leaf image:

```powershell
.\.venv\Scripts\python.exe ml/inference/crop_predictor.py --image "path\to\leaf.jpg" --crop tomato --use-tflite
```

---

### Step 6: Run Mobile Application (React Native Frontend)

```powershell
cd mobile_app
npm install
npm start
```

---

## 📑 Summary Command Reference

```powershell
# 1. Run Unit Tests
.\run_tests.bat

# 2. Run Backend Server
.\run_backend.bat

# 3. Predict Disease CLI
.\.venv\Scripts\python.exe ml/inference/crop_predictor.py --image "path/to/leaf.jpg" --crop tomato
```
