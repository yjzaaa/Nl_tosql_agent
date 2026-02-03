"""
人在回路工具支持 - 为 LangGraph 1.0.7+ 提供中间件支持

本模块提供在工具执行前暂停并等待用户确认的功能，
支持三种用户操作：接受(accept)、编辑(edit)、响应(respond)。
"""

from typing import Callable, Any, Dict  # 类型定义
from langchain_core.tools import BaseTool as LangChainBaseTool  # LangChain 基础工具类
from langchain_core.tools import tool as create_tool  # 工具创建装饰器
from langchain_core.runnables import RunnableConfig  # 可运行配置
from langgraph.types import interrupt  # 中断函数


class HumanInterruptConfig:
    """
    人在回路中断配置类

    用于配置用户在工具执行前可执行的操作类型。
    """

    def __init__(
        self,
        allow_accept: bool = True,  # 是否允许接受操作
        allow_edit: bool = True,  # 是否允许编辑操作
        allow_respond: bool = True,  # 是否允许响应操作
        description: str = "Tool execution requires your confirmation",  # 描述信息
    ):
        self.allow_accept = allow_accept  # 接受操作开关
        self.allow_edit = allow_edit  # 编辑操作开关
        self.allow_respond = allow_respond  # 响应操作开关
        self.description = description  # 描述信息


def add_human_in_the_loop(
    tool: Callable | LangChainBaseTool,
    *,
    interrupt_config: HumanInterruptConfig = None,
) -> LangChainBaseTool:
    """
    为工具添加人在回路支持

    包装一个工具，使其在执行前暂停并等待用户确认。

    参数:
        tool: 要包装的工具（可以是函数或 BaseTool）
        interrupt_config: 中断行为配置

    返回:
        新的 BaseTool，在执行前会暂停等待用户确认
    """
    # 如果传入的是函数，转换为工具
    if not isinstance(tool, LangChainBaseTool):
        tool = create_tool(tool)

    # 如果没有提供配置，使用默认配置
    if interrupt_config is None:
        interrupt_config = HumanInterruptConfig(
            allow_accept=True,
            allow_edit=True,
            allow_respond=True,
        )

    # 保存原始工具信息和调用方法
    tool_name = tool.name
    original_invoke = tool.invoke

    def call_tool_with_interrupt(config: RunnableConfig, **tool_input: Any) -> Any:
        """
        包装后的工具调用函数

        在执行原始工具前触发中断，等待用户确认。

        参数:
            config: 可运行配置
            **tool_input: 工具输入参数

        返回:
            工具执行结果
        """
        # 构建中断信息
        interrupt_value = {
            "action_request": {
                "action": tool_name,
                "args": tool_input
            },
            "config": {
                "allow_accept": interrupt_config.allow_accept,
                "allow_edit": interrupt_config.allow_edit,
                "allow_respond": interrupt_config.allow_respond,
            },
            "description": interrupt_config.description,
        }

        # 触发中断，等待用户响应
        response = interrupt(interrupt_value)

        # 处理用户响应
        if response is None:
            raise ValueError("Interrupt returned None - user may have cancelled")

        if isinstance(response, dict):
            action = response.get("action", "accept")

            if action == "accept":
                # 用户接受，执行原始工具
                return original_invoke(tool_input, config)
            elif action == "edit":
                # 用户编辑参数，使用编辑后的参数执行
                edited_args = response.get("args", tool_input)
                return original_invoke(edited_args, config)
            elif action == "respond":
                # 用户直接响应，返回用户反馈
                return response.get("feedback", "User provided feedback")
            else:
                raise ValueError(f"Unsupported action: {action}")
        else:
            raise ValueError(f"Unexpected response type: {type(response)}")

    # 保留原始工具引用
    call_tool_with_interrupt.original_tool = tool
    call_tool_with_interrupt.name = f"{tool_name}_with_human_loop"
    call_tool_with_interrupt.description = interrupt_config.description

    # 获取原始工具的参数模式
    args_schema = getattr(tool, 'args_schema', None)

    # 创建包装后的工具
    wrapped_tool = create_tool(
        call_tool_with_interrupt,
        description=interrupt_config.description,
        args_schema=args_schema,
    )

    return wrapped_tool


def create_execute_sql_tool(
    data_source_type: str = "excel",
) -> LangChainBaseTool:
    """
    创建带人在回路支持的 SQL 执行工具

    参数:
        data_source_type: 数据源类型（excel, sqlserver 等）

    返回:
        带人在回路确认的 SQL 执行工具
    """
    import re  # 正则表达式库
    from src.core.data_sources.context_provider import get_data_source_context_provider  # 数据源上下文提供者

    def execute_sql_fn(sql_query: str) -> str:
        """
        执行 SQL 查询函数

        参数:
            sql_query: SQL 查询语句

        返回:
            查询结果字符串
        """
        context_provider = get_data_source_context_provider()

        # 清理 SQL 查询字符串
        cleaned_sql = sql_query.strip()
        # 移除可能的 "sql" 前缀
        if cleaned_sql.lower().startswith("sql"):
            cleaned_sql = cleaned_sql[3:].lstrip()
        # 移除代码块标记
        if cleaned_sql.startswith("```"):
            cleaned_sql = cleaned_sql.strip("`").lstrip()

        # SQL Server 模式下转换 LIMIT 为 TOP
        if data_source_type == "sqlserver" or context_provider.is_sql_server_mode():
            match = re.search(r"\blimit\s+(\d+)\s*;?\s*$", cleaned_sql, re.IGNORECASE)
            if match and "top" not in cleaned_sql.lower():
                limit_n = match.group(1)
                cleaned_sql = re.sub(
                    r"^\s*select\s+",
                    f"SELECT TOP {limit_n} ",
                    cleaned_sql,
                    flags=re.IGNORECASE,
                )
                cleaned_sql = re.sub(
                    r"\blimit\s+\d+\s*;?\s*$",
                    "",
                    cleaned_sql,
                    flags=re.IGNORECASE,
                ).strip()

        # 执行查询
        df = context_provider.execute_sql(cleaned_sql, data_source_type=data_source_type)
        return df.to_string(index=False)

    # 创建基础工具
    base_tool = create_tool(
        execute_sql_fn,
        description="Execute a SQL query against the configured data source"
    )

    # 添加人在回路支持
    return add_human_in_the_loop(
        base_tool,
        interrupt_config=HumanInterruptConfig(
            allow_accept=True,
            allow_edit=True,
            allow_respond=True,
            description="SQL execution requires your confirmation. Please review the SQL before proceeding."
        )
    )
