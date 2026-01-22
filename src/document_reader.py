"""
Document Reader - Multi-format Document Processing

Supports reading various document formats for AI processing:
- Plain text files (.txt, .md, .csv, .json, .xml, .yaml, etc.)
- PDF documents (.pdf)
- Microsoft Word documents (.docx, .doc)
- EPUB e-books (.epub)
- HTML files and web links (.html, http://, https://)
- Rich Text Format (.rtf)
- OpenDocument Text (.odt)
- Images (.jpg, .jpeg, .png, .gif, .webp, .bmp) - Gemma 3 multimodal
- Audio files (.mp3, .wav, .ogg, .flac, .m4a) - metadata extraction
- Video files (.mp4, .webm, .mkv, .avi) - metadata extraction

Gemma 3 4B is multimodal and can process:
- Text (128K token context window)
- Images (JPEG/PNG, normalized to 896x896)
- Audio (with appropriate framework support)
- Video (short clips, emerging support)

All documents are converted to text or appropriate format for AI consumption.
"""

import base64
import io
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union
from urllib.parse import urlparse
import html.parser
import json


# Set up logging
logger = logging.getLogger(__name__)


# Supported file extensions and their MIME types
SUPPORTED_EXTENSIONS = {
    # Plain text formats
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.markdown': 'text/markdown',
    '.rst': 'text/x-rst',
    '.csv': 'text/csv',
    '.tsv': 'text/tab-separated-values',
    '.json': 'application/json',
    '.xml': 'text/xml',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.xhtml': 'application/xhtml+xml',
    '.yaml': 'text/yaml',
    '.yml': 'text/yaml',
    '.toml': 'text/toml',
    '.ini': 'text/plain',
    '.cfg': 'text/plain',
    '.conf': 'text/plain',
    '.log': 'text/plain',
    
    # Code files
    '.py': 'text/x-python',
    '.js': 'text/javascript',
    '.ts': 'text/typescript',
    '.jsx': 'text/javascript',
    '.tsx': 'text/typescript',
    '.java': 'text/x-java',
    '.c': 'text/x-c',
    '.cpp': 'text/x-c++',
    '.h': 'text/x-c',
    '.hpp': 'text/x-c++',
    '.cs': 'text/x-csharp',
    '.go': 'text/x-go',
    '.rs': 'text/x-rust',
    '.rb': 'text/x-ruby',
    '.php': 'text/x-php',
    '.swift': 'text/x-swift',
    '.kt': 'text/x-kotlin',
    '.scala': 'text/x-scala',
    '.sql': 'text/x-sql',
    '.sh': 'text/x-shellscript',
    '.bash': 'text/x-shellscript',
    '.zsh': 'text/x-shellscript',
    '.ps1': 'text/x-powershell',
    '.r': 'text/x-r',
    '.m': 'text/x-matlab',
    '.lua': 'text/x-lua',
    '.pl': 'text/x-perl',
    '.dart': 'text/x-dart',
    
    # Document formats (require special handling)
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.odt': 'application/vnd.oasis.opendocument.text',
    '.rtf': 'application/rtf',
    '.epub': 'application/epub+zip',
    
    # Image formats (Gemma 3 multimodal - native support)
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.bmp': 'image/bmp',
    '.tiff': 'image/tiff',
    '.tif': 'image/tiff',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    
    # Audio formats (metadata extraction, transcription with Whisper)
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.ogg': 'audio/ogg',
    '.flac': 'audio/flac',
    '.m4a': 'audio/mp4',
    '.aac': 'audio/aac',
    '.wma': 'audio/x-ms-wma',
    '.opus': 'audio/opus',
    
    # Video formats (metadata extraction, frame extraction)
    '.mp4': 'video/mp4',
    '.webm': 'video/webm',
    '.mkv': 'video/x-matroska',
    '.avi': 'video/x-msvideo',
    '.mov': 'video/quicktime',
    '.wmv': 'video/x-ms-wmv',
    '.flv': 'video/x-flv',
    '.m4v': 'video/x-m4v',
    
    # Archive formats (list contents)
    '.zip': 'application/zip',
    '.tar': 'application/x-tar',
    '.gz': 'application/gzip',
    '.7z': 'application/x-7z-compressed',
    '.rar': 'application/vnd.rar',
    
    # Spreadsheet formats
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
    '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
    
    # Presentation formats  
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.odp': 'application/vnd.oasis.opendocument.presentation',
}


