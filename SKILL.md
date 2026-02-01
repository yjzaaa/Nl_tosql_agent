---
name: nl-to-sql-agent
description: "通用自然语言转SQL查询智能体 - 将用户自然语言查询转换为SQL语句并执行，支持多数据源接入和业务规则定制"
license: MIT
---

# NL to SQL Agent Skill

This skill provides a general-purpose natural language to SQL query conversion agent.

## Core Capabilities

1. **Intent Analysis** - Understand user query intent
2. **SQL Generation** - Convert natural language to SQL
3. **SQL Validation** - Validate generated SQL syntax
4. **SQL Execution** - Execute queries and return results
5. **Result Refinement** - Format and present results

## Architecture

### Data Source Types

The agent supports multiple data source types:

- **excel** - Excel files via SQLite adapter
- **sqlserver** - SQL Server databases
- **mysql** - MySQL databases (extensible)
- **postgresql** - PostgreSQL databases (extensible)

### Workflow Stages

```
User Query → Intent Analysis → SQL Generation → SQL Validation → SQL Execution → Result Refinement
```

## Configuration

### Skill Configuration Structure

```yaml
skill:
  name: "nl-to-sql-agent"
  version: "1.0.0"
  
data_sources:
  - type: "excel"
    enabled: true
    config:
      file_paths: {}
      max_preview_rows: 20
      default_result_limit: 20
      
  - type: "sqlserver"
    enabled: false
    config:
      host: "${SQL_SERVER_HOST}"
      database: "${SQL_SERVER_DB}"
      user: "${SQL_SERVER_USER}"
      password: "${SQL_SERVER_PASSWORD}"
      
llm:
  provider: "openai"  # openai, ollama, self_hosted
  model: "qwen2.5-1.5b-instruct"
  temperature: 0.1
  max_tokens: 4096
  
embedding:
  enabled: true
  provider: "self_hosted"
  model: "qwen3-embedding-0.6b"
```

### Business Rules Configuration

Business rules should be defined in separate skill modules:

```yaml
# skill_modules/business_rules.yaml
rules:
  - name: "field_naming"
    pattern: "field.*bracket"
    rule: "Use brackets for field names: [FieldName]"
    
  - name: "amount_conversion"
    pattern: "amount.*cast"
    rule: "Always CAST([Amount] AS FLOAT)"
    
  - name: "null_handling"
    pattern: "null.*handle"
    rule: "Use COALESCE(field, 0) for null handling"
```

## Skill Modules

### Available Skill Modules

1. **business_metadata** - Table structures, field rules, terminology
2. **sql_templates** - Reusable SQL generation templates
3. **sql_examples** - Example queries for common scenarios
4. **business_rules** - Field mapping and validation rules
5. **output_formatters** - Result formatting templates

### Loading Skill Modules

```python
from skills.loader import SkillLoader

loader = SkillLoader(skill_path="./skills")
skill = loader.load_skill("nl-to-sql-agent")

# Access business rules
business_rules = skill.get_module("business_rules")
templates = skill.get_module("sql_templates")
```

## Agent Configuration

### Intent Analysis Agent

```yaml
intent_agent:
  system_prompt: |
    You are an intent analysis agent for SQL query generation.
    Analyze user queries and identify:
    - Query intent (allocation, comparison, trend, general)
    - Relevant tables
    - Required parameters
    
  output_format:
    intent_type: str
    parameters: dict
    reasoning: str
```

### SQL Generation Agent

```yaml
sql_agent:
  system_prompt: |
    You are a SQL generation agent.
    Generate SQL based on:
    - Database schema
    - User intent
    - Business rules
    
  rules:
    - "Use [Brackets] for field names"
    - "CAST([Amount] AS FLOAT) for numeric fields"
    - "Use COALESCE(field, 0) for null handling"
```

### SQL Validation Agent

```yaml
validation_agent:
  checks:
    - syntax_check
    - permission_check
    - performance_check
    - injection_check
```

## Extensibility

### Adding New Data Sources

1. Create a new data source class:

```python
from core.data_sources.base import BaseDataSource

class MySQLDataSource(BaseDataSource):
    def connect(self, config):
        # Implement connection logic
        
    def execute(self, query):
        # Implement query execution
        
    def get_schema(self):
        # Return database schema
```

2. Register in configuration:

```yaml
data_sources:
  - type: "mysql"
    enabled: true
    config:
      host: "${MYSQL_HOST}"
      database: "${MYSQL_DB}"
```

### Adding Custom Business Rules

Create a new skill module:

```markdown
# Custom Business Rules

## Rule 1: Custom Field Mapping
- Description: Custom field naming conventions
- Pattern: custom_field_*
- Rule: Use UPPER_CASE for custom fields
```

## Output Formats

### Supported Output Formats

- **table** - Tabular format with headers
- **json** - JSON object format
- **markdown** - Markdown table format
- **csv** - CSV format

### Custom Output Formatter

```python
from skills.formatters import BaseFormatter

class CustomFormatter(BaseFormatter):
    def format(self, data, query):
        # Custom formatting logic
        return formatted_result
```

## Error Handling

### Error Types

1. **IntentAnalysisError** - Failed to analyze user intent
2. **SQLGenerationError** - Failed to generate SQL
3. **SQLValidationError** - Invalid SQL syntax
4. **ExecutionError** - Query execution failed
5. **ResultRefinementError** - Failed to format results

### Error Recovery

```yaml
error_handling:
  max_retries: 3
  retry_strategy: "exponential_backoff"
  fallback: "return_error_message"
```

## Usage Examples

### Basic Query

```python
from agents.nl_to_sql_agent import NLToSQLAgent

agent = NLToSQLAgent()
result = agent.query("Show me total sales by region")
print(result)
```

### With Custom Skill

```python
from skills.loader import SkillLoader

loader = SkillLoader(skill_path="./skills")
skill = loader.load_skill("nl-to-sql-agent")

agent = NLToSQLAgent(skill=skill)
result = agent.query("Calculate cost allocation for Q4")
```
