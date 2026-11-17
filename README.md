# AI IT Troubleshooting Assistant

**AI-Powered IT Application Maintenance and Deployment Troubleshooting Assistant** is a desktop application built with Python 3.10+, PySide6 (Qt for Python), and SQLite. It helps software engineers, DevOps practitioners, and computer science students diagnose, analyze, and resolve complex application errors encountered during **Application Maintenance** and **Application Deployment**.

---

## 🌟 Key Features

1. **Dual Problem Domain Coverage:**
   - **Application Maintenance:** Troubleshoot syntax errors, runtime exceptions, logic bugs, ORM/database issues, and code-level defects in existing applications.
   - **Application Deployment:** Diagnose container crashes, Dockerfile build failures, missing runtime dependencies, port conflicts (`EADDRINUSE`), and cloud environment discrepancies.
   - **Automatic Detection:** Automatically infers whether a pasted log indicates an internal maintenance problem or an environment/deployment failure.

2. **Strict Multi-Section Diagnostic Breakdown:**
   Every diagnosis delivers 10 structured sections:
   1. Error Summary
   2. Programming Language
   3. Problem Type (Maintenance vs. Deployment, with auto-detection reasoning)
   4. Error Category (1 of 10 canonical categories: *Syntax Error, Runtime Error, Logical Error, Dependency Error, Configuration Error, Database Error, Network Error, Permission Error, Build Error, Deployment Error*)
   5. Severity Level (*Low, Medium, High, Critical*)
   6. Beginner-Friendly Explanation of the Error
   7. **Confirmed Facts vs. Possible Hypotheses:** Rigorously separates what is directly confirmed in the logs from ranked potential causes.
   8. Ordered Step-by-Step Troubleshooting Instructions
   9. Suggested Concrete Solution with code/configuration snippets
   10. Verification Steps to confirm the problem is resolved

3. **Client-Side Security & Privacy Redaction:**
   - Automatically detects and redacts sensitive data (API keys, JWT tokens, AWS credentials, database passwords, authorization headers, private key blocks) before sending logs to an external AI provider.
   - Displays an explicit privacy confirmation dialog prior to any external API transmission.
   - Stores only redacted logs in the local database.

4. **Multi-Provider AI Abstraction & Built-In Demo Mode:**
   - **Google Gemini:** High-speed, high-accuracy analysis powered by `gemini-2.5-flash` via the `google-genai` SDK.
   - **OpenAI:** Powered by `gpt-4o-mini` (or user-chosen model) via the `openai` SDK.
   - **Demo Mode:** Fully offline, deterministic simulation mode tailored for college demonstrations, offline presentations, or testing when no API key is available.

5. **Persistent History & Searchable Database:**
   - Built with SQLite using parameterized queries for complete injection protection.
   - Multi-filter search (search bar, language filter, problem type filter, status filter).
   - Instant full-session viewer without re-calling the AI API.
   - Export session diagnostics as clean Markdown reports.
   - One-click status management (*Unresolved*, *In Progress*, *Solved*).

6. **Modern, Responsive Native UI:**
   - Built on PySide6 with custom Qt Style Sheets (QSS).
   - Deep navy sidebar, rounded cards, high-contrast badges, and custom scrollbars.
   - Completely non-blocking background workers (`QThread`) ensure the user interface never freezes during requests.

---

## 📁 Project Structure

