#!/usr/bin/env python3
"""Tests for the Model Download Manager"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model_manager import (
    ModelDownloadManager, ModelInfo, ModelFormat, ModelSize,
    DownloadProgress, MODEL_CATALOG, get_model_manager
)


class TestModelInfo:
    """Test ModelInfo dataclass"""
    
    def test_size_human_bytes(self):
        """Test human-readable size for bytes"""
        model = ModelInfo(
            id="test", name="Test", description="", size_bytes=500,
            size_category=ModelSize.TINY, format=ModelFormat.GGUF, download_url=""
        )
        assert model.size_human == "0.5 KB"
    
    def test_size_human_kb(self):
        """Test human-readable size for KB"""
        model = ModelInfo(
            id="test", name="Test", description="", size_bytes=512 * 1024,
            size_category=ModelSize.TINY, format=ModelFormat.GGUF, download_url=""
        )
        assert model.size_human == "512.0 KB"
    
    def test_size_human_mb(self):
        """Test human-readable size for MB"""
        model = ModelInfo(
            id="test", name="Test", description="", size_bytes=750 * 1024 * 1024,
            size_category=ModelSize.SMALL, format=ModelFormat.GGUF, download_url=""
        )
        assert model.size_human == "750.0 MB"
    
    def test_size_human_gb(self):
        """Test human-readable size for GB"""
        model = ModelInfo(
            id="test", name="Test", description="", size_bytes=2_500_000_000,
            size_category=ModelSize.MEDIUM, format=ModelFormat.GGUF, download_url=""
        )
        assert "2." in model.size_human and "GB" in model.size_human


class TestDownloadProgress:
    """Test DownloadProgress dataclass"""
    
    def test_percent_calculation(self):
        """Test percentage calculation"""
        progress = DownloadProgress(
            model_id="test", total_bytes=1000, downloaded_bytes=500,
            speed_bps=100, eta_seconds=5, status="downloading"
        )
        assert progress.percent == 50.0
    
    def test_percent_zero_total(self):
        """Test percentage with zero total"""
        progress = DownloadProgress(
            model_id="test", total_bytes=0, downloaded_bytes=0,
            speed_bps=0, eta_seconds=0, status="downloading"
        )
        assert progress.percent == 0.0
    
    def test_speed_human_bytes(self):
        """Test human-readable speed for B/s"""
        progress = DownloadProgress(
            model_id="test", total_bytes=1000, downloaded_bytes=0,
            speed_bps=500, eta_seconds=0, status="downloading"
        )
        assert progress.speed_human == "500 B/s"
    
    def test_speed_human_kb(self):
        """Test human-readable speed for KB/s"""
        progress = DownloadProgress(
            model_id="test", total_bytes=1000, downloaded_bytes=0,
            speed_bps=50 * 1024, eta_seconds=0, status="downloading"
        )
        assert progress.speed_human == "50.0 KB/s"
    
    def test_speed_human_mb(self):
        """Test human-readable speed for MB/s"""
        progress = DownloadProgress(
            model_id="test", total_bytes=1000, downloaded_bytes=0,
            speed_bps=5 * 1024 * 1024, eta_seconds=0, status="downloading"
        )
        assert progress.speed_human == "5.0 MB/s"
    
    def test_eta_human_seconds(self):
        """Test human-readable ETA for seconds"""
        progress = DownloadProgress(
            model_id="test", total_bytes=1000, downloaded_bytes=0,
            speed_bps=0, eta_seconds=45, status="downloading"
        )
        assert progress.eta_human == "45s"
    
    def test_eta_human_minutes(self):
        """Test human-readable ETA for minutes"""
        progress = DownloadProgress(
            model_id="test", total_bytes=1000, downloaded_bytes=0,
            speed_bps=0, eta_seconds=180, status="downloading"
        )
        assert progress.eta_human == "3.0m"
    
    def test_eta_human_hours(self):
        """Test human-readable ETA for hours"""
        progress = DownloadProgress(
            model_id="test", total_bytes=1000, downloaded_bytes=0,
            speed_bps=0, eta_seconds=7200, status="downloading"
        )
        assert progress.eta_human == "2.0h"


class TestModelCatalog:
    """Test MODEL_CATALOG"""
    
    def test_catalog_not_empty(self):
        """Test that catalog has models"""
        assert len(MODEL_CATALOG) > 0
    
    def test_gemma_models_exist(self):
        """Test that Gemma models exist"""
        assert "gemma3-4b-gguf" in MODEL_CATALOG
        assert "gemma3-1b-gguf" in MODEL_CATALOG
    
    def test_model_has_required_fields(self):
        """Test that models have required fields"""
        for model_id, model in MODEL_CATALOG.items():
            assert model.id == model_id
            assert model.name
            assert model.description
            assert model.size_bytes > 0
            assert model.download_url
            assert model.format in ModelFormat
            assert model.size_category in ModelSize
    
    def test_gemma_models_support_tpu(self):
        """Test that Gemma models support TPU"""
        gemma_4b = MODEL_CATALOG.get("gemma3-4b-gguf")
        assert gemma_4b is not None
        assert gemma_4b.supports_tpu is True
    
    def test_recommended_tag_exists(self):
        """Test that at least one model has recommended tag"""
        has_recommended = any("recommended" in m.tags for m in MODEL_CATALOG.values())
        assert has_recommended


class TestModelDownloadManager:
    """Test ModelDownloadManager class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)
    
    @pytest.fixture
    def manager(self, temp_dir):
        """Create manager with temp directory"""
        return ModelDownloadManager(temp_dir)
    
    def test_init_creates_directory(self, temp_dir):
        """Test that init creates storage directory"""
        storage_dir = os.path.join(temp_dir, "models")
        manager = ModelDownloadManager(storage_dir)
        assert os.path.exists(storage_dir)
    
    def test_get_available_models(self, manager):
        """Test getting available models"""
        models = manager.get_available_models()
        assert len(models) > 0
        assert all(isinstance(m, ModelInfo) for m in models)
    
    def test_filter_by_size_category(self, manager):
        """Test filtering by size category"""
        small = manager.get_available_models(size_category=ModelSize.SMALL)
        assert all(m.size_category == ModelSize.SMALL for m in small)
    
    def test_filter_by_tpu_support(self, manager):
        """Test filtering by TPU support"""
        tpu_models = manager.get_available_models(supports_tpu=True)
        assert all(m.supports_tpu for m in tpu_models)
    
    def test_filter_by_tags(self, manager):
        """Test filtering by tags"""
        google_models = manager.get_available_models(tags=["google"])
        assert all("google" in m.tags for m in google_models)
    
    def test_get_recommended_models(self, manager):
        """Test getting recommended models"""
        # With plenty of RAM
        models = manager.get_recommended_models(device_ram_mb=16384, has_tpu=False)
        assert len(models) > 0
        
        # First model should fit in memory
        assert models[0].required_ram_mb <= 16384
    
    def test_get_recommended_models_tpu(self, manager):
        """Test recommended models prioritize TPU when available"""
        models = manager.get_recommended_models(device_ram_mb=8192, has_tpu=True)
        
        # TPU models should be ranked higher
        tpu_models = [m for m in models if m.supports_tpu]
        if tpu_models:
            # First TPU model should be near the top
            first_tpu_idx = next(i for i, m in enumerate(models) if m.supports_tpu)
            assert first_tpu_idx < 3  # Should be in top 3
    
    def test_get_recommended_models_limited_ram(self, manager):
        """Test recommended models respect RAM limit"""
        # Very limited RAM
        models = manager.get_recommended_models(device_ram_mb=1024, has_tpu=False)
        
        # All models should fit
        for m in models:
            assert m.required_ram_mb <= 1024
    
    def test_is_model_installed_false(self, manager):
        """Test model not installed"""
        assert manager.is_model_installed("gemma3-4b-gguf") is False
    
    def test_get_model_path_not_installed(self, manager):
        """Test model path when not installed"""
        assert manager.get_model_path("gemma3-4b-gguf") is None
    
    def test_get_installed_models_empty(self, manager):
        """Test getting installed models when none installed"""
        installed = manager.get_installed_models()
        assert installed == []
    
    def test_get_storage_usage_empty(self, manager):
        """Test storage usage when empty"""
        usage = manager.get_storage_usage()
        assert usage["total_bytes"] == 0
        assert usage["model_count"] == 0
    
    def test_download_unknown_model(self, manager):
        """Test downloading unknown model raises error"""
        with pytest.raises(ValueError, match="Unknown model"):
            manager.download_model("unknown-model-id")
    
    def test_import_model_file_not_found(self, manager):
        """Test importing non-existent file"""
        with pytest.raises(FileNotFoundError):
            manager.import_model("/nonexistent/path/to/model.gguf")
    
    def test_import_model(self, manager, temp_dir):
        """Test importing a model file"""
        # Create a fake model file in a subdirectory (different from storage dir)
        import_dir = os.path.join(temp_dir, "imports")
        os.makedirs(import_dir, exist_ok=True)
        fake_model = os.path.join(import_dir, "fake-model.gguf")
        with open(fake_model, 'wb') as f:
            f.write(b"fake model data" * 100)
        
        # Import it
        model_id = manager.import_model(fake_model, model_id="test-import", name="Test Import")
        
        assert model_id == "test-import"
        assert manager.is_model_installed("test-import")
        
        # Check metadata
        installed = manager.get_installed_models()
        assert len(installed) == 1
        assert installed[0]["id"] == "test-import"
        assert installed[0]["name"] == "Test Import"
    
    def test_delete_model_not_found(self, manager):
        """Test deleting non-existent model"""
        result = manager.delete_model("nonexistent")
        assert result is False
    
    def test_delete_model(self, manager, temp_dir):
        """Test deleting an imported model"""
        # Create and import a model
        import_dir = os.path.join(temp_dir, "imports2")
        os.makedirs(import_dir, exist_ok=True)
        fake_model = os.path.join(import_dir, "deleteme.gguf")
        with open(fake_model, 'wb') as f:
            f.write(b"test data")
        
        manager.import_model(fake_model, model_id="deleteme")
        assert manager.is_model_installed("deleteme")
        
        # Delete it
        result = manager.delete_model("deleteme")
        assert result is True
        assert manager.is_model_installed("deleteme") is False
    
    def test_metadata_persistence(self, temp_dir):
        """Test that metadata persists across manager instances"""
        # Create storage dir separate from import source
        storage_dir = os.path.join(temp_dir, "storage")
        import_dir = os.path.join(temp_dir, "imports3")
        os.makedirs(storage_dir, exist_ok=True)
        os.makedirs(import_dir, exist_ok=True)
        
        # Create manager and import model
        manager1 = ModelDownloadManager(storage_dir)
        fake_model = os.path.join(import_dir, "persist.gguf")
        with open(fake_model, 'wb') as f:
            f.write(b"data")
        manager1.import_model(fake_model, model_id="persist")
        
        # Create new manager instance
        manager2 = ModelDownloadManager(storage_dir)
        
        # Should see the model
        assert manager2.is_model_installed("persist")


