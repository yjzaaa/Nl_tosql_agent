"""
SQL 验证 Agent - 使用依赖注入

本模块负责校验生成的 SQL 语句的安全性，
检查危险关键词和语法正确性。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage  # 人类消息类型

from src.core.data_sources.context_provider import get_data_source_context_provider  # 数据源上下文提供者
from src.core.llm import get_llm  # LLM 工厂函数
from src.prompts.manager import SQL_VALIDATION_PROMPT, render_prompt_template  # SQL 校验提示模板
from src.core.metadata import get_sql_generation_rules  # SQL 生成规则

if TYPE_CHECKING:
    from workflow.graph import AgentState  # 工作流状态类型


def validate_sql_node(state: AgentState) -> AgentState:
    """
    SQL 校验节点 - 验证 SQL 语句的安全性和正确性

    本节点完成以下功能：
    1. 检查 SQL 是否包含危险操作关键词
    2. 校验 SQL 语法正确性
    3. 仅允许 SELECT 查询（只读操作）

    参数:
        state: 当前工作流状态

    返回:
        更新后的工作流状态，包含校验结果
    """
    try:
        # 从状态中获取 SQL 语句
        sql = state.get("sql_query", "")
        # 获取数据源上下文提供者
        context_provider = get_data_source_context_provider()

        # 如果是工具调用（JSON 格式），直接标记为有效
        if sql.strip().startswith("{") and "tool_call" in sql:
            state["sql_valid"] = True
            state["error_message"] = ""
            return state

        # 检查 SQL 是否为空
        if not sql or sql.strip() == "":
            state["error_message"] = "Code validation failed: SQL query cannot be empty."
            state["sql_valid"] = False
            return state

        # 危险操作关键词黑名单
        # 这些关键词可能导致数据修改或安全风险
        forbidden_keywords = [
            "delete",      # 删除数据
            "drop",        # 删除表/数据库
            "insert",      # 插入数据
            "update",      # 更新数据
            "replace",     # 替换数据
            "alter",       # 修改表结构
            "create",      # 创建对象
            "truncate",    # 清空表
            "exec(",       # 执行存储过程
            "eval(",       # 动态代码执行
            "__import__",  # 动态导入
            "open(",       # 文件操作
            "write(",      # 写文件
            "system(",     # 系统命令执行
            "os.",         # OS 模块调用
            "sys.",        # sys 模块调用
        ]

        # 检查是否包含危险关键词
        sql_upper = sql.upper()
        for keyword in forbidden_keywords:
            if keyword in sql:
                state["error_message"] = (
                    f"Code validation failed: contains forbidden keyword '{keyword}'."
                    "Please use read-only SELECT syntax only."
                )
                state["sql_valid"] = False
                return state

        # Excel 模式下不需要校验
        if context_provider.is_excel_mode():
            state["sql_valid"] = True
            state["error_message"] = ""
            return state

        # 获取数据源上下文（表结构信息）
        columns_info = context_provider.get_data_source_context(state.get("table_names"))

        # 确定数据源类型
        data_source_type = state.get("data_source_type") or "postgresql"
        if context_provider.is_excel_mode():
            data_source_type = "excel"
        elif context_provider.is_sql_server_mode():
            data_source_type = "sqlserver"

        # 获取 SQL 生成规则
        skill = state.get("skill")
        sql_rules = get_sql_generation_rules(data_source_type, skill=skill)

        # 构建校验提示词
        prompt = render_prompt_template(
            SQL_VALIDATION_PROMPT,
            database_context=columns_info,
            sql_query=sql,
            extra_rule=f"""
            重要校验规则：
            {sql_rules}
            3. 语法错误/字段错误/非 SELECT 语法 => INVALID；
            4. 仅返回【VALID】或【INVALID + 原因】。
            """,
        )

        # 调用 LLM 进行 SQL 语法校验
        llm = state.get("llm") or get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        result = response.content.strip().upper()

        # 解析校验结果
        if "INVALID" in result:
            state["error_message"] = f"Code validation failed: {response.content.strip()}"
            state["sql_valid"] = False
            return state

        # 校验通过
        state["sql_valid"] = True
        state["error_message"] = ""
        return state

    except Exception as e:
        # 捕获异常，设置错误信息
        state["error_message"] = f"validate_sql_node error: {str(e)}"
        return state
