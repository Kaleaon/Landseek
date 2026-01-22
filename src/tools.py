"""
AI Tools Module - Function calling capabilities for AI Chat Room

This module provides a collection of tools that AI participants can use
to perform various actions like calculations, web searches, file operations,
date/time queries, and more.

Tools are designed to be safe and run locally on Pixel 10 Pro.
"""

import json
import math
import os
import re
import subprocess
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    
    def __str__(self) -> str:
        if self.success:
            return f"✅ {self.output}"
        return f"❌ Error: {self.error}"


@dataclass
class Tool:
    """Represents a callable tool for AI agents."""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable[..., ToolResult]
    category: str = "general"
    
    def to_schema(self) -> Dict[str, Any]:
        """Convert tool to OpenAI-compatible function schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": [k for k, v in self.parameters.items() 
                                if v.get("required", False)]
                }
            }
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        try:
            return self.function(**kwargs)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_builtin_tools()
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[Tool]:
        """List all tools, optionally filtered by category."""
        tools = list(self.tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible schemas for all tools."""
        return [tool.to_schema() for tool in self.tools.values()]
    
    def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False, 
                output=None, 
                error=f"Tool '{name}' not found"
            )
        return tool.execute(**kwargs)
    
    def _register_builtin_tools(self) -> None:
        """Register all built-in tools."""
        # Math tools
        self.register(Tool(
            name="calculate",
            description="Evaluate a mathematical expression. Supports basic arithmetic, "
                       "trigonometry, logarithms, and common math functions.",
            parameters={
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sin(pi/2)', 'sqrt(16)')",
                    "required": True
                }
            },
            function=calculate,
            category="math"
        ))
        
        self.register(Tool(
            name="unit_convert",
            description="Convert between units of measurement.",
            parameters={
                "value": {
                    "type": "number",
                    "description": "The value to convert",
                    "required": True
                },
                "from_unit": {
                    "type": "string",
                    "description": "Source unit (e.g., 'km', 'miles', 'celsius', 'fahrenheit')",
                    "required": True
                },
                "to_unit": {
                    "type": "string",
                    "description": "Target unit",
                    "required": True
                }
            },
            function=unit_convert,
            category="math"
        ))
        
        # Date/Time tools
        self.register(Tool(
            name="get_current_time",
            description="Get the current date and time.",
            parameters={
                "timezone": {
                    "type": "string",
                    "description": "Timezone (e.g., 'UTC', 'US/Pacific'). Default is local time.",
                    "required": False
                },
                "format": {
                    "type": "string",
                    "description": "Output format (e.g., 'iso', 'human', 'date', 'time')",
                    "required": False
                }
            },
            function=get_current_time,
            category="datetime"
        ))
        
        self.register(Tool(
            name="calculate_date",
            description="Calculate a date by adding or subtracting days, weeks, months from a date.",
            parameters={
                "base_date": {
                    "type": "string",
                    "description": "Base date in YYYY-MM-DD format. Use 'today' for current date.",
                    "required": True
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to add (negative to subtract)",
                    "required": False
                },
                "weeks": {
                    "type": "integer",
                    "description": "Number of weeks to add (negative to subtract)",
                    "required": False
                }
            },
            function=calculate_date,
            category="datetime"
        ))
        
        # Text tools
        self.register(Tool(
            name="word_count",
            description="Count words, characters, sentences, and paragraphs in text.",
            parameters={
                "text": {
                    "type": "string",
                    "description": "Text to analyze",
                    "required": True
                }
            },
            function=word_count,
            category="text"
        ))
        
        self.register(Tool(
            name="search_text",
            description="Search for a pattern in text using regular expressions.",
            parameters={
                "text": {
                    "type": "string",
                    "description": "Text to search in",
                    "required": True
                },
                "pattern": {
                    "type": "string",
                    "description": "Regular expression pattern to search for",
                    "required": True
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Whether search is case sensitive (default: False)",
                    "required": False
                }
            },
            function=search_text,
            category="text"
        ))
        
        self.register(Tool(
            name="extract_urls",
            description="Extract all URLs from text.",
            parameters={
                "text": {
                    "type": "string",
                    "description": "Text to extract URLs from",
                    "required": True
                }
            },
            function=extract_urls,
            category="text"
        ))
        
        self.register(Tool(
            name="extract_emails",
            description="Extract all email addresses from text.",
            parameters={
                "text": {
                    "type": "string",
                    "description": "Text to extract emails from",
                    "required": True
                }
            },
            function=extract_emails,
            category="text"
        ))
        
        # Data tools
        self.register(Tool(
            name="json_parse",
            description="Parse and query JSON data.",
            parameters={
                "json_string": {
                    "type": "string",
                    "description": "JSON string to parse",
                    "required": True
                },
                "query_path": {
                    "type": "string",
                    "description": "Dot-notation path to extract (e.g., 'data.users[0].name')",
                    "required": False
                }
            },
            function=json_parse,
            category="data"
        ))
        
        self.register(Tool(
            name="list_files",
            description="List files in a directory.",
            parameters={
                "path": {
                    "type": "string",
                    "description": "Directory path to list",
                    "required": True
                },
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g., '*.txt')",
                    "required": False
                }
            },
            function=list_files,
            category="filesystem"
        ))
        
        self.register(Tool(
            name="read_file",
            description="Read the contents of a text file.",
            parameters={
                "path": {
                    "type": "string",
                    "description": "Path to the file to read",
                    "required": True
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to read (default: all)",
                    "required": False
                }
            },
            function=read_file,
            category="filesystem"
        ))
        
        # System tools
        self.register(Tool(
            name="get_system_info",
            description="Get system information (OS, Python version, etc.).",
            parameters={},
            function=get_system_info,
            category="system"
        ))
        
        self.register(Tool(
            name="run_command",
            description="Run a safe shell command (limited to safe commands).",
            parameters={
                "command": {
                    "type": "string",
                    "description": "Command to run (only safe commands allowed: echo, date, pwd, whoami, ls, cat, head, tail, wc)",
                    "required": True
                }
            },
            function=run_command,
            category="system"
        ))


