"""Tests for AI Free Will functionality."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chat_room import AIChatRoom, AIParticipant


@pytest.fixture
def mock_rlm():
    """Create a mock RLM."""
    rlm = MagicMock()
    rlm.acompletion = AsyncMock(return_value="PASS")
    return rlm


@pytest.fixture
def ai_participant(mock_rlm):
    """Create a mock AI participant."""
    participant = AIParticipant(
        name="TestBot",
        personality="Helpful",
        model="test-model"
    )
    participant.rlm = mock_rlm
    return participant


@pytest.fixture
def chat_room(ai_participant):
    """Create a chat room with one participant."""
    room = AIChatRoom("Test Room")
    room.add_participant(ai_participant)
    return room


@pytest.mark.asyncio
async def test_free_will_toggle(chat_room):
    """Test toggling free will."""
    assert chat_room.free_will_enabled is False
    assert chat_room.free_will_task is None

    chat_room.start_free_will_loop()
    assert chat_room.free_will_enabled is True
    assert chat_room.free_will_task is not None

    # Should be idempotent
    task = chat_room.free_will_task
    chat_room.start_free_will_loop()
    assert chat_room.free_will_task is task

    chat_room.stop_free_will_loop()
    assert chat_room.free_will_enabled is False
    assert chat_room.free_will_task is None


@pytest.mark.asyncio
async def test_check_ai_free_will_pass(chat_room, ai_participant):
    """Test when AI decides to PASS."""
    ai_participant.rlm.acompletion.return_value = "PASS"

    await chat_room.check_ai_free_will(ai_participant.ai_id)

    # Should not send message
    assert len(chat_room.messages) == 1  # Only "joined" message

    # Should have called RLM
    ai_participant.rlm.acompletion.assert_called_once()


@pytest.mark.asyncio
async def test_check_ai_free_will_act(chat_room, ai_participant):
    """Test when AI decides to speak."""
    ai_participant.rlm.acompletion.return_value = "Hello world!"

    await chat_room.check_ai_free_will(ai_participant.ai_id)

    # Should send message
    assert len(chat_room.messages) == 2
    assert chat_room.messages[-1].content == "Hello world!"
    assert chat_room.messages[-1].sender == "TestBot"


@pytest.mark.asyncio
async def test_check_ai_free_will_tool(chat_room, ai_participant):
    """Test when AI uses a tool."""
    ai_participant.rlm.acompletion.return_value = "@calculate(expression=1+1)"

    # Mock tool execution
    with patch.object(chat_room, 'execute_tool', return_value="2") as mock_execute:
        await chat_room.check_ai_free_will(ai_participant.ai_id)

        mock_execute.assert_called_once_with('calculate', expression='1+1')

        # Message should contain tool result
        assert len(chat_room.messages) == 2
        assert "Tool Result: 2" in chat_room.messages[-1].content
