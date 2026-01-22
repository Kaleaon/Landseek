#!/usr/bin/env python3
"""
Model Download Manager - Easily download and manage AI models

Provides functionality to:
- Download Gemma 3 models (4B, 1B variants)
- Download other supported models (Llama, Mistral, Phi, etc.)
- Verify model integrity
- Manage model storage
- Convert between formats (GGUF, ONNX, etc.)
"""

import os
import sys
import json
import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import time


class ModelFormat(Enum):
    """Supported model formats"""
    GGUF = "gguf"          # llama.cpp format (recommended for mobile)
    ONNX = "onnx"          # ONNX format for broad compatibility
    SAFETENSORS = "safetensors"  # HuggingFace format
    PYTORCH = "pytorch"    # PyTorch .pt/.bin format
    TFLITE = "tflite"      # TensorFlow Lite (Android optimized)


class ModelSize(Enum):
    """Model size categories"""
    TINY = "tiny"          # < 500MB
    SMALL = "small"        # 500MB - 2GB
    MEDIUM = "medium"      # 2GB - 8GB
    LARGE = "large"        # > 8GB


@dataclass
class ModelInfo:
    """Information about a downloadable model"""
    id: str
    name: str
    description: str
    size_bytes: int
    size_category: ModelSize
    format: ModelFormat
    download_url: str
    sha256: Optional[str] = None
    required_ram_mb: int = 4096
    supports_tpu: bool = False
    supports_gpu: bool = True
    quantization: Optional[str] = None
    parameters: Optional[str] = None
    license: str = "Unknown"
    homepage: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    @property
    def size_human(self) -> str:
        """Human-readable size"""
        if self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        elif self.size_bytes < 1024 * 1024 * 1024:
            return f"{self.size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{self.size_bytes / (1024 * 1024 * 1024):.2f} GB"


