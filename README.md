# AI Chat Room for Pixel 10 Pro 🤖💬

A conversational AI chat room application powered by [Recursive Language Models (RLM)](https://github.com/ysz/recursive-llm) and Google's **Gemma 3 4B** model. Designed to run locally on Android devices like Pixel 10 Pro, optimized for **Google Pixel TPU**.

## Features

- 🎭 **10 AI Personalities**: Chat room with up to 10 unique AI personalities (Nova, Echo, Sage, Spark, Atlas, Luna, Cipher, Muse, Phoenix, Zen)
- 🌐 **P2P Networking**: Share your LLM capabilities with others via share codes - no server required!
- 🚀 **Gemma 3 4B Powered**: Optimized for Google Pixel TPU acceleration
- 📱 **Android App**: Native Android application with Kivy
- 📦 **Add-on System**: Extensible plugin architecture for custom functionality
- 🔧 **Tool Use**: AI can use built-in tools (calculator, file ops, text analysis, etc.)
- 📄 **Document Processing**: Upload and analyze documents with AI
- 🔄 **Recursive Context**: Uses RLM for intelligent context processing
- 🏠 **Local First**: Runs fully on-device - no cloud required
- 💾 **Lightweight**: ~4GB model size, efficient memory usage

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

# Cloud models (require API key)
model="gemini/gemini-2.0-flash"
model="gemini/gemini-1.5-pro"
model="gpt-4o"
model="claude-sonnet-4"
```

### Pixel TPU Compatibility

| Model | Size | Pixel TPU Performance |
|-------|------|----------------------|
| gemma3:2b | ~2GB | ⚡ Excellent (fastest) |
| **gemma3:4b** | ~4GB | ⚡ Very Good (recommended) |
| gemma3:8b | ~8GB | 🔄 Good (slower, more capable) |

## Architecture

```
AI Chat Room
├── chat_room.py          # Main terminal application
├── android/              # Android app (Kivy)
│   └── main.py          # Kivy Android entry point
├── src/
│   ├── rlm/              # RLM library
│   │   ├── core.py      # Core RLM logic
│   │   ├── parser.py    # Response parsing
│   │   ├── prompts.py   # System prompts
│   │   ├── repl.py      # Safe code execution
│   │   └── types.py     # Type definitions
│   ├── tools.py          # Built-in tools
│   ├── personalities.py  # AI personality definitions (10 personalities)
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

### Building the APK

The Android app is built using Kivy and Buildozer:

```bash
# Install Buildozer
pip install buildozer

# Install Android SDK dependencies (Linux/macOS)
buildozer android debug

# The APK will be in the bin/ directory
```

### Features
- Native Android UI with Material Design
- Chat with multiple AI personalities
- Document upload and analysis
- Add-on management
- Settings for model configuration

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