# Categories for format grouping
FORMAT_CATEGORIES = {
    'text': ['.txt', '.md', '.markdown', '.rst'],
    'data': ['.json', '.csv', '.tsv', '.xml', '.yaml', '.yml', '.toml'],
    'code': ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
             '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.sql',
             '.sh', '.bash', '.zsh', '.ps1', '.r', '.m', '.lua', '.pl', '.dart'],
    'documents': ['.pdf', '.docx', '.doc', '.odt', '.rtf'],
    'ebooks': ['.epub'],
    'web': ['.html', '.htm', '.xhtml'],
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif', '.svg'],
    'audio': ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.opus'],
    'video': ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.m4v'],
    'archives': ['.zip', '.tar', '.gz', '.7z', '.rar'],
    'spreadsheets': ['.xlsx', '.xls', '.ods'],
    'presentations': ['.pptx', '.ppt', '.odp'],
    'config': ['.ini', '.cfg', '.conf', '.log'],
}


@dataclass
class DocumentContent:
    """Represents extracted document content."""
    text: str
    title: Optional[str] = None
    author: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    pages: int = 1
    word_count: int = 0
    char_count: int = 0
    source_type: str = "file"  # file, url, text
    original_format: str = "text"
    # For multimodal content
    image_data: Optional[bytes] = None  # Raw image bytes for Gemma vision
    image_base64: Optional[str] = None  # Base64 encoded image
    audio_data: Optional[bytes] = None  # Raw audio bytes
    video_frames: Optional[List[bytes]] = None  # Extracted video frames
    is_multimodal: bool = False
    
    def __post_init__(self):
        """Calculate word and character counts."""
        if self.text:
            self.char_count = len(self.text)
            self.word_count = len(self.text.split())


class SimpleHTMLParser(html.parser.HTMLParser):
    """Simple HTML parser that extracts text content."""
    
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.current_tag = None
        self.skip_tags = {'script', 'style', 'noscript', 'head', 'meta', 'link'}
        self.block_tags = {'p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                          'li', 'tr', 'td', 'th', 'blockquote', 'pre', 'article',
                          'section', 'header', 'footer', 'nav', 'aside'}
        self.title = None
        self.in_title = False
    
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag.lower()
        if self.current_tag == 'title':
            self.in_title = True
        if self.current_tag in self.block_tags:
            self.text_parts.append('\n')
        if self.current_tag == 'br':
            self.text_parts.append('\n')
    
    def handle_endtag(self, tag):
        if tag.lower() == 'title':
            self.in_title = False
        if tag.lower() in self.block_tags:
            self.text_parts.append('\n')
        self.current_tag = None
    
    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            text = data.strip()
            if text:
                if self.in_title and not self.title:
                    self.title = text
                self.text_parts.append(text + ' ')
    
    def get_text(self) -> str:
        """Get extracted text."""
        text = ''.join(self.text_parts)
        # Clean up multiple whitespace/newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()