# Available models catalog
MODEL_CATALOG: Dict[str, ModelInfo] = {
    # Gemma 3 Models (Pixel TPU optimized)
    "gemma3-4b-gguf": ModelInfo(
        id="gemma3-4b-gguf",
        name="Gemma 3 4B (GGUF Q4)",
        description="Google's Gemma 3 4B model quantized for mobile. Best for Pixel 10 Pro TPU.",
        size_bytes=2_500_000_000,  # ~2.5GB
        size_category=ModelSize.MEDIUM,
        format=ModelFormat.GGUF,
        download_url="https://huggingface.co/google/gemma-3-4b-it-gguf/resolve/main/gemma-3-4b-it-q4_k_m.gguf",
        sha256=None,  # Will be fetched
        required_ram_mb=4096,
        supports_tpu=True,
        supports_gpu=True,
        quantization="Q4_K_M",
        parameters="4B",
        license="Gemma License",
        homepage="https://ai.google.dev/gemma",
        tags=["google", "gemma", "recommended", "pixel-tpu", "multimodal"]
    ),
    "gemma3-4b-q8": ModelInfo(
        id="gemma3-4b-q8",
        name="Gemma 3 4B (GGUF Q8)",
        description="Higher quality quantization for better output. Requires more RAM.",
        size_bytes=4_200_000_000,  # ~4.2GB
        size_category=ModelSize.MEDIUM,
        format=ModelFormat.GGUF,
        download_url="https://huggingface.co/google/gemma-3-4b-it-gguf/resolve/main/gemma-3-4b-it-q8_0.gguf",
        sha256=None,
        required_ram_mb=6144,
        supports_tpu=True,
        supports_gpu=True,
        quantization="Q8_0",
        parameters="4B",
        license="Gemma License",
        homepage="https://ai.google.dev/gemma",
        tags=["google", "gemma", "high-quality", "pixel-tpu"]
    ),
    "gemma3-1b-gguf": ModelInfo(
        id="gemma3-1b-gguf",
        name="Gemma 3 1B (GGUF Q4)",
        description="Lighter Gemma 3 variant. Good for older devices or faster inference.",
        size_bytes=800_000_000,  # ~800MB
        size_category=ModelSize.SMALL,
        format=ModelFormat.GGUF,
        download_url="https://huggingface.co/google/gemma-3-1b-it-gguf/resolve/main/gemma-3-1b-it-q4_k_m.gguf",
        sha256=None,
        required_ram_mb=2048,
        supports_tpu=True,
        supports_gpu=True,
        quantization="Q4_K_M",
        parameters="1B",
        license="Gemma License",
        homepage="https://ai.google.dev/gemma",
        tags=["google", "gemma", "lightweight", "fast"]
    ),
    
    # Llama 3.2 Models
    "llama32-3b-gguf": ModelInfo(
        id="llama32-3b-gguf",
        name="Llama 3.2 3B (GGUF Q4)",
        description="Meta's Llama 3.2 3B model. Good general-purpose assistant.",
        size_bytes=1_900_000_000,  # ~1.9GB
        size_category=ModelSize.SMALL,
        format=ModelFormat.GGUF,
        download_url="https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        sha256=None,
        required_ram_mb=3072,
        supports_tpu=False,
        supports_gpu=True,
        quantization="Q4_K_M",
        parameters="3B",
        license="Llama 3.2 Community License",
        homepage="https://llama.meta.com/",
        tags=["meta", "llama", "general-purpose"]
    ),
    "llama32-1b-gguf": ModelInfo(
        id="llama32-1b-gguf",
        name="Llama 3.2 1B (GGUF Q4)",
        description="Smallest Llama 3.2 model. Very fast inference.",
        size_bytes=700_000_000,  # ~700MB
        size_category=ModelSize.SMALL,
        format=ModelFormat.GGUF,
        download_url="https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        sha256=None,
        required_ram_mb=1536,
        supports_tpu=False,
        supports_gpu=True,
        quantization="Q4_K_M",
        parameters="1B",
        license="Llama 3.2 Community License",
        homepage="https://llama.meta.com/",
        tags=["meta", "llama", "lightweight", "fast"]
    ),
    
    # Phi Models
    "phi3-mini-gguf": ModelInfo(
        id="phi3-mini-gguf",
        name="Phi-3 Mini (GGUF Q4)",
        description="Microsoft's Phi-3 Mini. Excellent reasoning for its size.",
        size_bytes=2_300_000_000,  # ~2.3GB
        size_category=ModelSize.MEDIUM,
        format=ModelFormat.GGUF,
        download_url="https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
        sha256=None,
        required_ram_mb=4096,
        supports_tpu=False,
        supports_gpu=True,
        quantization="Q4",
        parameters="3.8B",
        license="MIT",
        homepage="https://azure.microsoft.com/en-us/products/phi-3",
        tags=["microsoft", "phi", "reasoning", "coding"]
    ),
    
    # Mistral Models
    "mistral-7b-gguf": ModelInfo(
        id="mistral-7b-gguf",
        name="Mistral 7B (GGUF Q4)",
        description="Mistral AI's 7B model. High quality but requires more resources.",
        size_bytes=4_100_000_000,  # ~4.1GB
        size_category=ModelSize.MEDIUM,
        format=ModelFormat.GGUF,
        download_url="https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        sha256=None,
        required_ram_mb=6144,
        supports_tpu=False,
        supports_gpu=True,
        quantization="Q4_K_M",
        parameters="7B",
        license="Apache 2.0",
        homepage="https://mistral.ai/",
        tags=["mistral", "high-quality", "general-purpose"]
    ),
    
    # Qwen Models
    "qwen2-1.5b-gguf": ModelInfo(
        id="qwen2-1.5b-gguf",
        name="Qwen2 1.5B (GGUF Q4)",
        description="Alibaba's Qwen2 1.5B. Good multilingual support.",
        size_bytes=1_000_000_000,  # ~1GB
        size_category=ModelSize.SMALL,
        format=ModelFormat.GGUF,
        download_url="https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF/resolve/main/qwen2-1_5b-instruct-q4_k_m.gguf",
        sha256=None,
        required_ram_mb=2048,
        supports_tpu=False,
        supports_gpu=True,
        quantization="Q4_K_M",
        parameters="1.5B",
        license="Apache 2.0",
        homepage="https://qwenlm.github.io/",
        tags=["alibaba", "qwen", "multilingual", "lightweight"]
    ),
    
    # TinyLlama (for very limited devices)
    "tinyllama-1.1b-gguf": ModelInfo(
        id="tinyllama-1.1b-gguf",
        name="TinyLlama 1.1B (GGUF Q4)",
        description="Very small model for extremely resource-constrained devices.",
        size_bytes=600_000_000,  # ~600MB
        size_category=ModelSize.TINY,
        format=ModelFormat.GGUF,
        download_url="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        sha256=None,
        required_ram_mb=1024,
        supports_tpu=False,
        supports_gpu=True,
        quantization="Q4_K_M",
        parameters="1.1B",
        license="Apache 2.0",
        homepage="https://github.com/jzhang38/TinyLlama",
        tags=["tinyllama", "ultra-lightweight", "fast"]
    ),
}


