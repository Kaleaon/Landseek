# AI Chat Room for Pixel 10 Pro 🤖💬

A conversational AI chat room application powered by [Recursive Language Models (RLM)](https://github.com/ysz/recursive-llm) and Google's **Gemma 3 4B** model. Designed to run locally on Android devices like Pixel 10 Pro, optimized for **Google Pixel TPU**.

## Features

- 🎭 **Multi-AI Participants**: Chat room with multiple AI personalities
- 🚀 **Gemma 3 4B Powered**: Optimized for Google Pixel TPU acceleration
- 📱 **Pixel TPU Optimized**: Leverages on-device TPU for fast local inference
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
├── chat_room.py          # Main application
├── src/rlm/              # RLM library
│   ├── core.py          # Core RLM logic
│   ├── parser.py        # Response parsing
│   ├── prompts.py       # System prompts
│   ├── repl.py          # Safe code execution
│   └── types.py         # Type definitions
├── tests/               # Test suite
├── examples/            # Usage examples
├── pyproject.toml       # Package configuration
└── .env.example         # Environment template
```

## How It Works

1. **Multi-Agent Chat**: Multiple AI participants with distinct personalities
2. **RLM Context**: Uses Recursive Language Models for efficient context handling
3. **Safe Execution**: RestrictedPython for secure code execution
4. **Async Design**: Efficient async/await pattern for responsive chat

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
