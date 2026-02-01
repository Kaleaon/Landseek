# CLAUDE.md - AI Assistant Configuration for Landseek

This file provides guidance for AI assistants (Claude, Copilot, etc.) working on the Landseek AI Chat Room project.

## Project Overview

Landseek is a multi-platform AI chat room application designed to run locally on Android devices (optimized for Pixel TPU). It features:

- **10 AI Personalities** with persistent state, emotions, and relationships
- **RAG System** with 10M+ token knowledge base per AI
- **P2P Networking** for sharing LLM capabilities
- **Multi-Platform Support**: Python CLI, Kivy Android, and Native Kotlin Android

## Repository Structure

```
Landseek/
├── chat_room.py              # Main CLI entry point
├── src/                      # Python backend
│   ├── rlm/                  # Recursive Language Model library
│   │   ├── core.py          # Core RLM logic
│   │   ├── parser.py        # Response parsing
│   │   ├── prompts.py       # System prompts
│   │   ├── repl.py          # Safe code execution
│   │   └── types.py         # Type definitions
│   ├── personalities.py      # AI personality definitions
│   ├── ai_state.py           # Persistent state management
│   ├── tools.py              # Built-in tools (calculator, datetime, etc.)
│   ├── rag.py                # RAG/MemRL implementation
│   ├── model_manager.py      # LLM model catalog
│   ├── local_storage.py      # SQLite storage
│   ├── p2p.py                # P2P networking
│   └── addons/               # Plugin system
├── android/                  # Kivy/Python Android app
│   └── main.py              # Kivy entry point
├── android_kotlin/           # Native Kotlin Android app (primary)
│   ├── app/
│   │   ├── build.gradle.kts
│   │   └── src/main/java/com/landseek/aichat/
│   │       ├── domain/model/   # Data models (Kotlin)
│   │       ├── data/           # Room database
│   │       └── ui/             # Jetpack Compose UI
│   ├── build.gradle.kts
│   ├── gradlew / gradlew.bat
│   └── gradle/wrapper/
├── tests/                    # Python test suite
├── .github/workflows/        # CI/CD workflows
│   ├── kotlin-apk.yml       # Android Kotlin build
│   ├── main.yml             # Python tests
│   └── static-analysis.yml  # Linting
├── pyproject.toml           # Python package config
└── buildozer.spec           # Kivy/Buildozer Android config
```

## Development Commands

### Python Backend

```bash
# Install dependencies
pip install -e .                    # Basic install
pip install -e ".[dev]"             # With dev tools

# Run tests
pytest tests/ -v                    # All tests
pytest tests/ -v --cov=src          # With coverage

# Linting
ruff check src/                     # Linting
black src/ tests/ chat_room.py      # Formatting
mypy src/rlm                        # Type checking

# Run application
python chat_room.py                 # Local mode (Ollama)
python chat_room.py --cloud         # Cloud mode (Gemini API)
```

### Android Kotlin App

```bash
cd android_kotlin

# Verify Gradle wrapper
./gradlew --version

# Build debug APK
./gradlew assembleDebug

# Run tests
./gradlew testDebugUnitTest

# Compile only (faster for checking errors)
./gradlew compileDebugKotlin

# Lint
./gradlew lintDebug

# Clean build
./gradlew clean
```

### CI/CD

The project uses GitHub Actions for:
- `kotlin-apk.yml` - Builds Android Kotlin APK, runs tests
- `main.yml` - Python tests
- `static-analysis.yml` - Linting and code quality

## Key Architecture Patterns

### AI Personality System

Each AI personality has:
- Unique ID (e.g., "nova", "echo", "sage")
- Display name (customizable)
- Personality description
- Avatar emoji
- Tags for categorization
- Model settings (temperature, maxTokens)

**Python**: `src/personalities.py` → `BUILTIN_PERSONALITIES`
**Kotlin**: `domain/model/Personalities.kt` → `BUILTIN_PERSONALITIES`

### State Management

AI state includes:
- Chat history
- Emotional state
- Relationships with other participants
- Custom memories/traits

**Python**: `src/ai_state.py` → `AIState` class
**Kotlin**: `domain/model/AIState.kt` → `AIState` data class

