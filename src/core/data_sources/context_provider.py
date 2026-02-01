"""数据源上下文提供者 - 唯一的数据源入口"""

from typing import Dict, Any, Optional, List
import pandas as pd
import uuid


class DataSourceContextProvider:
    """数据源上下文提供者 - 工作流与数据源交互的唯一入口"""

    _instance: Optional["DataSourceContextProvider"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """确保初始化完成"""
        if self._initialized:
            return

        from src.core.loader.excel_loader import get_loader
        from src.core.data_sources.manager import get_data_source_manager
        from src.core.data_sources.executor import get_executor

        self._loader = get_loader()
        self._manager = get_data_source_manager()
        self._executor = get_executor()
        self._initialized = True

    def detect_sources(self, table_names: List[str]) -> Dict[str, Any]:
        """检测并准备数据源

        Args:
            table_names: 要检测的表名列表

        Returns:
            数据源信息字典
        """
        self._ensure_initialized()
        return self._manager.detect_sources(table_names)

    def get_data_source_context(self, table_names: Optional[List[str]] = None, skill: Optional[Any] = None) -> str:
        """获取数据源上下文

        Args:
            table_names: 表名列表（SQL模式需要）
            skill: 业务技能对象 (可选)

        Returns:
            上下文字符串
        """
        self._ensure_initialized()

        context_str = ""

        # 1. 优先从 Skill 获取业务规则
        if skill:
            from src.core.metadata import get_business_logic_context
            business_logic = get_business_logic_context(skill)
            if business_logic:
                context_str += "## Business Logic & Rules\n"
                context_str += business_logic + "\n\n"

        # 2. 获取数据库 Schema
        if self._manager.get_strategy():
            context = self._manager.get_context()
            available_tables = []
            if "tables" in context:
                available_tables = list(context["tables"].keys())

            target_tables = table_names if table_names else available_tables

            if not target_tables:
                context_str += "No active tables loaded in data source."
                return context_str

            try:
                # Return detailed schema info
                context_str += "## Database Schema\n"
                context_str += self._manager.get_schema_info(target_tables)
                return context_str
            except Exception as e:
                return context_str + f"Error getting schema info: {str(e)}"

        # 3. Fallback to Excel Loader
        loaded_tables = self._loader.list_tables()

        if not loaded_tables:
            return context_str + "No active tables loaded."

        lines = ["## Available Tables\n\n"]

        for table_info in loaded_tables:
            t_loader = self._loader.get_table(table_info["id"])
            if not t_loader:
                continue

            structure = t_loader.get_structure()
            preview = t_loader.get_preview(n_rows=3)
            sheet_name = structure["sheet_name"]

            lines.append(f"### Table: {sheet_name}\n")
            lines.append("Columns & Examples:\n")

            for col in structure["columns"]:
                col_name = col["name"]
                dtype = col["dtype"]

                examples = []
                for row in preview["data"]:
                    val = row.get(col_name)
                    if val is not None:
                        examples.append(str(val)[:30])

                example_str = ", ".join(examples[:2])
                if len(examples) > 2:
                    example_str += "..."

                lines.append(f"  - {col_name} ({dtype}): [{example_str}]\n")

            lines.append("\n")

        if len(loaded_tables) > 1:
            lines.append("## Multi-table Query\n")
            lines.append("You can JOIN multiple tables using their Sheet names:\n")
            lines.append("```sql\n")
            lines.append("SELECT a.Column1, b.Column2\n")
            lines.append("FROM TableA a\n")
            lines.append("JOIN TableB b ON a.Key = b.Key\n")
            lines.append("```\n")
        
        return context_str + "".join(lines)

    def get_sql_rules(self) -> str:
        """获取SQL规则 - 根据数据源类型返回对应规则"""
        self._ensure_initialized()

        # If manager has a strategy, generic rules might apply?
        # Actually metadata.py has get_sql_generation_rules which is better.
        # This method is a bit redundant or should delegate to metadata.

        # For now, keep the SQLite rules as default fallback for Excel
        return """
    - **SQLite 专用规则** (当数据源为 Excel 时必须遵守):
      - 日期函数：禁止使用 YEAR()/MONTH()，必须使用 strftime('%Y', DateCol) 或 strftime('%m', DateCol)。
      - 字符串拼接：必须使用 || 运算符，禁止使用 +。
      - 行数限制：必须使用 LIMIT N，禁止使用 TOP N。
      - 类型转换：使用 CAST(col AS REAL) 或 CAST(col AS TEXT)。
      - 空值处理：禁止使用 ISNULL()，必须使用 COALESCE()。
      - 字符串引号：推荐使用单引号 'value'。
            """

    def is_excel_mode(self) -> bool:
        """判断是否为Excel模式"""
        self._ensure_initialized()
        return not self._manager.sql_server_available

    def is_sql_server_mode(self) -> bool:
        """判断是否为SQL Server模式"""
        self._ensure_initialized()
        return self._manager.sql_server_available

    def execute_sql(
        self, sql_query: str, data_source_type: Optional[str] = None
    ) -> pd.DataFrame:
        """执行SQL查询

        Args:
            sql_query: SQL查询语句
            data_source_type: 数据源类型 (可选)

        Returns:
            查询结果DataFrame
        """
        self._ensure_initialized()

        # If type is provided, use it
        if data_source_type:
            return self._executor.execute_from_state(
                {"sql_query": sql_query, "data_source_type": data_source_type}
            )

        # Fallback logic
        if self.is_excel_mode():
            return self._executor.execute_from_state(
                {"sql_query": sql_query, "data_source_type": "excel"}
            )
        else:
            return self._executor.execute_from_state(
                {"sql_query": sql_query, "data_source_type": "sql_server"}
            )

    def clear(self) -> None:
        """清除所有数据源状态"""
        from src.core.loader.excel_loader import reset_loader

        reset_loader()
        self._executor.clear() if hasattr(self, "_executor") else None
        self._initialized = False


def get_data_source_context_provider() -> DataSourceContextProvider:
    """获取数据源上下文提供者单例"""
    return DataSourceContextProvider()


# Backwards compatibility alias
ContextProvider = DataSourceContextProvider
