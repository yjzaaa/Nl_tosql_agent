"""Common Tools

Provides basic tools for agent use.
"""

from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod


class Tool(ABC):
    """Base tool class"""

    @abstractmethod
    def get_name(self) -> str:
        """Get tool name"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get tool description"""
        pass

    @abstractmethod
    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """Invoke tool with parameters"""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get tool parameter schema"""
        pass


class SQLTool(Tool):
    """SQL query tool"""

    def get_name(self) -> str:
        return "sql_query"

    def get_description(self) -> str:
        return "Execute a SQL query on the data source"

    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """
        Execute SQL query

        Args:
            parameters: Dictionary with 'query' key containing SQL string

        Returns:
            Query result
        """
        from core.data_sources.context_provider import get_data_source_context_provider

        query = parameters.get('query', '')
        if not query:
            return {'error': 'No query provided'}

        try:
            context_provider = get_data_source_context_provider()
            df = context_provider.execute_sql(query)
            return {'result': df.to_string(index=False), 'success': True}
        except Exception as e:
            return {'error': str(e), 'success': False}

    def get_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'SQL query to execute'
                }
            },
            'required': ['query']
        }


class CostSummaryTool(Tool):
    """Cost summary tool"""

    def get_name(self) -> str:
        return "cost_summary"

    def get_description(self) -> str:
        return "Get cost summary by function, key, or month"

    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """
        Get cost summary

        Args:
            parameters: Optional dictionary with 'by' key (function, key, month)

        Returns:
            Cost summary result
        """
        from core.data_sources.tools import get_cost_summary

        try:
            summary = get_cost_summary()
            return {'result': summary, 'success': True}
        except Exception as e:
            return {'error': str(e), 'success': False}

    def get_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'by': {
                    'type': 'string',
                    'description': 'Group by field (function, key, month)',
                    'enum': ['function', 'key', 'month']
                }
            }
        }


class RateSummaryTool(Tool):
    """Rate summary tool"""

    def get_name(self) -> str:
        return "rate_summary"

    def get_description(self) -> str:
        return "Get rate summary by key or business line"

    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """
        Get rate summary

        Args:
            parameters: Optional dictionary with 'by' key (key, business_line)

        Returns:
            Rate summary result
        """
        from core.data_sources.tools import get_rate_summary

        try:
            summary = get_rate_summary()
            return {'result': summary, 'success': True}
        except Exception as e:
            return {'error': str(e), 'success': False}

    def get_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'by': {
                    'type': 'string',
                    'description': 'Group by field (key, business_line)',
                    'enum': ['key', 'business_line']
                }
            }
        }


class ListTablesTool(Tool):
    """List tables tool"""

    def get_name(self) -> str:
        return "list_tables"

    def get_description(self) -> str:
        return "List all available tables in the data source"

    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """
        List all tables

        Returns:
            List of table names
        """
        from core.data_sources.tools import list_all_tables

        try:
            tables = list_all_tables()
            return {'result': tables, 'success': True}
        except Exception as e:
            return {'error': str(e), 'success': False}

    def get_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'properties': {},
            'required': []
        }


class GetTableInfoTool(Tool):
    """Get table info tool"""

    def get_name(self) -> str:
        return "get_table_info"

    def get_description(self) -> str:
        return "Get information about a specific table including row count"

    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """
        Get table information

        Args:
            parameters: Dictionary with 'table_name' key

        Returns:
            Table information
        """
        from core.data_sources.tools import get_table_info

        table_name = parameters.get('table_name')
        if not table_name:
            return {'error': 'No table_name provided', 'success': False}

        try:
            info = get_table_info(table_name)
            return {'result': info, 'success': True}
        except Exception as e:
            return {'error': str(e), 'success': False}

    def get_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'table_name': {
                    'type': 'string',
                    'description': 'Name of the table to get info for'
                }
            },
            'required': ['table_name']
        }


# Create list of all available tools
ALL_TOOLS: List[Tool] = [
    SQLTool(),
    CostSummaryTool(),
    RateSummaryTool(),
    ListTablesTool(),
    GetTableInfoTool()
]


def get_tool_by_name(tool_name: str) -> Optional[Tool]:
    """
    Get a tool by name

    Args:
        tool_name: Name of the tool

    Returns:
        Tool instance or None if not found
    """
    for tool in ALL_TOOLS:
        if tool.get_name() == tool_name:
            return tool
    return None


def list_tools() -> List[str]:
    """
    List all available tool names

    Returns:
        List of tool names
    """
    return [tool.get_name() for tool in ALL_TOOLS]


def get_tool_schemas() -> Dict[str, Dict[str, Any]]:
    """
    Get schemas for all tools

    Returns:
        Dictionary mapping tool names to their schemas
    """
    return {tool.get_name(): tool.get_schema() for tool in ALL_TOOLS}


# Alias for execute_pandas_query (backward compatibility)
def execute_pandas_query(query: str, **kwargs) -> Any:
    """
    Execute a SQL query using data source context

    Args:
        query: SQL query string

    Returns:
        Query result
    """
    from core.data_sources.context_provider import get_data_source_context_provider

    try:
        context_provider = get_data_source_context_provider()
        df = context_provider.execute_sql(query)
        return df.to_string(index=False)
    except Exception as e:
        return f"Error executing query: {str(e)}"


# Placeholder functions for business logic
def calculate_allocated_costs(**kwargs) -> str:
    """Calculate allocated costs"""
    return "Allocated costs calculation"


def compare_scenarios(**kwargs) -> str:
    """Compare scenarios"""
    return "Scenario comparison"


def compare_allocated_costs(**kwargs) -> str:
    """Compare allocated costs"""
    return "Allocated costs comparison"


def analyze_cost_composition(**kwargs) -> str:
    """Analyze cost composition"""
    return "Cost composition analysis"
