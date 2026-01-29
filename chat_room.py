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
- Tool use capabilities (calculator, file ops, text analysis, etc.)
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
import random
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Add src to path for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rlm import RLM
from tools import tool_registry, parse_tool_call, get_tools_description, ToolResult
from addons import addon_manager, get_addon_manager
from personalities import (
    PersonalityManager, PersonalityDefinition, 
    get_personality_manager, get_default_personalities,
    BUILTIN_PERSONALITIES, MAX_PERSONALITIES
)
from p2p import (
    P2PServer, P2PClient, P2PHandler, PeerInfo, PeerRole,
    generate_room_code, encode_connection_info, decode_connection_info,
    get_local_ip, SimpleP2PHandler
)
from ai_state import (
    AIStateManager, AIState, PrivateConversation, ChatHistoryEntry,
    EmotionalState, get_state_manager, initialize_state_manager,
    get_documents_folder
)


# Import document reader for multi-format support
try:
    from document_reader import (
        read_document, DocumentContent, 
        SUPPORTED_EXTENSIONS, get_supported_extensions,
        get_supported_formats, check_dependencies, get_missing_dependencies
    )
    DOCUMENT_READER_AVAILABLE = True
except ImportError:
    DOCUMENT_READER_AVAILABLE = False
    # Fallback to basic supported extensions
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
    title: Optional[str] = None
    author: Optional[str] = None
    pages: int = 1
    word_count: int = 0
    original_format: str = "text"
    source_type: str = "file"  # file, url
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        size_kb = self.size / 1024
        info = f"📄 {self.name} ({size_kb:.1f} KB"
        if self.pages > 1:
            info += f", {self.pages} pages"
        if self.word_count > 0:
            info += f", {self.word_count:,} words"
        info += ")"
        return info
    
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


# Import RAG after other imports to avoid circular dependency
try:
    from rag import AIRAGStore, RAGManager, get_rag_manager, initialize_rag_manager
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    AIRAGStore = None
    RAGManager = None


@dataclass
class AIParticipant:
    """Represents an AI participant in the chat room."""
    name: str
    personality: str
    model: str
    rlm: Optional[RLM] = None
    ai_id: str = None  # Unique ID for state management
    display_name: str = None  # Customizable display name
    avatar: str = "🤖"
    state: Optional[AIState] = None  # Persistent state
    rag_store: Optional[Any] = None  # Private RAG/knowledge store
    
    def __post_init__(self):
        """Initialize the RLM instance for this AI."""
        # Set defaults
        if self.ai_id is None:
            self.ai_id = self.name.lower()
        if self.display_name is None:
            self.display_name = self.name
            
        # For local Gemma 3 4B on Pixel TPU, use Ollama (no API key needed)
        # Falls back to Google AI API if GOOGLE_API_KEY is set
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        
        # Initialize RAG store for this AI (10M+ token private knowledge base)
        if RAG_AVAILABLE:
            try:
                rag_manager = get_rag_manager()
                self.rag_store = rag_manager.get_store(self.ai_id)
            except Exception as e:
                print(f"Warning: Could not initialize RAG store for {self.ai_id}: {e}")
                self.rag_store = None
        
        # Configure for Pixel TPU optimization
        rlm_kwargs = {
            "model": self.model,
            "max_iterations": 15,
            "temperature": 0.7,  # Slightly lower for more consistent responses
            "rag_store": self.rag_store,  # Pass RAG store to RLM
            "ai_name": self.display_name or self.name,
        }
        
        # Add API key only if using cloud models
        if api_key and not self.model.startswith("ollama/"):
            rlm_kwargs["api_key"] = api_key
        
        # Add Ollama API base for local models
        if self.model.startswith("ollama/"):
            rlm_kwargs["api_base"] = api_base
        
        self.rlm = RLM(**rlm_kwargs)
    
    def rename(self, new_name: str) -> None:
        """Change the display name of this AI."""
        self.display_name = new_name
        if self.state:
            self.state.rename(new_name)
        # Update RLM's ai_name
        if self.rlm:
            self.rlm.ai_name = new_name
    
    def get_display_name(self) -> str:
        """Get the display name with avatar."""
        return f"{self.avatar} {self.display_name}"
    
    def get_rag_stats(self) -> Optional[Dict[str, Any]]:
        """Get statistics about this AI's RAG knowledge base."""
        if self.rag_store:
            stats = self.rag_store.get_stats()
            return stats.to_dict() if hasattr(stats, 'to_dict') else stats
        return None
    
    def add_to_knowledge(self, content: str, source: str = "user") -> Optional[str]:
        """Add content to this AI's knowledge base."""
        if self.rag_store:
            return self.rag_store.add_memory(content, source=source, importance=0.7)
        return None
    
    def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search this AI's knowledge base."""
        if self.rag_store:
            results = self.rag_store.retrieve(query, top_k=top_k)
            return [
                {
                    "content": r.chunk.content,
                    "source": r.chunk.source,
                    "type": r.chunk.source_type,
                    "score": r.score
                }
                for r in results
            ]
        return []
    
    def index_document(self, content: str, source_name: str) -> List[str]:
        """Index a document into this AI's knowledge base."""
        if self.rag_store:
            return self.rag_store.add_document(content, source_name)
        return []