# Tool implementations

def calculate(expression: str) -> ToolResult:
    """Evaluate a mathematical expression safely."""
    # Safe math functions
    safe_dict = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'pow': pow,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,
        'exp': math.exp,
        'floor': math.floor,
        'ceil': math.ceil,
        'pi': math.pi,
        'e': math.e,
        'tau': math.tau,
    }
    
    try:
        # Strict validation: only allow safe characters for math expressions
        # Allows: digits, operators, parentheses, dots, spaces, and function names
        allowed_pattern = r'^[\d\s\+\-\*/\(\)\.\,a-zA-Z_]+$'
        if not re.match(allowed_pattern, expression):
            return ToolResult(success=False, output=None, error="Expression contains invalid characters")
        
        # Remove dangerous keywords
        forbidden = ['import', 'exec', 'eval', '__', 'open', 'file', 'os', 'sys', 
                    'subprocess', 'lambda', 'class', 'def', 'global', 'locals', 'globals']
        expr_lower = expression.lower()
        if any(kw in expr_lower for kw in forbidden):
            return ToolResult(success=False, output=None, error="Expression contains forbidden keywords")
        
        # Limit expression length to prevent DoS
        if len(expression) > 200:
            return ToolResult(success=False, output=None, error="Expression too long (max 200 characters)")
        
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return ToolResult(success=True, output=result)
    except Exception as e:
        return ToolResult(success=False, output=None, error=str(e))


def unit_convert(value: float, from_unit: str, to_unit: str) -> ToolResult:
    """Convert between units."""
    conversions = {
        # Length
        ('km', 'miles'): lambda x: x * 0.621371,
        ('miles', 'km'): lambda x: x * 1.60934,
        ('m', 'ft'): lambda x: x * 3.28084,
        ('ft', 'm'): lambda x: x * 0.3048,
        ('cm', 'inches'): lambda x: x * 0.393701,
        ('inches', 'cm'): lambda x: x * 2.54,
        
        # Temperature
        ('celsius', 'fahrenheit'): lambda x: x * 9/5 + 32,
        ('fahrenheit', 'celsius'): lambda x: (x - 32) * 5/9,
        ('celsius', 'kelvin'): lambda x: x + 273.15,
        ('kelvin', 'celsius'): lambda x: x - 273.15,
        
        # Weight
        ('kg', 'lbs'): lambda x: x * 2.20462,
        ('lbs', 'kg'): lambda x: x * 0.453592,
        ('g', 'oz'): lambda x: x * 0.035274,
        ('oz', 'g'): lambda x: x * 28.3495,
        
        # Volume
        ('liters', 'gallons'): lambda x: x * 0.264172,
        ('gallons', 'liters'): lambda x: x * 3.78541,
        ('ml', 'fl_oz'): lambda x: x * 0.033814,
        ('fl_oz', 'ml'): lambda x: x * 29.5735,
    }
    
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        result = conversions[key](value)
        return ToolResult(success=True, output=f"{value} {from_unit} = {result:.4f} {to_unit}")
    
    return ToolResult(
        success=False, 
        output=None, 
        error=f"Unknown conversion: {from_unit} to {to_unit}"
    )


