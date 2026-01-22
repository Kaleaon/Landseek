"""Tests for tools module."""

import pytest
import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools import (
    tool_registry, ToolResult, Tool, ToolRegistry,
    calculate, unit_convert, get_current_time, calculate_date,
    word_count, search_text, extract_urls, extract_emails,
    json_parse, list_files, read_file, get_system_info,
    parse_tool_call, get_tools_description
)


class TestToolResult:
    """Tests for ToolResult class."""
    
    def test_success_result(self):
        """Test successful result."""
        result = ToolResult(success=True, output="test output")
        assert result.success is True
        assert result.output == "test output"
        assert "✅" in str(result)
    
    def test_error_result(self):
        """Test error result."""
        result = ToolResult(success=False, output=None, error="test error")
        assert result.success is False
        assert result.error == "test error"
        assert "❌" in str(result)


class TestCalculateTool:
    """Tests for calculate tool."""
    
    def test_basic_arithmetic(self):
        """Test basic arithmetic."""
        result = calculate("2 + 2")
        assert result.success is True
        assert result.output == 4
    
    def test_multiplication(self):
        """Test multiplication."""
        result = calculate("3 * 4")
        assert result.success is True
        assert result.output == 12
    
    def test_division(self):
        """Test division."""
        result = calculate("10 / 2")
        assert result.success is True
        assert result.output == 5.0
    
    def test_sqrt(self):
        """Test square root."""
        result = calculate("sqrt(16)")
        assert result.success is True
        assert result.output == 4.0
    
    def test_trig(self):
        """Test trigonometry."""
        result = calculate("sin(0)")
        assert result.success is True
        assert result.output == 0.0
    
    def test_pi(self):
        """Test pi constant."""
        result = calculate("pi")
        assert result.success is True
        assert abs(result.output - 3.14159) < 0.01
    
    def test_forbidden_import(self):
        """Test that imports are blocked."""
        result = calculate("import os")
        assert result.success is False


class TestUnitConvert:
    """Tests for unit_convert tool."""
    
    def test_km_to_miles(self):
        """Test kilometers to miles."""
        result = unit_convert(10, "km", "miles")
        assert result.success is True
        assert "6.21" in str(result.output)
    
    def test_celsius_to_fahrenheit(self):
        """Test celsius to fahrenheit."""
        result = unit_convert(0, "celsius", "fahrenheit")
        assert result.success is True
        assert "32" in str(result.output)
    
    def test_unknown_conversion(self):
        """Test unknown conversion."""
        result = unit_convert(10, "foo", "bar")
        assert result.success is False


class TestDateTimeTools:
    """Tests for date/time tools."""
    
    def test_get_current_time(self):
        """Test get current time."""
        result = get_current_time()
        assert result.success is True
        assert result.output is not None
    
    def test_get_current_time_iso(self):
        """Test ISO format."""
        result = get_current_time(format="iso")
        assert result.success is True
        assert "T" in result.output
    
    def test_calculate_date(self):
        """Test date calculation."""
        result = calculate_date("2025-01-01", days=10)
        assert result.success is True
        assert "2025-01-11" in result.output
    
    def test_calculate_date_today(self):
        """Test date calculation from today."""
        result = calculate_date("today", days=0)
        assert result.success is True


class TestTextTools:
    """Tests for text analysis tools."""
    
    def test_word_count(self):
        """Test word count."""
        result = word_count("Hello world. This is a test.")
        assert result.success is True
        assert result.output["words"] == 6
        assert result.output["sentences"] == 2
    
    def test_search_text(self):
        """Test text search."""
        result = search_text("Hello World", r"\w+", case_sensitive=False)
        assert result.success is True
        assert result.output["count"] == 2
    
    def test_extract_urls(self):
        """Test URL extraction."""
        text = "Visit https://example.com and http://test.org for more info."
        result = extract_urls(text)
        assert result.success is True
        assert result.output["count"] == 2
    
    def test_extract_emails(self):
        """Test email extraction."""
        text = "Contact us at test@example.com or support@test.org"
        result = extract_emails(text)
        assert result.success is True
        assert result.output["count"] == 2


