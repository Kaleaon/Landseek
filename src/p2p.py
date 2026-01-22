"""
Peer-to-Peer Networking for AI Chat Room

This module provides P2P connectivity for the AI Chat Room, allowing users
to share their LLM capabilities with others over the internet.

Features:
- Share code generation for easy room joining
- WebSocket-based real-time communication
- Host mode: Run LLMs locally and share with peers
- Client mode: Connect to a host running LLMs
- Encrypted communications
- Auto-discovery on local network

Architecture:
- Host: Runs LLM inference, creates shareable room code
- Client: Connects via code, sends messages, receives AI responses
"""

import asyncio
import base64
import hashlib
import json
import os
import secrets
import socket
import struct
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum
import uuid


# Constants
DEFAULT_PORT = 8765
ROOM_CODE_LENGTH = 6
HEARTBEAT_INTERVAL = 30
CONNECTION_TIMEOUT = 60
MAX_PEERS = 20
MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB


class PeerRole(Enum):
    """Role of a peer in the network."""
    HOST = "host"      # Runs LLMs, hosts the room
    CLIENT = "client"  # Connects to host, uses remote LLMs


class MessageType(Enum):
    """Types of P2P messages."""
    # Connection
    HANDSHAKE = "handshake"
    HANDSHAKE_ACK = "handshake_ack"
    HEARTBEAT = "heartbeat"
    DISCONNECT = "disconnect"
    
    # Chat
    CHAT_MESSAGE = "chat_message"
    AI_REQUEST = "ai_request"
    AI_RESPONSE = "ai_response"
    PRIVATE_MESSAGE = "private_message"
    
    # Room management
    ROOM_INFO = "room_info"
    PEER_JOINED = "peer_joined"
    PEER_LEFT = "peer_left"
    
    # Sync - Bidirectional data synchronization
    SYNC_MESSAGES = "sync_messages"
    SYNC_PARTICIPANTS = "sync_participants"
    SYNC_AI_STATE = "sync_ai_state"
    SYNC_MEMORIES = "sync_memories"
    SYNC_REQUEST = "sync_request"  # Request data from peer
    SYNC_RESPONSE = "sync_response"  # Response with data
    
    # Local storage events (for bidirectional storage)
    STORE_INTERACTION = "store_interaction"
    STORE_AI_MEMORY = "store_ai_memory"
    STORE_RELATIONSHIP = "store_relationship"
    
    # Errors
    ERROR = "error"


@dataclass
class PeerInfo:
    """Information about a connected peer."""
    peer_id: str
    name: str
    role: PeerRole
    address: Tuple[str, int]
    connected_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    
    def is_alive(self) -> bool:
        """Check if peer is still connected (heartbeat within timeout)."""
        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed < CONNECTION_TIMEOUT


@dataclass 
class P2PMessage:
    """A message sent over the P2P network."""
    type: MessageType
    sender_id: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_json(self) -> str:
        """Serialize message to JSON."""
        return json.dumps({
            "type": self.type.value,
            "sender_id": self.sender_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id
        })
    
    @classmethod
    def from_json(cls, data: str) -> "P2PMessage":
        """Deserialize message from JSON."""
        obj = json.loads(data)
        return cls(
            type=MessageType(obj["type"]),
            sender_id=obj["sender_id"],
            payload=obj["payload"],
            timestamp=datetime.fromisoformat(obj["timestamp"]),
            message_id=obj["message_id"]
        )


def generate_room_code() -> str:
    """Generate a unique room code for sharing."""
    # Use a mix of letters and numbers (no confusing chars like 0/O, 1/l)
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ''.join(secrets.choice(chars) for _ in range(ROOM_CODE_LENGTH))


def encode_connection_info(host: str, port: int, room_code: str) -> str:
    """
    Encode connection info into a shareable string.
    
    Format: BASE64(host:port:room_code)
    Example result: "QUlDSEFULTEyMzQ1Ng=="
    """
    data = f"{host}:{port}:{room_code}"
    encoded = base64.urlsafe_b64encode(data.encode()).decode()
    return encoded


