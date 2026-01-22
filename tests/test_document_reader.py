"""
Tests for Document Reader - Multi-format Document Processing
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from document_reader import (
    DocumentContent, SimpleHTMLParser,
    read_plain_text, read_html, read_json, parse_html_content,
    read_document, get_supported_extensions, get_supported_formats,
    check_dependencies, get_missing_dependencies,
    SUPPORTED_EXTENSIONS
)


class TestDocumentContent:
    """Tests for DocumentContent dataclass."""
    
    def test_create_content(self):
        """Test creating document content."""
        content = DocumentContent(
            text="Hello world this is a test",
            title="Test Doc"
        )
        assert content.text == "Hello world this is a test"
        assert content.title == "Test Doc"
        assert content.word_count == 6
        assert content.char_count == 26
    
    def test_empty_content(self):
        """Test empty document content."""
        content = DocumentContent(text="")
        assert content.word_count == 0
        assert content.char_count == 0
    
    def test_content_with_metadata(self):
        """Test content with metadata."""
        content = DocumentContent(
            text="Some text",
            title="Title",
            author="Author",
            metadata={"key": "value"},
            pages=5
        )
        assert content.author == "Author"
        assert content.metadata["key"] == "value"
        assert content.pages == 5


class TestSimpleHTMLParser:
    """Tests for HTML parsing."""
    
    def test_basic_html(self):
        """Test parsing basic HTML."""
        html = "<html><body><p>Hello World</p></body></html>"
        parser = SimpleHTMLParser()
        parser.feed(html)
        text = parser.get_text()
        assert "Hello World" in text
    
    def test_extract_title(self):
        """Test extracting title from HTML."""
        html = "<html><head><title>My Title</title></head><body>Content</body></html>"
        parser = SimpleHTMLParser()
        parser.feed(html)
        assert parser.title == "My Title"
    
    def test_skip_script_tags(self):
        """Test that script content is skipped."""
        html = "<html><body><script>alert('hi');</script><p>Text</p></body></html>"
        parser = SimpleHTMLParser()
        parser.feed(html)
        text = parser.get_text()
        assert "alert" not in text
        assert "Text" in text
    
    def test_skip_style_tags(self):
        """Test that style content is skipped."""
        html = "<html><body><style>.red{color:red}</style><p>Text</p></body></html>"
        parser = SimpleHTMLParser()
        parser.feed(html)
        text = parser.get_text()
        assert "color" not in text
        assert "Text" in text
    
    def test_handle_newlines_for_blocks(self):
        """Test that block elements create newlines."""
        html = "<p>First</p><p>Second</p>"
        parser = SimpleHTMLParser()
        parser.feed(html)
        text = parser.get_text()
        assert "First" in text
        assert "Second" in text


class TestReadPlainText:
    """Tests for plain text reading."""
    
    def test_read_txt_file(self):
        """Test reading a .txt file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Hello World")
            f.flush()
            
            content = read_plain_text(Path(f.name))
            assert content.text == "Hello World"
            assert content.original_format == ".txt"
        
        os.unlink(f.name)
    
    def test_read_with_encoding(self):
        """Test reading with different encoding."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write("Héllo Wörld".encode('utf-8'))
            f.flush()
            
            content = read_plain_text(Path(f.name), encoding='utf-8')
            assert "Héllo" in content.text
        
        os.unlink(f.name)


class TestReadHTML:
    """Tests for HTML file reading."""
    
    def test_read_html_file(self):
        """Test reading an HTML file."""
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Header</h1>
                <p>This is a paragraph.</p>
            </body>
        </html>
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            f.flush()
            
            content = read_html(Path(f.name))
            assert "Header" in content.text
            assert "This is a paragraph" in content.text
            assert content.original_format == "html"
        
        os.unlink(f.name)


class TestReadJSON:
    """Tests for JSON file reading."""
    
    def test_read_json_file(self):
        """Test reading a JSON file."""
        data = {"name": "test", "value": 123}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            f.flush()
            
            content = read_json(Path(f.name))
            assert '"name"' in content.text
            assert '"test"' in content.text
            assert content.original_format == "json"
        
        os.unlink(f.name)
    
    def test_read_invalid_json(self):
        """Test reading invalid JSON (treated as text)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{not valid json")
            f.flush()
            
            content = read_json(Path(f.name))
            assert "{not valid json" in content.text
        
        os.unlink(f.name)


class TestReadDocument:
    """Tests for the main read_document function."""
    
    def test_read_txt(self):
        """Test reading a text file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            f.flush()
            
            content = read_document(f.name)
            assert content.text == "Test content"
            assert content.source_type == "file"
        
        os.unlink(f.name)
    
    def test_read_md(self):
        """Test reading a markdown file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Header\n\nParagraph text.")
            f.flush()
            
            content = read_document(f.name)
            assert "Header" in content.text
            assert "Paragraph" in content.text
        
        os.unlink(f.name)
    
    def test_file_not_found(self):
        """Test reading non-existent file."""
        with pytest.raises(FileNotFoundError):
            read_document("/nonexistent/path/file.txt")
    
    def test_unsupported_extension(self):
        """Test reading unsupported file type."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("content")
            f.flush()
            
            with pytest.raises(ValueError, match="Unsupported file type"):
                read_document(f.name)
        
        os.unlink(f.name)


class TestSupportedExtensions:
    """Tests for supported extensions."""
    
    def test_get_supported_extensions(self):
        """Test getting list of supported extensions."""
        extensions = get_supported_extensions()
        assert '.txt' in extensions
        assert '.pdf' in extensions
        assert '.docx' in extensions
        assert '.epub' in extensions
        assert '.html' in extensions
    
    def test_get_supported_formats(self):
        """Test getting formats by category."""
        formats = get_supported_formats()
        assert 'text' in formats
        assert 'documents' in formats
        assert 'code' in formats
        assert 'ebooks' in formats
        assert '.txt' in formats['text']
        assert '.pdf' in formats['documents']
    
    def test_supported_extensions_dict(self):
        """Test SUPPORTED_EXTENSIONS dictionary."""
        assert SUPPORTED_EXTENSIONS['.txt'] == 'text/plain'
        assert SUPPORTED_EXTENSIONS['.pdf'] == 'application/pdf'
        assert SUPPORTED_EXTENSIONS['.html'] == 'text/html'


class TestCheckDependencies:
    """Tests for dependency checking."""
    
    def test_check_dependencies_returns_dict(self):
        """Test that check_dependencies returns a dict."""
        deps = check_dependencies()
        assert isinstance(deps, dict)
        # Should check for various PDF libraries
        assert 'pymupdf' in deps or 'pypdf' in deps or 'pdfplumber' in deps
    
    def test_get_missing_dependencies(self):
        """Test getting missing dependencies."""
        missing = get_missing_dependencies()
        assert isinstance(missing, list)
        # Each item should be a string with install instructions
        for item in missing:
            assert 'pip install' in item


class TestParseHTMLContent:
    """Tests for parse_html_content function."""
    
    def test_parse_simple_html(self):
        """Test parsing simple HTML."""
        html = "<p>Hello World</p>"
        content = parse_html_content(html)
        assert "Hello World" in content.text
    
    def test_parse_with_title(self):
        """Test parsing HTML with title."""
        html = "<html><head><title>My Page</title></head><body>Content</body></html>"
        content = parse_html_content(html, title="Fallback")
        assert content.title == "My Page"
    
    def test_parse_fallback_title(self):
        """Test fallback title when no title tag."""
        html = "<body>Content</body>"
        content = parse_html_content(html, title="Fallback Title")
        # Should use parser title (None) or fall back
        assert content.text == "Content"


class TestCodeFiles:
    """Tests for code file reading."""
    
    def test_read_python_file(self):
        """Test reading a Python file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def hello():\n    print('Hello')")
            f.flush()
            
            content = read_document(f.name)
            assert "def hello" in content.text
            assert "print" in content.text
        
        os.unlink(f.name)
    
    def test_read_javascript_file(self):
        """Test reading a JavaScript file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write("function hello() { console.log('Hi'); }")
            f.flush()
            
            content = read_document(f.name)
            assert "function hello" in content.text
        
        os.unlink(f.name)


class TestURLReading:
    """Tests for URL fetching (mocked)."""
    
    def test_fetch_html_url(self):
        """Test fetching HTML from URL."""
        import urllib.request
        from unittest.mock import patch, MagicMock
        from document_reader import fetch_url
        
        mock_response = MagicMock()
        mock_response.headers = {'Content-Type': 'text/html; charset=utf-8'}
        mock_response.read.return_value = b"<html><body><p>Hello from URL</p></body></html>"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch.object(urllib.request, 'urlopen', return_value=mock_response):
            with patch.object(urllib.request, 'Request', return_value=MagicMock()):
                content = fetch_url("https://example.com")
                assert "Hello from URL" in content.text
                assert content.source_type == "url"
    
    def test_fetch_json_url(self):
        """Test fetching JSON from URL."""
        import urllib.request
        from unittest.mock import patch, MagicMock
        from document_reader import fetch_url
        
        mock_response = MagicMock()
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.read.return_value = b'{"name": "test"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch.object(urllib.request, 'urlopen', return_value=mock_response):
            with patch.object(urllib.request, 'Request', return_value=MagicMock()):
                content = fetch_url("https://api.example.com/data")
                assert '"name"' in content.text
                assert content.original_format == "json"


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_file(self):
        """Test reading empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            f.flush()
            
            content = read_document(f.name)
            assert content.text == ""
            assert content.word_count == 0
        
        os.unlink(f.name)
    
    def test_large_file(self):
        """Test reading a larger file."""
        large_content = "word " * 10000  # 50,000 chars
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(large_content)
            f.flush()
            
            content = read_document(f.name)
            assert content.word_count == 10000
        
        os.unlink(f.name)
    
    def test_file_with_special_characters(self):
        """Test reading file with special characters."""
        special_content = "Hello 🌍 World! こんにちは €100"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(special_content)
            f.flush()
            
            content = read_document(f.name)
            assert "🌍" in content.text
            assert "こんにちは" in content.text
            assert "€" in content.text
        
        os.unlink(f.name)


class TestYAMLAndConfig:
    """Tests for YAML and config files."""
    
    def test_read_yaml_file(self):
        """Test reading a YAML file."""
        yaml_content = """
name: test
version: 1.0
features:
  - feature1
  - feature2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            content = read_document(f.name)
            assert "name: test" in content.text
            assert "features:" in content.text
        
        os.unlink(f.name)
    
    def test_read_ini_file(self):
        """Test reading an INI file."""
        ini_content = """
[section]
key = value
another = 123
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(ini_content)
            f.flush()
            
            content = read_document(f.name)
            assert "[section]" in content.text
            assert "key = value" in content.text
        
        os.unlink(f.name)