class TestDataTools:
    """Tests for data tools."""
    
    def test_json_parse(self):
        """Test JSON parsing."""
        result = json_parse('{"name": "test", "value": 42}')
        assert result.success is True
        assert result.output["name"] == "test"
    
    def test_json_parse_with_path(self):
        """Test JSON parsing with path."""
        result = json_parse('{"data": {"name": "test"}}', "data.name")
        assert result.success is True
        assert result.output == "test"
    
    def test_json_parse_invalid(self):
        """Test invalid JSON."""
        result = json_parse("not json")
        assert result.success is False


class TestFileTools:
    """Tests for file tools."""
    
    def test_list_files(self):
        """Test listing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            Path(tmpdir, "test1.txt").write_text("test")
            Path(tmpdir, "test2.txt").write_text("test")
            
            result = list_files(tmpdir)
            assert result.success is True
            assert result.output["count"] >= 2
    
    def test_list_files_with_pattern(self):
        """Test listing files with pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").write_text("test")
            Path(tmpdir, "test.py").write_text("test")
            
            result = list_files(tmpdir, "*.txt")
            assert result.success is True
            assert result.output["count"] == 1
    
    def test_read_file(self):
        """Test reading a file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Hello\nWorld\nTest")
            temp_path = f.name
        
        try:
            result = read_file(temp_path)
            assert result.success is True
            assert "Hello" in result.output
        finally:
            os.unlink(temp_path)
    
    def test_read_file_max_lines(self):
        """Test reading file with line limit."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4")
            temp_path = f.name
        
        try:
            result = read_file(temp_path, max_lines=2)
            assert result.success is True
            assert "Line 1" in result.output
            assert "Line 3" not in result.output
        finally:
            os.unlink(temp_path)


class TestSystemTools:
    """Tests for system tools."""
    
    def test_get_system_info(self):
        """Test getting system info."""
        result = get_system_info()
        assert result.success is True
        assert "os" in result.output
        assert "python_version" in result.output


class TestToolRegistry:
    """Tests for ToolRegistry."""
    
    def test_list_tools(self):
        """Test listing tools."""
        tools = tool_registry.list_tools()
        assert len(tools) > 0
    
    def test_get_tool(self):
        """Test getting a specific tool."""
        tool = tool_registry.get("calculate")
        assert tool is not None
        assert tool.name == "calculate"
    
    def test_execute_tool(self):
        """Test executing a tool."""
        result = tool_registry.execute("calculate", expression="1+1")
        assert result.success is True
        assert result.output == 2
    
    def test_execute_unknown_tool(self):
        """Test executing unknown tool."""
        result = tool_registry.execute("unknown_tool")
        assert result.success is False
    
    def test_get_schemas(self):
        """Test getting tool schemas."""
        schemas = tool_registry.get_schemas()
        assert len(schemas) > 0
        assert all("function" in s for s in schemas)


class TestToolParsing:
    """Tests for tool call parsing."""
    
    def test_parse_simple_call(self):
        """Test parsing simple tool call."""
        result = parse_tool_call("Let me @calculate(expression=2+2) for you")
        assert result is not None
        assert result["tool"] == "calculate"
        assert result["arguments"]["expression"] == "2+2"
    
    def test_parse_multiple_args(self):
        """Test parsing multiple arguments."""
        result = parse_tool_call("@unit_convert(value=10, from_unit=km, to_unit=miles)")
        assert result is not None
        assert result["tool"] == "unit_convert"
        assert result["arguments"]["value"] == 10
    
    def test_parse_json_format(self):
        """Test parsing JSON format."""
        result = parse_tool_call('@calculate{"expression": "2+2"}')
        assert result is not None
        assert result["tool"] == "calculate"
    
    def test_parse_no_tool(self):
        """Test parsing text without tool call."""
        result = parse_tool_call("Just a normal message")
        assert result is None


class TestGetToolsDescription:
    """Tests for tools description."""
    
    def test_get_description(self):
        """Test getting tools description."""
        desc = get_tools_description()
        assert "Available Tools" in desc
        assert "calculate" in desc
