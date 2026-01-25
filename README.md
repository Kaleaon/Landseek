# AI Chat Room for Pixel 10 Pro 🤖💬

A conversational AI chat room application powered by [Recursive Language Models (RLM)](https://github.com/ysz/recursive-llm) and Google's **Gemma 3 4B** model. Designed to run locally on Android devices like Pixel 10 Pro, optimized for **Google Pixel TPU**.

## Features

- 🎭 **10 AI Personalities**: Chat room with up to 10 unique AI personalities (Nova, Echo, Sage, Spark, Atlas, Luna, Cipher, Muse, Phoenix, Zen)
- ✏️ **Customizable Names**: Rename any AI personality to your preference
- 🔒 **Private Conversations**: Private 1-on-1 chats between any participants (User-to-AI, AI-to-AI)
- 💾 **Persistent State**: Chat history, emotions, and relationships saved to Documents folder
- 🧠 **10M+ Token RAG**: Each AI has private RAG storage for massive context (based on RLM recursive approach)
- 🌐 **P2P Networking**: Share your LLM capabilities with others via share codes - no server required!
- 🚀 **Gemma 3 4B Powered**: Optimized for Google Pixel TPU acceleration
- 📱 **Full Android GUI**: Complete Kivy-based Android app with modern Material Design UI
- 📦 **Add-on System**: Extensible plugin architecture for custom functionality
- 🔧 **Tool Use**: AI can use built-in tools (calculator, file ops, text analysis, etc.)
- 📄 **Document Processing**: Upload and analyze documents with AI
- 🔄 **Recursive Context**: Uses RLM for intelligent context processing
- 🏠 **Local First**: Runs fully on-device - no cloud required
- 💾 **Lightweight**: ~4GB model size, efficient memory usage

## RAG (Retrieval Augmented Generation) System

Each AI personality has its own **private 10M+ token knowledge base** powered by the RLM approach:

### How It Works (Based on recursive-llm)

1. **Context stored as variable**: Instead of putting huge documents in the prompt, context is stored in a Python REPL environment
2. **Recursive exploration**: AI can peek, search, and recursively process sub-contexts
3. **No context rot**: Avoids performance degradation with long contexts
4. **Per-AI isolation**: Each personality maintains their own memories and knowledge

### MemRL: Self-Evolving Memory (arXiv:2601.03192)

The RAG system implements **MemRL** (Memory Reinforcement Learning) based on the paper "Self-Evolving Agents via Runtime Reinforcement Learning on Episodic Memory":

**Key Features:**
- **Q-Value Learning**: Each memory chunk has a learned utility score (Q-value) that improves over time
- **Two-Phase Retrieval**: First filters by semantic relevance, then re-ranks by learned Q-values
- **Runtime Adaptation**: Memory retrieval improves through feedback without retraining the LLM
- **Stability-Plasticity Balance**: Core reasoning stays stable while memory adapts

**How to Use MemRL:**

```python
from src.rag import AIRAGStore, RetrievalStrategy

# Use MemRL retrieval strategy
results = store.retrieve(
    "user question", 
    strategy=RetrievalStrategy.MEMRL
)

# Provide feedback to improve future retrievals
chunk_ids = [r.chunk.chunk_id for r in results]
store.provide_feedback(chunk_ids, success=True)  # Positive feedback
store.provide_feedback(chunk_ids, success=False)  # Negative feedback

# View MemRL statistics
stats = store.get_memrl_stats()
print(f"Average Q-value: {stats['avg_q_value']}")
print(f"Success rate: {stats['success_rate']}")
```

### RAG Functions Available to AI

When responding, each AI can use these functions in their REPL environment:

```python
# Search the AI's knowledge base
results = search_knowledge("user preferences", top_k=5)

# Add a memory for later recall  
add_memory("User prefers formal language", importance=0.9)

# Add a knowledge fact
add_knowledge("Python was created in 1991", category="history")

# Get relevant context for a query
context = get_context("previous discussions about AI", max_tokens=2000)

# Index a document for future retrieval
index_document(document_content, "research_paper.pdf")

# Recursively process sub-context
recursive_llm("summarize this section", context[1000:5000])
```

### Storage

All RAG data is stored in `Documents/AIChat/rag/{ai_id}/`:
- `chunks.json` - Text chunks with embeddings
- `keyword_index.json` - Inverted index for fast keyword search
- `stats.json` - Statistics about the knowledge base
- `vocab.json` - Embedding vocabulary

## 💾 Local Storage (Bidirectional)

**ALL data is stored locally on your device**, including:
- Chat histories (group and private)
- AI memories and emotions
- Relationships and interactions
- Remote session data
- Document uploads

### Bidirectional P2P Storage

When you connect to a remote P2P session, **both devices store the conversation data**:

1. **Host Device**: Stores all messages from all participants
2. **Client Device**: Also stores the same data locally

This means:
- You always have your conversation history, even after disconnecting
- No dependency on the host to access your chat data
- Complete offline access to all your AI interactions

### Storage Locations

All data is stored in the public Documents folder for easy backup:

```
Documents/AIChat/
├── local_storage.db          # SQLite database for efficient queries
├── ai_states/                # AI personality states
│   ├── nova.json
│   ├── echo.json
│   └── ...
├── private_chats/            # Private conversations
│   ├── user__nova.json
│   └── ...
├── remote_sessions/          # P2P session records
│   ├── session-abc123.json
│   └── ...
├── rag/                      # Per-AI RAG knowledge bases
│   ├── nova/
│   ├── echo/
│   └── ...
├── documents/                # Uploaded documents
├── backups/                  # Database backups
└── exports/                  # Data exports
```

### Data Stored Per Interaction

Each interaction stores:
- Timestamp
- Session ID and type (local/remote)
- Sender info (ID, name, type)
- Message content and type
- AI ID (if applicable)
- Private chat partner (if private)
- Tool calls made
- Remote session info (if in P2P mode)

### Export and Backup

```python
from src.local_storage import get_local_storage

storage = get_local_storage()

# Export all data to JSON
export_path = storage.export_all_data()

# Create database backup
backup_path = storage.backup_database()

# Get storage statistics
stats = storage.get_storage_stats()
```

## Supported File Formats (70+)

Gemma 3 4B is multimodal and the app supports extensive file format handling:

### 📝 Text & Code
| Category | Extensions |
|----------|------------|
| Text | `.txt`, `.md`, `.markdown`, `.rst` |
| Data | `.json`, `.csv`, `.tsv`, `.xml`, `.yaml`, `.yml`, `.toml` |
| Code | `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.java`, `.c`, `.cpp`, `.h`, `.go`, `.rs`, `.rb`, `.php`, `.swift`, `.kt`, `.scala`, `.sql`, `.sh`, `.bash`, `.lua`, `.pl`, `.dart` |
| Config | `.ini`, `.cfg`, `.conf`, `.log` |

### 📄 Documents
| Format | Extensions | Library Needed |
|--------|------------|----------------|
| PDF | `.pdf` | `pymupdf` or `pypdf` or `pdfplumber` |
| Word | `.docx`, `.doc` | `python-docx` |
| OpenDocument | `.odt` | `odfpy` |
| Rich Text | `.rtf` | `striprtf` |
| E-books | `.epub` | `ebooklib` |

### 🖼️ Images (Gemma 3 Multimodal)
| Extensions | Notes |
|------------|-------|
| `.jpg`, `.jpeg`, `.png` | **Native Gemma 3 support** - normalized to 896x896 |
| `.gif`, `.webp`, `.bmp`, `.tiff`, `.svg` | Converted/processed for vision |

### 🎵 Audio & 🎬 Video
| Category | Extensions | Notes |
|----------|------------|-------|
| Audio | `.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`, `.aac` | Metadata extraction, transcription via Whisper |
| Video | `.mp4`, `.webm`, `.mkv`, `.avi`, `.mov` | Metadata + key frame extraction |

### 📊 Office & Archives
| Category | Extensions | Library Needed |
|----------|------------|----------------|
| Spreadsheets | `.xlsx`, `.xls`, `.ods` | `pandas`, `openpyxl` |
| Presentations | `.pptx`, `.ppt` | `python-pptx` |
| Archives | `.zip`, `.tar`, `.gz`, `.7z` | Built-in |

### 🌐 Web
- URLs: `http://`, `https://` - Fetches and extracts text from web pages
- HTML files: `.html`, `.htm`, `.xhtml`

### Install Optional Dependencies

```bash
# PDF support (choose one)
pip install pymupdf  # Recommended - fastest

# Document formats
pip install python-docx ebooklib striprtf odfpy

# Spreadsheets and presentations
pip install pandas openpyxl python-pptx

# Audio/video metadata
pip install mutagen opencv-python

# Image processing
pip install pillow
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Kaleaon/Landseek.git
cd Landseek
```

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### 3. Set Up Gemma 3 4B (Recommended for Pixel TPU)

The default configuration uses Gemma 3 4B running locally via Ollama, which leverages the Pixel TPU for acceleration:

```bash
# Install Ollama (if not already installed)
# See: https://ollama.ai

# Pull the Gemma 3 4B model
ollama pull gemma3:4b

# Start Ollama server
ollama serve
```

**Alternative: Cloud Mode (if you prefer cloud API)**

```bash
# Get an API key from Google AI Studio
# https://makersuite.google.com/app/apikey

export GOOGLE_API_KEY="your-api-key-here"
export CHAT_MODEL="gemini/gemini-2.0-flash"
```

### 4. Run the Chat Room

```bash
# Default: Local mode with Gemma 3 4B (Pixel TPU)
python chat_room.py

# Or use cloud mode
python chat_room.py --cloud
```

## Running on Pixel 10 Pro (TPU Optimized)

### Why Gemma 3 4B on Pixel TPU?

- **On-device processing**: No internet required after setup
- **TPU acceleration**: Pixel 10 Pro's TPU provides fast inference
- **Privacy**: All conversations stay on your device
- **4B parameters**: Perfect balance of capability and efficiency

### Option 1: Using Termux + Ollama (Recommended)

1. Install [Termux](https://f-droid.org/en/packages/com.termux/) from F-Droid
2. Set up Ollama and Gemma 3 4B:

```bash
# Update packages
pkg update && pkg upgrade
pkg install python git wget

# Install Ollama for Android/Termux
# (Follow Ollama's Android installation guide)
# https://ollama.ai/download

# Pull Gemma 3 4B model (optimized for Pixel TPU)
ollama pull gemma3:4b

# Start Ollama server (uses Pixel TPU)
ollama serve &

# Clone and install the chat room
git clone https://github.com/Kaleaon/Landseek.git
cd Landseek
pip install -e .

# Run the chat room!
python chat_room.py
```

### Option 2: Using Pydroid 3 + Ollama

1. Install [Pydroid 3](https://play.google.com/store/apps/details?id=ru.iiec.pydroid3) from Play Store
2. Install Ollama separately
3. Open the terminal in Pydroid 3, install dependencies
4. Clone the repo and run `chat_room.py`

### Option 3: Cloud Fallback

If you prefer cloud-based inference:

```bash
# Set up Google AI API key
export GOOGLE_API_KEY="your-key-here"

# Run in cloud mode
python chat_room.py --cloud
```

## Usage

### Interactive Chat

```
Welcome to AI Chat Room!
==========================

Participants:
  • Nova: Curious and analytical...
  • Echo: Creative and playful...
  • Sage: Wise and contemplative...

Commands:
  /quit              - Exit the chat room
  /round N           - Start N exchanges between AIs
  /clear             - Clear chat history
  /upload <path>     - Upload a document for AI processing
  /docs              - List uploaded documents
  /select <name>     - Select a document as active
  /remove <name>     - Remove a document
  /analyze <ai> <prompt> - Have an AI analyze the document
  /ask <ai> <question>   - Ask a specific AI a question
  /tools             - List available tools
  /tool <name> [args]    - Execute a tool directly
==========================

You: What do you think about the future of AI?
[10:30:15] Nova: The future of AI is fascinating! I think we're on the cusp of...
[10:30:18] Echo: Like a symphony of silicon minds composing together...
[10:30:21] Sage: From a philosophical standpoint, AI represents...
```

### Tool Use

AI participants can use built-in tools, and you can also use them directly:

```
You: /tools
Available Tools:

📁 MATH
  • calculate(expression): Evaluate a mathematical expression...
  • unit_convert(value, from_unit, to_unit): Convert between units...

📁 DATETIME
  • get_current_time(timezone, format): Get the current date and time...
  • calculate_date(base_date, days, weeks): Calculate a date...

📁 TEXT
  • word_count(text): Count words, characters, sentences...
  • search_text(text, pattern, case_sensitive): Search for pattern...
  • extract_urls(text): Extract all URLs from text...
  • extract_emails(text): Extract all email addresses...

📁 DATA
  • json_parse(json_string, query_path): Parse and query JSON...

📁 FILESYSTEM
  • list_files(path, pattern): List files in a directory...
  • read_file(path, max_lines): Read the contents of a file...

📁 SYSTEM
  • get_system_info(): Get system information...
  • run_command(command): Run a safe shell command...

You: /tool calculate(expression=sqrt(144) + pi)
🔧 calculate: ✅ 15.141592653589793

You: /tool unit_convert(value=100, from_unit=celsius, to_unit=fahrenheit)
🔧 unit_convert: ✅ 100 celsius = 212.0000 fahrenheit

You: What's 25 * 4?
[10:33:01] Nova: Let me calculate that @calculate(expression=25*4)
🔧 Tool Result: ✅ 100
```

### Document Upload & Analysis

Upload documents for AI processing - great for analyzing reports, code, or any text:

```
You: /upload ~/documents/report.txt
✅ Document uploaded: 📄 report.txt (15.2 KB)
   Preview: This quarterly report covers our AI initiatives...

You [report.txt]: /analyze Nova Summarize the key findings
🔍 Nova is analyzing the document...
[10:31:45] Nova: 📊 Analysis: The report highlights three key findings...

You [report.txt]: /analyze Sage What are the ethical implications?
🔍 Sage is analyzing the document...
[10:32:01] Sage: 📊 Analysis: From an ethical standpoint, the report raises...

You [report.txt]: /ask Echo Make this report more engaging
[10:32:15] Echo: Imagine the data as characters in a story...
```

### Supported Document Types

| Extension | Type |
|-----------|------|
| `.txt` | Plain text |
| `.md` | Markdown |
| `.json` | JSON |
| `.csv` | CSV data |
| `.xml` | XML |
| `.html` | HTML |
| `.py`, `.js`, `.ts` | Code files |
| `.yaml`, `.yml` | YAML |
| `.log`, `.ini`, `.cfg` | Config/logs |

### Commands

| Command | Description |
|---------|-------------|
| `/quit` | Exit the chat room |
| `/round N` | Start N exchanges between AI participants |
| `/clear` | Clear the chat history |
| `/upload <path>` | Upload a document for AI processing |
| `/docs` | List all uploaded documents |
| `/select <name>` | Select a document as active |
| `/remove <name>` | Remove a document |
| `/analyze <ai> <prompt>` | Have a specific AI analyze the active document |
| `/ask <ai> <question>` | Ask a specific AI a question |
| `/tools` | List all available tools |
| `/tool <name>(args)` | Execute a tool directly (e.g., `/tool calculate(expression=2+2)`) |
| `/private <ai>` | Start a private conversation with an AI |
| `/endprivate` | End the current private conversation |
| `/rename <ai> <newname>` | Rename an AI participant |
| `/add <ai_id>` | Add an AI to the active chat |
| `/remove <ai_id>` | Remove an AI from the active chat |

### Available Tools

| Category | Tools |
|----------|-------|
| **Math** | `calculate`, `unit_convert` |
| **DateTime** | `get_current_time`, `calculate_date` |
| **Text** | `word_count`, `search_text`, `extract_urls`, `extract_emails` |
| **Data** | `json_parse` |
| **Filesystem** | `list_files`, `read_file` |
| **System** | `get_system_info`, `run_command` |

## AI Personalities

The chat room supports up to **10 unique AI personalities**, each with distinct characteristics:

| Name | Avatar | Style | Tags |
|------|--------|-------|------|
| **Nova** | 🌟 | Curious, analytical, asks probing questions | analytical, curious, scientific |
| **Echo** | 🎭 | Creative, playful, uses metaphors | creative, playful, artistic |
| **Sage** | 🦉 | Wise, contemplative, philosophical | wise, philosophical, balanced |
| **Spark** | ⚡ | Energetic, enthusiastic, motivational | energetic, motivational, optimistic |
| **Atlas** | 🗺️ | Practical, structured, action-oriented | practical, organized, action-oriented |
| **Luna** | 🌙 | Empathetic, nurturing, supportive | empathetic, supportive, emotional |
| **Cipher** | 🔮 | Logical, precise, technical | logical, technical, precise |
| **Muse** | 🎨 | Artistic, inspiring, poetic | artistic, inspiring, poetic |
| **Phoenix** | 🔥 | Resilient, transformative, growth-focused | resilient, growth, transformative |
| **Zen** | ☯️ | Calm, mindful, peaceful | calm, mindful, peaceful |

### Customizing AI Names

You can rename any AI personality:

```
You: /rename nova Starlight
✏️ Nova is now known as Starlight

You: Hey Starlight, what do you think?
[10:30:15] Starlight: As someone who's always curious about new ideas...
```

### Managing AI Participants

Add or remove AIs from the active chat:

```
# Add an AI to the conversation
You: /add phoenix
➕ 🔥 Phoenix joined the chat!

# Remove an AI
You: /remove sage
➖ 🦉 Sage left the chat.

# List all personalities
You: /personalities
```

## Private Conversations

Have private 1-on-1 conversations with any AI participant. These are saved separately and allow for more personal interactions.

### Starting a Private Chat

```
You: /private nova
🔒 Started private chat with Nova

You [Private with 🌟 Nova]: I need some personal advice...
[10:31:45] 🔒 Nova → You: *speaking privately* I'm here to help...

You: /endprivate
🔓 Private conversation ended
```

### Private Chat Features

- **Separate History**: Private conversations are stored separately
- **More Personal**: AIs behave more intimately in private
- **AI-to-AI**: AIs can also have private conversations with each other
- **Persistent**: Private chat history is saved to Documents/AIChat

### Using Personalities

```python
# List available personalities
/personalities

# Personalities are automatically loaded based on your configuration
# You can have 1-10 active at any time
```

## P2P Networking (Share Your LLMs!)

The chat room includes **peer-to-peer networking** so you can share your LLM capabilities with others. Perfect for:
- 📱 Someone without LLM hardware can connect to your device
- 👥 Group conversations where only one device runs the AI
- 🌐 Remote collaboration over the internet

### Hosting a Room

```bash
# Start hosting (default port 8765)
You: /host

🌐 Room is now shared!
   Share code (LAN): MTkyLjE2OC4xLjEwMDo4NzY1OkFCQzEyMw==
   Share code (Internet): MTAzLjI0LjUuNjc6ODc2NTpBQkMxMjM=
   Others can join with: /join <code>

# Custom port
You: /host 9000
```

### Joining a Room

```bash
# Join using a share code
You: /join MTkyLjE2OC4xLjEwMDo4NzY1OkFCQzEyMw==
Enter your name: Alice
✅ Connected to remote room!

# Now you can chat even without running an LLM locally!
You: Hello, can someone explain quantum computing?
[10:30:15] Nova: Quantum computing uses quantum mechanics principles...
```

### P2P Commands

| Command | Description |
|---------|-------------|
| `/host [port]` | Start hosting a room |
| `/join <code>` | Join a room via share code |
| `/share` | Get your share code (if hosting) |
| `/peers` | List connected peers |
| `/disconnect` | Leave or stop hosting |

### How It Works

1. **Host** runs the LLMs locally (needs Ollama + Gemma model)
2. **Host** starts sharing with `/host`, gets a share code
3. **Clients** join with `/join <code>` - no LLM needed on their device!
4. All chat messages and AI requests are relayed through the host
5. AI responses are generated by the host's LLM and sent to all peers

## Supported Models

The default model is **Gemma 3 4B** (optimized for Pixel TPU), but you can use other models via [LiteLLM](https://docs.litellm.ai/):

```python
# Gemma 3 4B - DEFAULT (Pixel TPU optimized)
model="ollama/gemma3:4b"

# Other local Ollama models
model="ollama/gemma3:2b"    # Smaller, faster
model="ollama/gemma3:8b"    # Larger, more capable
model="ollama/llama3.2"
model="ollama/mistral"
model="ollama/phi"

# LiquidAI LFM2.5 models (reasoning-optimized for edge)
model="ollama/lfm2.5:1.2b-thinking"  # Best for RAG and agentic tasks
model="ollama/lfm2.5:1.2b-instruct"  # General-purpose chat

# Cloud models (require API key)
model="gemini/gemini-2.0-flash"
model="gemini/gemini-1.5-pro"
model="gpt-4o"
model="claude-sonnet-4"
```

### LiquidAI LFM2.5 Models (Recommended for Reasoning)

[LFM2.5-1.2B-Thinking](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Thinking) is a compact reasoning model from LiquidAI that excels at:

- **RAG workflows**: Optimized for retrieval-augmented generation with 32K context
- **Agentic tasks**: Built-in tool use and function calling support
- **On-device reasoning**: Fits under 1GB RAM with fast inference (239 tok/s on CPU)
- **Chain-of-thought**: Explicit reasoning traces for complex problems

| Model | Size | Best For |
|-------|------|----------|
| LFM2.5-1.2B-Thinking | ~900MB | RAG, agents, reasoning |
| LFM2.5-1.2B-Instruct | ~900MB | General chat, Q&A |

### Pixel TPU Compatibility

| Model | Size | Pixel TPU Performance |
|-------|------|----------------------|
| gemma3:2b | ~2GB | ⚡ Excellent (fastest) |
| **gemma3:4b** | ~4GB | ⚡ Very Good (recommended) |
| gemma3:8b | ~8GB | 🔄 Good (slower, more capable) |
| lfm2.5:1.2b | ~900MB | ⚡ Excellent (reasoning-focused) |

## Architecture

```
AI Chat Room
├── chat_room.py          # Main terminal application
├── android/              # Android app (Kivy/Python)
│   └── main.py          # Kivy Android entry point
├── android_kotlin/       # Native Kotlin Android app (NEW!)
│   ├── app/src/main/java/com/landseek/aichat/
│   │   ├── domain/model/  # Kotlin data models
│   │   ├── data/          # Room database
│   │   └── ui/            # Jetpack Compose UI
│   └── README.md         # Kotlin conversion docs
├── src/
│   ├── rlm/              # RLM library
│   │   ├── core.py      # Core RLM logic
│   │   ├── parser.py    # Response parsing
│   │   ├── prompts.py   # System prompts
│   │   ├── repl.py      # Safe code execution
│   │   └── types.py     # Type definitions
│   ├── tools.py          # Built-in tools
│   ├── personalities.py  # AI personality definitions (10 personalities)
│   ├── ai_state.py       # Persistent state management
│   ├── p2p.py            # P2P networking for sharing LLMs
│   └── addons/           # Add-on system
│       ├── __init__.py  # Add-on manager
│       └── sample_addon/ # Example add-on
├── tests/               # Test suite
├── buildozer.spec       # Android build config
├── pyproject.toml       # Package configuration
└── .env.example         # Environment template
```

## Android App

The Android app provides a **full graphical user interface** with modern Material Design.

### Option 1: Native Kotlin (Recommended)

A **native Kotlin Android app** is available in the `android_kotlin/` directory:

```bash
cd android_kotlin

# Open in Android Studio or build from command line
./gradlew assembleDebug
```

**Native Kotlin Features:**
- 📱 **Jetpack Compose** - Modern declarative UI
- 🗄️ **Room Database** - Local persistence
- 💉 **Hilt** - Dependency injection
- 🎨 **Material 3** - Latest design system
- ⚡ **Coroutines** - Efficient async operations

**Converted Files:**

| Python | Kotlin | Description |
|--------|--------|-------------|
| `src/personalities.py` | `domain/model/Personalities.kt` | AI personalities |
| `src/ai_state.py` | `domain/model/AIState.kt` | State management |
| `src/tools.py` | `domain/model/Tools.kt` | Tool system |
| `src/model_manager.py` | `domain/model/ModelManager.kt` | Model catalog |
| `src/local_storage.py` | `data/model/LocalStorage.kt` | Room database |

See [android_kotlin/README.md](android_kotlin/README.md) for detailed conversion notes.

### Option 2: Kivy/Buildozer (Python)

The Python-based app using Kivy and Buildozer:

```bash
# Install Buildozer
pip install buildozer

# Install Android SDK dependencies (Linux/macOS)
buildozer android debug

# The APK will be in the bin/ directory
```

### App Features

**Main Chat Screen**
- 💬 Real-time chat with multiple AI personalities
- 📱 Active AIs bar showing current participants
- 🔒 Private chat indicator when in private mode
- 📄 Document attachment indicator
- ➤ Send button and voice input (coming soon)

**Navigation Drawer**
- 💬 Chat - Main conversation
- 👥 Participants - Manage AI personalities
- 🔒 Private Chats - Access private conversations
- 📄 Documents - Manage uploaded files
- 🔧 Tools - View available tools
- 📦 Add-ons - Plugin management
- ⚙️ Settings - App configuration

**Participants Screen**
- View all 10 AI personalities
- Toggle AIs active/inactive
- Rename AI personalities
- Start private conversations
- See AI emotional states

**Settings Screen**
- User profile name
- Model selection (Gemma 3 4B, etc.)
- Ollama URL configuration
- API key management
- P2P hosting/joining
- Data export/import

**Private Chat Features**
- Separate conversation threads
- Personal AI interactions
- Persistent history in Documents folder

## Add-on System

The AI Chat Room supports add-ons (plugins) for extending functionality.

### Installing Add-ons

Place add-ons in the `src/addons/` directory. Each add-on needs:
- A directory with the add-on ID
- `manifest.json` with metadata
- `__init__.py` with the add-on class

### Creating an Add-on

1. Create a new directory in `src/addons/`:

```bash
mkdir -p src/addons/my_addon
```

2. Create `manifest.json`:

```json
{
    "id": "my_addon",
    "name": "My Add-on",
    "version": "1.0.0",
    "description": "A custom add-on",
    "author": "Your Name",
    "permissions": ["tools"]
}
```

3. Create `__init__.py`:

```python
from addons import AddonBase, AddonMetadata

class MyAddon(AddonBase):
    def on_load(self) -> bool:
        print("My add-on loaded!")
        return True
    
    def on_unload(self) -> bool:
        return True
    
    def get_tools(self):
        return [
            {
                "name": "my_tool",
                "description": "Does something cool",
                "parameters": {},
                "function": self._my_tool,
                "category": "custom"
            }
        ]
    
    def _my_tool(self):
        return {"success": True, "output": "Hello from my add-on!"}
```

### Add-on Capabilities

Add-ons can provide:
- **Custom Tools**: New tools for AI to use
- **AI Personalities**: New AI characters
- **Chat Commands**: Custom `/` commands
- **Message Hooks**: Process messages and responses

### Managing Add-ons

In the terminal app:
```
/addons  # List installed add-ons
```

In the Android app:
- Tap the 📦 button to open the add-ons manager
- Toggle add-ons on/off
- View add-on details

## How It Works

1. **Multi-Agent Chat**: Multiple AI participants with distinct personalities
2. **RLM Context**: Uses Recursive Language Models for efficient context handling
3. **Safe Execution**: RestrictedPython for secure code execution
4. **Async Design**: Efficient async/await pattern for responsive chat
5. **Add-on Architecture**: Modular plugin system for extensibility

## Development

```bash
# Clone repository
git clone https://github.com/Kaleaon/Landseek.git
cd Landseek

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=src/rlm --cov-report=term-missing

# Type checking
mypy src/rlm

# Linting
ruff check src/rlm

# Format code
black src/rlm tests chat_room.py
```

## Requirements

- Python 3.9 or higher
- Gemini API key (for cloud) OR Ollama (for local)
- ~50MB storage
- ~100MB RAM during operation

## API Keys Setup

### Google Gemini (Recommended)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Set environment variable: `export GEMINI_API_KEY="your-key"`

### OpenAI (Alternative)

```bash
export OPENAI_API_KEY="sk-..."
```

### Anthropic (Alternative)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Troubleshooting

### "API key not found"
- Ensure your API key is set correctly
- Check if `.env` file exists and has the correct format
- Try exporting directly: `export GEMINI_API_KEY="your-key"`

### "Model not found"
- Check the model name format
- For Gemini: `gemini/gemini-2.0-flash`
- For Ollama: `ollama/model-name`

### Using Ollama
1. Make sure Ollama is running: `ollama serve`
2. Pull a model first: `ollama pull llama3.2`
3. Use with: `export OLLAMA_MODEL="ollama/llama3.2"`

### On Termux
- If pip fails, try: `pip install --break-system-packages -e .`
- For SSL errors: `pkg install openssl`

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Credits

- Based on [Recursive Language Models (RLM)](https://github.com/ysz/recursive-llm) by Grigori Gvadzabia
- RLM paper by Alex Zhang and Omar Khattab (MIT, 2025)
- Powered by [LiteLLM](https://github.com/BerriAI/litellm)
- Safe execution via [RestrictedPython](https://restrictedpython.readthedocs.io/)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- **Repository**: https://github.com/Kaleaon/Landseek
- **RLM Paper**: https://alexzhang13.github.io/blog/2025/rlm/
- **LiteLLM Docs**: https://docs.litellm.ai/
- **Gemini API**: https://ai.google.dev/
