"""Tests for chat room functionality."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import after path setup
from chat_room import (
    AIChatRoom, AIParticipant, ChatMessage, Document,
    SUPPORTED_EXTENSIONS, create_default_participants
)


@pytest.fixture
def temp_document():
    """Create a temporary document file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document.\n")
        f.write("It contains multiple lines.\n")
        f.write("Used for testing document upload functionality.\n")
        temp_path = f.name
    yield temp_path
    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def chat_room():
    """Create a chat room without AI participants (for unit testing)."""
    return AIChatRoom("Test Chat Room")


class TestDocument:
    """Tests for Document class."""
    
    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            name="test.txt",
            content="Hello, World!",
            path="/tmp/test.txt",
            size=13,
            mime_type="text/plain"
        )
        assert doc.name == "test.txt"
        assert doc.content == "Hello, World!"
        assert doc.size == 13
        
    def test_document_str(self):
        """Test document string representation."""
        doc = Document(
            name="report.txt",
            content="Content",
            path="/tmp/report.txt",
            size=2048,
            mime_type="text/plain"
        )
        result = str(doc)
        assert "report.txt" in result
        assert "2.0 KB" in result
        
    def test_document_summary(self):
        """Test document summary generation."""
        long_content = "A" * 500
        doc = Document(
            name="long.txt",
            content=long_content,
            path="/tmp/long.txt",
            size=500,
            mime_type="text/plain"
        )
        summary = doc.get_summary(100)
        assert len(summary) <= 103  # 100 + "..."
        assert summary.endswith("...")


class TestChatRoom:
    """Tests for AIChatRoom class."""
    
    def test_chat_room_creation(self, chat_room):
        """Test creating a chat room."""
        assert chat_room.name == "Test Chat Room"
        assert len(chat_room.messages) == 0
        assert len(chat_room.participants) == 0
        assert len(chat_room.documents) == 0
        
    def test_upload_document(self, chat_room, temp_document):
        """Test uploading a document."""
        doc = chat_room.upload_document(temp_document)
        
        assert doc is not None
        assert doc.name == os.path.basename(temp_document)
        assert "test document" in doc.content.lower()
        assert chat_room.active_document == doc.name
        assert doc.name in chat_room.documents
        
    def test_upload_nonexistent_file(self, chat_room):
        """Test uploading a file that doesn't exist."""
        doc = chat_room.upload_document("/nonexistent/file.txt")
        assert doc is None
        
    def test_upload_unsupported_file(self, chat_room):
        """Test uploading an unsupported file type."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"test")
            temp_path = f.name
        try:
            doc = chat_room.upload_document(temp_path)
            assert doc is None
        finally:
            os.unlink(temp_path)
            
    def test_list_documents(self, chat_room, temp_document):
        """Test listing documents."""
        chat_room.upload_document(temp_document)
        docs = chat_room.list_documents()
        
        assert len(docs) == 1
        assert docs[0].name == os.path.basename(temp_document)
        
    def test_select_document(self, chat_room, temp_document):
        """Test selecting a document."""
        doc = chat_room.upload_document(temp_document)
        
        # Upload another document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Another document")
            another_path = f.name
        try:
            chat_room.upload_document(another_path)
            
            # Select the first document
            result = chat_room.select_document(doc.name)
            assert result is True
            assert chat_room.active_document == doc.name
            
            # Try to select non-existent document
            result = chat_room.select_document("nonexistent.txt")
            assert result is False
        finally:
            os.unlink(another_path)
            
    def test_remove_document(self, chat_room, temp_document):
        """Test removing a document."""
        doc = chat_room.upload_document(temp_document)
        
        result = chat_room.remove_document(doc.name)
        assert result is True
        assert doc.name not in chat_room.documents
        assert chat_room.active_document is None
        
        # Try to remove non-existent document
        result = chat_room.remove_document("nonexistent.txt")
        assert result is False
        
    def test_get_active_document(self, chat_room, temp_document):
        """Test getting the active document."""
        # No active document initially
        assert chat_room.get_active_document() is None
        
        # Upload and get active
        doc = chat_room.upload_document(temp_document)
        active = chat_room.get_active_document()
        
        assert active is not None
        assert active.name == doc.name


class TestChatMessage:
    """Tests for ChatMessage class."""
    
    def test_message_creation(self):
        """Test creating a chat message."""
        msg = ChatMessage(sender="User", content="Hello!")
        
        assert msg.sender == "User"
        assert msg.content == "Hello!"
        assert msg.timestamp is not None
        
    def test_message_str(self):
        """Test message string representation."""
        msg = ChatMessage(sender="Nova", content="Interesting question!")
        result = str(msg)
        
        assert "Nova" in result
        assert "Interesting question!" in result


class TestSupportedExtensions:
    """Tests for supported file extensions."""
    
    def test_common_extensions_supported(self):
        """Test that common extensions are supported."""
        common = ['.txt', '.md', '.json', '.csv', '.py', '.js']
        for ext in common:
            assert ext in SUPPORTED_EXTENSIONS
            
    def test_extension_mime_types(self):
        """Test that extensions have correct MIME types."""
        assert SUPPORTED_EXTENSIONS['.txt'] == 'text/plain'
        assert SUPPORTED_EXTENSIONS['.json'] == 'application/json'
        assert SUPPORTED_EXTENSIONS['.py'] == 'text/x-python'


class TestCreateDefaultParticipants:
    """Tests for default participant creation."""
    
    def test_creates_three_participants(self):
        """Test that three default participants are created."""
        participants = create_default_participants()
        assert len(participants) == 3
        
    def test_participant_names(self):
        """Test default participant names."""
        participants = create_default_participants()
        names = [p.name for p in participants]
        
        assert "Nova" in names
        assert "Echo" in names
        assert "Sage" in names
        
    def test_custom_model(self):
        """Test creating participants with custom model."""
        model = "ollama/gemma3:2b"
        participants = create_default_participants(model=model)
        
        for p in participants:
            assert p.model == model


@pytest.mark.asyncio
async def test_send_message(chat_room):
    """Test sending a message."""
    msg = await chat_room.send_message("User", "Hello everyone!")
    
    assert msg.sender == "User"
    assert msg.content == "Hello everyone!"
    assert len(chat_room.messages) == 1


@pytest.mark.asyncio
async def test_conversation_context(chat_room):
    """Test getting conversation context."""
    await chat_room.send_message("User", "First message")
    await chat_room.send_message("AI", "Response")
    
    context = chat_room._get_conversation_context()
    
    assert "First message" in context
    assert "Response" in context


@pytest.mark.asyncio
async def test_document_context(chat_room, temp_document):
    """Test getting document context."""
    # No document initially
    context = chat_room._get_document_context()
    assert context == ""
    
    # With document
    doc = chat_room.upload_document(temp_document)
    context = chat_room._get_document_context()
    
    assert doc.name in context
    assert "test document" in context.lower()