```
AI_IT_Troubleshooting_Assistant/
├── main.py                     # Application entry point, QSS loader, global exception handler
├── requirements.txt            # Python dependencies with pinned versions
├── README.md                   # Complete developer and user documentation
├── .env.example                # Example environment variable template
├── .gitignore                  # Git ignore rules for venv, caches, and secrets
├── AI_IT_Troubleshooting_Assistant.spec # PyInstaller Windows packaging specification
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Settings dataclass, path resolution (dev & PyInstaller), user prefs
│
├── database/
│   ├── __init__.py
│   ├── schema.py               # SQLite schema definition and indexing
│   └── db_manager.py           # Thread-safe database manager with parameterized queries
│
├── modules/
│   ├── __init__.py
│   ├── languages.py            # Extensible language profiles (Python, Java, JavaScript)
│   ├── maintenance.py          # Application Maintenance domain context & validation
│   └── deployment.py           # Application Deployment domain context & validation
│
├── prompts/
│   ├── __init__.py
│   └── troubleshooting_prompts.py # System prompt, structured schema, and prompt builder
│
├── services/
│   ├── __init__.py
│   ├── ai_service.py           # AIProvider base class, Gemini/OpenAI implementations, DemoProvider
│   ├── error_classifier.py     # Canonical category and severity normalizer & heuristic fallback
│   ├── log_processor.py        # File validation, normalization, secret redaction, truncation
│   └── workers.py              # Background QThread worker for responsive UI
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py          # Main QMainWindow, left sidebar, stacked navigation, API settings dialog
│   ├── dashboard.py            # Screen 1: Dashboard with metric cards, quick actions, recent sessions
│   ├── new_troubleshooting.py  # Screen 2: Input form, log uploader, privacy dialog, analysis trigger
│   ├── analysis_screen.py      # Screen 3: 10-section diagnostic report, markdown export, status updater
│   ├── history_screen.py       # Screen 4: Searchable table, combined filters, detail dialog, deletion
│   ├── widgets.py              # Reusable cards, badges, loading overlay, stat cards
│   └── styles.qss              # Custom Qt Style Sheet
│
├── assets/
│   └── icons/                  # Local SVG icons for offline operation (dashboard, settings, etc.)
│
└── tests/
    ├── __init__.py
    ├── test_database.py        # Automated SQLite tests (CRUD, SQL injection safety, filters)
    ├── test_log_processor.py   # Redaction patterns, normalization, truncation, signals
    ├── test_classifier.py      # Normalization and heuristic classification tests
    ├── test_ai_service.py      # JSON parsing, error mapping, DemoProvider tests
    ├── test_gui.py             # PySide6 offscreen GUI and navigation tests
    └── test_workflow.py        # End-to-end diagnosis and persistence integration tests
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** (Python 3.10, 3.11, 3.12, or 3.13)
- Windows 10/11 (or macOS / Linux)

### 2. Installation Steps

1. **Clone or navigate to the repository:**
   ```bash
   cd AI_IT_Troubleshooting_Assistant
   ```

2. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD):**
     ```cmd
     python -m venv venv
     .\venv\Scripts\activate.bat
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configuring Your AI API Key (Optional)

You can run the application with **Gemini**, **OpenAI**, or in **Demo Mode**.

#### Option A: In-App Settings Dialog (Recommended)
Launch the application and click **⚙️ API Settings** at the bottom of the left sidebar. Select your provider and paste your key. Your credentials will be saved locally in your user profile.

#### Option B: `.env` File
Create a `.env` file from `.env.example`:
```powershell
Copy-Item .env.example .env
```
Open `.env` in any text editor and fill in your key:
```env
# Choose: gemini, openai, or demo
AI_PROVIDER=gemini

# For Google Gemini (Free tier available):
# Obtain at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere

# For OpenAI:
# Obtain at: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-YourOpenAIApiKeyHere
```

#### Option C: Demo Mode (No API Key Required)
If you do not have an API key, switch the provider to **Demo Mode** in the in-app Settings dialog or run with `AI_PROVIDER=demo`. The application will provide realistic, context-aware diagnostic demonstrations offline.

---

## 🖥️ Running the Application

Launch the desktop application:
```bash
python main.py
```

The native desktop window will open with the title **"AI IT Troubleshooting Assistant"**.

---

## 🧪 Running Automated Tests

Run the complete test suite using pytest:
```bash
pytest -v
```

All 35 automated unit, GUI, and integration tests will execute and verify database operations, log redaction patterns, JSON parsing, error classifiers, and UI navigation.

---

## 🎓 College Presentation & Demonstration Guide

### Demo Scenario 1: Application Deployment (Docker Missing Dependency)
1. Launch the app and click **Application Deployment** on the Dashboard.
2. Select:
   - **Language:** `Python`
   - **Problem Type:** `Deployment` (preselected)
   - **Target Environment:** `Docker`
   - **Application / Framework:** `Flask`
3. Paste the following error into the text area:
   ```
   web_1  | Traceback (most recent call last):
   web_1  |   File "/app/server.py", line 3, in <module>
   web_1  |     import flask
   web_1  | ModuleNotFoundError: No module named 'flask'
   ```
4. Click **⚡ Analyze Problem**.
5. Observe:
   - Category is classified as **Dependency Error** with **High** severity.
   - Clear distinction between confirmed facts (ModuleNotFoundError visible) and possible hypotheses (missing in `requirements.txt` vs. Dockerfile build caching).
   - Concrete, ordered Docker commands provided for remediation.
   - Click **✓ Mark as Resolved** to record the resolution in the persistent database.

