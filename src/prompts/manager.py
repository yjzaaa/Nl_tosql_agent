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


SQL_GENERATION_PROMPT = """
你是专业的 SQL 查询生成器。

你的任务是基于用户问题与意图分析生成 SQL 查询。

## 数据库上下文（来自 skill）
{database_context}

## 用户问题
{user_query}

## 意图分析
{intent_analysis}

## 错误上下文
{error_context}

## skill 上下文
{skill_context}

## SQL 规则（来自 skill / 数据源）
{sql_rules}

## 指令
1. 生成能够回答用户问题的有效 SQL 查询
2. 使用提供的数据库 schema 信息
3. 遵循 SQL 生成规则
4. 保证查询高效并使用合适索引
5. 正确处理 NULL 值
6. 如字段名可能为保留字或含特殊字符，请使用双引号
7. 只返回 SQL，不要解释

## 重要说明
- 使用合适的 WHERE 条件
- 需要聚合时使用 GROUP BY
- 仅在规则要求时添加结果限制

## 输出格式
仅返回 SQL 语句，不要 Markdown 代码块，不要解释。

示例：
SELECT col_a, SUM(col_b) AS total_value
FROM some_table
GROUP BY col_a
ORDER BY total_value DESC
"""


SQL_VALIDATION_PROMPT = """
你是专业的 SQL 查询校验器。

你的任务是校验 SQL 查询并识别问题。

## 数据库上下文（来自 skill）
{database_context}

## 待校验 SQL
{sql_query}

## 指令
1. 检查 SQL 语法错误
2. 验证表与字段是否存在于 schema
3. 检查 JOIN 条件是否正确
4. 校验 WHERE 子句
5. 确保 GROUP BY 与 HAVING 使用正确
6. 检查潜在性能问题
7. 验证数据类型兼容性

## 校验清单
- [ ] 表存在于 schema
- [ ] 字段存在于对应表
- [ ] JOIN 语法正确
- [ ] WHERE 子句有效
- [ ] GROUP BY 包含所有非聚合字段
- [ ] HAVING 使用正确
- [ ] 无语法错误

## 输出格式
返回 JSON 对象，结构如下：
{{
    "is_valid": true|false,
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1", "suggestion2"],
    "parsed_query": "normalized query if needed"
}}

如果查询有效，返回：
{{
    "is_valid": true,
    "issues": [],
    "suggestions": [],
    "parsed_query": null
}}
"""


RESULT_REVIEW_PROMPT = """
你是专业的 SQL 结果评审员。

你的任务是评审查询结果是否正确回答了用户问题。

## 原始用户问题
{user_query}

## 已执行的 SQL
{sql_query}

## 查询结果
{execution_result}

## 指令
1. 评估结果是否回答了用户问题
2. 检查结果格式是否合适
3. 识别异常或不符合预期的结果
4. 给出评审置信度（0.0 到 1.0）
5. 如发现问题，给出改进建议

## 评审标准
- [ ] 结果直接回答问题
- [ ] 结果格式合适（表格/摘要/单值等）
- [ ] 无明显错误或异常
- [ ] 结果完整且准确
- [ ] 结果可被用户理解

## 输出格式
返回 JSON 对象，结构如下：
{{
    "passed": true|false,
    "confidence": 0.0,
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1", "suggestion2"],
    "refined_answer": "对结果的自然语言解释"
}}

如果结果良好，请提供清晰的自然语言说明。
"""


ANSWER_REFINEMENT_PROMPT = """
你是将数据库查询结果优化为清晰自然语言回答的专家。

你的任务是基于查询结果，生成清晰且有帮助的回答。

## 原始用户问题
{user_query}

## 已执行的 SQL
{sql_query}

## 查询结果
{execution_result}

## 评审反馈
{review_feedback}

## 指令
1. 生成清晰、简洁的自然语言回答
2. 突出关键结论/洞察
3. 使用合适的格式（表格、列表等）
4. 数字与比例要具体
5. 必要时提供上下文解读
6. 尽量避免技术术语
7. 如存在多种解释，需说明

## 回答结构
- 直接回答问题
- 关键发现/洞察
- 佐证细节
- 建议（如适用）

## 输出格式
输出自然语言回答，要求：
- 清晰易懂
- 基于数据准确
- 有帮助且信息充分
- 排版良好

示例：
根据查询结果，各类别的汇总数值如下：
- A: 139,274,913.84
- B: 70,191,482.78
- C: 25,657,466.00

A 类别最高，占总量的约 55%。B 和 C 分别为 28% 和 17%。
"""