def read_plain_text(file_path: Path, encoding: str = 'utf-8') -> DocumentContent:
    """Read plain text file."""
    try:
        content = file_path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        # Try alternative encodings
        for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                content = file_path.read_text(encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError(f"Could not decode file with any known encoding")
    
    return DocumentContent(
        text=content,
        title=file_path.stem,
        original_format=file_path.suffix.lower(),
        source_type="file"
    )


def read_html(file_path: Path) -> DocumentContent:
    """Read HTML file and extract text."""
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    return parse_html_content(content, title=file_path.stem)


def parse_html_content(html_content: str, title: str = None) -> DocumentContent:
    """Parse HTML content and extract text."""
    parser = SimpleHTMLParser()
    try:
        parser.feed(html_content)
    except Exception as e:
        logger.warning(f"HTML parsing error: {e}")
        # Fall back to basic regex-based extraction
        # Use flexible regex that handles malformed closing tags with any whitespace/attributes
        text = re.sub(r'<script\b[^>]*>.*?</script[^>]*>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style\b[^>]*>.*?</style[^>]*>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return DocumentContent(
            text=text.strip(),
            title=title,
            original_format="html",
            source_type="file"
        )
    
    return DocumentContent(
        text=parser.get_text(),
        title=parser.title or title,
        original_format="html",
        source_type="file"
    )


def read_json(file_path: Path) -> DocumentContent:
    """Read JSON file and convert to readable text."""
    content = file_path.read_text(encoding='utf-8')
    try:
        data = json.loads(content)
        # Pretty print for readability
        text = json.dumps(data, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        text = content
    
    return DocumentContent(
        text=text,
        title=file_path.stem,
        original_format="json",
        source_type="file"
    )


def read_pdf(file_path: Path) -> DocumentContent:
    """
    Read PDF file and extract text.
    
    Tries multiple PDF libraries in order of preference.
    """
    text = ""
    pages = 0
    title = file_path.stem
    metadata = {}
    
    # Try PyMuPDF (fitz) first - fastest and most reliable
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(file_path))
        pages = len(doc)
        
        # Extract metadata
        meta = doc.metadata
        if meta:
            title = meta.get('title') or title
            metadata = {k: v for k, v in meta.items() if v}
        
        # Extract text from all pages
        text_parts = []
        for page_num in range(pages):
            page = doc[page_num]
            text_parts.append(page.get_text())
        
        doc.close()
        text = '\n\n'.join(text_parts)
        
    except ImportError:
        # Try pypdf as fallback
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            pages = len(reader.pages)
            
            # Extract metadata
            if reader.metadata:
                title = reader.metadata.title or title
                metadata = {k: str(v) for k, v in reader.metadata.items() if v}
            
            # Extract text
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            text = '\n\n'.join(text_parts)
            
        except ImportError:
            # Try pdfplumber as last resort
            try:
                import pdfplumber
                with pdfplumber.open(str(file_path)) as pdf:
                    pages = len(pdf.pages)
                    text_parts = []
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    text = '\n\n'.join(text_parts)
                    
            except ImportError:
                raise ImportError(
                    "No PDF library available. Install one of: "
                    "pip install pymupdf OR pip install pypdf OR pip install pdfplumber"
                )
    
    if not text.strip():
        text = f"[PDF document: {file_path.name} - {pages} pages. Text extraction failed or document is image-based.]"
    
    return DocumentContent(
        text=text,
        title=title,
        metadata=metadata,
        pages=pages,
        original_format="pdf",
        source_type="file"
    )


def read_docx(file_path: Path) -> DocumentContent:
    """Read Microsoft Word .docx file."""
    try:
        from docx import Document as DocxDocument
        doc = DocxDocument(str(file_path))
        
        # Extract text from paragraphs
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        
        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = '\t'.join(cell.text for cell in row.cells)
                if row_text.strip():
                    text_parts.append(row_text)
        
        text = '\n\n'.join(text_parts)
        
        # Extract metadata
        metadata = {}
        core_props = doc.core_properties
        title = core_props.title or file_path.stem
        if core_props.author:
            metadata['author'] = core_props.author
        if core_props.created:
            metadata['created'] = str(core_props.created)
        
        return DocumentContent(
            text=text,
            title=title,
            author=core_props.author,
            metadata=metadata,
            original_format="docx",
            source_type="file"
        )
        
    except ImportError:
        raise ImportError("python-docx not installed. Run: pip install python-docx")


def read_doc(file_path: Path) -> DocumentContent:
    """Read legacy Microsoft Word .doc file."""
    # Try using antiword or textract
    try:
        import subprocess
        result = subprocess.run(
            ['antiword', str(file_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return DocumentContent(
                text=result.stdout,
                title=file_path.stem,
                original_format="doc",
                source_type="file"
            )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Try python-docx2txt
    try:
        import docx2txt
        text = docx2txt.process(str(file_path))
        return DocumentContent(
            text=text,
            title=file_path.stem,
            original_format="doc",
            source_type="file"
        )
    except ImportError:
        pass
    
    raise ImportError(
        "Cannot read .doc files. Install antiword (system) or run: pip install docx2txt"
    )


def read_epub(file_path: Path) -> DocumentContent:
    """Read EPUB e-book file."""
    try:
        import ebooklib
        from ebooklib import epub
        
        book = epub.read_epub(str(file_path))
        
        # Get metadata
        title = file_path.stem
        author = None
        metadata = {}
        
        titles = book.get_metadata('DC', 'title')
        if titles:
            title = titles[0][0]
        
        authors = book.get_metadata('DC', 'creator')
        if authors:
            author = authors[0][0]
            metadata['author'] = author
        
        # Extract text from all document items
        text_parts = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8', errors='ignore')
                # Parse HTML content
                doc_content = parse_html_content(content)
                if doc_content.text.strip():
                    text_parts.append(doc_content.text)
        
        text = '\n\n'.join(text_parts)
        
        return DocumentContent(
            text=text,
            title=title,
            author=author,
            metadata=metadata,
            original_format="epub",
            source_type="file"
        )
        
    except ImportError:
        raise ImportError("ebooklib not installed. Run: pip install ebooklib")


def read_rtf(file_path: Path) -> DocumentContent:
    """Read Rich Text Format file."""
    try:
        from striprtf.striprtf import rtf_to_text
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        text = rtf_to_text(content)
        
        return DocumentContent(
            text=text,
            title=file_path.stem,
            original_format="rtf",
            source_type="file"
        )
        
    except ImportError:
        raise ImportError("striprtf not installed. Run: pip install striprtf")


def read_odt(file_path: Path) -> DocumentContent:
    """Read OpenDocument Text file."""
    try:
        from odf import text as odf_text
        from odf.opendocument import load
        
        doc = load(str(file_path))
        
        # Extract all text
        text_parts = []
        for para in doc.getElementsByType(odf_text.P):
            para_text = ""
            for node in para.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    para_text += str(node)
                elif hasattr(node, 'childNodes'):
                    for child in node.childNodes:
                        if child.nodeType == child.TEXT_NODE:
                            para_text += str(child)
            if para_text.strip():
                text_parts.append(para_text)
        
        text = '\n\n'.join(text_parts)
        
        return DocumentContent(
            text=text,
            title=file_path.stem,
            original_format="odt",
            source_type="file"
        )
        
    except ImportError:
        raise ImportError("odfpy not installed. Run: pip install odfpy")


def read_image(file_path: Path) -> DocumentContent:
    """
    Read an image file for Gemma 3 multimodal processing.
    
    Gemma 3 4B natively supports image input (JPEG/PNG preferred).
    Images are normalized to 896x896 for optimal processing.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        DocumentContent with image data and metadata
    """
    # Read raw image bytes
    image_bytes = file_path.read_bytes()
    
    # Encode as base64 for API transmission
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    # Get image metadata
    metadata = {
        'file_size': len(image_bytes),
        'format': file_path.suffix.lower().replace('.', ''),
    }
    
    # Try to get image dimensions using PIL
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            metadata['width'] = img.width
            metadata['height'] = img.height
            metadata['mode'] = img.mode
            if hasattr(img, 'info'):
                for key in ['dpi', 'exif']:
                    if key in img.info:
                        metadata[key] = str(img.info[key])[:100]  # Truncate long data
    except ImportError:
        pass  # PIL not available
    except Exception as e:
        logger.warning(f"Could not read image metadata: {e}")
    
    # Create descriptive text
    text = f"[Image: {file_path.name}]\n"
    text += f"Format: {metadata.get('format', 'unknown').upper()}\n"
    if 'width' in metadata and 'height' in metadata:
        text += f"Dimensions: {metadata['width']}x{metadata['height']} pixels\n"
    text += f"Size: {metadata['file_size']:,} bytes\n"
    text += "\n[This image can be analyzed by Gemma 3's vision capabilities]"
    
    return DocumentContent(
        text=text,
        title=file_path.stem,
        metadata=metadata,
        original_format=file_path.suffix.lower(),
        source_type="file",
        image_data=image_bytes,
        image_base64=image_base64,
        is_multimodal=True
    )


def read_audio(file_path: Path) -> DocumentContent:
    """
    Read an audio file and extract metadata.
    
    For transcription, use Whisper or similar ASR model.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        DocumentContent with audio metadata
    """
    audio_bytes = file_path.read_bytes()
    
    metadata = {
        'file_size': len(audio_bytes),
        'format': file_path.suffix.lower().replace('.', ''),
    }
    
    # Try to get audio metadata using mutagen
    try:
        import mutagen
        audio = mutagen.File(str(file_path))
        if audio:
            if hasattr(audio, 'info'):
                if hasattr(audio.info, 'length'):
                    metadata['duration_seconds'] = round(audio.info.length, 2)
                if hasattr(audio.info, 'sample_rate'):
                    metadata['sample_rate'] = audio.info.sample_rate
                if hasattr(audio.info, 'channels'):
                    metadata['channels'] = audio.info.channels
                if hasattr(audio.info, 'bitrate'):
                    metadata['bitrate'] = audio.info.bitrate
            
            # Get tags
            if audio.tags:
                for tag in ['title', 'artist', 'album', 'date', 'genre']:
                    if tag in audio.tags:
                        metadata[tag] = str(audio.tags[tag][0])[:100]
    except ImportError:
        pass  # mutagen not available
    except Exception as e:
        logger.warning(f"Could not read audio metadata: {e}")
    
    # Format duration nicely
    duration_str = ""
    if 'duration_seconds' in metadata:
        mins = int(metadata['duration_seconds'] // 60)
        secs = int(metadata['duration_seconds'] % 60)
        duration_str = f"{mins}:{secs:02d}"
    
    # Create descriptive text
    text = f"[Audio: {file_path.name}]\n"
    text += f"Format: {metadata.get('format', 'unknown').upper()}\n"
    if duration_str:
        text += f"Duration: {duration_str}\n"
    if 'sample_rate' in metadata:
        text += f"Sample Rate: {metadata['sample_rate']} Hz\n"
    if 'title' in metadata:
        text += f"Title: {metadata['title']}\n"
    if 'artist' in metadata:
        text += f"Artist: {metadata['artist']}\n"
    text += f"Size: {metadata['file_size']:,} bytes\n"
    text += "\n[Use Whisper or similar for transcription]"
    
    return DocumentContent(
        text=text,
        title=metadata.get('title', file_path.stem),
        author=metadata.get('artist'),
        metadata=metadata,
        original_format=file_path.suffix.lower(),
        source_type="file",
        audio_data=audio_bytes,
        is_multimodal=True
    )


def read_video(file_path: Path) -> DocumentContent:
    """
    Read a video file and extract metadata and key frames.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        DocumentContent with video metadata and optionally frames
    """
    video_bytes = file_path.read_bytes()
    
    metadata = {
        'file_size': len(video_bytes),
        'format': file_path.suffix.lower().replace('.', ''),
    }
    
    frames = []
    
    # Try to get video metadata and frames using OpenCV
    try:
        import cv2
        cap = cv2.VideoCapture(str(file_path))
        
        if cap.isOpened():
            metadata['frame_count'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            metadata['fps'] = cap.get(cv2.CAP_PROP_FPS)
            metadata['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            metadata['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if metadata['fps'] > 0:
                metadata['duration_seconds'] = round(metadata['frame_count'] / metadata['fps'], 2)
            
            # Extract up to 5 key frames (evenly spaced)
            if metadata['frame_count'] > 0:
                frame_indices = [
                    int(i * metadata['frame_count'] / 5) 
                    for i in range(5)
                ]
                
                for idx in frame_indices:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                    ret, frame = cap.read()
                    if ret:
                        # Encode frame as JPEG
                        _, buffer = cv2.imencode('.jpg', frame)
                        frames.append(buffer.tobytes())
        
        cap.release()
        
    except ImportError:
        pass  # OpenCV not available
    except Exception as e:
        logger.warning(f"Could not read video metadata: {e}")
    
    # Format duration nicely
    duration_str = ""
    if 'duration_seconds' in metadata:
        mins = int(metadata['duration_seconds'] // 60)
        secs = int(metadata['duration_seconds'] % 60)
        duration_str = f"{mins}:{secs:02d}"
    
    # Create descriptive text
    text = f"[Video: {file_path.name}]\n"
    text += f"Format: {metadata.get('format', 'unknown').upper()}\n"
    if duration_str:
        text += f"Duration: {duration_str}\n"
    if 'width' in metadata and 'height' in metadata:
        text += f"Resolution: {metadata['width']}x{metadata['height']}\n"
    if 'fps' in metadata:
        text += f"FPS: {metadata['fps']:.1f}\n"
    if 'frame_count' in metadata:
        text += f"Frames: {metadata['frame_count']:,}\n"
    text += f"Size: {metadata['file_size']:,} bytes\n"
    if frames:
        text += f"\n[Extracted {len(frames)} key frames for analysis]"
    
    return DocumentContent(
        text=text,
        title=file_path.stem,
        metadata=metadata,
        original_format=file_path.suffix.lower(),
        source_type="file",
        video_frames=frames if frames else None,
        is_multimodal=True
    )


def read_spreadsheet(file_path: Path) -> DocumentContent:
    """
    Read a spreadsheet file (.xlsx, .xls, .ods).
    
    Args:
        file_path: Path to the spreadsheet file
        
    Returns:
        DocumentContent with spreadsheet data as text
    """
    ext = file_path.suffix.lower()
    
    try:
        import pandas as pd
        
        if ext == '.xlsx':
            df_dict = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
        elif ext == '.xls':
            df_dict = pd.read_excel(file_path, sheet_name=None, engine='xlrd')
        elif ext == '.ods':
            df_dict = pd.read_excel(file_path, sheet_name=None, engine='odf')
        else:
            raise ValueError(f"Unsupported spreadsheet format: {ext}")
        
        # Convert all sheets to text
        text_parts = []
        metadata = {'sheets': list(df_dict.keys())}
        
        for sheet_name, df in df_dict.items():
            text_parts.append(f"=== Sheet: {sheet_name} ===")
            text_parts.append(df.to_string(index=False))
            text_parts.append("")
        
        return DocumentContent(
            text='\n'.join(text_parts),
            title=file_path.stem,
            metadata=metadata,
            original_format=ext,
            source_type="file"
        )
        
    except ImportError:
        raise ImportError(
            "pandas and openpyxl not installed. Run: pip install pandas openpyxl"
        )


def read_presentation(file_path: Path) -> DocumentContent:
    """
    Read a presentation file (.pptx, .ppt, .odp).
    
    Args:
        file_path: Path to the presentation file
        
    Returns:
        DocumentContent with presentation text
    """
    ext = file_path.suffix.lower()
    
    if ext == '.pptx':
        try:
            from pptx import Presentation
            prs = Presentation(str(file_path))
            
            text_parts = []
            slide_num = 0
            
            for slide in prs.slides:
                slide_num += 1
                text_parts.append(f"=== Slide {slide_num} ===")
                
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        text_parts.append(shape.text)
                
                text_parts.append("")
            
            return DocumentContent(
                text='\n'.join(text_parts),
                title=file_path.stem,
                metadata={'slides': slide_num},
                pages=slide_num,
                original_format="pptx",
                source_type="file"
            )
            
        except ImportError:
            raise ImportError("python-pptx not installed. Run: pip install python-pptx")
    
    else:
        raise ImportError(f"Reading {ext} presentations requires additional libraries")


def read_archive(file_path: Path) -> DocumentContent:
    """
    Read archive file and list contents.
    
    Args:
        file_path: Path to the archive file
        
    Returns:
        DocumentContent with archive listing
    """
    import zipfile
    import tarfile
    
    ext = file_path.suffix.lower()
    contents = []
    metadata = {'format': ext}
    
    try:
        if ext == '.zip':
            with zipfile.ZipFile(file_path, 'r') as zf:
                for info in zf.infolist():
                    contents.append({
                        'name': info.filename,
                        'size': info.file_size,
                        'compressed': info.compress_size
                    })
        
        elif ext in ['.tar', '.gz', '.tgz']:
            mode = 'r:gz' if ext in ['.gz', '.tgz'] else 'r'
            with tarfile.open(file_path, mode) as tf:
                for member in tf.getmembers():
                    contents.append({
                        'name': member.name,
                        'size': member.size
                    })
        
        else:
            return DocumentContent(
                text=f"[Archive: {file_path.name}]\nFormat not directly supported for listing.",
                title=file_path.stem,
                original_format=ext,
                source_type="file"
            )
        
    except Exception as e:
        return DocumentContent(
            text=f"[Archive: {file_path.name}]\nError reading: {e}",
            title=file_path.stem,
            original_format=ext,
            source_type="file"
        )
    
    # Format contents list
    text_parts = [f"[Archive: {file_path.name}]", f"Contains {len(contents)} files:", ""]
    
    for item in contents[:100]:  # Limit to first 100 entries
        size_kb = item['size'] / 1024
        text_parts.append(f"  {item['name']} ({size_kb:.1f} KB)")
    
    if len(contents) > 100:
        text_parts.append(f"  ... and {len(contents) - 100} more files")
    
    metadata['file_count'] = len(contents)
    metadata['total_size'] = sum(item['size'] for item in contents)
    
    return DocumentContent(
        text='\n'.join(text_parts),
        title=file_path.stem,
        metadata=metadata,
        original_format=ext,
        source_type="file"
    )


def fetch_url(url: str, timeout: int = 30) -> DocumentContent:
    """
    Fetch content from a URL and extract text.
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        DocumentContent with extracted text
    """
    try:
        import urllib.request
        import urllib.error
        
        # Add headers to mimic browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; AIChat/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        request = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get('Content-Type', '')
            content = response.read()
            
            # Determine encoding
            encoding = 'utf-8'
            if 'charset=' in content_type:
                encoding = content_type.split('charset=')[-1].split(';')[0].strip()
            
            try:
                text_content = content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                text_content = content.decode('utf-8', errors='ignore')
            
            # Parse based on content type
            if 'html' in content_type.lower() or 'xhtml' in content_type.lower():
                result = parse_html_content(text_content)
                result.source_type = "url"
                result.metadata['url'] = url
                return result
            elif 'json' in content_type.lower():
                try:
                    data = json.loads(text_content)
                    text = json.dumps(data, indent=2, ensure_ascii=False)
                except json.JSONDecodeError:
                    text = text_content
                return DocumentContent(
                    text=text,
                    title=urlparse(url).netloc,
                    original_format="json",
                    source_type="url",
                    metadata={'url': url}
                )
            else:
                # Treat as plain text
                return DocumentContent(
                    text=text_content,
                    title=urlparse(url).netloc,
                    original_format="text",
                    source_type="url",
                    metadata={'url': url}
                )
                
    except urllib.error.URLError as e:
        raise ValueError(f"Failed to fetch URL: {e}")
    except Exception as e:
        raise ValueError(f"Error fetching URL: {e}")


def read_document(source: str, encoding: str = 'utf-8') -> DocumentContent:
    """
    Read a document from a file path or URL.
    
    Supports 70+ file formats including:
    - Text: .txt, .md, .csv, .json, .xml, .yaml, etc.
    - Code: .py, .js, .ts, .java, .go, .rs, etc.
    - Documents: .pdf, .docx, .doc, .odt, .rtf
    - E-books: .epub
    - Web: .html, http://, https://
    - Images: .jpg, .png, .gif, .webp (Gemma 3 multimodal)
    - Audio: .mp3, .wav, .ogg, .flac
    - Video: .mp4, .webm, .mkv
    - Spreadsheets: .xlsx, .xls, .ods
    - Presentations: .pptx, .ppt
    - Archives: .zip, .tar, .gz
    
    Args:
        source: File path or URL
        encoding: Text encoding for plain text files
        
    Returns:
        DocumentContent with extracted text/data
        
    Raises:
        ValueError: If the file type is not supported
        FileNotFoundError: If the file doesn't exist
        ImportError: If required library is not installed
    """
    # Check if it's a URL
    if source.startswith('http://') or source.startswith('https://'):
        return fetch_url(source)
    
    # It's a file path
    path = Path(source).expanduser().resolve()
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")
    
    if not path.is_file():
        raise ValueError(f"Not a file: {source}")
    
    ext = path.suffix.lower()
    
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {ext}\n"
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS.keys()))}"
        )
    
    # Route to appropriate reader based on format category
    
    # Documents
    if ext == '.pdf':
        return read_pdf(path)
    elif ext == '.docx':
        return read_docx(path)
    elif ext == '.doc':
        return read_doc(path)
    elif ext == '.epub':
        return read_epub(path)
    elif ext == '.rtf':
        return read_rtf(path)
    elif ext == '.odt':
        return read_odt(path)
    
    # Web/HTML
    elif ext in ['.html', '.htm', '.xhtml']:
        return read_html(path)
    
    # Data formats
    elif ext == '.json':
        return read_json(path)
    
    # Images (Gemma 3 multimodal)
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif', '.svg', '.ico']:
        return read_image(path)
    
    # Audio
    elif ext in ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.opus']:
        return read_audio(path)
    
    # Video
    elif ext in ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.m4v']:
        return read_video(path)
    
    # Spreadsheets
    elif ext in ['.xlsx', '.xls', '.ods']:
        return read_spreadsheet(path)
    
    # Presentations
    elif ext in ['.pptx', '.ppt', '.odp']:
        return read_presentation(path)
    
    # Archives
    elif ext in ['.zip', '.tar', '.gz', '.7z', '.rar']:
        return read_archive(path)
    
    # Plain text (default)
    else:
        return read_plain_text(path, encoding)


def get_supported_extensions() -> List[str]:
    """Get list of all supported file extensions."""
    return sorted(SUPPORTED_EXTENSIONS.keys())


def get_supported_formats() -> Dict[str, List[str]]:
    """Get supported formats grouped by category."""
    return FORMAT_CATEGORIES.copy()


def check_dependencies() -> Dict[str, bool]:
    """Check which optional dependencies are installed."""
    deps = {}
    
    # PDF readers
    try:
        import fitz
        deps['pymupdf'] = True
    except ImportError:
        deps['pymupdf'] = False
    
    try:
        from pypdf import PdfReader
        deps['pypdf'] = True
    except ImportError:
        deps['pypdf'] = False
    
    try:
        import pdfplumber
        deps['pdfplumber'] = True
    except ImportError:
        deps['pdfplumber'] = False
    
    # Word documents
    try:
        from docx import Document
        deps['python-docx'] = True
    except ImportError:
        deps['python-docx'] = False
    
    # EPUB
    try:
        import ebooklib
        deps['ebooklib'] = True
    except ImportError:
        deps['ebooklib'] = False
    
    # RTF
    try:
        from striprtf.striprtf import rtf_to_text
        deps['striprtf'] = True
    except ImportError:
        deps['striprtf'] = False
    
    # ODT
    try:
        from odf.opendocument import load
        deps['odfpy'] = True
    except ImportError:
        deps['odfpy'] = False
    
    return deps


def get_missing_dependencies() -> List[str]:
    """Get list of missing optional dependencies with install commands."""
    deps = check_dependencies()
    missing = []
    
    if not any([deps.get('pymupdf'), deps.get('pypdf'), deps.get('pdfplumber')]):
        missing.append("PDF support: pip install pymupdf  # or pypdf or pdfplumber")
    
    if not deps.get('python-docx'):
        missing.append("Word .docx support: pip install python-docx")
    
    if not deps.get('ebooklib'):
        missing.append("EPUB support: pip install ebooklib")
    
    if not deps.get('striprtf'):
        missing.append("RTF support: pip install striprtf")
    
    if not deps.get('odfpy'):
        missing.append("ODT support: pip install odfpy")
    
    return missing