### Demo Scenario 2: Application Maintenance (Authentication Exception)
1. Click **Application Maintenance** on the Dashboard.
2. Select:
   - **Language:** `Python`
   - **Problem Type:** `Maintenance`
   - **Target Environment:** `Development`
3. Paste the following runtime error:
   ```
   [ERROR] Exception on /api/login [POST]
   Traceback (most recent call last):
     File "/app/auth.py", line 42, in login
       if not verify_password(password, user.password_hash):
   AttributeError: 'NoneType' object has no attribute 'password_hash'
   ```
4. Click **⚡ Analyze Problem**.
5. Observe:
   - Category is classified as **Runtime Error**.
   - Explanation highlights that the database query returned `None` when looking up the user, causing an unhandled attribute access.
   - Solution suggests defensive null checks before verifying credentials.

### Demo Scenario 3: Secret Redaction Verification
1. Paste an error log containing dummy sensitive data:
   ```
   Database connection failed: postgresql://admin:MySecretPass123@db:5432/app
   API Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotShareThisSecretToken
   ```
2. Click **⚡ Analyze Problem**.
3. In Screen 3, scroll to the **Original Error / Log Data** section at the bottom.
4. Verify that passwords and tokens are replaced with `[REDACTED_PASSWORD]` and `[REDACTED_BEARER_TOKEN]`.

---

## 📦 Packaging as a Windows Executable (.exe)

You can package the application into a standalone Windows executable using PyInstaller:

```powershell
pyinstaller AI_IT_Troubleshooting_Assistant.spec --noconfirm
```

The output bundle will be located in:
```
dist/AI_IT_Troubleshooting_Assistant/AI_IT_Troubleshooting_Assistant.exe
```

### Providing API Keys to the Packaged `.exe`
When sharing the executable:
1. Users do **not** need to install Python.
2. Users can supply their API key by opening the application, clicking **⚙️ API Settings**, and typing their key (or placing a `.env` file in the same directory as the executable).
3. The executable will store user settings and SQLite history in `%APPDATA%\AI_IT_Troubleshooting_Assistant\`.

---

## 🔌 How to Add New Language Profiles (e.g., C / C++)

The architecture is modular and uses language profiles. To add C or C++ support:

1. Open `modules/languages.py`.
2. Define a new `LanguageProfile`:
   ```python
   CPP_PROFILE = LanguageProfile(
       name="C++",
       display_name="C / C++",
       file_extensions=[".c", ".cpp", ".cc", ".h", ".hpp"],
       common_exceptions=[
           "Segmentation fault (core dumped)",
           "SIGSEGV",
           "undefined reference to",
           "fatal error: ... no such file or directory",
           "double free or corruption",
           "CMake Error",
       ],
       dependency_files=["CMakeLists.txt", "Makefile", "conanfile.txt", "vcpkg.json"],
       common_frameworks=["Boost", "Qt", "Catch2", "GoogleTest"],
       build_and_run_tools=["gcc", "g++", "clang", "cmake", "make", "ninja", "gdb", "valgrind"],
       troubleshooting_guidance=[
           "Inspect memory boundaries with Valgrind or AddressSanitizer (-fsanitize=address).",
           "Verify header include paths (-I flags) and linked library paths (-L and -l flags).",
           "Check CMake target_link_libraries for missing definitions causing linker errors.",
       ],
   )
   ```
3. Register the profile in `modules/languages.py`:
   ```python
   register_language_profile(CPP_PROFILE)
   ```
4. That's it! The dropdown on Screen 2, the filter on Screen 4, and the prompt injection automatically adopt the new language without touching the core engine.

---

## 🔒 Security Summary

- **Zero Arbitrary Execution:** Uploaded log files and user inputs are strictly read as text. No user input or AI suggestion is ever executed, evaluated (`eval`/`exec`), or passed to system shells.
- **Client-Side Secret Redaction:** Common credentials (API keys, passwords, bearer tokens, private keys) are scrubbed before sending data over the network.
- **SQL Injection Defense:** All SQLite interactions use parameterized queries (`?` placeholders) with strict column whitelisting for sort operations.
- **Safe Persistence:** Keys are kept in user-local directories or environment variables and are excluded from Git via `.gitignore`.
