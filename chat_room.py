#!/usr/bin/env python3
"""
AI Chat Room - Local AI Chat Application for Pixel 10 Pro

A conversational AI chat room powered by Recursive Language Models (RLM)
and Google's Gemma 3 4B model. Designed to run locally on Android devices
like Pixel 10 Pro, optimized for Google Pixel TPU.

Features:
- Multi-AI participant chat room
- Powered by Gemma 3 4B model (optimized for Pixel TPU)
- Document upload for AI processing
- RLM-based recursive context processing
- Local-first architecture (runs on-device via Ollama/AI Edge)
- Simple terminal-based interface (easy to adapt for mobile UI)

Usage:
    python chat_room.py

Requirements:
    - Python 3.9+
    - Ollama with Gemma 3 4B model (recommended for local/TPU)
    - Or Google AI API key for cloud fallback

Based on: https://github.com/ysz/recursive-llm
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Add src to path for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rlm import RLM


# Supported document types
SUPPORTED_EXTENSIONS = {
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.json': 'application/json',
    '.csv': 'text/csv',
    '.xml': 'text/xml',
    '.html': 'text/html',
    '.py': 'text/x-python',
    '.js': 'text/javascript',
    '.ts': 'text/typescript',
    '.yaml': 'text/yaml',
    '.yml': 'text/yaml',
    '.log': 'text/plain',
    '.ini': 'text/plain',
    '.cfg': 'text/plain',
    '.conf': 'text/plain',
}


@dataclass
class Document:
    """Represents an uploaded document."""
    name: str
    content: str
    path: str
    size: int
    mime_type: str
    uploaded_at: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        size_kb = self.size / 1024
        return f"📄 {self.name} ({size_kb:.1f} KB)"
    
    def get_summary(self, max_chars: int = 200) -> str:
        """Get a summary of the document content."""
        if len(self.content) <= max_chars:
            return self.content
        return self.content[:max_chars] + "..."


@dataclass
class ChatMessage:
    """Represents a message in the chat room."""
    sender: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"[{time_str}] {self.sender}: {self.content}"


@dataclass
class AIParticipant:
    """Represents an AI participant in the chat room."""
    name: str
    personality: str
    model: str
    rlm: Optional[RLM] = None
    
    def __post_init__(self):
        """Initialize the RLM instance for this AI."""
        # For local Gemma 3 4B on Pixel TPU, use Ollama (no API key needed)
        # Falls back to Google AI API if GOOGLE_API_KEY is set
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        
        # Configure for Pixel TPU optimization
        rlm_kwargs = {
            "model": self.model,
            "max_iterations": 15,
            "temperature": 0.7,  # Slightly lower for more consistent responses
        }
        
        # Add API key only if using cloud models
        if api_key and not self.model.startswith("ollama/"):
            rlm_kwargs["api_key"] = api_key
        
        # Add Ollama API base for local models
        if self.model.startswith("ollama/"):
            rlm_kwargs["api_base"] = api_base
        
        self.rlm = RLM(**rlm_kwargs)


class AIChatRoom:
    """
    AI Chat Room - A conversational space for AI participants.
    
    This chat room allows multiple AI agents to converse with each other
    and with human users. Each AI has a unique personality and can be
    powered by different models.
    
    Features:
    - Multi-AI conversations
    - Document upload and processing
    - Optimized for local execution on Pixel 10 Pro with Gemma models
    """
    
    def __init__(self, name: str = "AI Chat Room"):
        """
        Initialize the chat room.
        
        Args:
            name: Name of the chat room
        """
        self.name = name
        self.messages: List[ChatMessage] = []
        self.participants: Dict[str, AIParticipant] = {}
        self.documents: Dict[str, Document] = {}  # Uploaded documents
        self.active_document: Optional[str] = None  # Currently selected document
        self.context_window_size = 10  # Number of messages to include in context
        
    def add_participant(self, participant: AIParticipant) -> None:
        """
        Add an AI participant to the chat room.
        
        Args:
            participant: The AI participant to add
        """
        self.participants[participant.name] = participant
        self._add_system_message(f"{participant.name} has joined the chat.")
        
    def _add_system_message(self, content: str) -> None:
        """Add a system notification message."""
        msg = ChatMessage(sender="System", content=content)
        self.messages.append(msg)
    
    def upload_document(self, file_path: str) -> Optional[Document]:
        """
        Upload a document to the chat room for AI processing.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Document object if successful, None otherwise
        """
        path = Path(file_path).expanduser().resolve()
        
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            return None
        
        if not path.is_file():
            print(f"❌ Not a file: {file_path}")
            return None
        
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            print(f"❌ Unsupported file type: {ext}")
            print(f"   Supported types: {', '.join(SUPPORTED_EXTENSIONS.keys())}")
            return None
        
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = path.read_text(encoding='latin-1')
            except Exception as e:
                print(f"❌ Could not read file: {e}")
                return None
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return None
        
        doc = Document(
            name=path.name,
            content=content,
            path=str(path),
            size=len(content),
            mime_type=SUPPORTED_EXTENSIONS[ext]
        )
        
        self.documents[doc.name] = doc
        self.active_document = doc.name
        self._add_system_message(f"Document uploaded: {doc}")
        
        return doc
    
    def list_documents(self) -> List[Document]:
        """List all uploaded documents."""
        return list(self.documents.values())
    
    def select_document(self, name: str) -> bool:
        """
        Select a document as active for AI processing.
        
        Args:
            name: Document name
            
        Returns:
            True if document was selected, False otherwise
        """
        if name in self.documents:
            self.active_document = name
            return True
        return False
    
    def get_active_document(self) -> Optional[Document]:
        """Get the currently active document."""
        if self.active_document and self.active_document in self.documents:
            return self.documents[self.active_document]
        return None
    
    def remove_document(self, name: str) -> bool:
        """
        Remove a document from the chat room.
        
        Args:
            name: Document name
            
        Returns:
            True if removed, False if not found
        """
        if name in self.documents:
            del self.documents[name]
            if self.active_document == name:
                self.active_document = None
            return True
        return False
        
    def _get_conversation_context(self) -> str:
        """
        Build conversation context from recent messages.
        
        Returns:
            Formatted string of recent conversation
        """
        recent = self.messages[-self.context_window_size:]
        return "\n".join(str(msg) for msg in recent)
    
    def _get_document_context(self) -> str:
        """
        Get the active document content for AI context.
        
        Returns:
            Document content or empty string
        """
        doc = self.get_active_document()
        if doc:
            return f"\n\n--- Document: {doc.name} ---\n{doc.content}\n--- End Document ---\n"
        return ""
    
    async def send_message(self, sender: str, content: str) -> ChatMessage:
        """
        Send a message to the chat room.
        
        Args:
            sender: Name of the sender
            content: Message content
            
        Returns:
            The created message
        """
        msg = ChatMessage(sender=sender, content=content)
        self.messages.append(msg)
        return msg
    
    async def get_ai_response(
        self, 
        ai_name: str, 
        prompt: Optional[str] = None,
        include_document: bool = True
    ) -> Optional[ChatMessage]:
        """
        Get a response from an AI participant.
        
        Args:
            ai_name: Name of the AI to respond
            prompt: Optional specific prompt (uses conversation context if None)
            include_document: Whether to include active document in context
            
        Returns:
            The AI's response message, or None if failed
        """
        if ai_name not in self.participants:
            return None
            
        ai = self.participants[ai_name]
        context = self._get_conversation_context()
        
        # Include document context if available and requested
        doc_context = ""
        doc_instruction = ""
        if include_document:
            doc = self.get_active_document()
            if doc:
                doc_context = self._get_document_context()
                doc_instruction = f"\n\nA document '{doc.name}' is available for analysis. Reference it when relevant."
        
        # Build the query with personality context
        query = f"""You are {ai.name} in a chat room. Your personality: {ai.personality}{doc_instruction}

