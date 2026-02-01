"""
Logger 单元测试
测试 LoggerManager 的核心功能，包括单例模式、异步日志队列和消息格式化。
"""

import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from config.logger import LoggerManager

# 重置单例状态的 Fixture
@pytest.fixture(autouse=True)
def reset_logger_singleton():
    """每个测试前重置单例状态，确保测试隔离"""
    LoggerManager._instance = None
    LoggerManager._initialized = False
    yield
    # 清理
    if LoggerManager._instance:
        LoggerManager._instance.shutdown()
        LoggerManager._instance = None
        LoggerManager._initialized = False

class TestLoggerManager:
    """测试 LoggerManager 类"""

    def test_singleton_pattern(self):
        """测试单例模式：多次实例化应返回同一对象"""
        logger1 = LoggerManager()
        logger2 = LoggerManager()
        assert logger1 is logger2
        assert logger1._initialized is True

    def test_format_message_content_string(self):
        """测试字符串消息格式化"""
        logger = LoggerManager()
        msg = "Hello World"
        formatted = logger.format_message_content(msg)
        assert formatted == "Hello World"

    def test_format_message_content_object(self):
        """测试对象消息格式化 (如 AIMessage)"""
        class MockMessage:
            content = "AI Response"
        
        logger = LoggerManager()
        msg = MockMessage()
        formatted = logger.format_message_content(msg)
        assert formatted == "AI Response"

    def test_format_message_truncation(self):
        """测试消息截断功能"""
        # Mock 配置
        with patch('config.settings.get_config') as mock_config:
            mock_config.return_value.logging.format_max_chars = 10
            mock_config.return_value.logging.format_max_lines = 5
            
            logger = LoggerManager()
            msg = "This is a very long message that should be truncated"
            formatted = logger.format_message_content(msg, max_chars=10)
            
            assert len(formatted) > 10
            assert "... (truncated)" in formatted
            assert formatted.startswith("This is a ")

    def test_async_logging_queue(self):
        """测试异步日志队列机制"""
        logger = LoggerManager()
        
        # Mock _sync_info 方法来验证是否被调用
        logger._sync_info = MagicMock()
        
        # 调用异步 info 方法
        logger.info("Test Async Log")
        
        # 等待后台线程处理队列
        time.sleep(0.2)
        
        # 验证同步方法被调用
        logger._sync_info.assert_called_once_with("Test Async Log")

    def test_shutdown(self):
        """测试关停逻辑"""
        logger = LoggerManager()
        assert logger._worker_thread.is_alive()
        
        logger.shutdown()
        
        assert not logger._worker_thread.is_alive()
        assert logger._stop_event.is_set()

    def test_log_rich_object(self):
        """测试 Rich 对象日志记录"""
        logger = LoggerManager()
        logger._sync_rich_object = MagicMock()
        
        mock_obj = {"key": "value"}
        logger.log_rich_object(mock_obj)
        
        time.sleep(0.1)
        logger._sync_rich_object.assert_called_once_with(mock_obj)

    def test_log_sql_query(self):
        """测试 SQL 查询日志记录"""
        logger = LoggerManager()
        logger._log_queue = MagicMock()
        
        sql = "SELECT * FROM table"
        logger.log_sql_query(sql)
        
        # 验证是否正确放入队列
        logger._log_queue.put.assert_called_once()
        args = logger._log_queue.put.call_args[0][0]
        assert args[0] == "sql_query"
        assert args[1][0] == sql
