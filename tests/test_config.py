"""Tests for configuration management"""

import pytest
import os
from pathlib import Path
import tempfile
import yaml

from config.settings import load_config, get_config, set_config, AppConfig, ModelConfig, ProviderConfig


class TestConfigLoading:
    """Test configuration loading"""

    @pytest.fixture
    def sample_config(self):
        """Sample configuration content"""
        return {
            "model": {
                "active": "test_provider",
                "providers": {
                    "test_provider": {
                        "provider": "openai",
                        "model_name": "gpt-4",
                        "api_key": "test-key",
                        "base_url": "http://localhost:1234/v1",
                        "temperature": 0.1,
                        "max_tokens": 4096
                    }
                }
            },
            "excel": {
                "max_preview_rows": 20,
                "default_result_limit": 20,
                "max_result_limit": 1000
            },
            "data_source": {
                "type": "excel"
            },
            "logging": {
                "level": "INFO"
            }
        }

    @pytest.fixture
    def temp_config_file(self, sample_config):
        """Create a temporary config file"""
        temp_dir = Path(tempfile.mkdtemp())
        config_path = temp_dir / "config.yaml"
        
        with open(config_path, 'w') as f:
            yaml.dump(sample_config, f)
        
        yield str(config_path)
        
        if config_path.exists():
            config_path.unlink()

    def test_load_config_from_file(self, temp_config_file):
        """Test loading config from file"""
        config = load_config(temp_config_file)
        
        assert config is not None
        assert config.model.active == "test_provider"
        active_provider = config.model.get_active_provider()
        assert active_provider.provider == "openai"
        assert active_provider.model_name == "gpt-4"

    def test_load_config_defaults(self):
        """Test loading config with defaults when file doesn't exist"""
        config = load_config("/nonexistent/path/config.yaml")
        
        assert config is not None
        # Default fallback behavior
        active_provider = config.model.get_active_provider()
        assert active_provider.provider == "openai" # Default env var fallback

    def test_load_config_env_vars(self, monkeypatch):
        """Test loading config with environment variables"""
        temp_dir = Path(tempfile.mkdtemp())
        config_path = temp_dir / "config.yaml"
        
        sample_config = {
            "model": {
                "active": "env_provider",
                "providers": {
                    "env_provider": {
                        "provider": "openai",
                        "api_key": "${TEST_API_KEY}",
                        "base_url": "${TEST_BASE_URL}"
                    }
                }
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(sample_config, f)
        
        monkeypatch.setenv("TEST_API_KEY", "env-key")
        monkeypatch.setenv("TEST_BASE_URL", "http://env-url")
        
        config = load_config(str(config_path))
        
        active_provider = config.model.get_active_provider()
        assert active_provider.api_key == "env-key"
        assert active_provider.base_url == "http://env-url"
        
        if config_path.exists():
            config_path.unlink()

    def test_get_config_singleton(self, temp_config_file):
        """Test get_config returns singleton"""
        config1 = load_config(temp_config_file)
        set_config(config1)
        
        config2 = get_config()
        
        assert config1 is config2

    def test_set_config(self):
        """Test set_config"""
        config = AppConfig()
        set_config(config)
        
        assert get_config() is config


class TestAppConfig:
    """Test AppConfig class"""

    def test_app_config_defaults(self, monkeypatch):
        """Test AppConfig defaults"""
        # Ensure env vars don't interfere with defaults testing
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.delenv("LLM_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_TEMPERATURE", raising=False)
        monkeypatch.delenv("LLM_MAX_TOKENS", raising=False)

        config = AppConfig()
        
        active_provider = config.model.get_active_provider()
        assert active_provider.provider == "openai"
        assert active_provider.model_name == "gpt-4"
        assert config.excel.max_preview_rows == 5
        assert config.data_source.type == "excel"

    def test_model_config(self):
        """Test ModelConfig"""
        provider_config = ProviderConfig(
            provider="test",
            model_name="test-model",
            api_key="test-key"
        )
        
        config = ModelConfig(
            active="test",
            providers={"test": provider_config}
        )
        
        active = config.get_active_provider()
        assert active.provider == "test"
        assert active.model_name == "test-model"
        assert active.api_key == "test-key"

    def test_excel_config(self):
        """Test ExcelConfig"""
        from config.settings import ExcelConfig
        
        config = ExcelConfig(
            max_preview_rows=10,
            default_result_limit=50
        )
        
        assert config.max_preview_rows == 10
        assert config.default_result_limit == 50

    def test_data_source_config(self):
        """Test DataSourceConfig"""
        from config.settings import DataSourceConfig
        
        config = DataSourceConfig(
            type="sqlserver",
            config={"host": "localhost"}
        )
        
        assert config.type == "sqlserver"
        assert config.config["host"] == "localhost"

    def test_logging_config(self):
        """Test LoggingConfig"""
        from config.settings import LoggingConfig
        
        config = LoggingConfig(level="DEBUG")
        
        assert config.level == "DEBUG"


class TestConfigValidation:
    """Test configuration validation"""

    def test_invalid_config_type(self):
        """Test handling invalid config type"""
        with pytest.raises(Exception):
            AppConfig(
                model="invalid"  # Should be dict or ModelConfig
            )

    def test_nested_config_validation(self):
        """Test nested config validation"""
        provider_config = ProviderConfig(
            provider="openai",
            model_name="gpt-4",
            temperature=0.5,  # Valid float
            max_tokens=2048   # Valid int
        )
        
        model_config = ModelConfig(
            active="default",
            providers={"default": provider_config}
        )
        
        active = model_config.get_active_provider()
        assert active.temperature == 0.5
        assert active.max_tokens == 2048
