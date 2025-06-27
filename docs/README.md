# Subtranslator Documentation Index

This directory contains comprehensive documentation for the Subtranslator application - a FastAPI-based web service for translating subtitle files using AI-powered language translation.

## Documentation Structure

### High-Level Documentation

| Document | Purpose | Path |
|----------|---------|------|
| **Product Requirements** | Business requirements, user needs, and project scope | [00-PRD.md](./00-PRD.md) |
| **System Overview** | Architecture, tech stack, and design decisions | [01-system-overview.md](./01-system-overview.md) |
| **Data Models** | Core data structures and relationships | [02-data-models.md](./02-data-models.md) |

### Component Documentation

| Component | Overview | Modules |
|-----------|----------|---------|
| **Core** | Configuration, dependencies, errors, statistics | [core/overview.md](./core/overview.md) |
| **Translator** | Business logic for subtitle translation pipeline | [translator/overview.md](./translator/overview.md) |
| **Routers** | HTTP API endpoints and request handling | [routers/overview.md](./routers/overview.md) |
| **Frontend** | Web interface templates and client-side logic | [frontend/overview.md](./frontend/overview.md) |

### Application Entry Point

| Component | Purpose | Path |
|-----------|---------|------|
| **Main Application** | FastAPI app configuration and bootstrap | [main.md](./main.md) |

## Module-Level Documentation

### Core Modules (`src/core/`)

| File | Documentation | Purpose |
|------|---------------|---------|
| `config.py` | [core/modules/config.md](./core/modules/config.md) | Pydantic-based configuration management |
| `dependencies.py` | [core/modules/dependencies.md](./core/modules/dependencies.md) | FastAPI dependency injection providers |
| `errors.py` | [core/modules/errors.md](./core/modules/errors.md) | Standardized error response utilities |
| `providers.py` | [core/modules/providers.md](./core/modules/providers.md) | AI provider abstraction layer |
| `rate_limiter.py` | [core/modules/rate_limiter.md](./core/modules/rate_limiter.md) | Session-based rate limiting system |
| `stats.py` | [core/modules/stats.md](./core/modules/stats.md) | In-memory application statistics tracking |

### Translator Modules (`src/translator/`)

| File | Documentation | Purpose |
|------|---------------|---------|
| `exceptions.py` | [translator/modules/exceptions.md](./translator/modules/exceptions.md) | Custom exception hierarchy |
| `models.py` | [translator/modules/models.md](./translator/modules/models.md) | Core data models (SubtitleBlock) |
| `parser.py` | [translator/modules/parser.md](./translator/modules/parser.md) | SRT file parsing and validation |
| `gemini_helper.py` | [translator/modules/gemini_helper.md](./translator/modules/gemini_helper.md) | AI client initialization |
| `context_detector.py` | [translator/modules/context_detector.md](./translator/modules/context_detector.md) | AI-powered context detection |
| `chunk_translator.py` | [translator/modules/chunk_translator.md](./translator/modules/chunk_translator.md) | Concurrent translation processing |
| `reassembler.py` | [translator/modules/reassembler.md](./translator/modules/reassembler.md) | SRT file reconstruction |

### Router Modules (`src/routers/`)

| File | Documentation | Purpose |
|------|---------------|---------|
| `translate.py` | [routers/modules/translate.md](./routers/modules/translate.md) | HTTP endpoints for translation and statistics |

### Frontend Modules (`src/templates/`, `src/static/`)

| File | Documentation | Purpose |
|------|---------------|---------|
| `index.html` | [frontend/modules/index.md](./frontend/modules/index.md) | Main web interface template |
| `app.js` | [frontend/modules/app.md](./frontend/modules/app.md) | Client-side JavaScript logic |
| `style.css` | [frontend/modules/style.md](./frontend/modules/style.md) | CSS styling and layout |

## Test Documentation

| Overview | Purpose | Path |
|----------|---------|------|
| **Test Strategy** | Testing approach, coverage analysis, recommendations | [tests/README.md](./tests/README.md) |

### Test Files (`tests/manual/`)

| Test File | Documentation | Purpose |
|-----------|---------------|---------|
| `test_chunk_translator.py` | [tests/test_chunk_translator.md](./tests/test_chunk_translator.md) | End-to-end chunk translation testing |
| `test_config.py` | [tests/test_config.md](./tests/test_config.md) | Configuration loading and validation |
| `test_context_detector.py` | [tests/test_context_detector.md](./tests/test_context_detector.md) | AI context detection testing |
| `test_gemini_helper.py` | [tests/test_gemini_helper.md](./tests/test_gemini_helper.md) | AI client initialization testing |
| `test_parser.py` | [tests/test_parser.md](./tests/test_parser.md) | SRT parsing and chunking tests |
| `test_rate_limiter.py` | [tests/test_rate_limiter.md](./tests/test_rate_limiter.md) | Session-based rate limiting testing |
| `test_reassembly_flow.py` | [tests/test_reassembly_flow.md](./tests/test_reassembly_flow.md) | Complete workflow integration testing |
| `test_translate_api.sh` | [tests/test_translate_api.md](./tests/test_translate_api.md) | HTTP API endpoint testing |

