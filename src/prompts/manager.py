"""Prompt Manager

Provides prompt templates for various NL to SQL agents.
"""

from typing import Dict, Any, Optional
from src.core.metadata import (
    get_business_logic_context,
    get_sql_generation_rules,
    get_table_schema,
    get_table_relationships,
    get_all_tables,
)


def render_prompt_template(
    template: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any
) -> str:
    context_data = context or {}
    context_data.update(kwargs)

    if not context_data:
        return template

    result = template
    for key, value in context_data.items():
        placeholder = f"{{{key}}}"
        result = result.replace(placeholder, str(value))

    return result


def get_data_source_context(
    table_names: Optional[list] = None, data_source_type: str = "postgresql"
) -> str:
    """
    Get data source context for prompts

    Args:
        table_names: List of table names to include
        data_source_type: Type of data source (postgresql, excel)

    Returns:
        Formatted context string
    """

    if not table_names:
        table_names = get_all_tables()

    context_lines = ["## Database Schema\n"]

    # Add table schemas
    for table_name in table_names:
        schema = get_table_schema(table_name)
        if not schema:
            continue

        context_lines.append(f"\n### {schema['table_name']}")
        context_lines.append(f"Description: {schema.get('description', 'N/A')}")
        context_lines.append(f"Row Count: {schema.get('row_count', 0)}")
        context_lines.append("Columns:")

        for col in schema.get("columns", []):
            col_name = col.get("name", "")
            col_type = col.get("type", "")
            col_desc = col.get("description", "")
            context_lines.append(f"  - {col_name} ({col_type}): {col_desc}")

    # Add table relationships
    relationships = get_table_relationships()
    if relationships:
        context_lines.append("\n## Table Relationships")

        for table_name, rels in relationships.items():
            if table_name not in table_names:
                continue

            for rel in rels:
                if rel["foreign_table"] not in table_names:
                    continue

                context_lines.append(
                    f"\n- {table_name} {rel['join_type']} {rel['foreign_table']} "
                    f"ON {rel['join_on']}\n  ({rel['description']})"
                )

    # Add business logic
    context_lines.append("\n" + get_business_logic_context())

    # Add SQL rules
    context_lines.append("\n" + get_sql_generation_rules(data_source_type))

    return "\n".join(context_lines)


INTENT_ANALYSIS_PROMPT = """
You are an expert SQL query analyzer for a cost allocation database.

Your task is to analyze the user's natural language query and determine:
1. Query intent (query, aggregate, filter, join, etc.)
2. Tables involved
3. Columns needed
4. Filter conditions
5. Grouping requirements
6. Aggregation functions needed
7. Sorting requirements
8. Limit requirements

## Database Context
{database_context}

## User Query
{user_query}

## Instructions
1. Analyze the user query to understand the intent
2. Identify which tables are relevant to the query
3. Extract any filters, groupings, aggregations mentioned
4. Determine the query type (simple, aggregate, join, complex)
5. Provide confidence score (0.0 to 1.0) for your analysis

## Output Format
Return a JSON object with the following structure:
{{
  "intent_type": "string",
  "confidence": 0.0,
  "entities": [
    {{"type": "table", "value": "table_name"}},
    {{"type": "column", "value": "column_name"}}
  ],
  "query_type": "simple|aggregate|join|complex",
  "filters": [
    {{"column": "col_name", "value": "val", "operator": "="}}
  ],
  "groupings": ["col1", "col2"],
  "aggregations": [
    {{"column": "col_name", "function": "SUM|COUNT|AVG|MAX|MIN"}}
  ],
  "sort_order": {{"column": "col_name", "direction": "ASC|DESC"}},
  "limit": null,
  "explanation": "Brief explanation of the analysis"
}}
"""