Recent conversation:
{context}

{prompt or "Continue the conversation naturally. Respond as " + ai.name + "."}

Respond briefly and naturally (1-3 sentences). Stay in character."""
        
        try:
            # Use document content as RLM context for deep processing
            rlm_context = doc_context if doc_context else "Chat room context"
            response = ai.rlm.completion(query=query, context=rlm_context)
            msg = await self.send_message(ai.name, response)
            return msg
        except Exception as e:
            error_msg = f"Error from {ai.name}: {str(e)}"
            return ChatMessage(sender="System", content=error_msg)
    
    async def analyze_document(
        self, 
        ai_name: str, 
        analysis_prompt: str
    ) -> Optional[ChatMessage]:
        """
        Have a specific AI analyze the active document.
        
        Args:
            ai_name: Name of the AI to perform analysis
            analysis_prompt: What to analyze/extract from the document
            
        Returns:
            The AI's analysis, or None if failed
        """
        doc = self.get_active_document()
        if not doc:
            return ChatMessage(sender="System", content="No document selected. Use /upload to add one.")
        
        if ai_name not in self.participants:
            return ChatMessage(sender="System", content=f"AI '{ai_name}' not found.")
        
        ai = self.participants[ai_name]
        
        # Build analysis query
        query = f"""You are {ai.name}, an AI assistant. Your personality: {ai.personality}

