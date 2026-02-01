from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd


class DataSourceStrategy(ABC):
    """Abstract base class for data source strategies."""

    @abstractmethod
    def load_data(self) -> pd.DataFrame:
        """Load data into a pandas DataFrame."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata about the data source (e.g. filename, table name)."""
        pass

    @abstractmethod
    def get_context(self) -> Dict[str, str]:
        """Return business logic or question context found in the source.

        Returns:
            Dict with keys like 'business_logic', 'common_questions'
        """
        pass

    @abstractmethod
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute a SQL query against the data source.

        Args:
            query: SQL query string to execute

        Returns:
            DataFrame containing query results
        """
        pass

    @abstractmethod
    def get_schema_info(self, table_names: List[str]) -> str:
        """Get schema information for specified tables.

        Args:
            table_names: List of table names to get schema for

        Returns:
            String containing schema information
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this data source is available/connected."""
        pass
