"""AI Provider abstraction layer, implementation for Gemini, and DemoProvider."""

from __future__ import annotations

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict

from config.settings import AppConfig, settings
from prompts.troubleshooting_prompts import SYSTEM_PROMPT, build_user_prompt
from services.error_classifier import ErrorClassifier

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
DEFAULT_TIMEOUT_SECONDS = 60


class AIProviderError(Exception):
    """Base exception for AI provider failures."""


class MissingAPIKeyError(AIProviderError):
    """Raised when an API key is required but missing."""


class AuthenticationError(AIProviderError):
    """Raised when an API key is invalid or rejected."""


class RateLimitError(AIProviderError):
    """Raised when rate limit or quota is exceeded."""


class NetworkTimeoutError(AIProviderError):
    """Raised when request times out or network is unreachable."""


class MalformedResponseError(AIProviderError):
    """Raised when the AI returns unparseable output."""


class AIProvider(ABC):
    """Abstract Base Class for AI troubleshooting providers."""

    @abstractmethod
    def analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute troubleshooting analysis and return structured result dictionary."""
        raise NotImplementedError


class DemoProvider(AIProvider):
    """Simulated AI provider for offline use, testing, and college presentations."""

    def analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate high-quality context-aware troubleshooting analysis without an external API."""
        language = payload.get("programming_language") or payload.get("language", "Python")
        problem_type = payload.get("problem_type", "Automatic Detection")
        environment = payload.get("environment", "Development")
        framework = payload.get("application_framework") or payload.get("framework", "")
        error_log = payload.get("error_log", "")
        signals = payload.get("extracted_signals") or payload.get("signals", {})

        # Context-aware logic for demo mode
        is_docker = "docker" in environment.lower() or "docker" in error_log.lower()
        is_missing_flask = "flask" in error_log.lower() and (
            "modulenotfound" in error_log.lower() or "no module" in error_log.lower()
        )
        is_db = "database" in error_log.lower() or "sql" in error_log.lower() or "connection refused" in error_log.lower()
        is_login = "login" in error_log.lower() or "auth" in error_log.lower()
        is_cpp = language.lower() in ("c", "c++") or "sigsegv" in error_log.lower() or "segmentation fault" in error_log.lower()

        # Determine problem type if automatic
        if problem_type == "Automatic Detection":
            if is_docker or is_missing_flask or "deploy" in error_log.lower() or "cmake error" in error_log.lower():
                detected_type = "Deployment"
            else:
                detected_type = "Maintenance"
        else:
            detected_type = ErrorClassifier.normalize_problem_type(problem_type)

        if is_cpp and ("segmentation fault" in error_log.lower() or "sigsegv" in error_log.lower()):
            category = "Runtime Error"
            severity = "Critical"
            summary = "SIGSEGV: Segmentation fault (core dumped) in memory pointer dereference"
            reasoning = "Critical memory access violation within compiled native application code."
            explanation = (
                f"The {language} application crashed with a Segmentation Fault (SIGSEGV). This occurs when a thread attempts "
                "to read or write an unallocated, protected, or already-freed virtual memory address (such as dereferencing a NULL pointer, "
                "exceeding an array boundary, or accessing an object after calling free/delete)."
            )
            confirmed_facts = [
                "Process terminated abnormally with SIGSEGV (signal 11).",
                f"Programming language: {language}.",
                "Core dump generated or fatal segmentation fault reported by kernel.",
            ]
            possible_causes = [
                "Dereferencing a NULL or uninitialized pointer.",
                "Buffer overrun writing past allocated heap/stack array bounds.",
                "Use-after-free (accessing memory after free() or delete).",
                "Stack overflow from excessive recursion or large stack-allocated arrays.",
            ]
            troubleshooting_steps = [
                "1. Recompile with debug symbols and AddressSanitizer: gcc/g++ -g -fsanitize=address,undefined -O1 main.cpp -o app",
                "2. Run under GDB to locate the exact crashing line: gdb ./app -> run -> backtrace (bt)",
                "3. Alternatively run under Valgrind: valgrind --leak-check=full --track-origins=yes ./app",
                "4. Check all pointers for NULL before dereferencing, and replace raw pointers with smart pointers (std::unique_ptr).",
            ]
            suggested_solution = (
                "// Replace unsafe raw pointer dereference with null check or smart pointer:\n"
                "if (ptr != nullptr) {\n"
                "    ptr->execute();\n"
                "} else {\n"
                "    // Handle null state gracefully\n"
                "    std::cerr << \"Warning: Pointer is null!\" << std::endl;\n"
                "}"
            )
            verification_steps = [
                "Compile with -fsanitize=address and execute with test inputs.",
                "Confirm AddressSanitizer reports no heap-use-after-free or null-dereference errors.",
                "Run test suite through Valgrind to ensure 0 memory leaks and clean exit code 0.",
            ]
        elif is_cpp and ("undefined reference" in error_log.lower() or "cmake" in error_log.lower()):
            category = "Build Error"
            severity = "High"
            summary = f"Linker / CMake build error: Undefined reference or unresolved external symbol in {language}"
            reasoning = "Build pipeline failed during linking or configuration generation phase."
            explanation = (
                f"The compiler was able to find the declarations (headers), but the linker (ld) could not locate the "
                "compiled object definitions or external library archives required to produce the final executable."
            )
            confirmed_facts = [
                "Linker failed to resolve referenced function or symbol.",
                f"Build system: CMake / Make with {language}.",
            ]
            possible_causes = [
                "The source file implementing the function was omitted from CMakeLists.txt add_executable/add_library.",
                "Missing library in target_link_libraries (e.g. -lpthread, -lssl, -lsqlite3).",
                "C++ name mangling mismatch when linking C code without extern \"C\" wrappers.",
            ]
            troubleshooting_steps = [
                "1. Check CMakeLists.txt to verify all .cpp/.c files are listed in add_executable().",
                "2. Add the required dependency to target_link_libraries(my_target PRIVATE LibName).",
                "3. If including a C header from C++, wrap the include in: extern \"C\" { #include \"header.h\" }",
                "4. Clean your build directory and reconfigure: rm -rf build && cmake -B build && cmake --build build",
            ]
            suggested_solution = (
                "# Example fix in CMakeLists.txt:\n"
                "add_executable(myapp main.cpp service.cpp utils.cpp)\n"
                "find_package(OpenSSL REQUIRED)\n"
                "target_link_libraries(myapp PRIVATE OpenSSL::SSL OpenSSL::Crypto)"
            )
            verification_steps = [
                "Re-run 'cmake --build build' and confirm 100% build completion without linker errors.",
                "Run the resulting executable to verify startup.",
            ]
        elif is_missing_flask and (is_docker or detected_type == "Deployment"):
            category = "Dependency Error"
            severity = "High"
            summary = "ModuleNotFoundError: No module named 'flask' in Docker container"
            reasoning = "The application fails during container startup due to a missing runtime dependency in the target environment."
            explanation = (
                "The application attempted to import Flask ('import flask'), but the Flask library is not installed "
                "or not available in the active Python site-packages of the Docker container environment. "
                "While the application may work on your local development machine where Flask is installed, "
                "the container image was built without installing Flask or was built with a different Python path."
            )
            confirmed_facts = [
                "ModuleNotFoundError: No module named 'flask' was raised at runtime.",
                f"Target environment is {environment}.",
                "Python interpreter attempted module resolution and failed to find 'flask'.",
            ]
            possible_causes = [
                "Flask is missing from 'requirements.txt' or dependency manifest.",
                "Dockerfile is missing 'RUN pip install -r requirements.txt' or the step was skipped by cache.",
                "In a multi-stage Docker build, installed packages from the builder stage were not copied to the final runner image.",
                "Container CMD/ENTRYPOINT is invoking a system Python rather than the virtual environment where dependencies were installed.",
            ]
            troubleshooting_steps = [
                "1. Check your requirements.txt or pyproject.toml to ensure 'Flask>=3.0.0' is explicitly listed.",
                "2. Verify your Dockerfile has: COPY requirements.txt . followed by RUN pip install --no-cache-dir -r requirements.txt.",
                "3. Inspect the built image dependencies by running: docker run --rm <image_name> pip list | grep -i flask",
                "4. Check if a virtual environment is used inside Docker and verify PATH includes /opt/venv/bin.",
                "5. Force a clean rebuild without cache: docker build --no-cache -t myapp:latest .",
            ]
            suggested_solution = (
                "# 1. Add to requirements.txt:\n"
                "Flask>=3.0.0\n\n"
                "# 2. Ensure your Dockerfile includes:\n"
                "COPY requirements.txt .\n"
                "RUN pip install --no-cache-dir -r requirements.txt\n"
                "COPY . .\n"
                "CMD [\"python\", \"app.py\"]"
            )
            verification_steps = [
                "Run 'docker run --rm <image_name> python -c \"import flask; print(flask.__version__)\"' to confirm Flask is present.",
                "Start the container with 'docker run -p 5000:5000 <image_name>' and verify clean startup logs without tracebacks.",
                "Send an HTTP request via curl or browser to http://localhost:5000/ to confirm the service responds.",
            ]
        elif is_login or (detected_type == "Maintenance" and "auth" in error_log.lower()):
            category = "Runtime Error"
            severity = "High"
            summary = "User Authentication / Login service failure during request processing"
            reasoning = "Occurs in application business logic while validating user credentials."
            explanation = (
                "The application encountered an unhandled exception or data mismatch during the login sequence. "
                "This typically happens when user password hashing fails, a user record cannot be found in the database, "
                "or a JWT/session signing token secret key is missing."
            )
            confirmed_facts = [
                "Exception triggered during authentication execution flow.",
                f"Language profile: {language}; Framework: {framework or 'Standard'}.",
            ]
            possible_causes = [
                "Database query returned None when looking up user, causing an unhandled AttributeError or NullPointerException.",
                "Secret key for session/JWT hashing is missing or empty in environment configuration.",
                "Password comparison algorithm threw a type mismatch (bytes vs string comparison).",
            ]
            troubleshooting_steps = [
                "1. Add defensive null/None checks before accessing user password hash properties.",
                "2. Verify SECRET_KEY or JWT_SECRET is set in your .env or configuration provider.",
                "3. Enable debug-level application logs around the login authentication route.",
                "4. Test authentication with a known seed user in your test suite.",
            ]
            suggested_solution = (
                "# Example defensive check in login handler:\n"
                "user = db.find_user_by_email(email)\n"
                "if not user:\n"
                "    return {'error': 'Invalid credentials'}, 401\n"
                "if not verify_password(password, user.password_hash):\n"
                "    return {'error': 'Invalid credentials'}, 401"
            )
            verification_steps = [
                "Run unit/integration tests for authentication routes.",
                "Attempt login with valid credentials and verify 200 OK with session/token.",
                "Attempt login with invalid credentials and verify graceful 401 Unauthorized without 500 server crash.",
            ]
        else:
            # Generic smart fallback
            category = ErrorClassifier.fallback_classify(payload)
            severity = "Medium"
            summary = f"{category} detected in {language} ({environment})"
            reasoning = f"Context points toward {detected_type} based on application runtime behavior in {environment}."
            explanation = (
                f"The application encountered a {category.lower()} while executing {language} code. "
                "Review the confirmed signals and follow the recommended troubleshooting steps below to diagnose and resolve."
            )
            confirmed_facts = [
                f"Language: {language}",
                f"Target Environment: {environment}",
                f"Primary detected signals: {', '.join(signals.get('exceptions', ['Standard error output']))}",
            ]
            possible_causes = [
                f"Application configuration mismatch for {environment}.",
                "Unhandled edge case in recent code changes or input data.",
                "Missing environment variable or dependency version discrepancy.",
            ]
            troubleshooting_steps = [
                "1. Inspect the stack trace frames closest to your application code.",
                "2. Verify all required environment variables are set in your local .env or configuration file.",
                "3. Check application logs immediately preceding the failure for relevant warning indicators.",
                "4. Reproduce the error in isolation using an automated test case or REPL session.",
            ]
            suggested_solution = (
                "Review the error line indicated in the stack trace, verify configuration variables, "
                "and ensure clean dependency isolation."
            )
            verification_steps = [
                "Re-run the failing command or scenario.",
                "Check system and application logs to ensure no remaining errors are reported.",
            ]

        return {
            "error_summary": summary,
            "detected_problem_type": detected_type,
            "detection_reasoning": reasoning,
            "error_category": category,
            "severity": severity,
            "explanation": explanation,
            "confirmed_facts": confirmed_facts,
            "possible_causes": possible_causes,
            "troubleshooting_steps": troubleshooting_steps,
            "suggested_solution": suggested_solution,
            "verification_steps": verification_steps,
            "assumptions_or_notes": "[DEMO MODE - not real AI analysis] Simulated analysis generated for demonstration.",
            "is_demo": True,
            "ai_provider": "demo",
            "ai_model": "offline-demo-engine",
        }


