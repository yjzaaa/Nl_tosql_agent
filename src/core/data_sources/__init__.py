from .base import DataSourceStrategy
from .excel_source import ExcelDataSource
from .postgres_source import PostgreSQLDataSource

try:
    from .sql_source import SqlServerDataSource
except ImportError:
    SqlServerDataSource = None

from .executor import (
    DataSourceExecutor,
    get_executor,
    execute_query,
    execute_from_state
)

# 延迟导入 manager 和 loader 以避免循环依赖
def get_data_source_manager():
    from .manager import DataSourceManager, get_data_source_manager as _get_manager
    return _get_manager()