class TestModelFormats:
    """Test model format support"""
    
    def test_all_formats_in_enum(self):
        """Test all expected formats exist"""
        assert ModelFormat.GGUF
        assert ModelFormat.ONNX
        assert ModelFormat.SAFETENSORS
        assert ModelFormat.PYTORCH
        assert ModelFormat.TFLITE
    
    def test_format_values(self):
        """Test format string values"""
        assert ModelFormat.GGUF.value == "gguf"
        assert ModelFormat.ONNX.value == "onnx"
        assert ModelFormat.TFLITE.value == "tflite"


class TestModelSizes:
    """Test model size categories"""
    
    def test_all_sizes_in_enum(self):
        """Test all expected sizes exist"""
        assert ModelSize.TINY
        assert ModelSize.SMALL
        assert ModelSize.MEDIUM
        assert ModelSize.LARGE
    
    def test_size_values(self):
        """Test size string values"""
        assert ModelSize.TINY.value == "tiny"
        assert ModelSize.LARGE.value == "large"


class TestGetModelManager:
    """Test the singleton get_model_manager function"""
    
    def test_returns_manager(self):
        """Test that it returns a manager"""
        # Reset singleton
        import model_manager
        model_manager._model_manager = None
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = get_model_manager(temp_dir)
            assert isinstance(manager, ModelDownloadManager)
    
    def test_returns_same_instance(self):
        """Test singleton behavior"""
        import model_manager
        model_manager._model_manager = None
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager1 = get_model_manager(temp_dir)
            manager2 = get_model_manager()  # Should return same instance
            assert manager1 is manager2