class GeminiProvider(AIProvider):
    """Google Gemini AI implementation using google-genai SDK."""

    def __init__(self, api_key: str, model_name: str = DEFAULT_GEMINI_MODEL, timeout: int = DEFAULT_TIMEOUT_SECONDS):
        if not api_key:
            raise MissingAPIKeyError("Gemini API key is missing. Set GEMINI_API_KEY in .env or the Settings dialog.")
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout

    def analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call Gemini API requesting structured JSON output with automatic model fallback."""
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise AIProviderError("google-genai library is not installed.")

        user_prompt = build_user_prompt(
            language=payload.get("programming_language") or payload.get("language", "Python"),
            problem_type=payload.get("problem_type", "Automatic Detection"),
            environment=payload.get("environment", "Development"),
            framework=payload.get("application_framework") or payload.get("framework", ""),
            redacted_log=payload.get("error_log", ""),
            signals=payload.get("extracted_signals") or payload.get("signals", {}),
        )

        # Build prioritized list of models to try
        candidates = []
        clean_model = (self.model_name or "").strip()
        if clean_model:
            candidates.append(clean_model)
        candidates.extend([
            "gemini-3.8-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.7-flash",
            "gemini-3.5-flash",
            "gemma-4-26b-a4b-it",
            "gemini-2.5-flash",
        ])
        # Deduplicate while preserving order
        models_to_try = list(dict.fromkeys(candidates))

        try:
            client = genai.Client(api_key=self.api_key, http_options={"api_version": "v1beta"})
        except Exception as e:
            raise AuthenticationError(f"Failed to initialize Gemini Client: {e}")

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.2,
        )

        last_exception: Exception | None = None
        for model in models_to_try:
            try:
                logger.info("Calling Gemini API with model: %s", model)
                response = client.models.generate_content(
                    model=model,
                    contents=user_prompt,
                    config=config,
                )

                raw_text = ""
                if hasattr(response, "text") and response.text:
                    raw_text = response.text
                elif hasattr(response, "candidates") and response.candidates:
                    for cand in response.candidates:
                        if cand.content and cand.content.parts:
                            for part in cand.content.parts:
                                if hasattr(part, "text") and part.text:
                                    raw_text += part.text

                if not raw_text.strip():
                    raise MalformedResponseError("Gemini returned an empty response.")

                return AIService.parse_and_validate_json(raw_text, payload, provider="gemini", model=model)

            except Exception as e:
                error_msg = str(e)
                last_exception = e

                # If model is not found (404) or temporarily overloaded (503 / high demand), try the next candidate
                if any(k in error_msg.lower() or k in type(e).__name__.lower() for k in ("404", "not found", "503", "unavailable", "high demand", "temporarily")):
                    logger.warning("Gemini model '%s' unavailable (%s). Attempting fallback to next model...", model, error_msg)
                    time.sleep(0.5)
                    continue

                # Authentication / Key errors
                if "API_KEY_INVALID" in error_msg or "400" in error_msg or "401" in error_msg or "api key not valid" in error_msg.lower() or "authentication" in error_msg.lower():
                    raise AuthenticationError(
                        f"Invalid Gemini API key. Please verify your key at https://aistudio.google.com/app/apikey.\nDetails: {error_msg}"
                    )

                # Rate Limit / Quota
                if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg or "quota" in error_msg.lower():
                    raise RateLimitError(
                        f"Gemini API rate limit or quota exceeded. Free tier accounts have rate limits (15 RPM). Please wait a moment and retry.\nDetails: {error_msg}"
                    )

                # Network / Timeout
                if "ConnectError" in type(e).__name__ or "getaddrinfo failed" in error_msg or "DEADLINE_EXCEEDED" in error_msg or "timeout" in error_msg.lower():
                    raise NetworkTimeoutError(
                        f"Network connection to Google Gemini API failed. Please check your internet connection.\nDetails: {error_msg}"
                    )

                raise AIProviderError(f"Gemini API Error: {error_msg}")

        if last_exception:
            raise AIProviderError(f"Gemini API Error across attempted models: {last_exception}")
        raise AIProviderError("Gemini analysis failed.")


class AIService:
    """Orchestrates AI troubleshooting requests, JSON parsing, validation, and fallbacks."""

    @classmethod
    def get_provider(cls, cfg: AppConfig | None = None) -> AIProvider:
        """Instantiate the configured provider or raise MissingAPIKeyError."""
        cfg = cfg or settings
        effective = cfg.get_effective_provider()

        if effective == "demo":
            return DemoProvider()

        if effective == "gemini":
            if not cfg.gemini_api_key:
                raise MissingAPIKeyError("Gemini API key is not configured.")
            return GeminiProvider(
                api_key=cfg.gemini_api_key,
                model_name=cfg.gemini_model,
                timeout=cfg.ai_timeout_seconds,
            )

        return DemoProvider()

    @classmethod
    def extract_json_object(cls, text: str) -> str:
        """Strip markdown code fences and locate the first balanced JSON object."""
        cleaned = text.strip()

        # Remove markdown code fences like ```json ... ``` or ``` ... ```
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()

        # Find first '{' and matching '}'
        start_idx = cleaned.find("{")
        if start_idx == -1:
            raise MalformedResponseError("No JSON object '{' found in response.")

        # Balanced brace search
        brace_count = 0
        in_string = False
        escape = False
        end_idx = -1

        for i in range(start_idx, len(cleaned)):
            c = cleaned[i]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if not in_string:
                if c == "{":
                    brace_count += 1
                elif c == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break

        if end_idx != -1:
            return cleaned[start_idx:end_idx]

        return cleaned[start_idx:]

    @classmethod
    def parse_and_validate_json(
        cls,
        raw_text: str,
        payload: Dict[str, Any],
        provider: str = "ai",
        model: str = "default",
    ) -> Dict[str, Any]:
        """Defensively parse raw text, validate required fields, and normalize categories."""
        json_str = cls.extract_json_object(raw_text)

        try:
            data = json.loads(json_str)
        except Exception as e:
            raise MalformedResponseError(f"Failed to parse JSON: {e}\nRaw output: {raw_text[:200]}")

        if not isinstance(data, dict):
            raise MalformedResponseError("AI response is not a valid JSON dictionary.")

        # Normalize category
        raw_category = data.get("error_category")
        canonical_category, _ = ErrorClassifier.normalize_category(raw_category, context=payload)
        data["error_category"] = canonical_category

        # Normalize severity
        data["severity"] = ErrorClassifier.normalize_severity(data.get("severity"), context=payload)

        # Normalize problem type
        detected = data.get("detected_problem_type")
        orig_problem_type = payload.get("problem_type", "Maintenance")
        if orig_problem_type == "Automatic Detection":
            data["detected_problem_type"] = ErrorClassifier.normalize_problem_type(detected, default="Maintenance")
        else:
            data["detected_problem_type"] = ErrorClassifier.normalize_problem_type(orig_problem_type)

        # Ensure required keys exist with safe defaults
        data.setdefault("error_summary", data.get("summary") or "Application Error Detected")
        data.setdefault("detection_reasoning", "Classified based on contextual signals and error characteristics.")
        data.setdefault("explanation", "An error was encountered during execution.")

        # Ensure list fields are valid lists of strings
        for list_field in ("confirmed_facts", "possible_causes", "troubleshooting_steps", "verification_steps"):
            val = data.get(list_field)
            if isinstance(val, list):
                data[list_field] = [str(item) for item in val if str(item).strip()]
            elif isinstance(val, str) and val.strip():
                data[list_field] = [val.strip()]
            else:
                data[list_field] = [f"No specific {list_field.replace('_', ' ')} provided."]

        data.setdefault("suggested_solution", "Review the troubleshooting steps and apply necessary configuration or code changes.")
        data.setdefault("assumptions_or_notes", "")

        data["is_demo"] = False
        data["ai_provider"] = provider
        data["ai_model"] = model

        return data

    @classmethod
    def execute_analysis(cls, payload: Dict[str, Any], cfg: AppConfig | None = None) -> Dict[str, Any]:
        """Execute the end-to-end analysis pipeline using the active provider with defensive retry."""
        provider = cls.get_provider(cfg)

        max_attempts = 2
        last_error: Exception | None = None

        for attempt in range(max_attempts):
            try:
                result = provider.analyze(payload)
                return result
            except (MalformedResponseError,) as e:
                last_error = e
                time.sleep(1.0)
            except Exception as e:
                raise e

        if last_error:
            raise last_error
        raise AIProviderError("Analysis execution failed.")

    @classmethod
    def test_connection(cls, provider: str, api_key: str, model_name: str = "") -> tuple[bool, str]:
        """Test API key and model connectivity for the chosen provider."""
        provider = (provider or "").lower().strip()
        key = (api_key or "").strip()

        if provider == "demo":
            return True, "Demo Mode is active. Works 100% offline without an external API."

        if not key:
            return False, f"API key for {provider.title()} is empty. Please enter your key."

        if provider == "gemini":
            try:
                from google import genai
                client = genai.Client(api_key=key, http_options={"api_version": "v1beta"})
                target_model = model_name.strip() if model_name.strip() else "gemini-3.8-flash"
                test_candidates = [target_model, "gemini-3.5-flash-lite", "gemini-3.7-flash", "gemini-3.5-flash", "gemma-4-26b-a4b-it"]
                test_candidates = list(dict.fromkeys(test_candidates))

                last_err = None
                for candidate in test_candidates:
                    try:
                        response = client.models.generate_content(
                            model=candidate,
                            contents="Respond with the single word: OK",
                        )
                        return True, f"Connection successful! Model '{candidate}' responded properly."
                    except Exception as model_err:
                        err_str = str(model_err)
                        last_err = model_err
                        if any(k in err_str.lower() for k in ("404", "not found", "503", "unavailable", "high demand")):
                            continue
                        raise model_err
                if last_err:
                    raise last_err

            except Exception as e:
                err = str(e)
                if "API_KEY_INVALID" in err or "400" in err or "api key not valid" in err.lower():
                    return False, "Invalid API key. Check or create a key at https://aistudio.google.com/app/apikey"
                if "ConnectError" in type(e).__name__ or "getaddrinfo failed" in err:
                    return False, "Network error: Unable to connect to Google API servers. Check your internet connection."
                if "RESOURCE_EXHAUSTED" in err or "429" in err:
                    return False, "Rate limit reached for this key. Please wait a moment and try again."
                return False, f"Gemini connection failed: {err}"

        return False, f"Unsupported provider: {provider}"
