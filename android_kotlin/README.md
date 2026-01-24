# AI Chat Room - Kotlin Android App

Native Kotlin Android implementation of the AI Chat Room application, converted from the original Python implementation.

## Overview

This is a **native Android application** built with:
- **Kotlin** - Primary programming language
- **Jetpack Compose** - Modern declarative UI framework
- **Hilt** - Dependency injection
- **Room** - Local database persistence
- **Coroutines & Flow** - Asynchronous programming
- **Material 3** - Modern Material Design components
- **Java-WebSocket** - P2P networking

## Conversion from Python

This Kotlin implementation is a **complete port** of all Python code in the parent directory:

| Python File | Kotlin File | Description |
|-------------|-------------|-------------|
| `src/personalities.py` | `domain/model/Personalities.kt` | AI personality definitions (10 personalities) |
| `src/ai_state.py` | `domain/model/AIState.kt` | AI state management, emotions, relationships |
| `src/tools.py` | `domain/model/Tools.kt` | Tool registry and implementations |
| `src/model_manager.py` | `domain/model/ModelManager.kt` | Model catalog and download |
| `src/local_storage.py` | `data/model/LocalStorage.kt` | Room database entities |
| `src/p2p.py` | `domain/model/P2P.kt` | **Full P2P networking** (WebSocket, room hosting/joining) |
| `src/document_reader.py` | `domain/model/DocumentReader.kt` | **Multi-format document processing** (PDF, images, etc.) |
| `src/rag.py` | `domain/model/RAG.kt` | **RAG system** (10M token context, per-AI storage) |
| `src/rlm/*.py` | `domain/model/RLM.kt` | **Recursive Language Model** (core, parser, REPL) |
| `src/addons/__init__.py` | `domain/model/Addons.kt` | **Add-on/plugin system** |
| `android/main.py` (Kivy) | `ui/*` | Complete Jetpack Compose UI |

## Tools Used for Conversion

The conversion was done using multiple approaches:

### 1. py2many Transpiler
```bash
pip install py2many
python -m py2many --kotlin src/personalities.py --comment-unsupported
```
- Provides initial code structure
- Handles basic data classes and functions
- Requires manual refinement for Android-specific code

### 2. Manual Idiomatic Conversion
- Converted Python dataclasses → Kotlin data classes
- Python enums → Kotlin enums
- Python type hints → Kotlin types
- asyncio → Kotlin Coroutines
- dict/list comprehensions → Kotlin collection operations
- File I/O → Room database

### 3. Architecture Adaptation
- Python modules → Kotlin packages with proper Android architecture (MVVM)
- Kivy UI → Jetpack Compose
- JSON file storage → Room SQLite database
- Python networking → WebSocket + OkHttp

## Project Structure

```
android_kotlin/
├── app/
│   ├── src/main/
│   │   ├── java/com/landseek/aichat/
│   │   │   ├── AIChatApplication.kt      # Application class
│   │   │   ├── MainActivity.kt           # Entry point
│   │   │   ├── data/
│   │   │   │   ├── AppDatabase.kt        # Room database
│   │   │   │   ├── model/                # Database entities
│   │   │   │   └── repository/           # Data repositories
│   │   │   ├── di/
│   │   │   │   └── DatabaseModule.kt     # Hilt DI module
│   │   │   ├── domain/
│   │   │   │   └── model/                # Domain models
│   │   │   │       ├── AIState.kt        # AI state classes
│   │   │   │       ├── Addons.kt         # Add-on system
│   │   │   │       ├── DocumentReader.kt # Document processing
│   │   │   │       ├── ModelManager.kt   # Model catalog
│   │   │   │       ├── P2P.kt            # P2P networking
│   │   │   │       ├── Personalities.kt  # AI personalities
│   │   │   │       ├── RAG.kt            # RAG system
│   │   │   │       ├── RLM.kt            # Recursive Language Model
│   │   │   │       └── Tools.kt          # Tool system
│   │   │   └── ui/
│   │   │       ├── AIChatApp.kt          # Main app composable
│   │   │       ├── chat/                 # Chat screen
│   │   │       ├── documents/            # Documents screen
│   │   │       ├── participants/         # AI management
│   │   │       ├── settings/             # Settings screen
│   │   │       ├── theme/                # Material theme
│   │   │       └── tools/                # Tools screen
│   │   ├── res/
│   │   │   ├── values/                   # Resources
│   │   │   └── xml/                      # Backup rules
│   │   └── AndroidManifest.xml
│   ├── build.gradle.kts
│   └── proguard-rules.pro
├── build.gradle.kts
├── gradle.properties
├── settings.gradle.kts
└── README.md
```

## Features Converted

- ✅ **10 AI Personalities** - All personalities with traits and tags
- ✅ **Chat Interface** - Complete chat UI with message bubbles
- ✅ **AI State Management** - Emotional states, relationships, memories
- ✅ **Tool System** - Calculator, date/time, text analysis, etc.
- ✅ **Model Catalog** - Gemma 3 4B, Llama, Phi, Mistral models
- ✅ **Local Storage** - Room database for persistence
- ✅ **Settings** - Model selection, user preferences
- ✅ **Document Management** - Upload and analyze documents
- ✅ **Material 3 Theme** - Dark mode with custom colors
- ✅ **P2P Networking** - Full WebSocket-based room hosting/joining
- ✅ **Document Reader** - Multi-format processing (PDF, images, code)
- ✅ **RAG System** - 10M+ token context with per-AI storage
- ✅ **RLM Core** - Recursive Language Model with REPL
- ✅ **Add-on System** - Plugin architecture for extensions

## Building

### Prerequisites
- Android Studio Hedgehog or later
- JDK 17
- Android SDK 34

### Build Steps

1. Open `android_kotlin` directory in Android Studio
2. Sync Gradle files
3. Build and run on device/emulator

```bash
# Or build from command line
cd android_kotlin
./gradlew assembleDebug
```

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| Jetpack Compose | BOM 2023.10.01 | UI framework |
| Hilt | 2.48 | Dependency injection |
| Room | 2.6.1 | Database |
| Retrofit | 2.9.0 | Networking |
| Kotlin Coroutines | 1.7.3 | Async programming |
| Material 3 | Latest | UI components |
| Coil | 2.5.0 | Image loading |
| Java-WebSocket | 1.5.4 | P2P networking |

## Key Conversion Notes

### Data Classes
```python
# Python
@dataclass
class PersonalityDefinition:
    name: str
    personality: str
    avatar: str = "🤖"
```

```kotlin
// Kotlin
data class PersonalityDefinition(
    val name: String,
    val personality: String,
    val avatar: String = "🤖"
)
```

### Enums
```python
# Python
class EmotionalState(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
```

```kotlin
// Kotlin
enum class EmotionalState(val value: String) {
    NEUTRAL("neutral"),
    HAPPY("happy")
}
```

### Collections
```python
# Python - list comprehension
[p for p in personalities if tag in p.tags]
```

```kotlin
// Kotlin
personalities.filter { tag in it.tags }
```

### Async Code
```python
# Python - asyncio
async def generate_response():
    await model.generate(prompt)
```

```kotlin
// Kotlin - coroutines
suspend fun generateResponse() {
    model.generate(prompt)
}
```

## License

MIT License - see parent directory LICENSE file.
