# System Overview

## System Architecture

The Subtranslator application follows a **layered monolithic architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   index.html    │  │    app.js       │  │   style.css  │ │
│  │ (Jinja2 Template)│  │ (Client Logic)  │  │  (Styling)   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    main.py                              │ │
│  │        • Application Bootstrap                          │ │
│  │        • Static File Mounting                          │ │
│  │        • Exception Handlers                            │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  routers/translate.py                   │ │
│  │        • Route Handlers (/, /translate, /stats)        │ │
│  │        • Request Orchestration                          │ │
│  │        • Response Generation                            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Business Logic Layer                        │
│  ┌──────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Parser     │  │ Context Detector│  │ Chunk Translator│ │
│  │              │  │                 │  │                 │ │
│  └──────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌──────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Reassembler  │  │   Statistics    │  │  Configuration  │ │
│  │              │  │     Store       │  │                 │ │
│  └──────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               External Integration Layer                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                Google Gemini API                        │ │
│  │        • Context Detection Requests                     │ │
│  │        • Translation Requests                           │ │
│  │        • Structured JSON Response Parsing              │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Frontend Components
- **index.html**: Jinja2 template providing user interface for file upload, language selection, and status display
- **app.js**: Client-side JavaScript handling form submission, validation, progress feedback, and file downloads
- **style.css**: Visual styling and responsive layout for the web interface

### API Layer Components
- **main.py**: FastAPI application entry point, configures middleware, static files, and global exception handlers
- **routers/translate.py**: Route handlers for core functionality (homepage, translation, statistics)

### Core Business Logic Components
- **translator/parser.py**: SRT file validation, parsing into structured blocks, and chunking for processing
- **translator/context_detector.py**: AI-powered context detection to improve translation quality
- **translator/chunk_translator.py**: Concurrent translation of subtitle chunks with retry logic
- **translator/reassembler.py**: Reconstruction of translated blocks into valid SRT format
- **core/stats.py**: In-memory statistics tracking for monitoring and performance analysis
- **core/config.py**: Configuration management using Pydantic Settings with environment variable support
- **core/providers.py**: AI provider abstraction layer supporting multiple backends (Google Gemini, Mock)
- **core/rate_limiter.py**: Session-based rate limiting for file upload abuse prevention

### Support Components
- **core/dependencies.py**: FastAPI dependency injection providers for settings, AI providers, semaphores, and rate limiters
- **core/errors.py**: Standardized error response models and utility functions
- **translator/exceptions.py**: Custom exception hierarchy for domain-specific error handling
- **translator/models.py**: Data models and DTOs for subtitle blocks and translation responses
- **translator/gemini_helper.py**: Google Gemini API client initialization and management

## Tech Stack Summary

### Backend Technologies
- **Runtime**: Python 3.11+ (leveraging async/await, TaskGroup, ExceptionGroups)
- **Web Framework**: FastAPI (ASGI-based, high-performance, automatic OpenAPI documentation)
- **Template Engine**: Jinja2 (server-side HTML rendering)
- **ASGI Server**: Uvicorn (production-ready async server)
- **Configuration**: Pydantic Settings (type-safe environment variable handling)
- **Concurrency**: asyncio (native Python async runtime)
- **Retry Logic**: Tenacity (configurable retry decorators)
- **File Operations**: aiofiles (asynchronous file I/O)

### External Services
- **AI Translation**: Multi-provider support via abstraction layer
  - Google Generative AI (Gemini) via `google-genai` SDK (production)
  - Mock provider with configurable delays (development/testing)
- **Session Management**: Starlette SessionMiddleware with UUID-based session IDs
- **Subtitle Processing**: `srt` library (parsing and generation of SubRip format)
- **Security**: Werkzeug utilities (secure filename handling)

### Frontend Technologies
- **Client-Side**: Vanilla JavaScript (ES6+, no frameworks)
- **Styling**: CSS3 (responsive design, no preprocessors)
- **HTML**: HTML5 with semantic markup

### Development Tools
- **Dependency Management**: uv (fast Python package manager)
- **Testing**: pytest with pytest-asyncio (unit and integration testing)
- **Static Analysis**: Built-in Python type hints with Pydantic validation

## Design Rationale

### Architectural Decisions

**Monolithic Architecture**: Chosen for simplicity and ease of deployment. The application scope is well-defined and doesn't require microservices complexity.

**FastAPI Framework**: Selected for its excellent async support, automatic API documentation, built-in dependency injection, and strong type safety with Pydantic integration.

**Dependency Injection**: Leverages FastAPI's DI system for clean separation of concerns, easier testing, and centralized configuration management.

**Provider Abstraction**: AI services are abstracted behind a common interface, enabling easy switching between production (Gemini) and development (Mock) providers without code changes.

**Session-Based Rate Limiting**: Implements user session tracking with configurable file upload limits to prevent abuse while maintaining usability for legitimate users.

