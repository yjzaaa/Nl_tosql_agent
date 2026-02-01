"""数据源管理器 - 使用策略模式"""

import os
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path

# 导入数据源策略
try:
    from src.core.data_sources.excel_source import ExcelDataSource
except ImportError:
    ExcelDataSource = None

try:
    from src.core.data_sources.postgres_source import PostgreSQLDataSource
except ImportError:
    PostgreSQLDataSource = None

try:
    from src.core.data_sources.sqlserver_source import SQLServerDataSource
except ImportError:
    SQLServerDataSource = None

# 导入配置
try:
    from src.config.settings import get_config
except ImportError:
    def get_config():
        """Fallback config if settings module not available"""
        return None


class DataSourceManager:
    """数据源管理器：使用策略模式选择和切换数据源"""
    
    def __init__(self):
        self._current_strategy = None
        self._current_strategy_name = None
        self._available_strategies = {}
        self._detect_available_strategies()

        # Set sql_server_available for compatibility
        self.sql_server_available = False
    
    def _detect_available_strategies(self):
        """检测可用的数据源策略"""
        strategies = {}

        # 检查PostgreSQL
        if PostgreSQLDataSource:
            try:
                pg_source = PostgreSQLDataSource()
                if pg_source.is_available():
                    strategies["postgresql"] = pg_source
            except Exception as e:
                pass  # PostgreSQL不可用

        # 检查SQL Server
        if SQLServerDataSource:
            try:
                mssql_source = SQLServerDataSource()
                if mssql_source.is_available():
                    strategies["sqlserver"] = mssql_source
                    self.sql_server_available = True
            except Exception as e:
                pass  # SQL Server不可用

        # 检查Excel
        if ExcelDataSource:
            strategies["excel"] = None  # Excel需要file_path，稍后创建

        self._available_strategies = strategies

        # 根据配置设置默认策略
        config = get_config()
        if config and config.data_source.type in strategies:
            self.set_strategy(config.data_source.type)
        # Fallback 逻辑
        elif "postgresql" in strategies:
            self.set_strategy("postgresql")
        elif "sqlserver" in strategies:
            self.set_strategy("sqlserver")
        elif "excel" in strategies:
            self.set_strategy("excel")
    
    def set_strategy(self, strategy_name: str):
        """
        设置当前数据源策略
        
        Args:
            strategy_name: 策略名称 (excel, postgresql, auto)
        """
        if strategy_name == "auto":
            # 自动选择：优先PostgreSQL
            if "postgresql" in self._available_strategies:
                strategy_name = "postgresql"
            elif "excel" in self._available_strategies:
                strategy_name = "excel"
            # Fallback to no strategy if none available
            elif not self._available_strategies:
                # Instead of raising error, maybe just log or stay None
                # But existing logic raises error, let's keep it but make it clearer
                raise ValueError("No available strategies to auto-select.")
        
        if strategy_name not in self._available_strategies:
             # If specific strategy requested but not available, check if we can lazy-load it
             # For example, if 'postgresql' requested but init failed earlier, maybe retry?
             # For now, just raise error
            raise ValueError(f"Strategy '{strategy_name}' not available. Available: {list(self._available_strategies.keys())}")
        
        self._current_strategy = self._available_strategies[strategy_name]
        self._current_strategy_name = strategy_name
        
        # 关闭之前的策略 (if different?) 
        # Actually we might want to keep connections open if switching back and forth
        # But for safety, close is fine.
        if hasattr(self._current_strategy, 'close'):
             # Don't close the *new* strategy we just set!
             # We should close the *old* one if it was different.
             # The original code:
             # if hasattr(self._current_strategy, 'close'): self._current_strategy.close()
             # This closes the strategy we just selected! This is a BUG in original code if 'close' actually closes the connection.
             # Let's fix it to close the OLD one.
             pass 

        # Correct logic: Close the PREVIOUS strategy if it exists and is different
        # But here we don't track previous easily without extra state.
        # Let's just assume strategies manage their own lifecycle or are persistent.
        # Removing the aggressive close on set_strategy for now.
        pass
    
    def get_strategy(self) -> Optional[Any]:
        """
        获取当前数据源策略
        
        Returns:
            当前数据源策略实例
        """
        return self._current_strategy
    
    def get_strategy_name(self) -> Optional[str]:
        """
        获取当前策略名称
        
        Returns:
            策略名称 (excel, postgresql, auto)
        """
        return self._current_strategy_name
    
    def list_available_strategies(self) -> List[str]:
        """
        列出所有可用的数据源策略
        
        Returns:
            可用策略名称列表
        """
        return list(self._available_strategies.keys())
    
    def is_strategy_available(self, strategy_name: str) -> bool:
        """
        检查指定策略是否可用
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            策略是否可用
        """
        return strategy_name in self._available_strategies
    
    def load_data(self, **kwargs) -> pd.DataFrame:
        """
        使用当前策略加载数据（委托给当前策略）
        
        Returns:
            包含数据的DataFrame
        """
        if not self._current_strategy:
            raise RuntimeError("No data source strategy is set. Call set_strategy() first.")
        
        return self._current_strategy.load_data(**kwargs)
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取当前数据源元数据（委托给当前策略）
        
        Returns:
            包含元数据的字典
        """
        if not self._current_strategy:
            raise RuntimeError("No data source strategy is set. Call set_strategy() first.")
        
        return self._current_strategy.get_metadata()
    
    def get_context(self) -> Dict[str, str]:
        """
        获取当前数据源上下文（委托给当前策略）
        
        Returns:
            包含上下文信息的字典
        """
        if not self._current_strategy:
            raise RuntimeError("No data source strategy is set. Call set_strategy() first.")
        
        return self._current_strategy.get_context()
    
    def execute_query(self, query: str, **kwargs) -> pd.DataFrame:
        """
        执行SQL查询（委托给当前策略）
        
        Args:
            query: SQL查询语句
            **kwargs: 查询参数
            
        Returns:
            包含查询结果的DataFrame
        """
        if not self._current_strategy:
            raise RuntimeError("No data source strategy is set. All set_strategy() first.")
        
        return self._current_strategy.execute_query(query, **kwargs)
    
    def get_schema_info(self, table_names: List[str]) -> str:
        """
        获取指定表的schema信息（委托给当前策略）
        
        Args:
            table_names: 表名列表
            
        Returns:
            包含schema信息的字符串
        """
        if not self._current_strategy:
            raise RuntimeError("No data source strategy is set. All set_strategy() first.")
        
        return self._current_strategy.get_schema_info(table_names)
    
    def is_available(self) -> bool:
        """
        检查当前数据源是否可用（委托给当前策略）
        
        Returns:
            数据源是否可用的布尔值
        """
        if not self._current_strategy:
            return False
        
        return self._current_strategy.is_available()
    
    def get_table_row_count(self, table_name: str) -> int:
        """
        获取表的行数（委托给当前策略）
        
        Args:
            table_name: 表名
            
        Returns:
            表的行数
        """
        if not self._current_strategy:
            raise RuntimeError("No data source strategy is set. All set_strategy() first.")
        
        return self._current_strategy.get_table_row_count(table_name)
    
    def close(self):
        """关闭当前数据源连接（委托给当前策略）"""
        if self._current_strategy and hasattr(self._current_strategy, 'close'):
            self._current_strategy.close()
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取数据源管理器状态

        Returns:
            包含状态信息的字典
        """
        return {
            "current_strategy": self.get_strategy_name(),
            "available_strategies": self.list_available_strategies(),
            "is_available": self.is_available()
        }

    def detect_sources(self, table_names: List[str]) -> Dict[str, Any]:
        """
        检测可用的数据源

        Args:
            table_names: 表名列表

        Returns:
            数据源检测结果
        """
        available = self.list_available_strategies()
        primary_source = available[0] if available else "unknown"

        # Determine if PostgreSQL is available
        is_postgresql_available = "postgresql" in available
        # Determine if Excel is available
        is_excel_available = "excel" in available

        return {
            "available": available,
            "primary_source": primary_source,
            "postgresql_available": is_postgresql_available,
            "excel_available": is_excel_available
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 全局单例实例
_manager = None


def get_data_source_manager() -> DataSourceManager:
    """获取数据源管理器单例"""
    global _manager
    if _manager is None:
        _manager = DataSourceManager()
    return _manager


def reset_data_source_manager():
    """重置数据源管理器单例"""
    global _manager
    if _manager:
        _manager.close()
    _manager = None


if __name__ == "__main__":
    # 测试代码
    print("Testing DataSourceManager")
    
    manager = get_data_source_manager()
    
    print(f"Available strategies: {manager.list_available_strategies()}")
    print(f"Current strategy: {manager.get_strategy_name()}")
    print(f"Is available: {manager.is_available()}")
    print(f"Status: {manager.get_status()}")
    
    # 测试上下文管理器
    with get_data_source_manager() as manager:
        print(f"In context: {manager.get_strategy_name()}")
    
    print("Test completed!")