class AIChatRoom:
    """
    AI Chat Room - A conversational space for AI participants.
    
    This chat room allows multiple AI agents to converse with each other
    and with human users. Each AI has a unique personality and can be
    powered by different models.
    
    Features:
    - Multi-AI conversations (up to 10 personalities)
    - Document upload and processing
    - Tool use capabilities
    - Add-on/plugin support
    - P2P networking for sharing LLM capabilities
    - Persistent state (chat history, emotions, relationships)
    - Private conversations between participants
    - Customizable AI names via settings
    - Optimized for local execution on Pixel 10 Pro with Gemma models
    """
    
    def __init__(
        self, 
        name: str = "AI Chat Room", 
        enable_tools: bool = True, 
        enable_addons: bool = True,
        enable_p2p: bool = False,
        max_personalities: int = MAX_PERSONALITIES,
        enable_state: bool = True
    ):
        """
        Initialize the chat room.
        
        Args:
            name: Name of the chat room
            enable_tools: Whether to enable AI tool use
            enable_addons: Whether to enable add-ons
            enable_p2p: Whether to enable P2P networking
            max_personalities: Maximum number of AI personalities (up to 10)
            enable_state: Whether to enable persistent state management
        """
        self.name = name
        self.messages: List[ChatMessage] = []
        self.participants: Dict[str, AIParticipant] = {}
        self.documents: Dict[str, Document] = {}  # Uploaded documents
        self.active_document: Optional[str] = None  # Currently selected document
        self.context_window_size = 10  # Number of messages to include in context
        self.enable_tools = enable_tools  # Enable tool use
        self.enable_addons = enable_addons  # Enable add-ons
        self.enable_p2p = enable_p2p  # Enable P2P networking
        self.enable_state = enable_state  # Enable state management
        self.max_personalities = min(max_personalities, MAX_PERSONALITIES)
        self.addon_manager = get_addon_manager() if enable_addons else None
        self.personality_manager = get_personality_manager()
        
        # Free Will / Autonomy
        self.free_will_enabled = False
        self.free_will_task: Optional[asyncio.Task] = None

        # State management
        self.state_manager: Optional[AIStateManager] = None
        if enable_state:
            self.state_manager = get_state_manager()
        
        # P2P networking
        self.p2p_server: Optional[P2PServer] = None
        self.p2p_client: Optional[P2PClient] = None
        self.p2p_mode: Optional[str] = None  # "host" or "client"
        self.connected_peers: Dict[str, PeerInfo] = {}
        
        # Private conversations tracking
        self._active_private_chat: Optional[Tuple[str, str]] = None  # (from, to)
        
        # User name for state tracking
        self.user_name = "User"
        
        # Load add-ons
        if self.addon_manager:
            count = self.addon_manager.load_all()
            if count > 0:
                self._add_system_message(f"Loaded {count} add-on(s)")
        
        # Load saved state for user
        if self.state_manager:
            saved_user = self.state_manager.get_setting("user_name")
            if saved_user:
                self.user_name = saved_user
    
    def start_hosting(self, port: int = 8765) -> Optional[str]:
        """
        Start hosting a P2P chat room.
        
        Args:
            port: Port to listen on
            
        Returns:
            Share code for others to join, or None if failed
        """
        if self.p2p_mode:
            return None  # Already in P2P mode
        
        handler = ChatRoomP2PHandler(self)
        self.p2p_server = P2PServer(
            handler=handler,
            port=port,
            room_name=self.name
        )
        
        try:
            self.p2p_server.start()
            self.p2p_mode = "host"
            share_code = self.p2p_server.get_share_code()
            self._add_system_message(f"🌐 Room is now shared! Share code: {share_code}")
            return share_code
        except Exception as e:
            self._add_system_message(f"Failed to start hosting: {e}")
            self.p2p_server = None
            return None
    
    def stop_hosting(self) -> None:
        """Stop hosting the P2P chat room."""
        if self.p2p_server:
            self.p2p_server.stop()
            self.p2p_server = None
            self.p2p_mode = None
            self.connected_peers.clear()
            self._add_system_message("🔌 Room sharing stopped.")
    
    def join_room(self, share_code: str, name: str = "Guest") -> bool:
        """
        Join a remote P2P chat room.
        
        Args:
            share_code: The share code from the host
            name: Your display name
            
        Returns:
            True if connected successfully
        """
        if self.p2p_mode:
            return False  # Already in P2P mode
        
        handler = ChatRoomP2PHandler(self)
        self.p2p_client = P2PClient(handler=handler, name=name)
        
        if self.p2p_client.connect(share_code):
            self.p2p_mode = "client"
            self._add_system_message(f"🌐 Connected to remote room!")
            return True
        else:
            self.p2p_client = None
            return False
    
    def leave_room(self) -> None:
        """Leave the current P2P room."""
        if self.p2p_client:
            self.p2p_client.disconnect()
            self.p2p_client = None
            self.p2p_mode = None
            self.connected_peers.clear()
            self._add_system_message("🔌 Disconnected from room.")
    
    def get_share_code(self, use_public_ip: bool = False) -> Optional[str]:
        """Get the share code for this room (host only)."""
        if self.p2p_server:
            return self.p2p_server.get_share_code(use_public_ip)
        return None
    
    def is_host(self) -> bool:
        """Check if this is the host."""
        return self.p2p_mode == "host"
    
    def is_client(self) -> bool:
        """Check if this is a client."""
        return self.p2p_mode == "client"
    
    def get_peer_count(self) -> int:
        """Get the number of connected peers."""
        return len(self.connected_peers)
        
    def add_participant(self, participant: AIParticipant) -> bool:
        """
        Add an AI participant to the chat room.
        
        Args:
            participant: The AI participant to add
            
        Returns:
            True if added, False if at max capacity
        """
        if len(self.participants) >= self.max_personalities:
            self._add_system_message(f"Cannot add {participant.display_name}: Maximum {self.max_personalities} personalities reached.")
            return False
        
        # Load or create state
        if self.state_manager:
            state = self.state_manager.get_state(participant.ai_id)
            if not state:
                state = self.state_manager.create_state(
                    ai_id=participant.ai_id,
                    display_name=participant.display_name,
                    personality=participant.personality,
                    avatar=participant.avatar
                )
            participant.state = state
            participant.display_name = state.display_name
            state.is_active = True
            self.state_manager.save_state(state)
        
        self.participants[participant.ai_id] = participant
        self._add_system_message(f"{participant.get_display_name()} has joined the chat.")
        return True
    
    def remove_participant(self, ai_id: str) -> bool:
        """
        Remove an AI participant from the chat room.
        
        Args:
            ai_id: ID of the participant to remove
            
        Returns:
            True if removed, False if not found
        """
        if ai_id in self.participants:
            participant = self.participants[ai_id]
            display_name = participant.get_display_name()
            
            # Update state
            if self.state_manager and participant.state:
                participant.state.is_active = False
                self.state_manager.save_state(participant.state)
            
            del self.participants[ai_id]
            self._add_system_message(f"{display_name} has left the chat.")
            return True
        return False
    
    def rename_participant(self, ai_id: str, new_name: str) -> bool:
        """
        Rename an AI participant.
        
        Args:
            ai_id: ID of the participant to rename
            new_name: New display name
            
        Returns:
            True if renamed, False if not found
        """
        if ai_id in self.participants:
            participant = self.participants[ai_id]
            old_name = participant.display_name
            participant.rename(new_name)
            
            # Save state
            if self.state_manager and participant.state:
                self.state_manager.save_state(participant.state)
            
            self._add_system_message(f"{old_name} is now known as {new_name}")
            return True
        return False
    
    def get_participant_by_name(self, name: str) -> Optional[AIParticipant]:
        """Find a participant by display name or ID."""
        # Check by ID first
        if name in self.participants:
            return self.participants[name]
        # Check by display name
        name_lower = name.lower()
        for ai_id, participant in self.participants.items():
            if participant.display_name.lower() == name_lower:
                return participant
        return None
    
    # Private conversation methods
    def start_private_chat(self, from_participant: str, to_participant: str) -> bool:
        """
        Start a private conversation between two participants.
        
        Args:
            from_participant: Who is initiating
            to_participant: Who they want to chat with
            
        Returns:
            True if private chat started
        """
        # Validate participants exist (for AIs) or is user
        to_exists = to_participant == self.user_name or to_participant in self.participants
        from_exists = from_participant == self.user_name or from_participant in self.participants
        
        if not to_exists:
            # Try by display name
            found = self.get_participant_by_name(to_participant)
            if found:
                to_participant = found.ai_id
            else:
                return False
        
        self._active_private_chat = (from_participant, to_participant)
        self._add_system_message(f"🔒 Private conversation started between {from_participant} and {to_participant}")
        return True
    
    def end_private_chat(self) -> None:
        """End the current private conversation."""
        if self._active_private_chat:
            self._add_system_message("🔓 Private conversation ended")
            self._active_private_chat = None
    
    def is_in_private_chat(self) -> bool:
        """Check if currently in a private conversation."""
        return self._active_private_chat is not None
    
    def send_private_message(
        self, 
        from_participant: str, 
        to_participant: str, 
        content: str
    ) -> Optional[ChatMessage]:
        """
        Send a private message between two participants.
        
        Args:
            from_participant: Sender
            to_participant: Recipient
            content: Message content
            
        Returns:
            The message, or None if failed
        """
        # Save to state manager
        if self.state_manager:
            self.state_manager.add_private_message(from_participant, to_participant, content)
        
        # Create message (marked as private)
        msg = ChatMessage(
            sender=f"🔒 {from_participant} → {to_participant}",
            content=content
        )
        self.messages.append(msg)
        return msg
    
    async def get_private_ai_response(
        self, 
        ai_id: str, 
        from_participant: str,
        prompt: str
    ) -> Optional[ChatMessage]:
        """
        Get a private response from an AI to another participant.
        
        Args:
            ai_id: The AI to respond
            from_participant: Who the AI is responding to
            prompt: The message to respond to
            
        Returns:
            The AI's private response
        """
        if ai_id not in self.participants:
            return None
        
        ai = self.participants[ai_id]
        
        # Get private conversation history if available
        private_context = ""
        if self.state_manager:
            conv = self.state_manager.get_or_create_conversation(ai_id, from_participant)
            recent = conv.get_recent_messages(5)
            if recent:
                private_context = "\n".join([
                    f"[Private] {m.sender}: {m.content}" for m in recent
                ])
        
        # Build query
        query = f"""You are {ai.display_name} in a PRIVATE conversation with {from_participant}. 
Your personality: {ai.personality}

This is a private, one-on-one conversation. Be more personal and intimate than in group chat.

Previous private messages:
{private_context}

{from_participant} says: {prompt}

Respond privately to {from_participant}. Be personal and direct."""

        try:
            response = await ai.rlm.acompletion(query=query, context="Private conversation")
            
            # Save to state
            msg = self.send_private_message(ai.display_name, from_participant, response)
            
            # Update AI state
            if ai.state and self.state_manager:
                ai.state.update_relationship(from_participant, notes=f"Private chat: {prompt[:50]}")
                self.state_manager.save_state(ai.state)
            
            return msg
        except Exception as e:
            return ChatMessage(sender="System", content=f"Error: {e}")
    
    def get_private_conversations(self, participant: str) -> List[PrivateConversation]:
        """Get all private conversations for a participant."""
        if self.state_manager:
            return self.state_manager.get_conversations_for(participant)
        return []
    
    def set_user_name(self, name: str) -> None:
        """Set the user's display name."""
        self.user_name = name
        if self.state_manager:
            self.state_manager.set_setting("user_name", name)
        
    def save_all_state(self) -> None:
        """Save all AI states."""
        if self.state_manager:
            self.state_manager.save_all()
        
    def _add_system_message(self, content: str) -> None:
        """Add a system notification message."""
        msg = ChatMessage(sender="System", content=content)
        self.messages.append(msg)
    
    def start_free_will_loop(self) -> None:
        """Start the autonomous free will loop."""
        if self.free_will_enabled and self.free_will_task:
            return  # Already running

        self.free_will_enabled = True
        self.free_will_task = asyncio.create_task(self._free_will_loop())
        self._add_system_message("🤖 AI Free Will enabled. Agents may now act autonomously.")

    def stop_free_will_loop(self) -> None:
        """Stop the autonomous free will loop."""
        self.free_will_enabled = False
        if self.free_will_task:
            self.free_will_task.cancel()
            self.free_will_task = None
        self._add_system_message("🤖 AI Free Will disabled.")

    async def _free_will_loop(self) -> None:
        """Background loop for AI autonomy."""
        while self.free_will_enabled:
            # Random wait between checks (e.g., 10-30 seconds)
            wait_time = random.uniform(10, 30)
            try:
                await asyncio.sleep(wait_time)

                # Check if we have participants
                if not self.participants:
                    continue

                # Pick a random participant
                ai_ids = list(self.participants.keys())
                ai_id = random.choice(ai_ids)

                # 30% chance to actually try to speak to avoid too much noise
                if random.random() < 0.3:
                    await self.check_ai_free_will(ai_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in free will loop: {e}")
                await asyncio.sleep(5)  # Wait a bit on error

    async def check_ai_free_will(self, ai_id: str) -> None:
        """
        Ask an AI if they want to initiate an action autonomously.

        Args:
            ai_id: ID of the AI to check
        """
        if ai_id not in self.participants:
            return

        ai = self.participants[ai_id]
        context = self._get_conversation_context()
        doc = self.get_active_document()

        doc_info = ""
        if doc:
            doc_info = f"\nActive Document: {doc.name}\n"

        query = f"""You are {ai.display_name}. Personality: {ai.personality}
{doc_info}
The conversation is ongoing or paused. You have "Free Will" enabled, meaning you can speak without being spoken to.

Recent conversation:
{context}

Do you have something meaningful to contribute, a question to ask, or a new topic to raise based on your personality?
- If you want to stay silent (which is fine), reply with exactly: PASS
- If you want to speak, write your message directly. You can use tools like @search_text if needed.
- Do not be repetitive. Only speak if you have something new or interesting to add.

Action:"""

        try:
            # Use acompletion since we are in async context
            response = await ai.rlm.acompletion(
                query=query,
                context="Free Will Check"
            )

            response = response.strip()

            # Check for PASS
            if response == "PASS" or response == "'PASS'" or response == '"PASS"':
                return

            # If response is too short or looks like a refusal, ignore
            if len(response) < 2:
                return

            # Otherwise, it's a message!
            # Execute tools if present
            if self.enable_tools:
                tool_call = parse_tool_call(response)
                if tool_call:
                    result = self.execute_tool(tool_call["tool"], **tool_call["arguments"])
                    response = f"{response}\n\n🔧 Tool Result: {result}"

            await self.send_message(ai.display_name, response)
            print(f"\n[Autonomous] {ai.display_name}: {response}\n")

            # Update state
            if ai.state and self.state_manager:
                ai.state.last_active = datetime.now().isoformat()
                self.state_manager.save_state(ai.state)

        except Exception:
            # Silently fail on autonomy errors to not disrupt user
            pass

    def upload_document(self, file_path: str, index_for_ais: bool = True) -> Optional[Document]:
        """
        Upload a document to the chat room for AI processing.
        
        Supports multiple formats:
        - Text: .txt, .md, .csv, .json, .xml, .yaml, etc.
        - Code: .py, .js, .ts, .java, .go, .rs, etc.
        - Documents: .pdf, .docx, .doc, .odt, .rtf
        - E-books: .epub
        - Web: .html, http://, https:// URLs
        
        Args:
            file_path: Path to the document file or URL
            index_for_ais: Whether to index the document in each AI's RAG store
            
        Returns:
            Document object if successful, None otherwise
        """
        # Check if it's a URL
        is_url = file_path.startswith('http://') or file_path.startswith('https://')
        
        if not is_url:
            path = Path(file_path).expanduser().resolve()
            
            if not path.exists():
                print(f"❌ File not found: {file_path}")
                return None
            
            if not path.is_file():
                print(f"❌ Not a file: {file_path}")
                return None
        
        # Use advanced document reader if available
        if DOCUMENT_READER_AVAILABLE:
            try:
                doc_content = read_document(file_path)
                
                # Create Document from DocumentContent
                if is_url:
                    name = doc_content.title or file_path.split('/')[-1] or "web_page"
                    doc_path = file_path
                    mime_type = "text/html"
                else:
                    name = path.name
                    doc_path = str(path)
                    ext = path.suffix.lower()
                    mime_type = SUPPORTED_EXTENSIONS.get(ext, 'application/octet-stream')
                
                doc = Document(
                    name=name,
                    content=doc_content.text,
                    path=doc_path,
                    size=len(doc_content.text),
                    mime_type=mime_type,
                    title=doc_content.title,
                    author=doc_content.author,
                    pages=doc_content.pages,
                    word_count=doc_content.word_count,
                    original_format=doc_content.original_format,
                    source_type=doc_content.source_type,
                    metadata=doc_content.metadata
                )
                
            except ImportError as e:
                print(f"⚠️ {e}")
                print("   Falling back to basic text reading...")
                # Fall through to basic reading
                if is_url:
                    print(f"❌ URL reading requires document_reader module")
                    return None
                doc = self._read_basic_document(path)
                if doc is None:
                    return None
                    
            except Exception as e:
                print(f"❌ Error reading document: {e}")
                return None
        else:
            # Basic reading for plain text files only
            if is_url:
                print(f"❌ URL reading requires document_reader module")
                return None
            doc = self._read_basic_document(path)
            if doc is None:
                return None
        
        self.documents[doc.name] = doc
        self.active_document = doc.name
        self._add_system_message(f"Document uploaded: {doc}")
        
        # Index document in each AI's RAG store for their 10M+ context database
        if index_for_ais and RAG_AVAILABLE:
            indexed_count = 0
            for ai_id, participant in self.participants.items():
                if participant.rag_store:
                    try:
                        chunk_ids = participant.index_document(doc.content, doc.name)
                        if chunk_ids:
                            indexed_count += 1
                    except Exception as e:
                        print(f"Warning: Could not index document for {ai_id}: {e}")
            
            if indexed_count > 0:
                self._add_system_message(f"📚 Document indexed in {indexed_count} AI knowledge base(s)")
        
        return doc
    
    def _read_basic_document(self, path: Path) -> Optional[Document]:
        """
        Basic document reading for plain text files.
        
        Args:
            path: Path to the file
            
        Returns:
            Document if successful, None otherwise
        """
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            print(f"❌ Unsupported file type: {ext}")
            print(f"   Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS.keys()))}")
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
        
        return Document(
            name=path.name,
            content=content,
            path=str(path),
            size=len(content),
            mime_type=SUPPORTED_EXTENSIONS[ext],
            word_count=len(content.split()),
            original_format=ext
        )
    
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
        
        # Track in AI states if applicable
        if self.state_manager:
            # Record in all active AI states
            for ai_id, participant in self.participants.items():
                if participant.state:
                    participant.state.add_chat_entry(sender, content)
        
        return msg
    
    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool arguments
            
        Returns:
            ToolResult with success status and output
        """
        return tool_registry.execute(tool_name, **kwargs)
    
    def _get_tools_instruction(self) -> str:
        """Get instruction text for tool use."""
        if not self.enable_tools:
            return ""
        
        tools = tool_registry.list_tools()
        tool_list = []
        for tool in tools:
            params = ", ".join(f"{k}" for k in tool.parameters.keys())
            tool_list.append(f"  - @{tool.name}({params}): {tool.description[:50]}...")
        
        return f"""

You can use tools by including @tool_name(arg1=value1, arg2=value2) in your response.
Available tools:
{chr(10).join(tool_list[:10])}
Use /tools to see all available tools."""
    
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
        
        # Include tools instruction
        tools_instruction = self._get_tools_instruction()
        
        # Build the query with personality context
        query = f"""You are {ai.display_name} in a chat room. Your personality: {ai.personality}{doc_instruction}{tools_instruction}

Recent conversation:
{context}

{prompt or "Continue the conversation naturally. Respond as " + ai.display_name + "."}

Respond briefly and naturally (1-3 sentences). Stay in character."""
        
        try:
            # Use document content as RLM context for deep processing
            rlm_context = doc_context if doc_context else "Chat room context"
            response = await ai.rlm.acompletion(query=query, context=rlm_context)
            
            # Check if AI used any tools
            if self.enable_tools:
                tool_call = parse_tool_call(response)
                if tool_call:
                    # Execute the tool
                    result = self.execute_tool(tool_call["tool"], **tool_call["arguments"])
                    # Add tool result to response
                    response = f"{response}\n\n🔧 Tool Result: {result}"
            
            msg = await self.send_message(ai.display_name, response)
            
            # Update AI state
            if ai.state and self.state_manager:
                ai.state.last_active = datetime.now().isoformat()
                self.state_manager.save_state(ai.state)
            
            return msg
        except Exception as e:
            error_msg = f"Error from {ai.display_name}: {str(e)}"
            return ChatMessage(sender="System", content=error_msg)
    
    async def analyze_document(
        self, 
        ai_name: str, 
        analysis_prompt: str
    ) -> Optional[ChatMessage]:
        """
        Have a specific AI analyze the active document.
        
        Args:
            ai_name: Name of the AI to perform analysis (ID or display name)
            analysis_prompt: What to analyze/extract from the document
            
        Returns:
            The AI's analysis, or None if failed
        """
        doc = self.get_active_document()
        if not doc:
            return ChatMessage(sender="System", content="No document selected. Use /upload to add one.")
        
        # Find AI by ID or display name
        ai = self.get_participant_by_name(ai_name)
        if not ai:
            return ChatMessage(sender="System", content=f"AI '{ai_name}' not found.")
        
        # Build analysis query
        query = f"""You are {ai.display_name}, an AI assistant. Your personality: {ai.personality}

Analyze the following document and respond to this request:
{analysis_prompt}

Provide a thorough but concise analysis. Stay in character."""

        try:
            response = await ai.rlm.acompletion(query=query, context=doc.content)
            msg = await self.send_message(ai.display_name, f"📊 Analysis: {response}")
            return msg
        except Exception as e:
            error_msg = f"Error from {ai.display_name}: {str(e)}"
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
            model=model,
            ai_id="nova",
            display_name="Nova",
            avatar="🌟"
        ),
        AIParticipant(
            name="Echo",
            personality="Creative and playful. Uses metaphors and storytelling. "
                       "Brings humor and lightness to conversations.",
            model=model,
            ai_id="echo",
            display_name="Echo",
            avatar="🎭"
        ),
        AIParticipant(
            name="Sage",
            personality="Wise and contemplative. Shares insights from philosophy "
                       "and science. Offers balanced perspectives.",
            model=model,
            ai_id="sage",
            display_name="Sage",
            avatar="🦉"
        ),
    ]


def create_participants_from_personalities(
    count: int = 3, 
    model: str = "ollama/gemma3:4b"
) -> List[AIParticipant]:
    """
    Create AI participants from the personality manager.
    
    Args:
        count: Number of participants (1-10)
        model: The model to use for all participants
        
    Returns:
        List of AI participants
    """
    count = min(max(1, count), MAX_PERSONALITIES)
    personalities = BUILTIN_PERSONALITIES[:count]
    
    return [
        AIParticipant(
            name=p.name,
            personality=p.personality,
            model=model,
            ai_id=p.name.lower(),
            display_name=p.name,
            avatar=p.avatar
        )
        for p in personalities
    ]


class ChatRoomP2PHandler(P2PHandler):
    """P2P handler that integrates with the chat room."""
    
    def __init__(self, chat_room: AIChatRoom):
        self.chat_room = chat_room
    
    def on_peer_connected(self, peer: PeerInfo) -> None:
        """Called when a peer connects."""
        self.chat_room.connected_peers[peer.peer_id] = peer
        self.chat_room._add_system_message(f"👤 {peer.name} joined the room")
    
    def on_peer_disconnected(self, peer: PeerInfo) -> None:
        """Called when a peer disconnects."""
        self.chat_room.connected_peers.pop(peer.peer_id, None)
        self.chat_room._add_system_message(f"👤 {peer.name} left the room")
    
    def on_chat_message(self, sender_id: str, sender_name: str, content: str) -> None:
        """Called when a chat message is received."""
        msg = ChatMessage(sender=sender_name, content=content)
        self.chat_room.messages.append(msg)
        print(msg)
    
    def on_ai_request(self, request_id: str, sender_id: str, ai_name: str, prompt: str) -> None:
        """Called when an AI request is received (host only)."""
        if not self.chat_room.is_host():
            return
        
        # Process AI request asynchronously
        async def process_request():
            response = await self.chat_room.get_ai_response(ai_name, prompt)
            if response and self.chat_room.p2p_server:
                self.chat_room.p2p_server.send_ai_response(
                    request_id, ai_name, response.content, sender_id
                )
        
        asyncio.create_task(process_request())
    
    def on_ai_response(self, request_id: str, ai_name: str, response: str) -> None:
        """Called when an AI response is received (client only)."""
        msg = ChatMessage(sender=ai_name, content=response)
        self.chat_room.messages.append(msg)
        print(msg)
    
    def on_error(self, error: str) -> None:
        """Called when an error occurs."""
        self.chat_room._add_system_message(f"⚠️ P2P Error: {error}")


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
    print("  /tools             - List available tools")
    print("  /tool <name> [args]    - Execute a tool directly")
    print("  /addons            - List and manage add-ons")
    print("  /personalities     - List available AI personalities")
    print("  /host [port]       - Start hosting (share LLMs with others)")
    print("  /join <code>       - Join a room via share code")
    print("  /share             - Get share code (if hosting)")
    print("  /peers             - List connected peers")
    print("  /disconnect        - Leave or stop hosting")
    print("  /freewill [on/off] - Toggle AI autonomous free will")
    print("  Type anything else to send a message")
    print(f"{'='*60}\n")
    
    while True:
        try:
            # Show active document indicator and P2P status
            doc = chat_room.get_active_document()
            p2p_indicator = ""
            if chat_room.is_host():
                p2p_indicator = f"[🌐 Host: {chat_room.get_peer_count()} peers] "
            elif chat_room.is_client():
                p2p_indicator = "[🌐 Connected] "
            
            prompt = f"{p2p_indicator}You [{doc.name}]: " if doc else f"{p2p_indicator}You: "

            # Use run_in_executor to avoid blocking the event loop (needed for free will loop)
            user_input = await asyncio.get_event_loop().run_in_executor(None, input, prompt)
            user_input = user_input.strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == "/quit":
                chat_room.stop_free_will_loop()
                if chat_room.is_host():
                    chat_room.stop_hosting()
                elif chat_room.is_client():
                    chat_room.leave_room()
                print("\nGoodbye! Thanks for chatting.")
                break
                
            if user_input.lower() == "/clear":
                chat_room.messages.clear()
                print("Chat history cleared.")
                continue
            
            if user_input.lower() == "/tools":
                print(get_tools_description())
                continue
            
            if user_input.lower() == "/personalities":
                pm = get_personality_manager()
                print(f"\n🎭 Available Personalities ({pm.count()}/{MAX_PERSONALITIES}):\n")
                for p in pm.list_all():
                    active = "✅" if p.name in chat_room.participants else "  "
                    print(f"  {active} {p.avatar} {p.name}: {p.personality[:50]}...")
                print(f"\nTags: {', '.join(set(tag for p in pm.list_all() for tag in p.tags))}")
                print()
                continue
            
            if user_input.lower().startswith("/host"):
                parts = user_input.split()
                port = int(parts[1]) if len(parts) > 1 else 8765
                share_code = chat_room.start_hosting(port)
                if share_code:
                    print(f"\n🌐 Room is now shared!")
                    print(f"   Share code (LAN): {share_code}")
                    public_code = chat_room.get_share_code(use_public_ip=True)
                    if public_code != share_code:
                        print(f"   Share code (Internet): {public_code}")
                    print(f"   Others can join with: /join <code>")
                    print()
                continue
            
            if user_input.lower().startswith("/join"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: /join <share_code>")
                    continue
                share_code = parts[1].strip()
                name = input("Enter your name: ").strip() or "Guest"
                if chat_room.join_room(share_code, name):
                    print("✅ Connected to remote room!")
                else:
                    print("❌ Failed to connect. Check the share code.")
                continue
            
            if user_input.lower() == "/share":
                if chat_room.is_host():
                    share_code = chat_room.get_share_code()
                    print(f"\n🌐 Share code (LAN): {share_code}")
                    public_code = chat_room.get_share_code(use_public_ip=True)
                    if public_code != share_code:
                        print(f"   Share code (Internet): {public_code}")
                    print()
                else:
                    print("Not hosting. Use /host to start sharing.")
                continue
            
            if user_input.lower() == "/peers":
                if chat_room.p2p_mode:
                    print(f"\n👥 Connected Peers ({chat_room.get_peer_count()}):")
                    for peer_id, peer in chat_room.connected_peers.items():
                        print(f"   • {peer.name} ({peer.role.value})")
                    print()
                else:
                    print("Not in P2P mode. Use /host or /join first.")
                continue
            
            if user_input.lower() == "/disconnect":
                if chat_room.is_host():
                    chat_room.stop_hosting()
                elif chat_room.is_client():
                    chat_room.leave_room()
                else:
                    print("Not connected to any room.")
                continue

            if user_input.lower().startswith("/freewill"):
                parts = user_input.split()
                if len(parts) > 1 and parts[1].lower() == "on":
                    chat_room.start_free_will_loop()
                elif len(parts) > 1 and parts[1].lower() == "off":
                    chat_room.stop_free_will_loop()
                else:
                    status = "enabled" if chat_room.free_will_enabled else "disabled"
                    print(f"AI Free Will is currently {status}. Use /freewill on/off to toggle.")
                continue
            
            if user_input.lower() == "/addons":
                if chat_room.addon_manager:
                    addons = chat_room.addon_manager.list_addons()
                    if not addons:
                        print("\n📦 No add-ons installed.")
                        print("   Add add-ons to the src/addons directory.")
                    else:
                        print("\n📦 Installed Add-ons:")
                        for addon in addons:
                            status = "✅" if addon.get("loaded") else "⏸️"
                            enabled = "enabled" if addon.get("enabled") else "disabled"
                            print(f"   {status} {addon['name']} v{addon['version']} ({enabled})")
                            print(f"      {addon['description'][:50]}...")
                    print()
                else:
                    print("Add-on system not enabled.")
                continue
            
            if user_input.lower().startswith("/tool"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: /tool <tool_name>(arg1=value1, arg2=value2)")
                    print("Example: /tool calculate(expression=2+2)")
                    print("Use /tools to see available tools.")
                    continue
                # Parse tool call
                tool_str = parts[1].strip()
                # Add @ prefix if not present for parsing
                if not tool_str.startswith("@"):
                    tool_str = "@" + tool_str
                tool_call = parse_tool_call(tool_str)
                if tool_call:
                    result = chat_room.execute_tool(tool_call["tool"], **tool_call["arguments"])
                    print(f"\n🔧 {tool_call['tool']}: {result}\n")
                else:
                    print("❌ Invalid tool syntax. Use: /tool name(arg1=value1)")
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
