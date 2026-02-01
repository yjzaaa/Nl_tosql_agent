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
        return skill_metadata.get("default_tables", [])

    # Remove duplicates while preserving order
    seen = set()
    result = []
    for table in tables:
        if table not in seen:
            seen.add(table)
            result.append(table)

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

    return schemas.get(real_name, {})


def get_all_tables(skill_metadata: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Get list of all available tables from skill metadata.

    Returns:
        List of table names
    """
    if not skill_metadata:
        return []

    schemas = skill_metadata.get("table_schemas", {})
    return list(schemas.keys())


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

    # If the skill provides specific SQL generation rules (e.g. in a sql_rules.md module), use them.
    if skill and hasattr(skill, "get_module_content"):
        content = skill.get_module_content("sql_rules")
        if content:
            return content

    # Fallback to generic rules if not provided by skill
    if data_source_type.lower() == "postgresql":
        return """
## PostgreSQL SQL Generation Rules

### General Rules
- Use standard SQL syntax compatible with PostgreSQL
- Use double quotes (") for column names if they contain spaces or special characters.
- Column names are case-sensitive when quoted.

### Date/Time Functions
- Use standard PostgreSQL date functions.

### Numeric Functions
- Use ABS() for absolute value if dealing with negative allocation amounts.
- Use COALESCE(col, 0) to handle NULLs.

### JOIN Syntax
- Use LEFT JOIN typically.
"""
    else:
        return """
## SQLite/Excel SQL Generation Rules

### General Rules
- Use SQLite syntax (for Excel data source)
- Table names: Sheet names from Excel
- Case-insensitive column names
- Use single quotes (') for string literals

### Date/Time Functions
- Use strftime('%Y', DateCol) for year extraction
- Use strftime('%m', DateCol) for month extraction
- Do NOT use YEAR() or MONTH() functions

### String Functions
- Use || for string concatenation
- Use UPPER(), LOWER() for case conversion
- Use SUBSTR() for string slicing
- Use TRIM() for removing whitespace

### Limiting Results
- Use LIMIT N (do NOT use TOP N)

### NULL Handling
- Use COALESCE(value, default) for NULL replacement
- Do NOT use ISNULL()

### Type Conversion
- Use CAST(col AS REAL) for numeric conversion
- Use CAST(col AS TEXT) for string conversion
"""
