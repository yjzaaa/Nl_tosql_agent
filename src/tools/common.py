"""
公共工具模块

提供智能体使用的基础工具，包括 SQL 查询、成本汇总、费率汇总等功能。
"""

from typing import Dict, Any, List, Optional, Callable  # 类型定义
from abc import ABC, abstractmethod  # 抽象基类


class Tool(ABC):
    """
    工具基类

    所有工具类的抽象基类，定义工具的通用接口。
    """

    @abstractmethod
    def get_name(self) -> str:
        """获取工具名称"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """获取工具描述"""
        pass

    @abstractmethod
    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """调用工具执行操作"""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
        pass


class SQLTool(Tool):
    """
    SQL 查询工具

    用于在数据源上执行 SQL 查询语句。
    """

    def get_name(self) -> str:
        """获取工具名称"""
        return "sql_query"

    def get_description(self) -> str:
        """获取工具描述"""
        return "Execute a SQL query on the data source"

    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """
        执行 SQL 查询

        参数:
            parameters: 包含 'query' 键的字典，值为 SQL 字符串

        返回:
            查询结果字典，包含 'result' 和 'success' 字段
        """
        from core.data_sources.context_provider import get_data_source_context_provider  # 数据源上下文提供者

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
        """获取工具参数模式"""
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
    """
    成本汇总工具

    用于按功能、键值或月份获取成本汇总信息。
    """

    def get_name(self) -> str:
        """获取工具名称"""
        return "cost_summary"

    def get_description(self) -> str:
        """获取工具描述"""
        return "Get cost summary by function, key, or month"

    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """
        获取成本汇总

        参数:
            parameters: 可选字典，包含 'by' 键（function, key, month）

        返回:
            成本汇总结果字典
        """
        from core.data_sources.tools import get_cost_summary  # 成本汇总函数

        try:
            summary = get_cost_summary()
            return {'result': summary, 'success': True}
        except Exception as e:
            return {'error': str(e), 'success': False}

    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
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
    """
    费率汇总工具

    用于按键值或业务线获取费率汇总信息。
    """

    def get_name(self) -> str:
        """获取工具名称"""
        return "rate_summary"

    def get_description(self) -> str:
        """获取工具描述"""
        return "Get rate summary by key or business line"

    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """
        获取费率汇总

        参数:
            parameters: 可选字典，包含 'by' 键（key, business_line）

        返回:
            费率汇总结果字典
        """
        from core.data_sources.tools import get_rate_summary  # 费率汇总函数

        try:
            summary = get_rate_summary()
            return {'result': summary, 'success': True}
        except Exception as e:
            return {'error': str(e), 'success': False}

    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
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
    """
    列出表工具

    用于列出数据源中所有可用的表。
    """

    def get_name(self) -> str:
        """获取工具名称"""
        return "list_tables"

    def get_description(self) -> str:
        """获取工具描述"""
        return "List all available tables in the data source"

    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """
        列出所有表

        返回:
            表名列表
        """
        from core.data_sources.tools import list_all_tables  # 列出所有表函数

        try:
            tables = list_all_tables()
            return {'result': tables, 'success': True}
        except Exception as e:
            return {'error': str(e), 'success': False}

    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
        return {
            'type': 'object',
            'properties': {},
            'required': []
        }


class GetTableInfoTool(Tool):
    """
    获取表信息工具

    用于获取指定表的详细信息，包括行数等。
    """

    def get_name(self) -> str:
        """获取工具名称"""
        return "get_table_info"

    def get_description(self) -> str:
        """获取工具描述"""
        return "Get information about a specific table including row count"

    def invoke(self, parameters: Dict[str, Any]) -> Any:
        """
        获取表信息

        参数:
            parameters: 包含 'table_name' 键的字典

        返回:
            表信息字典
        """
        from core.data_sources.tools import get_table_info  # 获取表信息函数

        table_name = parameters.get('table_name')
        if not table_name:
            return {'error': 'No table_name provided', 'success': False}

        try:
            info = get_table_info(table_name)
            return {'result': info, 'success': True}
        except Exception as e:
            return {'error': str(e), 'success': False}

    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
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


# 可用工具列表
ALL_TOOLS: List[Tool] = [
    SQLTool(),                    # SQL 查询工具
    CostSummaryTool(),            # 成本汇总工具
    RateSummaryTool(),            # 费率汇总工具
    ListTablesTool(),             # 列出表工具
    GetTableInfoTool()            # 获取表信息工具
]


def get_tool_by_name(tool_name: str) -> Optional[Tool]:
    """
    根据名称获取工具

    参数:
        tool_name: 工具名称

    返回:
        工具实例，如果未找到则返回 None
    """
    for tool in ALL_TOOLS:
        if tool.get_name() == tool_name:
            return tool
    return None


def list_tools() -> List[str]:
    """
    列出所有可用工具名称

    返回:
        工具名称列表
    """
    return [tool.get_name() for tool in ALL_TOOLS]


def get_tool_schemas() -> Dict[str, Dict[str, Any]]:
    """
    获取所有工具的参数模式

    返回:
        工具名称到参数模式的字典映射
    """
    return {tool.get_name(): tool.get_schema() for tool in ALL_TOOLS}


# 兼容别名 - execute_pandas_query 的向后兼容
def execute_pandas_query(query: str, **kwargs) -> Any:
    """
    使用数据源上下文执行 SQL 查询

    参数:
        query: SQL 查询字符串

    返回:
        查询结果字符串
    """
    from core.data_sources.context_provider import get_data_source_context_provider  # 数据源上下文提供者

    try:
        context_provider = get_data_source_context_provider()
        df = context_provider.execute_sql(query)
        return df.to_string(index=False)
    except Exception as e:
        return f"Error executing query: {str(e)}"


# 业务逻辑占位函数
def calculate_allocated_costs(**kwargs) -> str:
    """计算分摊成本"""
    return "Allocated costs calculation"


def compare_scenarios(**kwargs) -> str:
    """对比场景"""
    return "Scenario comparison"


def compare_allocated_costs(**kwargs) -> str:
    """对比分摊成本"""
    return "Allocated costs comparison"


def analyze_cost_composition(**kwargs) -> str:
    """分析成本构成"""
    return "Cost composition analysis"
