"""Core Schemas Module

Provides data models and type definitions for the NL to SQL workflow.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class IntentAnalysisResult(BaseModel):
    """Result of intent analysis"""

    intent_type: str = Field(
        ...,
        description="Type of query intent (e.g., 'query', 'aggregate', 'filter', 'join')",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the intent analysis (0.0 to 1.0)",
    )
    entities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Extracted entities from the query (e.g., table names, column names, filters)",
    )
    query_type: str = Field(
        default="simple",
        description="Type of SQL query (simple, aggregate, join, complex)",
    )
    filters: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Extracted filter conditions (e.g., {'column': 'function', 'value': 'IT', 'operator': '='})",
    )
    groupings: List[str] = Field(
        default_factory=list,
        description="Columns to group by (e.g., ['function', 'month'])",
    )
    aggregations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Aggregation operations (e.g., {'column': 'amount', 'function': 'SUM'})",
    )
    sort_order: Optional[Dict[str, str]] = Field(
        default=None,
        description="Sort order (e.g., {'column': 'amount', 'direction': 'DESC'})",
    )
    limit: Optional[int] = Field(default=None, description="Limit on number of results")
    explanation: Optional[str] = Field(
        default=None, description="Explanation of the intent analysis"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "intent_type": "aggregate",
                "confidence": 0.95,
                "entities": [
                    {"type": "table", "value": "SSME_FI_InsightBot_CostDataBase"},
                    {"type": "column", "value": "amount"},
                ],
                "query_type": "aggregate",
                "filters": [],
                "groupings": ["function"],
                "aggregations": [{"column": "amount", "function": "SUM"}],
                "sort_order": {"column": "amount", "direction": "DESC"},
                "limit": None,
                "explanation": "User wants to see total costs grouped by function type",
            }
        }


class SQLGenerationResult(BaseModel):
    """Result of SQL generation"""

    sql_query: str = Field(..., description="Generated SQL query")
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the SQL generation (0.0 to 1.0)",
    )
    explanation: Optional[str] = Field(
        default=None, description="Explanation of how the SQL query was generated"
    )
    tables_used: List[str] = Field(
        default_factory=list, description="Tables used in the SQL query"
    )
    columns_used: List[str] = Field(
        default_factory=list, description="Columns used in the SQL query"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sql_query": "SELECT function, SUM(amount) FROM SSME_FI_InsightBot_CostDataBase GROUP BY function ORDER BY SUM(amount) DESC",
                "confidence": 0.9,
                "explanation": "Aggregated amounts by function type",
                "tables_used": ["SSME_FI_InsightBot_CostDataBase"],
                "columns_used": ["function", "amount"],
            }
        }


class SQLValidationResult(BaseModel):
    """Result of SQL validation"""

    is_valid: bool = Field(..., description="Whether the SQL query is valid")
    issues: List[str] = Field(
        default_factory=list, description="List of validation issues found"
    )
    suggestions: List[str] = Field(
        default_factory=list, description="List of suggestions for improvement"
    )
    parsed_query: Optional[str] = Field(
        default=None, description="Parsed/normalized SQL query"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "issues": [],
                "suggestions": ["Consider adding LIMIT clause"],
                "parsed_query": "SELECT function, SUM(amount) FROM SSME_FI_InsightBot_CostDataBase GROUP BY function",
            }
        }


class QueryExecutionResult(BaseModel):
    """Result of SQL query execution"""

    success: bool = Field(..., description="Whether the query executed successfully")
    data: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Query result data as list of dictionaries"
    )
    row_count: int = Field(default=0, description="Number of rows returned")
    execution_time: Optional[float] = Field(
        default=None, description="Query execution time in seconds"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if execution failed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [
                    {"function": "IT", "sum": 139274913.84},
                    {"function": "HR", "sum": 70191482.78},
                ],
                "row_count": 6,
                "execution_time": 0.123,
                "error": None,
            }
        }


class ResultReviewResult(BaseModel):
    """Result of result review"""

    passed: bool = Field(..., description="Whether the result review passed")
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the result review (0.0 to 1.0)",
    )
    issues: List[str] = Field(
        default_factory=list, description="List of issues found in the result"
    )
    suggestions: List[str] = Field(
        default_factory=list, description="List of suggestions for improvement"
    )
    refined_answer: Optional[str] = Field(
        default=None, description="Refined natural language answer"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "passed": True,
                "confidence": 0.95,
                "issues": [],
                "suggestions": [],
                "refined_answer": "IT功能总成本为139,274,913.84元",
            }
        }


class AgentState(BaseModel):
    """Agent state for workflow"""

    trace_id: Optional[str] = Field(default=None, description="Unique trace ID")
    messages: List[Any] = Field(
        default_factory=list, description="Conversation messages"
    )
    user_query: Optional[str] = Field(
        default=None, description="User's natural language query"
    )
    intent_analysis: Optional[IntentAnalysisResult] = Field(
        default=None, description="Intent analysis result"
    )
    sql_query: Optional[str] = Field(default=None, description="Generated SQL query")
    sql_valid: bool = Field(default=False, description="Whether SQL is valid")
    execution_result: Optional[str] = Field(
        default=None, description="Query execution result"
    )
    review_passed: Optional[bool] = Field(
        default=None, description="Whether result review passed"
    )
    review_message: Optional[str] = Field(
        default=None, description="Refined answer message"
    )
    table_names: Optional[List[str]] = Field(
        default=None, description="Table names to query"
    )
    data_source_type: str = Field(default="excel", description="Data source type")
    error_message: Optional[str] = Field(
        default=None, description="Error message if any"
    )
    retry_count: int = Field(default=0, description="Number of retries attempted")
    skill: Optional[Any] = Field(default=None, description="Current skill")
    skill_name: Optional[str] = Field(default=None, description="Current skill name")

    class Config:
        arbitrary_types_allowed = True


class TableSchema(BaseModel):
    """Table schema definition"""

    table_name: str = Field(..., description="Table name")
    description: Optional[str] = Field(default=None, description="Table description")
    columns: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of column definitions"
    )
    primary_key: Optional[str] = Field(default=None, description="Primary key column")
    row_count: int = Field(default=0, description="Number of rows in table")

    class Config:
        json_schema_extra = {
            "example": {
                "table_name": "SSME_FI_InsightBot_CostDataBase",
                "description": "Cost database containing cost allocation records",
                "columns": [
                    {"name": "year", "type": "varchar", "description": "Fiscal year"},
                    {"name": "month", "type": "varchar", "description": "Month"},
                    {
                        "name": "function",
                        "type": "varchar",
                        "description": "Function type",
                    },
                    {"name": "amount", "type": "numeric", "description": "Cost amount"},
                ],
                "primary_key": "id",
                "row_count": 1584,
            }
        }


class DataSourceMetadata(BaseModel):
    """Data source metadata"""

    source_type: str = Field(..., description="Data source type (excel, postgresql)")
    host: Optional[str] = Field(default=None, description="Database host")
    port: Optional[int] = Field(default=None, description="Database port")
    database: Optional[str] = Field(default=None, description="Database name")
    schema: Optional[str] = Field(default=None, description="Database schema")
    tables: List[str] = Field(default_factory=list, description="Available table names")
    is_available: bool = Field(
        default=False, description="Whether data source is available"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "source_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "cost_allocation",
                "schema": "public",
                "tables": [
                    "SSME_FI_InsightBot_CostDataBase",
                    "SSME_FI_InsightBot_Rate",
                    "cc_mapping",
                ],
                "is_available": True,
            }
        }


class ExecutionContext(BaseModel):
    """Execution context for queries"""

    trace_id: str = Field(..., description="Unique trace ID")
    query_id: str = Field(..., description="Unique query ID")
    timestamp: str = Field(..., description="Execution timestamp")
    data_source_type: str = Field(..., description="Data source type")
    table_names: List[str] = Field(default_factory=list, description="Tables involved")
    query_type: Optional[str] = Field(default=None, description="Query type")
    user_query: Optional[str] = Field(default=None, description="Original user query")

    class Config:
        json_schema_extra = {
            "example": {
                "trace_id": "12345678-1234-1234-1234-123456789abc",
                "query_id": "query-001",
                "timestamp": "2024-01-01T12:00:00Z",
                "data_source_type": "postgresql",
                "table_names": ["SSME_FI_InsightBot_CostDataBase"],
                "query_type": "aggregate",
                "user_query": "按功能统计成本",
            }
        }