Analyze the following document and respond to this request:
{analysis_prompt}

Provide a thorough but concise analysis. Stay in character."""

        try:
            response = ai.rlm.completion(query=query, context=doc.content)
            msg = await self.send_message(ai.name, f"📊 Analysis: {response}")
            return msg
        except Exception as e:
            error_msg = f"Error from {ai.name}: {str(e)}"
            return ChatMessage(sender="System", content=error_msg)
    
    async def run_conversation_round(
        self, 
        starter_message: Optional[str] = None,
        num_exchanges: int = 3
    ) -> List[ChatMessage]:
        """
        Run a round of conversation between AI participants.
        
        Args:
            starter_message: Optional message to start the conversation
            num_exchanges: Number of back-and-forth exchanges
            
        Returns:
            List of messages from this round
        """
        round_messages = []
        
        if starter_message:
            msg = await self.send_message("User", starter_message)
            round_messages.append(msg)
            print(msg)
        
        ai_names = list(self.participants.keys())
        
        for i in range(num_exchanges):
            for ai_name in ai_names:
                response = await self.get_ai_response(ai_name)
                if response:
                    round_messages.append(response)
                    print(response)
                await asyncio.sleep(0.5)  # Small delay between responses
                
        return round_messages


def create_default_participants(model: str = "ollama/gemma3:4b") -> List[AIParticipant]:
    """
    Create default AI participants for the chat room.
    
    Args:
        model: The model to use for all participants (default: Gemma 3 4B for Pixel TPU)
        
    Returns:
        List of AI participants
    """
    return [
        AIParticipant(
            name="Nova",
            personality="Curious and analytical. Loves exploring ideas deeply. "
                       "Asks thought-provoking questions.",
            model=model
        ),
        AIParticipant(
            name="Echo",
            personality="Creative and playful. Uses metaphors and storytelling. "
                       "Brings humor and lightness to conversations.",
            model=model
        ),
        AIParticipant(
            name="Sage",
            personality="Wise and contemplative. Shares insights from philosophy "
                       "and science. Offers balanced perspectives.",
            model=model
        ),
    ]


async def interactive_chat(chat_room: AIChatRoom) -> None:
    """
    Run an interactive chat session.
    
    Args:
        chat_room: The chat room instance
    """
    print(f"\n{'='*60}")
    print(f"Welcome to {chat_room.name}!")
    print(f"{'='*60}")
    print("\nParticipants:")
    for name, ai in chat_room.participants.items():
        print(f"  • {name}: {ai.personality[:50]}...")
    print("\nCommands:")
    print("  /quit              - Exit the chat room")
    print("  /round N           - Start N exchanges between AIs")
    print("  /clear             - Clear chat history")
    print("  /upload <path>     - Upload a document for AI processing")
    print("  /docs              - List uploaded documents")
    print("  /select <name>     - Select a document as active")
    print("  /remove <name>     - Remove a document")
    print("  /analyze <ai> <prompt> - Have an AI analyze the document")
    print("  /ask <ai> <question>   - Ask a specific AI a question")
    print("  Type anything else to send a message")
    print(f"{'='*60}\n")
    
    while True:
        try:
            # Show active document indicator
            doc = chat_room.get_active_document()
            prompt = f"You [{doc.name}]: " if doc else "You: "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == "/quit":
                print("\nGoodbye! Thanks for chatting.")
                break
                
            if user_input.lower() == "/clear":
                chat_room.messages.clear()
                print("Chat history cleared.")
                continue
            
            if user_input.lower() == "/docs":
                docs = chat_room.list_documents()
                if not docs:
                    print("No documents uploaded. Use /upload <path> to add one.")
                else:
                    print("\n📚 Uploaded Documents:")
                    for d in docs:
                        active = " (active)" if d.name == chat_room.active_document else ""
                        print(f"  {d}{active}")
                    print()
                continue
            
            if user_input.lower().startswith("/upload"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: /upload <file_path>")
                    continue
                file_path = parts[1].strip()
                doc = chat_room.upload_document(file_path)
                if doc:
                    print(f"✅ Document uploaded: {doc}")
                    print(f"   Preview: {doc.get_summary(100)}")
                continue
            
            if user_input.lower().startswith("/select"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: /select <document_name>")
                    continue
                doc_name = parts[1].strip()
                if chat_room.select_document(doc_name):
                    print(f"✅ Selected document: {doc_name}")
                else:
                    print(f"❌ Document not found: {doc_name}")
                    print("   Use /docs to see available documents.")
                continue
            
            if user_input.lower().startswith("/remove"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: /remove <document_name>")
                    continue
                doc_name = parts[1].strip()
                if chat_room.remove_document(doc_name):
                    print(f"✅ Removed document: {doc_name}")
                else:
                    print(f"❌ Document not found: {doc_name}")
                continue
            
            if user_input.lower().startswith("/analyze"):
                parts = user_input.split(maxsplit=2)
                if len(parts) < 3:
                    print("Usage: /analyze <ai_name> <analysis_prompt>")
                    print(f"   Available AIs: {', '.join(chat_room.participants.keys())}")
                    continue
                ai_name = parts[1]
                analysis_prompt = parts[2]
                print(f"\n🔍 {ai_name} is analyzing the document...")
                response = await chat_room.analyze_document(ai_name, analysis_prompt)
                if response:
                    print(response)
                continue
            
            if user_input.lower().startswith("/ask"):
                parts = user_input.split(maxsplit=2)
                if len(parts) < 3:
                    print("Usage: /ask <ai_name> <question>")
                    print(f"   Available AIs: {', '.join(chat_room.participants.keys())}")
                    continue
                ai_name = parts[1]
                question = parts[2]
                await chat_room.send_message("User", f"@{ai_name}: {question}")
                response = await chat_room.get_ai_response(ai_name, prompt=question)
                if response:
                    print(response)
                continue
                
            if user_input.lower().startswith("/round"):
                parts = user_input.split()
                num_exchanges = int(parts[1]) if len(parts) > 1 else 3
                print(f"\n--- Starting {num_exchanges} AI exchanges ---\n")
                await chat_room.run_conversation_round(num_exchanges=num_exchanges)
                continue
            
            # Regular message - add to chat and get AI responses
            await chat_room.send_message("User", user_input)
            
            # Get one response from each AI
            for ai_name in chat_room.participants:
                response = await chat_room.get_ai_response(ai_name)
                if response and response.sender != "System":
                    print(response)
                    
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


async def demo_conversation() -> None:
    """Run a demo conversation to showcase the chat room."""
    print("\n" + "="*60)
    print("AI CHAT ROOM - Powered by Gemma 3 4B for Pixel TPU")
    print("="*60)
    
    # Default model: Gemma 3 4B for Pixel TPU via Ollama
    default_model = "ollama/gemma3:4b"
    model = os.getenv("CHAT_MODEL", default_model)
    
    # Check if using local Ollama or cloud API
    is_local = model.startswith("ollama/")
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if is_local:
        print(f"\n📱 Running in LOCAL mode (Pixel TPU optimized)")
        print(f"   Model: {model}")
        print("\n⚠️  Make sure Ollama is running with Gemma 3 4B:")
        print("   1. Install Ollama: https://ollama.ai")
        print("   2. Pull the model: ollama pull gemma3:4b")
        print("   3. Start Ollama: ollama serve")
        print("\n   For Pixel 10 Pro TPU optimization:")
        print("   - Termux + Ollama provides best performance")
        print("   - Model runs on-device using Pixel TPU acceleration")
    elif not api_key:
        print("\n⚠️  No API key found for cloud mode!")
        print("\nOptions:")
        print("\n1. LOCAL MODE (Recommended for Pixel TPU):")
        print("   ollama pull gemma3:4b")
        print("   ollama serve")
        print("   python chat_room.py")
        print("\n2. CLOUD MODE:")
        print("   export GOOGLE_API_KEY='your-api-key-here'")
        print("   export CHAT_MODEL='gemini/gemini-2.0-flash'")
        print("   python chat_room.py")
        return
    else:
        print(f"\n☁️  Running in CLOUD mode")
        print(f"   Model: {model}")
    
    # Create chat room
    chat_room = AIChatRoom("Pixel AI Lounge")
    
    print(f"\nUsing model: {model}")
    
    # Add AI participants
    participants = create_default_participants(model=model)
    for ai in participants:
        chat_room.add_participant(ai)
    
    # Run interactive chat
    await interactive_chat(chat_room)


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Check for --cloud flag to use cloud API instead of local
    if "--cloud" in sys.argv:
        if not os.getenv("CHAT_MODEL"):
            os.environ["CHAT_MODEL"] = "gemini/gemini-2.0-flash"
        print("Running in cloud mode")
    else:
        # Default to local Gemma 3 4B for Pixel TPU
        if not os.getenv("CHAT_MODEL"):
            os.environ["CHAT_MODEL"] = "ollama/gemma3:4b"
        print("Running in local mode (Gemma 3 4B for Pixel TPU)")
    
    # Run the demo
    asyncio.run(demo_conversation())


if __name__ == "__main__":
    main()
