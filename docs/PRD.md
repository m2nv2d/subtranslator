# Product Purpose & Vision
We’re building a minimal Flask‑based web app that lets a user upload an SRT subtitle file, choose a target language and “translation speed” (fast vs. normal), and download a correctly formatted, translated SRT. The app is purely for personal/educational use—no multi‑tenant scaling or user accounts—just a lightweight tool for anyone who needs quick subtitle translation.

# Goals & Success Criteria
1. Functional
   - User can upload a valid .srt ≤2 MB, choose a target language (from a configurable dropdown) and speed mode (“fast” or “normal”), and click “Translate.”
   - The app returns a valid translated .srt with the original timestamps intact and filename appended with `_vi`.
   - Any translation failure yields a generic error message.
2. UX
   - Single‑page interface with an uncluttered, industrial‑style look (vanilla CSS).
   - Status line shows “Translating…” while processing; button is disabled.
3. Quality
   - All translated chunks must retry on transient LLM errors (exponential backoff, max attempts), or else abort and inform the user.
   - Subtitle parsing and reassembly preserve block indexes and timestamps exactly.
4. Technical
   - Implements context‑aware chunking via srt and async API calls.
   - Configuration (API keys, language list) via `.env` files.

# Target Users & Stakeholders
- Primary users
  • Language learners, hobbyist translators, educators who need quick subtitle translation.
  • Need: Simple, fast tool with minimal friction.
- Secondary stakeholders
  • You (maintainer/learner)—want to practice Flask async flows, SRT parsing, LLM integration.

# Core Features
1. File Upload & Validation
   - Accept only `.srt` files ≤2 MB.
   - Reject invalid files or oversized uploads with a friendly error.
2. Settings Controls
   - Target language dropdown (configurable list).
   - Translation speed toggle: “Fast” or “Normal” (mapped internally to different LLM models).
3. Context Analysis
   - On upload, take first ~200 lines and send to LLM to detect video topic (drama, cooking, etc.).
4. Chunked Translate Pipeline
   - Parse full SRT with srt into blocks/chunks.
   - For each chunk, call an API‑helper (handles model choice, authentication, retries) asynchronously to translate.
   - Merge returned JSON (“index”:translated_text) back into blocks.
5. Output Generation
   - Reassemble only the translated text blocks into a valid SRT, preserving original timestamps and indexes.
   - Trigger browser download with original name + `_vi.srt`.
6. Error Handling & Status
   - Disable “Translate” while processing; display “Translating…” status.
   - On persistent chunk failure (after retries), abort and show a generic error banner.

# User Experience
- Persona: Ana, a language‑learning enthusiast who wants to read subtitles in her native tongue.
- Key Flow:
   1. Open `/` page → sees upload form with file chooser, language dropdown, speed toggle, and “Translate” button.
   2. Chooses file, language, speed → clicks “Translate.”
   3. Button disables; status line reads “Translating…”
   4. After a few seconds/minutes, browser download prompt for `original_vi.srt`.
   5. If an error occurs, status line changes to “Translation failed. Please try again.”
- UI/UX considerations:
   • Single responsive column layout.
   • Vanilla CSS for a clean, industrial feel—no heavy frameworks.

# High-Level Functional Requirements
1. The system shall serve a single Flask/Jinja2 page at `/`.
2. The system shall validate file extension `.srt` and size ≤ 2 MB.
3. The system shall read `.env` for API keys and available target languages.
4. The system shall parse the SRT with srt into chunked data structures.
5. The system shall asynchronously invoke an “API helper” per chunk, passing: chunk text, chunk indexes, detected context, target language, speed mode.
6. The system shall retry failed chunk translations with exponential backoff (configurable max attempts).
7. The system shall abort all processing and display a generic error on persistent failures.
8. The system shall reassemble translated blocks into a valid SRT with original timestamps and indexes.
9. The system shall deliver the translated SRT for download, appending `_vi` before the file extension.

# Out-of-Scope Functionality
- Supporting file types other than .srt.
- User authentication or accounts.
- Real‑time progress bars or per‑chunk status.
- Styling beyond basic industrial CSS.
- Performance SLAs or horizontal scaling.
- Alternative front‑end frameworks (React, Vue, etc.).

# Constraints & Assumptions
- Platform: Linux development environment.
- Language: Python (Flask) for backend, vanilla JS/CSS + Jinja2 for frontend.
- Package managers: `uv` for Python, `pnpm` if any JS dependencies.
- LLM integration via an external “API helper” module; authentication through `.env`.
- Use srt for parsing; assume input SRTs are well‑formed UTF‑8.
- Max subtitle file size is 2 MB.
- Only “fast” and “normal” speed modes exposed to the user—mapping hidden in helper.
- No explicit user‑facing progress indicator beyond a status line.