**Async-First Design**: All I/O operations (file handling, API calls, concurrent processing) use async/await patterns for optimal performance under load.

**In-Memory Processing**: Subtitle data is processed entirely in memory after initial file upload, minimizing disk I/O and improving performance.

**Stateful Session Management**: Uses session middleware for rate limiting while maintaining stateless design for translation processing.

### Performance Optimizations

**Concurrent Translation**: Uses `asyncio.TaskGroup` to translate multiple subtitle chunks simultaneously, dramatically reducing total processing time.

**Semaphore-Based Throttling**: Global semaphore prevents overwhelming the external API or system resources while maintaining high throughput.

**Chunked Processing**: Large subtitle files are broken into configurable chunks, enabling parallel processing and better memory management.

**Resource Cleanup**: Explicit try/finally blocks ensure temporary files are always cleaned up, preventing resource leaks.

### Quality Assurance

**Strong Typing**: Extensive use of Python type hints and Pydantic models for compile-time error detection and runtime validation.

**Structured Error Handling**: Custom exception hierarchy with appropriate HTTP status code mapping provides clear error feedback.

**Input Validation**: Multiple layers of validation (client-side, server-side, Pydantic models) prevent invalid data from entering the system.

**Retry Logic**: Configurable retry mechanisms handle transient API failures gracefully.

### Security Considerations

**Input Sanitization**: Secure filename handling and file size limits prevent common upload vulnerabilities.

**Environment-Based Secrets**: API keys and sensitive configuration stored in environment variables, never in code.

**Minimal Attack Surface**: Stateless design with no user accounts reduces potential security vectors.

**Error Information Disclosure**: Careful error message design prevents leaking internal system details to users.

## Data Flow Architecture

### Request Processing Pipeline

1. **Client Request**: Browser sends multipart form data to `/translate` endpoint
2. **Session Validation**: Middleware ensures session ID exists, creates if missing
3. **Rate Limiting**: Check session file upload count against configured limit
4. **Input Validation**: Server validates file format, size, language, and speed mode
5. **Provider Initialization**: AI provider (Gemini/Mock) initialized via dependency injection
6. **Temporary Storage**: File is saved to temporary directory with secure naming
7. **Statistics Initialization**: Request tracking entry created in statistics store
8. **Parsing Phase**: SRT file parsed into structured blocks and chunked
9. **Context Detection**: AI provider analyzes sample content to determine context
10. **Translation Phase**: Chunks processed concurrently with semaphore limiting
11. **Reassembly**: Translated blocks reconstructed into valid SRT format
12. **Response**: Translated file streamed back to client with download headers
13. **Cleanup**: Temporary files removed and statistics updated

### Concurrent Processing Model

```
Single Request Flow:
Upload → Parse → [Chunk1, Chunk2, Chunk3, ..., ChunkN]
                      ↓       ↓       ↓           ↓
                 Translate Translate Translate Translate (Concurrent)
                      ↓       ↓       ↓           ↓
                     [Result1, Result2, Result3, ..., ResultN]
                                      ↓
                                  Reassemble → Download
```

### State Management

**Application State**: Managed through FastAPI dependency injection
- Settings (cached, immutable after startup)
- AI Provider (singleton, shared across requests, supports multiple backends)
- Translation Semaphore (global concurrency control)
- Statistics Store (in-memory, thread-safe)
- Rate Limiter (singleton, session-based tracking)

**Request State**: Scoped to individual HTTP requests
- Session ID and rate limiting status
- Uploaded file content and metadata
- Temporary file paths and cleanup handlers
- Translation progress and error tracking
- Response streaming and headers

## Integration Patterns

### External API Integration
- **Provider Abstraction**: AI providers abstracted behind common interface for flexibility
- **Client Initialization**: Provider-specific client instances created at startup
- **Request Structure**: Uses `types.Content` and `types.Part` for proper prompt formatting (Gemini)
- **Mock Support**: Development and testing provider with realistic delays and behavior
- **Response Validation**: Structured JSON schemas with Pydantic model validation
- **Error Handling**: Comprehensive exception mapping for API failures
- **Rate Limiting**: Semaphore-based concurrency control respects API limits

### File System Integration
- **Temporary Storage**: Secure temporary directories for uploaded files
- **Async I/O**: All file operations use `aiofiles` for non-blocking processing
- **Cleanup Management**: Guaranteed cleanup using try/finally blocks
- **Security**: Werkzeug secure filename utilities prevent path traversal attacks

### Session Management Integration
- **Session Middleware**: Starlette SessionMiddleware manages session lifecycle
- **Session ID Assignment**: UUID-based session IDs assigned via custom middleware
- **Rate Limiting**: Per-session file upload tracking with configurable limits
- **Session Storage**: In-memory session state (resets on application restart)
- **Security**: Session-based rather than user-based for privacy and simplicity