def get_current_time(timezone: str = None, format: str = "human") -> ToolResult:
    """Get current date and time."""
    now = datetime.now()
    
    if format == "iso":
        output = now.isoformat()
    elif format == "date":
        output = now.strftime("%Y-%m-%d")
    elif format == "time":
        output = now.strftime("%H:%M:%S")
    else:  # human
        output = now.strftime("%A, %B %d, %Y at %I:%M %p")
    
    return ToolResult(success=True, output=output)


def calculate_date(
    base_date: str, 
    days: int = 0, 
    weeks: int = 0
) -> ToolResult:
    """Calculate a date from base date."""
    try:
        if base_date.lower() == "today":
            base = datetime.now().date()
        else:
            base = datetime.strptime(base_date, "%Y-%m-%d").date()
        
        delta = timedelta(days=days + (weeks * 7))
        result = base + delta
        
        return ToolResult(
            success=True, 
            output=f"{result.strftime('%Y-%m-%d')} ({result.strftime('%A, %B %d, %Y')})"
        )
    except Exception as e:
        return ToolResult(success=False, output=None, error=str(e))


def word_count(text: str) -> ToolResult:
    """Count words, characters, etc. in text."""
    words = len(text.split())
    chars = len(text)
    chars_no_spaces = len(text.replace(" ", ""))
    sentences = len(re.findall(r'[.!?]+', text))
    paragraphs = len([p for p in text.split('\n\n') if p.strip()])
    lines = len(text.split('\n'))
    
    return ToolResult(
        success=True,
        output={
            "words": words,
            "characters": chars,
            "characters_no_spaces": chars_no_spaces,
            "sentences": sentences,
            "paragraphs": paragraphs,
            "lines": lines
        }
    )


def search_text(text: str, pattern: str, case_sensitive: bool = False) -> ToolResult:
    """Search for pattern in text."""
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        matches = re.findall(pattern, text, flags)
        
        return ToolResult(
            success=True,
            output={
                "matches": matches,
                "count": len(matches)
            }
        )
    except Exception as e:
        return ToolResult(success=False, output=None, error=str(e))


def extract_urls(text: str) -> ToolResult:
    """Extract URLs from text."""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    return ToolResult(success=True, output={"urls": urls, "count": len(urls)})


