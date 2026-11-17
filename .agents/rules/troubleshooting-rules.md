# AI IT Troubleshooting Assistant - Workspace Rules for Antigravity IDE

This repository contains the **AI-Powered IT Application Maintenance and Deployment Troubleshooting Assistant** native desktop application.

## Key Architecture & Technology Stack
- **GUI Framework**: PySide6 (Qt for Python). Native desktop application window.
- **Styling**: `ui/styles.qss` (Dark navy `#0f172a` developer theme with high-contrast status and severity badges).
- **Database**: SQLite (`database/schema.py`, `database/db_manager.py`) using strictly parameterized queries (`?`).
- **AI Abstraction**: `services/ai_service.py` supporting `GeminiProvider`, `OpenAIProvider`, and offline `DemoProvider`.
- **Log Processing & Security**: `services/log_processor.py` for client-side regex secret redaction and intelligent truncation before AI submission.
- **Background Worker**: `services/workers.py` (`AnalysisWorker(QThread)`) to ensure the desktop UI never freezes.
- **Supported Languages**: Python, Java, JavaScript, C, C++ (`modules/languages.py`).

## Antigravity IDE Execution & Testing
- **Run the Application**:
  ```powershell
  python main.py
  ```
  Or run the helper script `.\run.ps1` or `.\run.bat`.
- **Run Headless Automated Tests (PyTest)**:
  ```powershell
  python -m pytest -v
  ```
- **CLI Headless Diagnostics**:
  ```powershell
  python main.py --cli --file sample_logs/python_docker_port_bind.log
  ```
- **Standalone Binary**:
  ```powershell
  .\dist\AI_IT_Troubleshooting_Assistant\AI_IT_Troubleshooting_Assistant.exe
  ```

## Development Guidelines
- Always use parameterized queries for database operations to prevent SQL injection.
- Keep PySide6 QWidget parent-child bindings intact to prevent Shiboken garbage collection issues.
- Never execute external application code or logs directly.
