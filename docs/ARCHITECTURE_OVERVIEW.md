# 1. Introduction
We’re building a minimal Flask‑based subtitle‑translation web app. A user uploads an SRT, picks a target language and speed mode, and downloads a correctly formatted, translated SRT. This document describes the system’s major components, their interactions, and the key architectural choices that make it work.

# 2. System Context
**Project Scope**
• IN‑SCOPE:
  – A single‑page Flask app (Jinja2 + vanilla JS/CSS) for uploading, translating, and downloading SRT files (≤2 MB).
  – Server‑side parsing (srt), context detection, chunked translation via a LLM helper, reassembly of subtitles, and file streaming back to the browser.
• OUT‑OF‑SCOPE:
  – Any file formats other than .srt.
  – User accounts, authentication, multi‑tenant or real‑time progress UI beyond a status line.
  – Horizontal scaling, CI/CD pipelines, containerization, or advanced monitoring.

**External Systems / Integrations**
• LLM Service (generic): called via a custom “LLM helper” module. Endpoint, model names, and API keys are configured in `.env`.
• srt library: used for parsing and reassembling SRTs.
• python‑dotenv: for configuration loading.

# 3. High‑Level Architecture Diagram

Browser
│ 1. Upload file + settings
▼
Flask App (single process)
├─ Route `/` (GET): serves Jinja2 template + JS/CSS
├─ Route `/translate` (POST):
│   • Validate file (ext, size)
│   • Read content → in‑memory
│   • Parse blocks via srt
│   • Extract first ~100 lines → Context Detector → call LLM helper → “video topic”
│   • Chunk Translator (async): for each chunk
│   │    • call LLM helper (target_lang, speed, relative index, lines)
│   │    • retry with backoff on transient errors
│   └─ await all results → merge into blocks
│   • Reassemble .srt with original timestamps/indexes
│   • Return as `attachment; filename_original_vi.srt`
└─ Static: vanilla CSS + JS

# 4. Technology Stack
- Languages
  • Python 3.9+ (Flask)
  • JavaScript (ES6+)
- Frameworks/Libraries
  • Flask + Jinja2
  • srt (subtitle parsing)
  • python‑dotenv (config)
- Databases/Storage
  • None persistent—uploads processed in memory only.
- Other Infrastructure
  • Hosted on a Linux VM (no containerization)
  • Run via Flask’s built‑in server or a simple WSGI server (e.g. Gunicorn)
  • No CI/CD or log aggregation; console‑based logging only.

# 5. Key Architectural Decisions
- **Flask + Jinja2**: minimal, easy to deploy, synchronous endpoint wrapping async translation operations.
- **srt**: robust SRT parsing and reassembly, preserves original timestamps/indexes.
- **Async chunked translation**: use Python async/await + user-built helpers to parallelize LLM calls and adhere to speed‑mode SLAs.
- **LLM helper modules**: centralizes LLM authentication, model selection (fast vs. normal), retry logic (exponential backoff), and error categorization.
- **In‑memory processing**: avoids disk I/O for simplicity and security. All upload content lives in RAM and is discarded after response.
- **Environment‑based config**: `.env` for API keys, endpoint URLs, language list—no hard‑coding.

# 6. Major System Components
1. **Web Frontend**
   - Purpose: single‑page UI for upload form, settings, and status line.
   - Interfaces: HTML form POST → `/translate`; JS listens for response and triggers download or error banner.
2. **Upload Validator**
   - Purpose: enforce `.srt` extension and ≤2 MB.
   - Interfaces: invoked early in `/translate` handler; raises HTTP 400 on failure.
3. **SRT Parser & Chunker**
   - Purpose: parse the raw SRT into blocks, chunk into manageable sizes.
   - Interfaces: internal function calls to srt, returns list of block objects.
4. **Context Detector**
   - Purpose: examine first ~100 lines of text and call LLM helper to get a video topic hint.
   - Interfaces: calls `detect_context(text_chunk)`.
5. **Chunk Translator**
   - Purpose: translate each chunk in parallel.
   - Interfaces: for each chunk, calls `translate_chunk({ target_lang, mode, index, lines })`. Uses asyncio.gather with retry wrapper.
6. **API Helper Module**
   - Purpose: abstract LLM provider calls, handle authentication, model selection, exponential‑backoff retries, and error handling.
   - Interfaces: HTTP calls to external LLM endpoint configured via `.env`.
7. **SRT Reassembler**
   - Purpose: merge translated texts into blocks, reserialize to valid .srt.
   - Interfaces: internal function, outputs a bytes or string stream for HTTP response.
8. **Config Loader**
   - Purpose: load `.env` at startup for API keys, language list, endpoints, retry settings.
   - Interfaces: python‑dotenv + os.environ.

# 7. Data Flow & State Management
1. Browser → Flask (`/translate`)
2. Flask reads file into memory → srt parse → list of blocks
3. First 100 lines → Context Detector → LLM API → context label
4. Chunk Translator:
   • Spawn async tasks for each chunk → LLM API calls via helper → retries on transient failure
   • Gather translated texts → if any chunk hits max retries, abort entire flow
5. SRT Reassembler merges blocks → returns HTTP response as attachment
6. Temporary state lives only in request scope; no database or filesystem persistence.

# 8. Security & Privacy Considerations
- Validate and reject invalid/oversized uploads to prevent DOS.
- Process everything in memory; do not persist user data.
- Do not log sensitive content or API keys.
- Trust boundary: all user uploads are untrusted; sanitize only by limiting size and extension.

# 9. Scalability & Reliability
- Single‑instance, CPU‑bound by async HTTP calls to LLM.
- Reliability bolstered by exponential‑backoff retries.
- No horizontal scaling or clustering planned.

# 10. Other Cross‑Cutting Concerns
- **Logging**: Python’s standard logging to console (INFO for flow steps, ERROR for failures).
- **Error Handling**: generic user‑facing errors; detailed traces only in server logs.
- **Configuration**: all env vars validated at startup.
- **Assets**: static vanilla CSS + JS; no build step beyond serving files from Flask.