def extract_emails(text: str) -> ToolResult:
    """Extract email addresses from text."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    return ToolResult(success=True, output={"emails": emails, "count": len(emails)})


def json_parse(json_string: str, query_path: str = None) -> ToolResult:
    """Parse JSON and optionally extract a path."""
    try:
        data = json.loads(json_string)
        
        if query_path:
            # Limit path depth to prevent DoS
            if query_path.count('.') + query_path.count('[') > 20:
                return ToolResult(success=False, output=None, error="Path too deep (max 20 levels)")
            
            # Simple dot notation path parser - filter out empty parts
            parts = [p for p in query_path.replace('[', '.').replace(']', '').split('.') if p]
            
            if not parts:
                return ToolResult(success=True, output=data)
            
            result = data
            for part in parts:
                try:
                    if part.isdigit():
                        if not isinstance(result, (list, tuple)):
                            return ToolResult(success=False, output=None, 
                                            error=f"Cannot index non-list with '{part}'")
                        idx = int(part)
                        if idx < 0 or idx >= len(result):
                            return ToolResult(success=False, output=None,
                                            error=f"Index {idx} out of range")
                        result = result[idx]
                    else:
                        if not isinstance(result, dict):
                            return ToolResult(success=False, output=None,
                                            error=f"Cannot access key '{part}' on non-dict")
                        if part not in result:
                            return ToolResult(success=False, output=None,
                                            error=f"Key '{part}' not found")
                        result = result[part]
                except (KeyError, IndexError, TypeError) as e:
                    return ToolResult(success=False, output=None, error=f"Path error: {str(e)}")
            
            return ToolResult(success=True, output=result)
        
        return ToolResult(success=True, output=data)
    except json.JSONDecodeError as e:
        return ToolResult(success=False, output=None, error=f"Invalid JSON: {str(e)}")
    except Exception as e:
        return ToolResult(success=False, output=None, error=str(e))


def list_files(path: str, pattern: str = "*") -> ToolResult:
    """List files in a directory."""
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return ToolResult(success=False, output=None, error=f"Path not found: {path}")
        if not p.is_dir():
            return ToolResult(success=False, output=None, error=f"Not a directory: {path}")
        
        files = list(p.glob(pattern))
        file_list = [
            {
                "name": f.name,
                "type": "directory" if f.is_dir() else "file",
                "size": f.stat().st_size if f.is_file() else None
            }
            for f in files[:100]  # Limit to 100 files
        ]
        
        return ToolResult(success=True, output={"files": file_list, "count": len(file_list)})
    except Exception as e:
        return ToolResult(success=False, output=None, error=str(e))


def read_file(path: str, max_lines: int = None) -> ToolResult:
    """Read a text file."""
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return ToolResult(success=False, output=None, error=f"File not found: {path}")
        if not p.is_file():
            return ToolResult(success=False, output=None, error=f"Not a file: {path}")
        
        content = p.read_text(encoding='utf-8')
        
        if max_lines:
            lines = content.split('\n')[:max_lines]
            content = '\n'.join(lines)
        
        return ToolResult(success=True, output=content)
    except Exception as e:
        return ToolResult(success=False, output=None, error=str(e))


def get_system_info() -> ToolResult:
    """Get system information."""
    import platform
    import sys
    
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": sys.version.split()[0],
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "hostname": platform.node(),
    }
    
    return ToolResult(success=True, output=info)


def run_command(command: str) -> ToolResult:
    """Run a safe shell command."""
    import shlex
    
    # Whitelist of safe commands
    safe_commands = ['echo', 'date', 'pwd', 'whoami', 'ls', 'cat', 'head', 'tail', 'wc']
    
    # Parse command safely using shlex
    try:
        cmd_parts = shlex.split(command)
    except ValueError as e:
        return ToolResult(success=False, output=None, error=f"Invalid command syntax: {str(e)}")
    
    if not cmd_parts:
        return ToolResult(success=False, output=None, error="Empty command")
    
    base_cmd = cmd_parts[0]
    
    if base_cmd not in safe_commands:
        return ToolResult(
            success=False, 
            output=None, 
            error=f"Command '{base_cmd}' not allowed. Safe commands: {', '.join(safe_commands)}"
        )
    
    # Additional security: check for shell metacharacters in arguments
    shell_chars = ['|', ';', '&', '$', '`', '(', ')', '{', '}', '<', '>', '\n']
    for arg in cmd_parts[1:]:
        if any(c in arg for c in shell_chars):
            return ToolResult(
                success=False,
                output=None,
                error=f"Shell metacharacters not allowed in arguments"
            )
    
    try:
        # Use shell=False and pass command as list for safety
        result = subprocess.run(
            cmd_parts,
            shell=False,
            capture_output=True,
            text=True,
            timeout=5  # 5 second timeout
        )
        
        if result.returncode == 0:
            return ToolResult(success=True, output=result.stdout.strip())
        else:
            return ToolResult(success=False, output=None, error=result.stderr.strip())
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, output=None, error="Command timed out")
    except Exception as e:
        return ToolResult(success=False, output=None, error=str(e))


# Global tool registry instance
tool_registry = ToolRegistry()


def get_tools_description() -> str:
    """Get a formatted description of all available tools."""
    categories = {}
    for tool in tool_registry.list_tools():
        if tool.category not in categories:
            categories[tool.category] = []
        categories[tool.category].append(tool)
    
    lines = ["Available Tools:\n"]
    for category, tools in sorted(categories.items()):
        lines.append(f"\n📁 {category.upper()}")
        for tool in tools:
            params = ", ".join(tool.parameters.keys()) if tool.parameters else "none"
            lines.append(f"  • {tool.name}({params}): {tool.description[:60]}...")
    
    return "\n".join(lines)


def parse_tool_call(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse a tool call from AI response text.
    
    Expected format: @tool_name(arg1=value1, arg2=value2)
    Or: @tool_name{"arg1": "value1", "arg2": "value2"}
    """
    # Pattern for @tool_name(args) or @tool_name{json}
    pattern = r'@(\w+)(?:\(([^)]*)\)|\{([^}]+)\})'
    match = re.search(pattern, text)
    
    if not match:
        return None
    
    tool_name = match.group(1)
    
    # Try parentheses format first
    if match.group(2) is not None:
        args_str = match.group(2)
        kwargs = {}
        if args_str.strip():
            # Parse key=value pairs
            for pair in args_str.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    # Try to convert to appropriate type
                    try:
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif re.match(r'^-?\d+\.?\d*$', value):
                            value = float(value)
                    except (ValueError, AttributeError):
                        pass  # Keep as string if conversion fails
                    kwargs[key] = value
        return {"tool": tool_name, "arguments": kwargs}
    
    # Try JSON format
    if match.group(3) is not None:
        try:
            kwargs = json.loads("{" + match.group(3) + "}")
            return {"tool": tool_name, "arguments": kwargs}
        except json.JSONDecodeError:
            pass  # Invalid JSON, return empty args
    
    return {"tool": tool_name, "arguments": {}}