### Tool System

Tools are functions that AIs can call:
- Math: `calculate`, `unit_convert`
- DateTime: `get_current_time`, `calculate_date`
- Text: `word_count`, `search_text`, `extract_urls`
- File: `list_files`, `read_file`
- System: `get_system_info`

**Python**: `src/tools.py`
**Kotlin**: `domain/model/Tools.kt`

### Kotlin Android Stack

- **Jetpack Compose** - Declarative UI
- **Room Database** - Local persistence
- **Hilt** - Dependency injection
- **Material 3** - Design system
- **Coroutines** - Async operations
- **kotlinx.serialization** - JSON serialization

## Common Tasks

### Adding a New AI Personality

1. **Python**: Add to `BUILTIN_PERSONALITIES` in `src/personalities.py`
2. **Kotlin**: Add to `BUILTIN_PERSONALITIES` in `Personalities.kt`

### Adding a New Tool

1. **Python**: Add function and registration in `src/tools.py`
2. **Kotlin**: Add to `ToolRegistry` in `Tools.kt`

### Fixing Kotlin Compilation Errors

Common issues:
- **Duplicate class names**: Rename one or move to different package
- **Missing imports**: Add the required import statement
- **JVM signature clash**: Rename property or function to avoid conflict
- **Serializer not found**: Use supported types or add `@Contextual`

### Gradle Wrapper Issues

If you see `Could not find or load main class org.gradle.wrapper.GradleWrapperMain`:
1. The `gradle-wrapper.jar` is corrupted or incomplete
2. Download the correct JAR from: `https://raw.githubusercontent.com/gradle/gradle/v{VERSION}/gradle/wrapper/gradle-wrapper.jar`
3. Replace `android_kotlin/gradle/wrapper/gradle-wrapper.jar`

## File Format Support

The app supports 70+ file formats for document processing:
- Text: `.txt`, `.md`, `.json`, `.csv`, `.xml`, `.yaml`
- Code: `.py`, `.js`, `.ts`, `.kt`, `.java`, `.go`, `.rs`
- Documents: `.pdf`, `.docx`, `.odt`, `.rtf`, `.epub`
- Images: `.jpg`, `.png`, `.gif`, `.webp` (Gemma 3 multimodal)
- Audio/Video: `.mp3`, `.wav`, `.mp4`, `.webm`

## Environment Variables

```bash
# For cloud mode
export GOOGLE_API_KEY="your-gemini-api-key"
export CHAT_MODEL="gemini/gemini-2.0-flash"

# For local mode (default)
export OLLAMA_HOST="http://localhost:11434"
export CHAT_MODEL="ollama/gemma3:4b"
```

## Testing Guidelines

### Python Tests
- Located in `tests/`
- Use pytest with async support
- Run with: `pytest tests/ -v`

### Kotlin Tests
- Located in `android_kotlin/app/src/test/`
- Use JUnit and MockK
- Run with: `./gradlew testDebugUnitTest`

## Code Style

### Python
- Line length: 100 characters
- Formatter: Black
- Linter: Ruff
- Type hints: Required (mypy enforced)

### Kotlin
- Standard Kotlin conventions
- Use data classes for models
- Prefer immutability
- Use coroutines for async operations

## Notes for AI Assistants

1. **Always check both Python and Kotlin** when modifying data models - they should stay in sync
2. **Gradle wrapper JAR** must be included in git - don't add `*.jar` to `.gitignore` in the gradle directory
3. **Icon resources** are required for Android - ensure mipmap folders have proper icons
4. **Theme overloads** in Compose can cause ambiguity - prefer single functions with default parameters
5. **Property/function name conflicts** cause JVM signature clashes - use different names
6. **MutableMap<String, Any>** is not serializable - use specific types like `MutableMap<String, String>`
7. **Run `./gradlew compileDebugKotlin`** before full build to catch errors faster

## Related Documentation

- [Android Kotlin README](android_kotlin/README.md) - Kotlin conversion details
- [GPT Mobile Design Analysis](GPT_MOBILE_DESIGN_ANALYSIS.md) - UI/UX patterns
- [RLM Documentation](https://github.com/ysz/recursive-llm) - Recursive Language Model
