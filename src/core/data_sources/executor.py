"""统一的数据源执行器 - 策略模式实现"""

from typing import Optional, Dict, Any, List
import pandas as pd
from .base import DataSourceStrategy
from .excel_source import ExcelDataSource
from .postgres_source import PostgreSQLDataSource

try:
    from .sqlserver_source import SQLServerDataSource
except ImportError:
    SQLServerDataSource = None

try:
    from src.config.settings import get_config
except ImportError:
    # Fallback config
    def get_config():
        return None


from src.config.logger_interface import get_logger

logger = get_logger("data_source_executor")


class DataSourceExecutor:
    """统一的数据源执行器 - 提供一致的 SQL 执行接口"""

    _instance: Optional["DataSourceExecutor"] = None

    def __init__(self):
        self._strategy: Optional[DataSourceStrategy] = None
        self._manager = None

    @classmethod
    def get_instance(cls) -> "DataSourceExecutor":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_manager(self):
        """延迟导入 manager 避免循环依赖"""
        if self._manager is None:
            from .manager import DataSourceManager

            self._manager = DataSourceManager()
        return self._manager

    @classmethod
    def get_instance(cls) -> "DataSourceExecutor":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def configure(self, source_type: str = "auto", **kwargs) -> None:
        """根据配置选择数据源策略

        Args:
            source_type: 数据源类型 ("sqlserver", "postgresql", "excel", "auto")
            **kwargs: 额外参数
                - query: SQL Server 查询语句
                - file_path: Excel 文件路径
                - sheet_name: Excel 工作表名称
        """
        config = get_config()

        if source_type == "sqlserver" or (
            source_type == "auto" and self._manager.sql_server_available
        ):
            if SQLServerDataSource:
                self._strategy = SQLServerDataSource(
                    # query=kwargs.get("query", ""), # SQLServerDataSource __init__ doesn't accept query
                    # table_name_alias=kwargs.get("table_name_alias", "SQL Query Result"),
                )
            else:
                raise ImportError("SQLServerDataSource not available")

        elif source_type == "postgresql":
            if PostgreSQLDataSource:
                self._strategy = PostgreSQLDataSource()
            else:
                raise ImportError("PostgreSQLDataSource not available")

        elif source_type == "excel" or (
            source_type == "auto" and kwargs.get("file_path")
        ):
            file_path = kwargs.get("file_path")
            sheet_name = kwargs.get("sheet_name")
            self._strategy = ExcelDataSource(file_path=file_path, sheet_name=sheet_name)

        else:
            raise ValueError(f"无法配置数据源策略: 未知的类型 {source_type}")

    def execute(self, query: str) -> pd.DataFrame:
        """执行 SQL 查询

        Args:
            query: SQL 查询语句

        Returns:
            DataFrame 包含查询结果
        """
        if self._strategy is None:
            raise RuntimeError("数据源策略未配置，请先调用 configure()")

        if not self._strategy.is_available():
            raise RuntimeError(f"数据源不可用: {self._strategy}")

        # logger.info(f"执行查询: {query[:100]}...")
        return self._strategy.execute_query(query)

    def execute_from_state(self, state: Dict[str, Any]) -> pd.DataFrame:
        """从 AgentState 中获取配置并执行查询

        Args:
            state: Agent 状态字典，需包含:
                - sql_query: SQL 查询语句
                - data_source_type: 数据源类型 ("sql_server", "excel")

        Returns:
            DataFrame 包含查询结果
        """
        sql_query = state.get("sql_query", "")
        data_source_type = state.get("data_source_type", "auto")

        kwargs = {"query": sql_query}

        if data_source_type == "excel":
            try:
                config = get_config()
                if config and hasattr(config, 'data_source') and hasattr(config.data_source, 'excel'):
                    excel_config = config.data_source.excel
                    if hasattr(excel_config, 'file_paths') and excel_config.file_paths:
                        first_table = list(excel_config.file_paths.keys())[0]
                        file_path = excel_config.file_paths.get(first_table)
                        if file_path:
                            kwargs["file_path"] = file_path
                            kwargs["sheet_name"] = first_table
            except Exception as e:
                logger.warning(f"无法获取 Excel 配置: {e}")

        self.configure(source_type=data_source_type, **kwargs)
        return self.execute(sql_query)

    def get_schema_info(self, table_names: List[str]) -> str:
        """获取表结构信息"""
        if self._strategy is None:
            return "数据源未配置"
        return self._strategy.get_schema_info(table_names)

    def get_context(self) -> Dict[str, str]:
        """获取业务上下文信息"""
        if self._strategy is None:
            return {"business_logic": "", "common_questions": ""}
        return self._strategy.get_context()

    def get_metadata(self) -> Dict[str, Any]:
        """获取数据源元数据"""
        if self._strategy is None:
            return {}
        return self._strategy.get_metadata()

    def is_available(self) -> bool:
        """检查当前数据源是否可用"""
        if self._strategy is None:
            return False
        return self._strategy.is_available()

    def detect_and_configure(self, table_names: List[str]) -> str:
        """自动检测可用的数据源并配置

        Args:
            table_names: 要查询的表名列表

        Returns:
            检测到的数据源类型
        """
        manager = self._get_manager()
        result = manager.detect_sources(table_names)
        primary_source = result["primary_source"]

        if primary_source == "sqlserver":
            self.configure(source_type="sqlserver", query="")
        elif primary_source == "excel":
            if table_names:
                self.configure(
                    source_type="excel",
                    file_path=(
                        table_names[0]
                        if table_names[0].endswith((".xlsx", ".xls"))
                        else None
                    ),
                )

        return primary_source

    def clear(self) -> None:
        """清除当前策略配置"""
        self._strategy = None


def get_executor() -> DataSourceExecutor:
    """获取数据源执行器单例"""
    return DataSourceExecutor.get_instance()


def execute_query(query: str, source_type: str = "auto", **kwargs) -> pd.DataFrame:
    """便捷函数：执行 SQL 查询

    Args:
        query: SQL 查询语句
        source_type: 数据源类型
        **kwargs: 额外参数

    Returns:
        DataFrame 包含查询结果
    """
    executor = get_executor()
    executor.configure(source_type=source_type, **kwargs)
    return executor.execute(query)


def execute_from_state(state: Dict[str, Any]) -> pd.DataFrame:
    """便捷函数：从 AgentState 执行查询"""
    executor = get_executor()
    return executor.execute_from_state(state)


# Backwards compatibility alias
SQLExecutor = DataSourceExecutor