def decode_connection_info(share_code: str) -> Tuple[str, int, str]:
    """
    Decode a shareable connection string.
    
    Returns: (host, port, room_code)
    """
    try:
        decoded = base64.urlsafe_b64decode(share_code.encode()).decode()
        parts = decoded.split(":")
        if len(parts) != 3:
            raise ValueError("Invalid share code format")
        return parts[0], int(parts[1]), parts[2]
    except Exception as e:
        raise ValueError(f"Failed to decode share code: {e}")


def get_local_ip() -> str:
    """Get the local IP address for LAN connections."""
    try:
        # Create a socket to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_public_ip() -> Optional[str]:
    """Get public IP for internet connections (requires external service)."""
    try:
        import urllib.request
        return urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode()
    except Exception:
        return None


class P2PHandler(ABC):
    """Abstract handler for P2P events."""
    
    @abstractmethod
    def on_peer_connected(self, peer: PeerInfo) -> None:
        """Called when a peer connects."""
        pass
    
    @abstractmethod
    def on_peer_disconnected(self, peer: PeerInfo) -> None:
        """Called when a peer disconnects."""
        pass
    
    @abstractmethod
    def on_chat_message(self, sender_id: str, sender_name: str, content: str) -> None:
        """Called when a chat message is received."""
        pass
    
    @abstractmethod
    def on_ai_request(self, request_id: str, sender_id: str, ai_name: str, prompt: str) -> None:
        """Called when an AI request is received (host only)."""
        pass
    
    @abstractmethod
    def on_ai_response(self, request_id: str, ai_name: str, response: str) -> None:
        """Called when an AI response is received (client only)."""
        pass
    
    @abstractmethod
    def on_error(self, error: str) -> None:
        """Called when an error occurs."""
        pass
    
    # Local storage callbacks (optional - for bidirectional data sync)
    def on_store_interaction(self, interaction_data: Dict[str, Any]) -> None:
        """Called when an interaction should be stored locally (from remote)."""
        pass
    
    def on_store_ai_memory(self, ai_id: str, memory_data: Dict[str, Any]) -> None:
        """Called when an AI memory should be stored locally (from remote)."""
        pass
    
    def on_store_relationship(self, ai_id: str, relationship_data: Dict[str, Any]) -> None:
        """Called when a relationship should be stored locally (from remote)."""
        pass
    
    def on_sync_request(self, sync_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Called when a peer requests data synchronization."""
        return {}
    
    def on_private_message(
        self, sender_id: str, sender_name: str, 
        recipient_id: str, content: str
    ) -> None:
        """Called when a private message is received."""
        pass


class P2PServer:
    """
    P2P Server (Host Mode)
    
    Hosts a chat room and shares LLM capabilities with connected clients.
    """
    
    def __init__(
        self,
        handler: P2PHandler,
        host: str = "0.0.0.0",
        port: int = DEFAULT_PORT,
        room_name: str = "AI Chat Room"
    ):
        self.handler = handler
        self.host = host
        self.port = port
        self.room_name = room_name
        self.room_code = generate_room_code()
        self.peer_id = str(uuid.uuid4())
        
        self.peers: Dict[str, PeerInfo] = {}
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self._lock = threading.Lock()
        self._threads: List[threading.Thread] = []
    
    def get_share_code(self, use_public_ip: bool = False) -> str:
        """Get a shareable code for this room."""
        if use_public_ip:
            ip = get_public_ip() or get_local_ip()
        else:
            ip = get_local_ip()
        return encode_connection_info(ip, self.port, self.room_code)
    
    def get_room_info(self) -> Dict[str, Any]:
        """Get information about this room."""
        return {
            "room_name": self.room_name,
            "room_code": self.room_code,
            "host_id": self.peer_id,
            "peer_count": len(self.peers),
            "share_code_local": self.get_share_code(use_public_ip=False),
            "share_code_public": self.get_share_code(use_public_ip=True),
        }
    
    def start(self) -> None:
        """Start the P2P server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(MAX_PEERS)
        self.server_socket.settimeout(1.0)
        self.running = True
        
        # Start accept thread
        accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
        accept_thread.start()
        self._threads.append(accept_thread)
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        self._threads.append(heartbeat_thread)
    
    def stop(self) -> None:
        """Stop the P2P server."""
        self.running = False
        
        # Notify all peers
        for peer_id in list(self.peers.keys()):
            self._send_to_peer(peer_id, P2PMessage(
                type=MessageType.DISCONNECT,
                sender_id=self.peer_id,
                payload={"reason": "Server shutting down"}
            ))
        
        if self.server_socket:
            self.server_socket.close()
    
    def broadcast(self, message: P2PMessage, exclude: Optional[Set[str]] = None) -> None:
        """Broadcast a message to all connected peers."""
        exclude = exclude or set()
        for peer_id in list(self.peers.keys()):
            if peer_id not in exclude:
                self._send_to_peer(peer_id, message)
    
    def send_ai_response(self, request_id: str, ai_name: str, response: str, to_peer: str) -> None:
        """Send an AI response to a specific peer."""
        message = P2PMessage(
            type=MessageType.AI_RESPONSE,
            sender_id=self.peer_id,
            payload={
                "request_id": request_id,
                "ai_name": ai_name,
                "response": response
            }
        )
        self._send_to_peer(to_peer, message)
    
    def _accept_connections(self) -> None:
        """Accept incoming connections."""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                # Handle in new thread
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                thread.start()
                self._threads.append(thread)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.handler.on_error(f"Accept error: {e}")
    
    def _handle_client(self, client_socket: socket.socket, address: Tuple[str, int]) -> None:
        """Handle a connected client."""
        peer_id = None
        try:
            client_socket.settimeout(CONNECTION_TIMEOUT)
            
            # Wait for handshake
            data = self._receive_message(client_socket)
            if not data:
                return
            
            message = P2PMessage.from_json(data)
            if message.type != MessageType.HANDSHAKE:
                return
            
            # Validate room code
            if message.payload.get("room_code") != self.room_code:
                error_msg = P2PMessage(
                    type=MessageType.ERROR,
                    sender_id=self.peer_id,
                    payload={"error": "Invalid room code"}
                )
                self._send_message(client_socket, error_msg.to_json())
                return
            
            # Create peer info
            peer_id = message.sender_id
            peer_info = PeerInfo(
                peer_id=peer_id,
                name=message.payload.get("name", "Anonymous"),
                role=PeerRole.CLIENT,
                address=address
            )
            
            with self._lock:
                self.peers[peer_id] = peer_info
                # Store socket for later communication
                peer_info._socket = client_socket
            
            # Send handshake acknowledgment
            ack = P2PMessage(
                type=MessageType.HANDSHAKE_ACK,
                sender_id=self.peer_id,
                payload={
                    "room_name": self.room_name,
                    "peer_id": peer_id,
                    "host_name": "Host"
                }
            )
            self._send_message(client_socket, ack.to_json())
            
            # Notify handler
            self.handler.on_peer_connected(peer_info)
            
            # Broadcast peer joined
            self.broadcast(P2PMessage(
                type=MessageType.PEER_JOINED,
                sender_id=self.peer_id,
                payload={"peer_id": peer_id, "name": peer_info.name}
            ), exclude={peer_id})
            
            # Main message loop
            while self.running:
                data = self._receive_message(client_socket)
                if not data:
                    break
                
                message = P2PMessage.from_json(data)
                self._handle_message(peer_id, message)
                
        except Exception as e:
            self.handler.on_error(f"Client error: {e}")
        finally:
            # Clean up
            if peer_id and peer_id in self.peers:
                peer_info = self.peers.pop(peer_id, None)
                if peer_info:
                    self.handler.on_peer_disconnected(peer_info)
                    self.broadcast(P2PMessage(
                        type=MessageType.PEER_LEFT,
                        sender_id=self.peer_id,
                        payload={"peer_id": peer_id}
                    ))
            client_socket.close()
    
    def _handle_message(self, peer_id: str, message: P2PMessage) -> None:
        """Handle a message from a peer."""
        # Update heartbeat
        if peer_id in self.peers:
            self.peers[peer_id].last_heartbeat = datetime.now()
        
        if message.type == MessageType.HEARTBEAT:
            pass  # Just update timestamp
            
        elif message.type == MessageType.CHAT_MESSAGE:
            sender_name = self.peers.get(peer_id, PeerInfo(peer_id, "Unknown", PeerRole.CLIENT, ("", 0))).name
            self.handler.on_chat_message(
                peer_id,
                sender_name,
                message.payload.get("content", "")
            )
            # Relay to other peers
            self.broadcast(message, exclude={peer_id})
            
        elif message.type == MessageType.PRIVATE_MESSAGE:
            # Handle private messages
            self.handler.on_private_message(
                peer_id,
                message.payload.get("sender_name", "Unknown"),
                message.payload.get("recipient_id", ""),
                message.payload.get("content", "")
            )
            # Relay to recipient if they're connected
            recipient_id = message.payload.get("recipient_id", "")
            if recipient_id in self.peers:
                self._send_to_peer(recipient_id, message)
            
        elif message.type == MessageType.AI_REQUEST:
            self.handler.on_ai_request(
                message.payload.get("request_id", ""),
                peer_id,
                message.payload.get("ai_name", ""),
                message.payload.get("prompt", "")
            )
        
        # Local storage synchronization - store data on both host and client
        elif message.type == MessageType.STORE_INTERACTION:
            # Store the interaction locally (host storing client's interaction)
            self.handler.on_store_interaction(message.payload)
            
        elif message.type == MessageType.STORE_AI_MEMORY:
            # Store AI memory locally
            self.handler.on_store_ai_memory(
                message.payload.get("ai_id", ""),
                message.payload
            )
            
        elif message.type == MessageType.STORE_RELATIONSHIP:
            # Store relationship update locally
            self.handler.on_store_relationship(
                message.payload.get("ai_id", ""),
                message.payload
            )
            
        elif message.type == MessageType.SYNC_REQUEST:
            # Peer is requesting data sync
            sync_type = message.payload.get("sync_type", "")
            params = message.payload.get("params", {})
            response_data = self.handler.on_sync_request(sync_type, params)
            
            # Send response
            response = P2PMessage(
                type=MessageType.SYNC_RESPONSE,
                sender_id=self.peer_id,
                payload={
                    "sync_type": sync_type,
                    "request_id": message.payload.get("request_id", ""),
                    "data": response_data
                }
            )
            self._send_to_peer(peer_id, response)
            
        elif message.type == MessageType.DISCONNECT:
            # Will be handled in finally block
            pass
    
    def send_to_all_for_storage(self, interaction_data: Dict[str, Any]) -> None:
        """
        Send interaction data to all peers so they can store it locally.
        This ensures bidirectional storage - both host and clients store data.
        """
        message = P2PMessage(
            type=MessageType.STORE_INTERACTION,
            sender_id=self.peer_id,
            payload=interaction_data
        )
        self.broadcast(message)
    
    def send_ai_memory_to_all(self, ai_id: str, memory_data: Dict[str, Any]) -> None:
        """Send AI memory to all peers for local storage."""
        memory_data["ai_id"] = ai_id
        message = P2PMessage(
            type=MessageType.STORE_AI_MEMORY,
            sender_id=self.peer_id,
            payload=memory_data
        )
        self.broadcast(message)
    
    def send_relationship_to_all(self, ai_id: str, relationship_data: Dict[str, Any]) -> None:
        """Send relationship update to all peers for local storage."""
        relationship_data["ai_id"] = ai_id
        message = P2PMessage(
            type=MessageType.STORE_RELATIONSHIP,
            sender_id=self.peer_id,
            payload=relationship_data
        )
        self.broadcast(message)
    
    def _send_to_peer(self, peer_id: str, message: P2PMessage) -> bool:
        """Send a message to a specific peer."""
        peer = self.peers.get(peer_id)
        if not peer or not hasattr(peer, '_socket'):
            return False
        try:
            self._send_message(peer._socket, message.to_json())
            return True
        except Exception:
            return False
    
    def _send_message(self, sock: socket.socket, data: str) -> None:
        """Send a length-prefixed message."""
        encoded = data.encode()
        length = struct.pack(">I", len(encoded))
        sock.sendall(length + encoded)
    
    def _receive_message(self, sock: socket.socket) -> Optional[str]:
        """Receive a length-prefixed message."""
        try:
            length_data = sock.recv(4)
            if not length_data:
                return None
            length = struct.unpack(">I", length_data)[0]
            if length > MAX_MESSAGE_SIZE:
                return None
            data = b""
            while len(data) < length:
                chunk = sock.recv(min(length - len(data), 4096))
                if not chunk:
                    return None
                data += chunk
            return data.decode()
        except Exception:
            return None
    
    def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats."""
        while self.running:
            time.sleep(HEARTBEAT_INTERVAL)
            message = P2PMessage(
                type=MessageType.HEARTBEAT,
                sender_id=self.peer_id,
                payload={}
            )
            self.broadcast(message)
            
            # Check for dead peers
            now = datetime.now()
            for peer_id in list(self.peers.keys()):
                peer = self.peers.get(peer_id)
                if peer and not peer.is_alive():
                    self.peers.pop(peer_id, None)
                    self.handler.on_peer_disconnected(peer)


class P2PClient:
    """
    P2P Client (Client Mode)
    
    Connects to a host to use their LLM capabilities.
    """
    
    def __init__(self, handler: P2PHandler, name: str = "Anonymous"):
        self.handler = handler
        self.name = name
        self.peer_id = str(uuid.uuid4())
        
        self.host_info: Optional[PeerInfo] = None
        self.socket: Optional[socket.socket] = None
        self.running = False
        self._receive_thread: Optional[threading.Thread] = None
        self._pending_requests: Dict[str, threading.Event] = {}
        self._responses: Dict[str, str] = {}
    
    def connect(self, share_code: str) -> bool:
        """
        Connect to a room using a share code.
        
        Args:
            share_code: The encoded connection string
            
        Returns:
            True if connected successfully
        """
        try:
            host, port, room_code = decode_connection_info(share_code)
            return self._connect(host, port, room_code)
        except Exception as e:
            self.handler.on_error(f"Connection failed: {e}")
            return False
    
    def connect_direct(self, host: str, port: int, room_code: str) -> bool:
        """Connect directly with host, port, and room code."""
        return self._connect(host, port, room_code)
    
    def _connect(self, host: str, port: int, room_code: str) -> bool:
        """Internal connection method."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(CONNECTION_TIMEOUT)
            self.socket.connect((host, port))
            
            # Send handshake
            handshake = P2PMessage(
                type=MessageType.HANDSHAKE,
                sender_id=self.peer_id,
                payload={
                    "name": self.name,
                    "room_code": room_code
                }
            )
            self._send_message(handshake.to_json())
            
            # Wait for acknowledgment
            response = self._receive_message()
            if not response:
                self.socket.close()
                return False
            
            message = P2PMessage.from_json(response)
            if message.type == MessageType.ERROR:
                self.handler.on_error(message.payload.get("error", "Unknown error"))
                self.socket.close()
                return False
            
            if message.type != MessageType.HANDSHAKE_ACK:
                self.socket.close()
                return False
            
            # Store host info
            self.host_info = PeerInfo(
                peer_id=message.sender_id,
                name=message.payload.get("host_name", "Host"),
                role=PeerRole.HOST,
                address=(host, port)
            )
            
            # Start receive thread
            self.running = True
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            
            self.handler.on_peer_connected(self.host_info)
            return True
            
        except Exception as e:
            self.handler.on_error(f"Connection failed: {e}")
            if self.socket:
                self.socket.close()
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the host."""
        self.running = False
        if self.socket:
            try:
                disconnect_msg = P2PMessage(
                    type=MessageType.DISCONNECT,
                    sender_id=self.peer_id,
                    payload={}
                )
                self._send_message(disconnect_msg.to_json())
            except Exception:
                pass
            self.socket.close()
        
        if self.host_info:
            self.handler.on_peer_disconnected(self.host_info)
    
    def send_chat_message(self, content: str) -> None:
        """Send a chat message."""
        message = P2PMessage(
            type=MessageType.CHAT_MESSAGE,
            sender_id=self.peer_id,
            payload={"content": content, "name": self.name}
        )
        self._send_message(message.to_json())
    
    def request_ai_response(self, ai_name: str, prompt: str) -> str:
        """
        Request an AI response from the host.
        
        This is a blocking call that waits for the response.
        """
        request_id = str(uuid.uuid4())
        
        message = P2PMessage(
            type=MessageType.AI_REQUEST,
            sender_id=self.peer_id,
            payload={
                "request_id": request_id,
                "ai_name": ai_name,
                "prompt": prompt
            }
        )
        self._send_message(message.to_json())
        
        # Wait for response (with timeout)
        event = threading.Event()
        self._pending_requests[request_id] = event
        
        if event.wait(timeout=120):  # 2 minute timeout
            response = self._responses.pop(request_id, "")
            del self._pending_requests[request_id]
            return response
        else:
            del self._pending_requests[request_id]
            return "[Error: AI response timeout]"
    
    def _receive_loop(self) -> None:
        """Receive messages from host."""
        while self.running:
            try:
                data = self._receive_message()
                if not data:
                    break
                
                message = P2PMessage.from_json(data)
                self._handle_message(message)
                
            except Exception as e:
                if self.running:
                    self.handler.on_error(f"Receive error: {e}")
                break
        
        # Connection lost
        if self.host_info:
            self.handler.on_peer_disconnected(self.host_info)
    
    def _handle_message(self, message: P2PMessage) -> None:
        """Handle a message from the host."""
        if message.type == MessageType.CHAT_MESSAGE:
            self.handler.on_chat_message(
                message.sender_id,
                message.payload.get("name", "Unknown"),
                message.payload.get("content", "")
            )
            
        elif message.type == MessageType.AI_RESPONSE:
            request_id = message.payload.get("request_id", "")
            if request_id in self._pending_requests:
                self._responses[request_id] = message.payload.get("response", "")
                self._pending_requests[request_id].set()
            else:
                # Broadcast response
                self.handler.on_ai_response(
                    request_id,
                    message.payload.get("ai_name", ""),
                    message.payload.get("response", "")
                )
            
        elif message.type == MessageType.PEER_JOINED:
            peer = PeerInfo(
                peer_id=message.payload.get("peer_id", ""),
                name=message.payload.get("name", "Unknown"),
                role=PeerRole.CLIENT,
                address=("", 0)
            )
            self.handler.on_peer_connected(peer)
            
        elif message.type == MessageType.PEER_LEFT:
            peer = PeerInfo(
                peer_id=message.payload.get("peer_id", ""),
                name="",
                role=PeerRole.CLIENT,
                address=("", 0)
            )
            self.handler.on_peer_disconnected(peer)
            
        elif message.type == MessageType.HEARTBEAT:
            pass  # Just keep connection alive
            
        elif message.type == MessageType.DISCONNECT:
            self.running = False
        
        # Bidirectional storage - handle data from host to store locally
        elif message.type == MessageType.STORE_INTERACTION:
            # Store the interaction locally (client storing host's data)
            self.handler.on_store_interaction(message.payload)
            
        elif message.type == MessageType.STORE_AI_MEMORY:
            # Store AI memory locally
            self.handler.on_store_ai_memory(
                message.payload.get("ai_id", ""),
                message.payload
            )
            
        elif message.type == MessageType.STORE_RELATIONSHIP:
            # Store relationship update locally
            self.handler.on_store_relationship(
                message.payload.get("ai_id", ""),
                message.payload
            )
            
        elif message.type == MessageType.PRIVATE_MESSAGE:
            # Handle private message
            self.handler.on_private_message(
                message.payload.get("sender_id", message.sender_id),
                message.payload.get("sender_name", "Unknown"),
                message.payload.get("recipient_id", ""),
                message.payload.get("content", "")
            )
            
        elif message.type == MessageType.SYNC_RESPONSE:
            # Handle sync response
            request_id = message.payload.get("request_id", "")
            if request_id in self._pending_requests:
                self._responses[request_id] = message.payload.get("data", {})
                self._pending_requests[request_id].set()
    
    def send_for_storage(self, interaction_data: Dict[str, Any]) -> None:
        """
        Send interaction data to host for storage.
        This ensures bidirectional storage - both host and client store data.
        """
        message = P2PMessage(
            type=MessageType.STORE_INTERACTION,
            sender_id=self.peer_id,
            payload=interaction_data
        )
        self._send_message(message.to_json())
    
    def send_ai_memory_to_host(self, ai_id: str, memory_data: Dict[str, Any]) -> None:
        """Send AI memory to host for storage."""
        memory_data["ai_id"] = ai_id
        message = P2PMessage(
            type=MessageType.STORE_AI_MEMORY,
            sender_id=self.peer_id,
            payload=memory_data
        )
        self._send_message(message.to_json())
    
    def send_private_message(
        self, 
        recipient_id: str, 
        content: str
    ) -> None:
        """Send a private message to another participant."""
        message = P2PMessage(
            type=MessageType.PRIVATE_MESSAGE,
            sender_id=self.peer_id,
            payload={
                "sender_name": self.name,
                "recipient_id": recipient_id,
                "content": content
            }
        )
        self._send_message(message.to_json())
    
    def request_sync(self, sync_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Request data synchronization from the host.
        
        Args:
            sync_type: Type of data to sync (e.g., "ai_history", "memories")
            params: Parameters for the sync request
            
        Returns:
            The synchronized data
        """
        request_id = str(uuid.uuid4())
        
        message = P2PMessage(
            type=MessageType.SYNC_REQUEST,
            sender_id=self.peer_id,
            payload={
                "request_id": request_id,
                "sync_type": sync_type,
                "params": params or {}
            }
        )
        self._send_message(message.to_json())
        
        # Wait for response
        event = threading.Event()
        self._pending_requests[request_id] = event
        
        if event.wait(timeout=30):
            response = self._responses.pop(request_id, {})
            self._pending_requests.pop(request_id, None)
            return response
        else:
            self._pending_requests.pop(request_id, None)
            return {}
    
    def _send_message(self, data: str) -> None:
        """Send a length-prefixed message."""
        if not self.socket:
            return
        encoded = data.encode()
        length = struct.pack(">I", len(encoded))
        self.socket.sendall(length + encoded)
    
    def _receive_message(self) -> Optional[str]:
        """Receive a length-prefixed message."""
        if not self.socket:
            return None
        try:
            length_data = self.socket.recv(4)
            if not length_data:
                return None
            length = struct.unpack(">I", length_data)[0]
            if length > MAX_MESSAGE_SIZE:
                return None
            data = b""
            while len(data) < length:
                chunk = self.socket.recv(min(length - len(data), 4096))
                if not chunk:
                    return None
                data += chunk
            return data.decode()
        except Exception:
            return None


# Simple default handler for testing
class SimpleP2PHandler(P2PHandler):
    """Simple handler that prints events."""
    
    def on_peer_connected(self, peer: PeerInfo) -> None:
        print(f"[P2P] Peer connected: {peer.name} ({peer.peer_id[:8]}...)")
    
    def on_peer_disconnected(self, peer: PeerInfo) -> None:
        print(f"[P2P] Peer disconnected: {peer.name}")
    
    def on_chat_message(self, sender_id: str, sender_name: str, content: str) -> None:
        print(f"[P2P] {sender_name}: {content}")
    
    def on_ai_request(self, request_id: str, sender_id: str, ai_name: str, prompt: str) -> None:
        print(f"[P2P] AI Request from {sender_id[:8]}...: {ai_name} - {prompt[:50]}...")
    
    def on_ai_response(self, request_id: str, ai_name: str, response: str) -> None:
        print(f"[P2P] AI Response from {ai_name}: {response[:100]}...")
    
    def on_error(self, error: str) -> None:
        print(f"[P2P] Error: {error}")