## File-to-Documentation Mapping

### Source Code Mapping

```
src/main.py                           → docs/main.md
src/core/config.py                    → docs/core/modules/config.md
src/core/dependencies.py              → docs/core/modules/dependencies.md
src/core/errors.py                    → docs/core/modules/errors.md
src/core/providers.py                 → docs/core/modules/providers.md
src/core/rate_limiter.py              → docs/core/modules/rate_limiter.md
src/core/stats.py                     → docs/core/modules/stats.md
src/translator/exceptions.py          → docs/translator/modules/exceptions.md
src/translator/models.py              → docs/translator/modules/models.md
src/translator/parser.py              → docs/translator/modules/parser.md
src/translator/gemini_helper.py       → docs/translator/modules/gemini_helper.md
src/translator/context_detector.py    → docs/translator/modules/context_detector.md
src/translator/chunk_translator.py    → docs/translator/modules/chunk_translator.md
src/translator/reassembler.py         → docs/translator/modules/reassembler.md
src/routers/translate.py              → docs/routers/modules/translate.md
src/templates/index.html              → docs/frontend/modules/index.md
src/static/js/app.js                  → docs/frontend/modules/app.md
src/static/css/style.css              → docs/frontend/modules/style.md
```

### Test Code Mapping

```
tests/manual/test_chunk_translator.py    → docs/tests/test_chunk_translator.md
tests/manual/test_config.py              → docs/tests/test_config.md
tests/manual/test_context_detector.py    → docs/tests/test_context_detector.md
tests/manual/test_gemini_helper.py       → docs/tests/test_gemini_helper.md
tests/manual/test_parser.py              → docs/tests/test_parser.md
tests/manual/test_rate_limiter.py        → docs/tests/test_rate_limiter.md
tests/manual/test_reassembly_flow.py     → docs/tests/test_reassembly_flow.md
tests/manual/test_translate_api.sh       → docs/tests/test_translate_api.md
```

## Quick Navigation

### For New Developers
1. Start with [00-PRD.md](./00-PRD.md) to understand the business requirements
2. Read [01-system-overview.md](./01-system-overview.md) for architectural understanding
3. Review [02-data-models.md](./02-data-models.md) for data structure comprehension
4. Explore component overviews in order: [core](./core/overview.md) → [translator](./translator/overview.md) → [routers](./routers/overview.md) → [frontend](./frontend/overview.md)

### For Feature Development
1. Identify the relevant component(s) from the component overview documents
2. Review the specific module documentation for implementation details
3. Check test documentation for existing test patterns and coverage
4. Reference the data models documentation for data structure requirements

### For Bug Investigation
1. Check the specific module documentation for the affected component
2. Review error handling patterns in [core/modules/errors.md](./core/modules/errors.md)
3. Examine test cases for expected behavior patterns
4. Use [main.md](./main.md) for application-level error handling

### For Testing
1. Start with [tests/README.md](./tests/README.md) for testing strategy
2. Review existing test documentation for patterns and coverage
3. Reference module documentation for expected behaviors and edge cases
4. Use sample files in `tests/samples/` for test data

## Documentation Standards

### Format Conventions
- **Module Overview**: Purpose, design patterns, integration points
- **🔍 Abstraction-Level Reference**: Detailed API documentation with signatures, parameters, returns, behavior, exceptions, examples, and tips
- **Code Examples**: Practical, runnable examples with realistic use cases
- **Cross-References**: Links between related documentation sections

### Maintenance Guidelines
- Documentation should be updated when code changes
- Examples should remain current and functional
- Cross-references should be verified during updates
- New modules require corresponding documentation

## Additional Resources

### Configuration
- Environment variable reference in [core/modules/config.md](./core/modules/config.md)
- Dependency injection patterns in [core/modules/dependencies.md](./core/modules/dependencies.md)

### Development Setup
- Application startup process in [main.md](./main.md)
- Test execution patterns in [tests/README.md](./tests/README.md)

### Deployment
- Application configuration in [01-system-overview.md](./01-system-overview.md)
- Performance considerations throughout component documentation

This documentation suite provides comprehensive coverage of the Subtranslator application, enabling efficient onboarding, development, testing, and maintenance activities.