SQL_GENERATION_PROMPT = """
You are an expert SQL query generator for a cost allocation database.

Your task is to generate a PostgreSQL SQL query based on the user's natural language query
and the intent analysis provided.

## Database Context
{database_context}

## User Query
{user_query}

## Intent Analysis
{intent_analysis}

## Instructions
1. Generate a valid PostgreSQL SQL query that answers the user's question
2. Use the database schema information provided
3. Follow the PostgreSQL SQL generation rules
4. Ensure the query is efficient and uses appropriate indexes
5. Handle NULL values properly
6. Use double quotes for column names if they might be reserved words
7. Return only the SQL query, no explanations

## Important Notes
- Cost amounts: Use ABS() when calculating allocation amounts
- Date handling: Use appropriate PostgreSQL date functions
- Filtering: Use appropriate WHERE clauses
- Grouping: Use GROUP BY when aggregating
- Limit: Add LIMIT clause to prevent excessive results

## Output Format
Return ONLY the SQL query, no markdown code blocks, no explanations.

Example:
SELECT function, SUM(amount) as total_cost
FROM cost_database
GROUP BY function
ORDER BY total_cost DESC
LIMIT 10
"""


SQL_VALIDATION_PROMPT = """
You are an expert SQL query validator.

Your task is to validate the SQL query and identify any issues.

## Database Context
{database_context}

## SQL Query to Validate
{sql_query}

## Instructions
1. Check for SQL syntax errors
2. Verify table and column names exist in the schema
3. Check for proper JOIN conditions
4. Validate WHERE clauses
5. Ensure proper GROUP BY and HAVING usage
6. Check for potential performance issues
7. Validate data type compatibility

## Validation Checks
- [ ] Tables exist in schema
- [ ] Columns exist in respective tables
- [ ] JOIN syntax is correct
- [ ] WHERE clauses are valid
- [ ] GROUP BY includes all non-aggregated columns
- [ ] HAVING is used correctly
- [ ] No syntax errors

## Output Format
Return a JSON object with the following structure:
{{
  "is_valid": true|false,
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1", "suggestion2"],
  "parsed_query": "normalized query if needed"
}}

If the query is valid, return:
{{
  "is_valid": true,
  "issues": [],
  "suggestions": [],
  "parsed_query": null
}}
"""


RESULT_REVIEW_PROMPT = """
You are an expert SQL result reviewer.

Your task is to review the query result and determine if it properly answers the user's question.

## Original User Query
{user_query}

## SQL Query Executed
{sql_query}

## Query Result
{execution_result}

## Instructions
1. Review if the result answers the user's question
2. Check if the result format is appropriate
3. Identify any anomalies or unexpected results
4. Provide confidence score (0.0 to 1.0) for the review
5. If issues are found, provide suggestions for improvement

## Review Criteria
- [ ] Result directly answers the question
- [ ] Result format is appropriate (table, summary, single value)
- [ ] No obvious errors or anomalies
- [ ] Result is complete and accurate
- [ ] Result is interpretable by the user

## Output Format
Return a JSON object with the following structure:
{{
  "passed": true|false,
  "confidence": 0.0,
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1", "suggestion2"],
  "refined_answer": "Natural language explanation of the result"
}}

If the result is good, provide a clear natural language explanation of what the result shows.
"""


ANSWER_REFINEMENT_PROMPT = """
You are an expert in refining database query results into clear, natural language answers.

Your task is to create a clear, helpful answer to the user's question based on the query result.

## Original User Query
{user_query}

## SQL Query Executed
{sql_query}

## Query Result
{execution_result}

## Review Feedback
{review_feedback}

## Instructions
1. Create a clear, concise natural language answer
2. Highlight key insights from the data
3. Use appropriate formatting (tables, bullet points, etc.)
4. Be specific with numbers and percentages
5. Provide context and interpretation where helpful
6. Avoid technical jargon when possible
7. If there are multiple interpretations, address them

## Answer Structure
- Direct answer to the question
- Key findings / insights
- Supporting details
- Recommendations (if applicable)

## Output Format
Provide a natural language answer that is:
- Clear and easy to understand
- Accurate based on the data
- Helpful and informative
- Well-formatted and readable

Example:
根据查询结果，各功能类型的成本总额如下：
- IT: 139,274,913.84元
- HR: 70,191,482.78元
- Procurement: 25,657,466.00元

IT功能成本最高，占总成本的约55%。HR和Procurement成本分别为28%和17%。
"""
