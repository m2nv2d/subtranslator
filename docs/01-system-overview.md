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

### Support Components
- **core/dependencies.py**: FastAPI dependency injection providers for settings, AI client, and semaphores
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
- **AI Translation**: Google Generative AI (Gemini) via `google-genai` SDK
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

**Async-First Design**: All I/O operations (file handling, API calls, concurrent processing) use async/await patterns for optimal performance under load.

**In-Memory Processing**: Subtitle data is processed entirely in memory after initial file upload, minimizing disk I/O and improving performance.

**Stateless Design**: No persistent storage or user sessions, enabling simple horizontal scaling if needed.

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
2. **Input Validation**: Server validates file format, size, language, and speed mode
3. **Temporary Storage**: File is saved to temporary directory with secure naming
4. **Statistics Initialization**: Request tracking entry created in statistics store
5. **Parsing Phase**: SRT file parsed into structured blocks and chunked
6. **Context Detection**: AI analyzes sample content to determine context
7. **Translation Phase**: Chunks processed concurrently with semaphore limiting
8. **Reassembly**: Translated blocks reconstructed into valid SRT format
9. **Response**: Translated file streamed back to client with download headers
10. **Cleanup**: Temporary files removed and statistics updated

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
- AI Client (singleton, shared across requests)
- Translation Semaphore (global concurrency control)
- Statistics Store (in-memory, thread-safe)

**Request State**: Scoped to individual HTTP requests
- Uploaded file content and metadata
- Temporary file paths and cleanup handlers
- Translation progress and error tracking
- Response streaming and headers

## Integration Patterns

### External API Integration
- **Client Initialization**: Single Gemini client instance created at startup
- **Request Structure**: Uses `types.Content` and `types.Part` for proper prompt formatting
- **Response Validation**: Structured JSON schemas with Pydantic model validation
- **Error Handling**: Comprehensive exception mapping for API failures
- **Rate Limiting**: Semaphore-based concurrency control respects API limits

### File System Integration
- **Temporary Storage**: Secure temporary directories for uploaded files
- **Async I/O**: All file operations use `aiofiles` for non-blocking processing
- **Cleanup Management**: Guaranteed cleanup using try/finally blocks
- **Security**: Werkzeug secure filename utilities prevent path traversal attacks