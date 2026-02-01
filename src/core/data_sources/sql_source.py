from typing import Any, Dict, List
import pandas as pd
from .base import DataSourceStrategy


class SqlServerDataSource(DataSourceStrategy):
    """Strategy for loading data from SQL Server."""

    def __init__(self, query: str = None, table_name_alias: str = "SQL Query Result"):
        self.query = query
        self.table_name_alias = table_name_alias
        self._is_available = None
        self._sql_server_available = False

    def load_data(self) -> pd.DataFrame:
        raise NotImplementedError("SQL Server data source is not available. Please configure sqlserver module.")

    def execute_query(self, query: str) -> pd.DataFrame:
        raise NotImplementedError("SQL Server data source is not available. Please configure sqlserver module.")

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source_type": "sql_server",
            "query": self.query,
            "filename": self.table_name_alias,
            "sheet_name": "sql_result",
            "all_sheets": ["sql_result"]
        }

    def get_context(self) -> Dict[str, str]:
        return {
            "business_logic": "",
            "common_questions": ""
        }

    def get_schema_info(self, table_names: List[str]) -> str:
        return "SQL Server data source is not available."

    def is_available(self) -> bool:
        return False


# Backwards compatibility alias
SQLDataSource = SqlServerDataSource