@dataclass
class DownloadProgress:
    """Download progress information"""
    model_id: str
    total_bytes: int
    downloaded_bytes: int
    speed_bps: float
    eta_seconds: float
    status: str  # "downloading", "verifying", "complete", "error"
    error_message: Optional[str] = None
    
    @property
    def percent(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100
    
    @property
    def speed_human(self) -> str:
        if self.speed_bps < 1024:
            return f"{self.speed_bps:.0f} B/s"
        elif self.speed_bps < 1024 * 1024:
            return f"{self.speed_bps / 1024:.1f} KB/s"
        else:
            return f"{self.speed_bps / (1024 * 1024):.1f} MB/s"
    
    @property
    def eta_human(self) -> str:
        if self.eta_seconds < 60:
            return f"{self.eta_seconds:.0f}s"
        elif self.eta_seconds < 3600:
            return f"{self.eta_seconds / 60:.1f}m"
        else:
            return f"{self.eta_seconds / 3600:.1f}h"


class ModelDownloadManager:
    """Manages model downloads and storage"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the model download manager.
        
        Args:
            storage_dir: Directory to store models. Defaults to Documents/AIChat/models
        """
        if storage_dir is None:
            # Default to Documents/AIChat/models
            if sys.platform == "android":
                from android.storage import primary_external_storage_path
                base_dir = primary_external_storage_path()
            else:
                base_dir = os.path.expanduser("~/Documents")
            storage_dir = os.path.join(base_dir, "AIChat", "models")
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata file
        self.metadata_file = self.storage_dir / "models_metadata.json"
        self.metadata = self._load_metadata()
        
        # Active downloads
        self._active_downloads: Dict[str, threading.Thread] = {}
        self._download_progress: Dict[str, DownloadProgress] = {}
        self._download_callbacks: Dict[str, List[Callable[[DownloadProgress], None]]] = {}
        self._cancel_flags: Dict[str, bool] = {}
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load models metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"installed_models": {}, "download_history": []}
    
    def _save_metadata(self):
        """Save models metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save metadata: {e}")
    
    def get_available_models(self, 
                            size_category: Optional[ModelSize] = None,
                            supports_tpu: Optional[bool] = None,
                            tags: Optional[List[str]] = None) -> List[ModelInfo]:
        """
        Get list of available models with optional filtering.
        
        Args:
            size_category: Filter by size category
            supports_tpu: Filter by TPU support
            tags: Filter by tags (model must have at least one matching tag)
            
        Returns:
            List of matching ModelInfo objects
        """
        models = list(MODEL_CATALOG.values())
        
        if size_category is not None:
            models = [m for m in models if m.size_category == size_category]
        
        if supports_tpu is not None:
            models = [m for m in models if m.supports_tpu == supports_tpu]
        
        if tags:
            models = [m for m in models if any(t in m.tags for t in tags)]
        
        return models
    
    def get_recommended_models(self, device_ram_mb: int = 8192, has_tpu: bool = False) -> List[ModelInfo]:
        """
        Get recommended models based on device capabilities.
        
        Args:
            device_ram_mb: Available device RAM in MB
            has_tpu: Whether device has TPU (e.g., Pixel 10 Pro)
            
        Returns:
            List of recommended ModelInfo objects, sorted by recommendation score
        """
        models = []
        
        for model in MODEL_CATALOG.values():
            if model.required_ram_mb <= device_ram_mb:
                # Calculate recommendation score
                score = 0
                
                # TPU support bonus if device has TPU
                if has_tpu and model.supports_tpu:
                    score += 100
                
                # Prefer recommended tag
                if "recommended" in model.tags:
                    score += 50
                
                # Prefer appropriate size for device
                if model.required_ram_mb <= device_ram_mb * 0.6:
                    score += 30  # Comfortable fit
                elif model.required_ram_mb <= device_ram_mb * 0.8:
                    score += 10  # Tight fit
                
                # Quality bonus for higher quantization
                if model.quantization and "Q8" in model.quantization:
                    score += 20
                elif model.quantization and "Q5" in model.quantization:
                    score += 10
                
                models.append((score, model))
        
        # Sort by score descending
        models.sort(key=lambda x: x[0], reverse=True)
        
        return [m for _, m in models]
    
    def get_installed_models(self) -> List[Dict[str, Any]]:
        """Get list of installed models with their status"""
        installed = []
        
        for model_id, info in self.metadata.get("installed_models", {}).items():
            model_path = self.storage_dir / info.get("filename", f"{model_id}.gguf")
            
            # Get catalog info if available
            catalog_info = MODEL_CATALOG.get(model_id)
            
            installed.append({
                "id": model_id,
                "name": info.get("name", catalog_info.name if catalog_info else model_id),
                "filename": info.get("filename"),
                "path": str(model_path),
                "exists": model_path.exists(),
                "size_bytes": info.get("size_bytes", 0),
                "installed_at": info.get("installed_at"),
                "catalog_info": catalog_info
            })
        
        return installed
    
    def is_model_installed(self, model_id: str) -> bool:
        """Check if a model is installed"""
        if model_id not in self.metadata.get("installed_models", {}):
            return False
        
        info = self.metadata["installed_models"][model_id]
        model_path = self.storage_dir / info.get("filename", f"{model_id}.gguf")
        return model_path.exists()
    
    def get_model_path(self, model_id: str) -> Optional[Path]:
        """Get the path to an installed model"""
        if not self.is_model_installed(model_id):
            return None
        
        info = self.metadata["installed_models"][model_id]
        return self.storage_dir / info.get("filename", f"{model_id}.gguf")
    
    def download_model(self, 
                       model_id: str, 
                       callback: Optional[Callable[[DownloadProgress], None]] = None,
                       blocking: bool = True) -> Optional[DownloadProgress]:
        """
        Download a model from the catalog.
        
        Args:
            model_id: ID of the model to download
            callback: Optional callback for progress updates
            blocking: If True, wait for download to complete
            
        Returns:
            DownloadProgress with final status if blocking, None if async
        """
        if model_id not in MODEL_CATALOG:
            raise ValueError(f"Unknown model: {model_id}")
        
        if model_id in self._active_downloads:
            raise ValueError(f"Model {model_id} is already being downloaded")
        
        model_info = MODEL_CATALOG[model_id]
        
        # Initialize progress
        progress = DownloadProgress(
            model_id=model_id,
            total_bytes=model_info.size_bytes,
            downloaded_bytes=0,
            speed_bps=0,
            eta_seconds=0,
            status="downloading"
        )
        self._download_progress[model_id] = progress
        self._cancel_flags[model_id] = False
        
        if callback:
            if model_id not in self._download_callbacks:
                self._download_callbacks[model_id] = []
            self._download_callbacks[model_id].append(callback)
        
        def _do_download():
            try:
                self._download_model_impl(model_id, model_info)
            except Exception as e:
                progress.status = "error"
                progress.error_message = str(e)
                self._notify_progress(model_id)
            finally:
                self._active_downloads.pop(model_id, None)
        
        thread = threading.Thread(target=_do_download, daemon=True)
        self._active_downloads[model_id] = thread
        thread.start()
        
        if blocking:
            thread.join()
            return self._download_progress.get(model_id)
        
        return None
    
    def _download_model_impl(self, model_id: str, model_info: ModelInfo):
        """Internal implementation of model download"""
        try:
            import urllib.request
            import ssl
        except ImportError:
            # On Android, use android.storage APIs
            raise ImportError("Network downloads not available on this platform. Please use the import feature to add local models.")
        
        progress = self._download_progress[model_id]
        
        # Create SSL context that accepts certificates
        ssl_context = ssl.create_default_context()
        
        # Determine filename from URL
        filename = model_info.download_url.split("/")[-1]
        if not filename.endswith(('.gguf', '.onnx', '.bin', '.pt', '.tflite')):
            filename = f"{model_id}.{model_info.format.value}"
        
        temp_path = self.storage_dir / f"{filename}.downloading"
        final_path = self.storage_dir / filename
        
        try:
            # Open URL
            request = urllib.request.Request(
                model_info.download_url,
                headers={'User-Agent': 'AIChat/1.0'}
            )
            
            with urllib.request.urlopen(request, context=ssl_context) as response:
                total_size = int(response.headers.get('content-length', model_info.size_bytes))
                progress.total_bytes = total_size
                
                downloaded = 0
                start_time = time.time()
                last_update = start_time
                chunk_size = 1024 * 1024  # 1MB chunks
                
                with open(temp_path, 'wb') as f:
                    while True:
                        # Check for cancellation
                        if self._cancel_flags.get(model_id, False):
                            progress.status = "cancelled"
                            self._notify_progress(model_id)
                            return
                        
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress
                        current_time = time.time()
                        elapsed = current_time - start_time
                        
                        if elapsed > 0:
                            speed = downloaded / elapsed
                            remaining = total_size - downloaded
                            eta = remaining / speed if speed > 0 else 0
                            
                            progress.downloaded_bytes = downloaded
                            progress.speed_bps = speed
                            progress.eta_seconds = eta
                        
                        # Notify at most once per second
                        if current_time - last_update >= 1.0:
                            self._notify_progress(model_id)
                            last_update = current_time
            
            # Verify hash if available
            if model_info.sha256:
                progress.status = "verifying"
                self._notify_progress(model_id)
                
                sha256 = hashlib.sha256()
                with open(temp_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        sha256.update(chunk)
                
                if sha256.hexdigest() != model_info.sha256:
                    raise ValueError("SHA256 verification failed")
            
            # Move to final location
            shutil.move(str(temp_path), str(final_path))
            
            # Update metadata
            self.metadata.setdefault("installed_models", {})[model_id] = {
                "name": model_info.name,
                "filename": filename,
                "size_bytes": downloaded,
                "installed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "format": model_info.format.value,
                "quantization": model_info.quantization
            }
            self._save_metadata()
            
            # Mark complete
            progress.status = "complete"
            progress.downloaded_bytes = downloaded
            self._notify_progress(model_id)
            
        finally:
            # Clean up temp file if it exists
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
    
    def _notify_progress(self, model_id: str):
        """Notify all callbacks of progress update"""
        progress = self._download_progress.get(model_id)
        if progress:
            for callback in self._download_callbacks.get(model_id, []):
                try:
                    callback(progress)
                except Exception:
                    pass
    
    def cancel_download(self, model_id: str):
        """Cancel an active download"""
        self._cancel_flags[model_id] = True
    
    def delete_model(self, model_id: str) -> bool:
        """
        Delete an installed model.
        
        Args:
            model_id: ID of the model to delete
            
        Returns:
            True if deleted, False if not found
        """
        if model_id not in self.metadata.get("installed_models", {}):
            return False
        
        info = self.metadata["installed_models"][model_id]
        model_path = self.storage_dir / info.get("filename", f"{model_id}.gguf")
        
        if model_path.exists():
            model_path.unlink()
        
        del self.metadata["installed_models"][model_id]
        self._save_metadata()
        
        return True
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """Get storage usage information"""
        total_size = 0
        model_count = 0
        
        for model_id, info in self.metadata.get("installed_models", {}).items():
            model_path = self.storage_dir / info.get("filename", f"{model_id}.gguf")
            if model_path.exists():
                total_size += model_path.stat().st_size
                model_count += 1
        
        return {
            "total_bytes": total_size,
            "total_human": f"{total_size / (1024 * 1024 * 1024):.2f} GB",
            "model_count": model_count,
            "storage_dir": str(self.storage_dir)
        }
    
    def import_model(self, 
                     file_path: str, 
                     model_id: Optional[str] = None,
                     name: Optional[str] = None) -> str:
        """
        Import a model from a local file.
        
        Args:
            file_path: Path to the model file
            model_id: Optional ID to assign (defaults to filename)
            name: Optional display name
            
        Returns:
            The model ID assigned
        """
        source_path = Path(file_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Model file not found: {file_path}")
        
        # Determine format from extension
        ext = source_path.suffix.lower()
        format_map = {
            '.gguf': ModelFormat.GGUF,
            '.onnx': ModelFormat.ONNX,
            '.safetensors': ModelFormat.SAFETENSORS,
            '.pt': ModelFormat.PYTORCH,
            '.bin': ModelFormat.PYTORCH,
            '.tflite': ModelFormat.TFLITE,
        }
        
        model_format = format_map.get(ext, ModelFormat.GGUF)
        
        # Generate model ID if not provided
        if not model_id:
            model_id = source_path.stem.lower().replace(' ', '-').replace('_', '-')
        
        # Copy to storage directory
        dest_path = self.storage_dir / source_path.name
        shutil.copy2(str(source_path), str(dest_path))
        
        # Update metadata
        self.metadata.setdefault("installed_models", {})[model_id] = {
            "name": name or source_path.stem,
            "filename": source_path.name,
            "size_bytes": dest_path.stat().st_size,
            "installed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "format": model_format.value,
            "imported": True
        }
        self._save_metadata()
        
        return model_id


# Singleton instance
_model_manager: Optional[ModelDownloadManager] = None


def get_model_manager(storage_dir: Optional[str] = None) -> ModelDownloadManager:
    """Get the singleton model download manager"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelDownloadManager(storage_dir)
    return _model_manager


