"""Core Metadata Module

Provides table name resolution for natural language queries.
"""

from typing import List, Optional, Dict, Any

# We need a way to access the active skill.
# Since this module is used by functions that might not have the skill object passed,
# we should rely on the caller passing the skill object or metadata.
# However, to maintain backward compatibility and clean architecture,
# we will update the signatures to accept an optional skill/metadata object.


def resolve_table_names(
    user_query: str,
    intent_analysis: Optional[Dict[str, Any]] = None,
    skill_metadata: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Resolve table names from user query and intent analysis using skill metadata.

    Args:
        user_query: User's natural language query
        intent_analysis: Intent analysis results (optional)
        skill_metadata: Metadata from the active skill (optional)

    Returns:
        List of table names that are likely relevant to the query
    """

    if not user_query:
        return []

    # If no skill metadata provided, return empty list (caller should handle default)
    if not skill_metadata:
        return []

    query_lower = user_query.lower()
    tables = []

    keyword_map = skill_metadata.get("keyword_table_map", {})
    tables_map = skill_metadata.get("tables", {})

    for keyword, table_list in keyword_map.items():
        if keyword.lower() in query_lower:
            tables.extend(table_list)

    # Also check intent_table_map if intent_analysis is provided
    if intent_analysis:
        intent_type = intent_analysis.get("intent_type")
        intent_map = skill_metadata.get("intent_table_map", {})
        if intent_type and intent_type in intent_map:
            tables.extend(intent_map[intent_type])

    # If no specific tables detected, return default tables
    if not tables:
        default_tables = skill_metadata.get("default_tables", [])
        mapped = []
        for table in default_tables:
            real_name = tables_map.get(table, table)
            if real_name not in mapped:
                mapped.append(real_name)
        return mapped

    # Remove duplicates while preserving order
    seen = set()
    result = []
    for table in tables:
        # Map logical name to physical name if provided
        real_name = tables_map.get(table, table)
        if real_name not in seen:
            seen.add(real_name)
            result.append(real_name)

    return result


def get_table_schema(
    table_name: str, skill_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get schema information for a specific table from skill metadata.

    Args:
        table_name: Name of the table
        skill_metadata: Metadata from the active skill

    Returns:
        Dictionary containing table schema information
    """
    if not skill_metadata:
        return {}

    schemas = skill_metadata.get("table_schemas", {})

    # Handle aliases if defined in metadata?
    # For now assume direct match or check tables dict
    tables_map = skill_metadata.get("tables", {})

    # Check if table_name is an alias key in "tables"
    real_name = tables_map.get(table_name, table_name)

    if schemas:
        return schemas.get(real_name, {})

    # No schema details provided in metadata
    return {}


def get_all_tables(skill_metadata: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Get list of all available tables from skill metadata.

    Returns:
        List of table names
    """
    if not skill_metadata:
        return []

    schemas = skill_metadata.get("table_schemas", {})
    if schemas:
        return list(schemas.keys())

    tables_map = skill_metadata.get("tables", {})
    # Prefer physical table names (values) if provided
    if tables_map:
        seen = set()
        result = []
        for value in tables_map.values():
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result

    return []


def get_table_relationships(
    skill_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, List[Dict[str, str]]]:
    """
    Get table relationships for JOIN queries from skill metadata.

    Returns:
        Dictionary mapping table names to their relationships
    """
    if not skill_metadata:
        return {}

    return skill_metadata.get("relationships", {})


def get_business_logic_context(skill: Any = None) -> str:
    """
    Get business logic context for the cost allocation system from the skill.

    Args:
        skill: The active Skill object

    Returns:
        String containing business logic description
    """
    if skill and hasattr(skill, "get_module_content"):
        # Try to get business_rules.md content directly
        # Or construct it from parsed rules

        # Option 1: Load raw content from business_rules.md
        content = skill.get_module_content("business_rules")
        if content:
            return content

        # Option 2: Construct from SKILL.md description
        return skill.description

    return ""


def get_sql_generation_rules(
    data_source_type: str = "postgresql", skill: Any = None
) -> str:
    """
    Get SQL generation rules based on data source type and skill.

    Args:
        data_source_type: Type of data source (postgresql, excel/sqlite)
        skill: The active Skill object

    Returns:
        String containing SQL generation rules
    """


    # Fallback to generic rules if not provided by skill
    if data_source_type.lower() == "postgresql":
        return """
## PostgreSQL SQL 生成规则

### 通用规则
- 使用与 PostgreSQL 兼容的标准 SQL 语法
- 字段名包含空格或特殊字符时使用双引号 (")
- 被双引号包裹的字段名区分大小写

### 日期/时间函数
- 使用 PostgreSQL 标准日期函数

### 数值函数
- 处理负数金额时使用 ABS()
- 使用 COALESCE(col, 0) 处理 NULL

### JOIN 语法
- 通常使用 LEFT JOIN
"""
    if data_source_type.lower() in {"sqlserver", "mssql", "ms_sql", "sql_server"}:
        return """
## SQL Server SQL 生成规则

### 通用规则
- 使用 SQL Server T-SQL 语法
- 字段名包含空格或特殊字符时使用方括号 [] 或双引号 (")
- 字符串字面量使用单引号 (')

### 日期/时间函数
- 需要时使用 YEAR(date_col)、MONTH(date_col)
- 日期转换使用 CAST/CONVERT
### Sql Server SQL 生成规则
- 必须使用[]包裹包含空格或特殊字符的字段名
### 数值函数
- 处理负数金额时使用 ABS()
- 使用 COALESCE(col, 0) 处理 NULL

### JOIN 语法
- 通常使用 LEFT JOIN

### 结果限制
- 使用 SELECT TOP (N) 或 OFFSET/FETCH
- 禁止使用 LIMIT

### NULL 处理
- 使用 COALESCE(value, default)
- 禁止使用 IFNULL()

### 类型转换
- 使用 CAST(col AS FLOAT) 或 CAST(col AS DECIMAL(18, 4))
"""
    else:
        return """
    ## SQLite/Excel SQL 生成规则

    ### 通用规则
    - 使用 SQLite 语法（用于 Excel 数据源）
    - 表名：Excel 的工作表名称
    - 字段名不区分大小写
    - 字符串字面量使用单引号 (')

    ### 日期/时间函数
    - 使用 strftime('%Y', DateCol) 提取年份
    - 使用 strftime('%m', DateCol) 提取月份
    - 禁止使用 YEAR() 或 MONTH()

    ### 字符串函数
    - 使用 || 进行字符串拼接
    - 使用 UPPER()/LOWER() 进行大小写转换
    - 使用 SUBSTR() 进行字符串切片
    - 使用 TRIM() 去除空白

    ### 结果限制
    - 使用 LIMIT N（禁止使用 TOP N）

    ### NULL 处理
    - 使用 COALESCE(value, default) 替换 NULL
    - 禁止使用 ISNULL()

    ### 类型转换
    - 使用 CAST(col AS REAL) 进行数值转换
    - 使用 CAST(col AS TEXT) 进行字符串转换
    """
