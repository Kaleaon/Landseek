"""Tests for P2P networking module."""

import pytest
import os
import sys
import threading
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from p2p import (
    generate_room_code, encode_connection_info, decode_connection_info,
    get_local_ip, P2PMessage, MessageType, PeerInfo, PeerRole,
    P2PServer, P2PClient, SimpleP2PHandler,
    ROOM_CODE_LENGTH, DEFAULT_PORT
)


class TestRoomCode:
    """Tests for room code generation."""
    
    def test_generate_room_code_length(self):
        """Test that room code has correct length."""
        code = generate_room_code()
        assert len(code) == ROOM_CODE_LENGTH
    
    def test_generate_room_code_unique(self):
        """Test that room codes are unique."""
        codes = [generate_room_code() for _ in range(100)]
        assert len(set(codes)) == 100  # All unique
    
    def test_generate_room_code_characters(self):
        """Test that room code uses safe characters."""
        code = generate_room_code()
        # Should not contain confusing characters
        assert '0' not in code
        assert 'O' not in code
        assert '1' not in code
        assert 'l' not in code
        assert 'I' not in code


class TestConnectionInfo:
    """Tests for connection info encoding/decoding."""
    
    def test_encode_decode_roundtrip(self):
        """Test that encoding and decoding produces original values."""
        host = "192.168.1.100"
        port = 8765
        room_code = "ABC123"
        
        encoded = encode_connection_info(host, port, room_code)
        decoded_host, decoded_port, decoded_code = decode_connection_info(encoded)
        
        assert decoded_host == host
        assert decoded_port == port
        assert decoded_code == room_code
    
    def test_encode_produces_base64(self):
        """Test that encoding produces valid base64."""
        encoded = encode_connection_info("localhost", 8765, "ABCDEF")
        # Should be URL-safe base64
        import base64
        try:
            base64.urlsafe_b64decode(encoded)
        except Exception:
            pytest.fail("Encoded string is not valid base64")
    
    def test_decode_invalid_raises(self):
        """Test that decoding invalid string raises error."""
        with pytest.raises(ValueError):
            decode_connection_info("not-valid-base64!!!")


class TestLocalIP:
    """Tests for local IP detection."""
    
    def test_get_local_ip_returns_string(self):
        """Test that get_local_ip returns a string."""
        ip = get_local_ip()
        assert isinstance(ip, str)
    
    def test_get_local_ip_format(self):
        """Test that IP has valid format."""
        ip = get_local_ip()
        parts = ip.split('.')
        assert len(parts) == 4
        for part in parts:
            assert 0 <= int(part) <= 255


class TestP2PMessage:
    """Tests for P2P message class."""
    
    def test_message_to_json(self):
        """Test message serialization."""
        msg = P2PMessage(
            type=MessageType.CHAT_MESSAGE,
            sender_id="test-id",
            payload={"content": "Hello"}
        )
        json_str = msg.to_json()
        assert "chat_message" in json_str
        assert "test-id" in json_str
        assert "Hello" in json_str
    
    def test_message_from_json(self):
        """Test message deserialization."""
        msg = P2PMessage(
            type=MessageType.CHAT_MESSAGE,
            sender_id="test-id",
            payload={"content": "Hello"}
        )
        json_str = msg.to_json()
        
        restored = P2PMessage.from_json(json_str)
        assert restored.type == MessageType.CHAT_MESSAGE
        assert restored.sender_id == "test-id"
        assert restored.payload["content"] == "Hello"
    
    def test_message_has_id(self):
        """Test that messages have unique IDs."""
        msg1 = P2PMessage(type=MessageType.HEARTBEAT, sender_id="a", payload={})
        msg2 = P2PMessage(type=MessageType.HEARTBEAT, sender_id="a", payload={})
        assert msg1.message_id != msg2.message_id


class TestPeerInfo:
    """Tests for peer info class."""
    
    def test_peer_info_creation(self):
        """Test creating peer info."""
        peer = PeerInfo(
            peer_id="test-id",
            name="Test User",
            role=PeerRole.CLIENT,
            address=("127.0.0.1", 8765)
        )
        assert peer.peer_id == "test-id"
        assert peer.name == "Test User"
        assert peer.role == PeerRole.CLIENT
    
    def test_peer_is_alive(self):
        """Test peer alive check."""
        peer = PeerInfo(
            peer_id="test-id",
            name="Test",
            role=PeerRole.CLIENT,
            address=("", 0)
        )
        # Should be alive immediately
        assert peer.is_alive() is True


class TestSimpleHandler:
    """Tests for SimpleP2PHandler."""
    
    def test_handler_methods_exist(self):
        """Test that handler has all required methods."""
        handler = SimpleP2PHandler()
        assert hasattr(handler, 'on_peer_connected')
        assert hasattr(handler, 'on_peer_disconnected')
        assert hasattr(handler, 'on_chat_message')
        assert hasattr(handler, 'on_ai_request')
        assert hasattr(handler, 'on_ai_response')
        assert hasattr(handler, 'on_error')


class TestMessageTypes:
    """Tests for message type enum."""
    
    def test_all_message_types(self):
        """Test that all message types are defined."""
        assert MessageType.HANDSHAKE.value == "handshake"
        assert MessageType.CHAT_MESSAGE.value == "chat_message"
        assert MessageType.AI_REQUEST.value == "ai_request"
        assert MessageType.AI_RESPONSE.value == "ai_response"
        assert MessageType.PEER_JOINED.value == "peer_joined"
        assert MessageType.DISCONNECT.value == "disconnect"


class TestPeerRole:
    """Tests for peer role enum."""
    
    def test_peer_roles(self):
        """Test peer roles are defined."""
        assert PeerRole.HOST.value == "host"
        assert PeerRole.CLIENT.value == "client"
