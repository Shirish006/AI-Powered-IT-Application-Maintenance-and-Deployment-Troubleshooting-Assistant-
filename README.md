# AI IT Troubleshooting Assistant

**AI-Powered IT Application Maintenance and Deployment Troubleshooting Assistant** (Window title: `"AI IT Troubleshooting Assistant"`) is a high-performance native desktop application built with Python 3.10+, PySide6 (Qt for Python), and SQLite. It helps software engineers, DevOps practitioners, and computer science students diagnose, analyze, and resolve complex application errors encountered during **Application Maintenance** and **Application Deployment**.

---

## 🌟 Key Features

1. **Dual Problem Domain Coverage:**
   - **Application Maintenance:** Troubleshoot syntax errors, runtime exceptions, logic bugs, ORM/database issues, memory violations (SIGSEGV), and code-level defects in existing applications.
   - **Application Deployment:** Diagnose container crashes, Dockerfile build failures, missing runtime dependencies, port conflicts (`EADDRINUSE`), linker/CMake failures, and cloud environment discrepancies.
   - **Automatic Detection:** Automatically infers whether a pasted log indicates an internal maintenance problem or an environment/deployment failure.

2. **Five Supported Programming Languages:**
   - **Python:** Tracebacks, ModuleNotFoundError, virtual environments, Django/Flask/FastAPI.
   - **Java:** NullPointerException, classpath, Spring Boot, Maven/Gradle.
   - **JavaScript:** EADDRINUSE, Node.js cluster, Express, npm/yarn.
   - **C:** Segmentation faults, memory pointers, GCC/Clang, GDB, Valgrind, Makefiles.
   - **C++:** CMake linking errors, undefined references, AddressSanitizer (`-fsanitize=address`), smart pointers.

3. **Strict Multi-Section Diagnostic Breakdown:**
   Every diagnosis delivers 10 structured sections:
   1. Error Summary
   2. Programming Language
   3. Problem Type (Maintenance vs. Deployment, with auto-detection reasoning)
   4. Error Category (1 of 10 canonical categories: *Syntax Error, Runtime Error, Logical Error, Dependency Error, Configuration Error, Database Error, Network Error, Permission Error, Build Error, Deployment Error*)
   5. Severity Level (*Low, Medium, High, Critical*)
   6. Beginner-Friendly Explanation of the Error
   7. **Confirmed Facts vs. Possible Causes (Hypotheses):** Rigorously separates what is directly confirmed in the logs from ranked potential causes.
   8. Ordered Step-by-Step Troubleshooting Instructions
   9. Suggested Concrete Solution with code/configuration snippets
   10. Verification Steps to confirm the problem is resolved

4. **Multi-Format Export & Sharing:**
   - **Standalone Styled HTML Report:** Clean, responsive, self-contained HTML document ready for printing or emailing.
   - **Markdown Report:** Clean GitHub-flavored Markdown for Jira, GitHub Issues, or Slack.
   - **JSON Session Backup & Import:** Complete session serialization allowing team members to import and inspect past troubleshooting sessions without internet or API calls.

5. **Client-Side Security & Privacy Redaction:**
   - Automatically detects and redacts sensitive data (API keys, JWT tokens, AWS credentials, database passwords, authorization headers, private key blocks) before sending logs to an external AI provider.
   - Displays an explicit privacy confirmation dialog prior to any external API transmission.
   - Stores only redacted logs in the local database.

6. **Multi-Provider AI Abstraction & Built-In Demo Mode:**
   - **Google Gemini:** High-speed, high-accuracy analysis powered by `gemini-3.8-flash` via the official `google-genai` SDK (Free tier).
   - **Demo Mode:** Fully offline, deterministic simulation mode tailored for offline presentations, demonstrations, or testing with zero API calls.

7. **Persistent History & Searchable Database:**
   - Built with SQLite using parameterized queries for complete injection protection.
   - Multi-filter search (search bar, language filter, problem type filter, status filter).
   - Instant full-session viewer without re-calling the AI API.
   - One-click status management (*Unresolved*, *In Progress*, *Solved*).

8. **Dual Execution Modes (Native GUI & CLI):**
   - **PySide6 Native Desktop GUI:** Rich, responsive window with dark navy developer theme.
   - **Headless CLI Runner:** Run fast diagnostics directly inside the Antigravity IDE terminal without launching the GUI (`python main.py --cli --file sample.log`).

---