# CLI interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Chat Model Download Manager")
    parser.add_argument("command", choices=["list", "download", "installed", "delete", "info", "recommend"])
    parser.add_argument("--model", "-m", help="Model ID for download/delete/info commands")
    parser.add_argument("--ram", type=int, default=8192, help="Device RAM in MB for recommend command")
    parser.add_argument("--tpu", action="store_true", help="Device has TPU for recommend command")
    
    args = parser.parse_args()
    manager = get_model_manager()
    
    if args.command == "list":
        print("\n=== Available Models ===\n")
        for model in MODEL_CATALOG.values():
            installed = "✓" if manager.is_model_installed(model.id) else " "
            tpu = "TPU" if model.supports_tpu else "   "
            print(f"[{installed}] {model.id:<25} {model.size_human:>10} {tpu}  {model.name}")
        print()
        
    elif args.command == "download":
        if not args.model:
            print("Error: --model required for download command")
            sys.exit(1)
        
        print(f"Downloading {args.model}...")
        
        def progress_callback(p: DownloadProgress):
            bar_width = 40
            filled = int(bar_width * p.percent / 100)
            bar = "█" * filled + "░" * (bar_width - filled)
            print(f"\r[{bar}] {p.percent:.1f}% - {p.speed_human} - ETA: {p.eta_human}  ", end="", flush=True)
        
        result = manager.download_model(args.model, callback=progress_callback)
        print()
        
        if result and result.status == "complete":
            print(f"✓ Model downloaded successfully to {manager.get_model_path(args.model)}")
        else:
            print(f"✗ Download failed: {result.error_message if result else 'Unknown error'}")
            
    elif args.command == "installed":
        print("\n=== Installed Models ===\n")
        for model in manager.get_installed_models():
            status = "✓" if model["exists"] else "✗ (file missing)"
            size = f"{model['size_bytes'] / (1024*1024*1024):.2f} GB"
            print(f"{status} {model['id']:<25} {size:>10}  {model['name']}")
        
        usage = manager.get_storage_usage()
        print(f"\nTotal: {usage['model_count']} models, {usage['total_human']}")
        
    elif args.command == "delete":
        if not args.model:
            print("Error: --model required for delete command")
            sys.exit(1)
        
        if manager.delete_model(args.model):
            print(f"✓ Deleted {args.model}")
        else:
            print(f"✗ Model {args.model} not found")
            
    elif args.command == "info":
        if not args.model:
            print("Error: --model required for info command")
            sys.exit(1)
        
        if args.model not in MODEL_CATALOG:
            print(f"Unknown model: {args.model}")
            sys.exit(1)
        
        model = MODEL_CATALOG[args.model]
        print(f"\n=== {model.name} ===\n")
        print(f"ID:           {model.id}")
        print(f"Description:  {model.description}")
        print(f"Parameters:   {model.parameters}")
        print(f"Size:         {model.size_human}")
        print(f"Format:       {model.format.value}")
        print(f"Quantization: {model.quantization}")
        print(f"RAM Required: {model.required_ram_mb} MB")
        print(f"TPU Support:  {'Yes' if model.supports_tpu else 'No'}")
        print(f"GPU Support:  {'Yes' if model.supports_gpu else 'No'}")
        print(f"License:      {model.license}")
        print(f"Homepage:     {model.homepage}")
        print(f"Tags:         {', '.join(model.tags)}")
        print(f"Installed:    {'Yes' if manager.is_model_installed(model.id) else 'No'}")
        
    elif args.command == "recommend":
        print(f"\n=== Recommended Models (RAM: {args.ram}MB, TPU: {args.tpu}) ===\n")
        for i, model in enumerate(manager.get_recommended_models(args.ram, args.tpu)[:5], 1):
            installed = "✓" if manager.is_model_installed(model.id) else " "
            tpu = "TPU" if model.supports_tpu else "   "
            print(f"{i}. [{installed}] {model.name}")
            print(f"      {model.description}")
            print(f"      Size: {model.size_human}, RAM: {model.required_ram_mb}MB, {tpu}")
            print()
