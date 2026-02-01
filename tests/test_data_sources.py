"""Tests for data source components"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from core.data_sources.manager import DataSourceManager, get_data_source_manager
from core.data_sources.executor import DataSourceExecutor
from core.data_sources.context_provider import DataSourceContextProvider


class TestDataSourceManager:
    """Test DataSourceManager class"""

    def setup_method(self):
        # Reset global manager instance if any
        import core.data_sources.manager as m
        m._manager = None

    def test_manager_init(self):
        """Test manager initialization"""
        manager = DataSourceManager()
        # It auto detects strategies, so available strategies might not be empty
        assert isinstance(manager._available_strategies, dict)

    @patch('core.data_sources.manager.PostgreSQLDataSource')
    def test_manager_detect_strategies(self, mock_pg_cls):
        """Test detecting strategies"""
        mock_pg_source = Mock()
        mock_pg_source.is_available.return_value = True
        mock_pg_cls.return_value = mock_pg_source
        
        manager = DataSourceManager()
        # Re-run detection
        manager._detect_available_strategies()
        assert "postgresql" in manager._available_strategies

    def test_set_strategy(self):
        """Test setting strategy"""
        manager = DataSourceManager()
        mock_strategy = Mock()
        manager._available_strategies = {"test": mock_strategy}
        
        manager.set_strategy("test")
        assert manager.get_strategy_name() == "test"
        
        # Test getting strategy
        assert manager.get_strategy() == mock_strategy

    def test_get_status(self):
        """Test getting status"""
        manager = DataSourceManager()
        status = manager.get_status()
        assert "current_strategy" in status
        assert "available_strategies" in status


class TestDataSourceExecutor:
    """Test DataSourceExecutor class"""
    
    def setup_method(self):
        DataSourceExecutor._instance = None

    @pytest.fixture
    def executor(self):
        return DataSourceExecutor.get_instance()

    def test_executor_init(self, executor):
        """Test executor initialization"""
        assert executor._strategy is None

    def test_configure_unknown_type(self, executor):
        """Test configuring with unknown type"""
        # Need to mock get_config if called
        with patch('core.data_sources.executor.get_config'):
            with pytest.raises(ValueError):
                executor.configure(source_type="unknown_random_type")

    @patch('core.data_sources.executor.ExcelDataSource')
    def test_configure_excel(self, mock_excel_cls, executor):
        """Test configuring Excel strategy"""
        mock_strategy = Mock()
        mock_excel_cls.return_value = mock_strategy
        
        # Mock get_config to return something if needed, or pass kwargs
        with patch('core.data_sources.executor.get_config'):
             executor.configure(source_type="excel", file_path="test.xlsx")
             assert executor._strategy is not None

    @patch('core.data_sources.executor.ExcelDataSource')
    def test_execute_query(self, mock_excel_cls, executor):
        """Test executing query"""
        mock_strategy = Mock()
        mock_strategy.is_available.return_value = True
        mock_strategy.execute_query.return_value = pd.DataFrame({"col": [1, 2]})
        mock_excel_cls.return_value = mock_strategy
        
        with patch('core.data_sources.executor.get_config'):
            executor.configure(source_type="excel", file_path="test.xlsx")
            result = executor.execute("SELECT * FROM table")
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2


class TestContextProvider:
    """Test ContextProvider class"""

    def setup_method(self):
        DataSourceContextProvider._instance = None

    def test_provider_init(self):
        """Test provider initialization"""
        provider = DataSourceContextProvider()
        assert provider._instance is not None

    def test_ensure_initialized(self):
        """Test initialization logic"""
        provider = DataSourceContextProvider()
        # Reset initialized state
        provider._initialized = False
        
        with patch('core.loader.excel_loader.get_loader'), \
             patch('core.data_sources.manager.get_data_source_manager'), \
             patch('core.data_sources.executor.get_executor'):
            
            provider._ensure_initialized()
            assert provider._initialized
            assert provider._loader is not None
            assert provider._manager is not None

    def test_get_sql_rules(self):
        """Test getting SQL rules"""
        provider = DataSourceContextProvider()
        # Ensure it doesn't fail on ensure_initialized
        with patch('core.loader.excel_loader.get_loader'), \
             patch('core.data_sources.manager.get_data_source_manager'), \
             patch('core.data_sources.executor.get_executor'):
            
            rules = provider.get_sql_rules()
            assert "SQLite" in rules