## 📁 Project Structure

```
AI_IT_Troubleshooting_Assistant/
├── main.py                     # Entry point supporting native PySide6 desktop GUI & CLI runner
├── requirements.txt            # Python dependencies with pinned versions
├── README.md                   # Comprehensive documentation
├── .env.example                # Example environment variable template
├── .gitignore                  # Git ignore rules for venv, caches, and secrets
├── AI_IT_Troubleshooting_Assistant.spec # PyInstaller Windows packaging specification
├── run.bat / run.ps1           # 1-click execution scripts for Antigravity IDE terminal
├── test.bat / test.ps1         # 1-click test scripts for Antigravity IDE terminal
│
├── .agents/
│   └── rules/
│       └── troubleshooting-rules.md # Antigravity IDE workspace-scoped agent rules
│
├── sample_logs/                # Demonstration logs for all 5 languages
│   ├── python_django_db_failure.log
│   ├── python_docker_port_bind.log
│   ├── java_spring_nullpointer.log
│   ├── javascript_node_eaddrinuse.log
│   ├── cpp_segfault_core_dump.log
│   └── cpp_cmake_missing_library.log
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Settings dataclass, path resolution (dev & PyInstaller), user prefs
│
├── database/
│   ├── __init__.py
│   ├── schema.py               # SQLite schema definition and indexing
│   └── db_manager.py           # Thread-safe database manager with parameterized queries & JSON I/O
│
├── modules/
│   ├── __init__.py
│   ├── languages.py            # Extensible language profiles (Python, Java, JavaScript, C, C++)
│   ├── maintenance.py          # Application Maintenance domain context & validation
│   └── deployment.py           # Application Deployment domain context & validation
│
├── prompts/
│   ├── __init__.py
│   └── troubleshooting_prompts.py # System prompt, structured schema, and prompt builder
│
├── services/
│   ├── __init__.py
│   ├── ai_service.py           # AIProvider base class, Gemini implementation, DemoProvider
│   ├── cli_runner.py           # Headless CLI runner for terminal troubleshooting
│   ├── error_classifier.py     # Canonical category and severity normalizer & heuristic fallback
│   ├── log_processor.py        # File validation, normalization, secret redaction, truncation
│   └── workers.py              # Background QThread worker for responsive UI
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py          # Main QMainWindow, left sidebar, stacked navigation, API settings dialog
│   ├── dashboard.py            # Screen 1: Dashboard with metric cards, quick actions, recent sessions
│   ├── new_troubleshooting.py  # Screen 2: Input form, log uploader, privacy dialog, analysis trigger
│   ├── analysis_screen.py      # Screen 3: 10-section diagnostic report, HTML/MD/JSON export, status updater
│   ├── history_screen.py       # Screen 4: Searchable table, combined filters, detail dialog, JSON import
│   ├── widgets.py              # Reusable cards, badges, loading overlay, stat cards
│   └── styles.qss              # Custom Qt Style Sheet (Dark navy developer palette)
│
├── assets/
│   └── icons/                  # Local SVG & ICO icons for offline operation (dashboard, settings, etc.)
│
└── tests/
    ├── __init__.py
    ├── test_database.py        # Automated SQLite tests (CRUD, SQL injection safety, filters)
    ├── test_log_processor.py   # Redaction patterns, normalization, truncation, signals
    ├── test_classifier.py      # Normalization and heuristic classification tests
    ├── test_ai_service.py      # JSON parsing, error mapping, DemoProvider tests
    ├── test_gui.py             # PySide6 offscreen GUI and navigation tests
    ├── test_workflow.py        # End-to-end diagnosis and persistence integration tests
    ├── test_cpp_support.py     # C and C++ profiles, signal extraction, and JSON import/export tests
    └── test_cli.py             # CLI runner parser, formatting, and headless workflow tests
```

---

## ⚡ How to Open and Work in Antigravity IDE (NOT VS Code)

Antigravity IDE is the dedicated AI-first developer environment. Follow these exact steps to open and use the project in Antigravity IDE:

### 1. Open the Project Folder in Antigravity IDE
1. Launch **Antigravity IDE**.
2. Go to the top menu bar and select **File > Open Folder...** (or press `Ctrl + K, Ctrl + O`).
3. Browse to and select the project directory:
   ```
   C:\Users\shiri\.gemini\antigravity\scratch\AI_IT_Troubleshooting_Assistant
   ```
   *(Alternatively, in Antigravity's left sidebar, click the **Projects** icon and choose this folder).*
4. Antigravity IDE will load the workspace. You will see all files, folders, and `.agents/rules/` directly in the Explorer tree.

### 2. Open the Antigravity Integrated Terminal
1. Press `Ctrl + ~` (tilde) or go to the top menu and select **Terminal > New Terminal**.
2. A PowerShell terminal will open directly inside the project root directory.

### 3. Run the Native Desktop Application
In the Antigravity terminal, run:
```powershell
python main.py
```
*(Or simply run `.\run.ps1` or `run.bat`)*

The native dark-themed PySide6 desktop window titled **"AI IT Troubleshooting Assistant"** will open immediately!

### 4. Run Fast Headless Diagnostics in Antigravity Terminal (CLI Mode)
If you want to diagnose an error log directly from your terminal inside Antigravity IDE without launching the GUI:
```powershell
python main.py --cli --file sample_logs/python_docker_port_bind.log
```
Or for a C++ memory segmentation fault with automatic report export:
```powershell
python main.py --cli --file sample_logs/cpp_segfault_core_dump.log --export memory_report.md
```

### 5. Run the Automated Test Suite
In the Antigravity integrated terminal, execute:
```powershell
python -m pytest -v
```
*(Or run `.\test.ps1`)*

All **44 automated tests** across 8 test suites will execute and pass in ~2 seconds.

### 6. Using Antigravity AI Features with This Project
- **Agent Chat & Sidebar**: In Antigravity's chat panel, you can type `@` to mention project files (e.g. `@main.py`, `@services/ai_service.py`, `@ui/new_troubleshooting.py`) to ask questions or review code.
- **Inline AI Code Editing**: Highlight any function or block and press `Ctrl + I` to refactor, explain, or add features with AI assistance.
- **Workspace Rules**: Antigravity IDE automatically reads `.agents/rules/troubleshooting-rules.md`, ensuring all agent interactions adhere to our project architecture and security rules.

---

## 🔑 AI Provider Configuration

You can run the application with **Google Gemini** (Free) or offline in **Demo Mode**.

### Option A: In-App Mode Selector (Recommended)
Use the **Troubleshooting Mode** selector at the bottom-left of the sidebar to seamlessly toggle between **🟢 Online (Gemini AI)** and **⚡ Offline (Local Mode)**.

### Option B: `.env` File
Create a `.env` file from `.env.example`:
```powershell
Copy-Item .env.example .env
```
Fill in your API key:
```env
# Choose: gemini or demo
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
```

### Option C: Demo Mode (Offline / No Key Required)
Select **Offline (Local Mode)** in the sidebar mode selector or set `AI_PROVIDER=demo`. The assistant will generate rich, realistic, context-aware diagnostic demonstrations locally without making any external network requests.

---

## 📦 Standalone Executable (Windows)

The application has been compiled with PyInstaller into a standalone Windows binary that runs on any modern Windows machine without requiring Python:

```powershell
.\dist\AI_IT_Troubleshooting_Assistant\AI_IT_Troubleshooting_Assistant.exe
```

To recompile the binary after making modifications:
```powershell
pyinstaller AI_IT_Troubleshooting_Assistant.spec --noconfirm
```

---

## 📋 Demonstration Guide

To test or demonstrate the application using real error logs:
1. Open the app (`python main.py`).
2. On Screen 1 (Dashboard), click **Application Maintenance** or **Application Deployment**.
3. On Screen 2, click **Upload Log File** and choose one of the pre-made sample logs in `sample_logs/`:
   - `python_django_db_failure.log` -> Tests Maintenance / Database Error
   - `python_docker_port_bind.log` -> Tests Deployment / EADDRINUSE Docker Error
   - `java_spring_nullpointer.log` -> Tests Maintenance / NullPointerException
   - `javascript_node_eaddrinuse.log` -> Tests Deployment / Express EADDRINUSE
   - `cpp_segfault_core_dump.log` -> Tests Maintenance / C++ Memory SIGSEGV
   - `cpp_cmake_missing_library.log` -> Tests Deployment / Linker Build Error
4. Click **Analyze Problem**.
5. On Screen 3 (AI Analysis), review the 10 diagnostic sections, switch the status to *In Progress* or *Solved*, and click **Export Report** to generate a styled HTML or Markdown report.
6. Open Screen 4 (History) to search, filter, and inspect past sessions.
