"""
大语言模型(LLM)交互测试

测试各个Agent节点与LLM的交互，专注于：
1. 发送给LLM的prompt内容格式
2. LLM返回的响应格式验证
3. Prompt模板中的变量替换
"""

import asyncio
import os
import pytest
import sys
from pathlib import Path
from typing import Dict, Any, List

# 强制禁用本地代理，解决 Ollama 502 错误
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# 添加项目路径到 sys.path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from langchain_core.messages import HumanMessage
from promts import get_graph, AgentState, GraphWorkflow
from excel_agent.logger import setup_logging, get_logger

# 强制禁用本地代理，解决 Ollama 502 错误
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# 添加项目路径到 sys.path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# 配置日志
setup_logging()
logger = get_logger("llm_interaction")


class TestIntentAnalysisPrompt:
    """测试意图分析Prompt"""

    def test_prompt_template_structure(self):
        """测试prompt模板结构"""
        assert INTENT_ANALYSIS_PROMPT is not None
        assert len(INTENT_ANALYSIS_PROMPT) > 100
        assert "intent" in INTENT_ANALYSIS_PROMPT.lower()

    def test_prompt_contains_required_placeholders(self):
        """测试prompt包含必需的占位符"""
        assert "{database_context}" in INTENT_ANALYSIS_PROMPT
        assert "{user_query}" in INTENT_ANALYSIS_PROMPT

    def test_prompt_rendering(self):
        """测试prompt渲染"""
        database_context = "Test database schema"
        user_query = "列出所有IT服务"

        rendered = render_prompt(
            INTENT_ANALYSIS_PROMPT,
            context={"database_context": database_context, "user_query": user_query}
        )

        assert database_context in rendered
        assert user_query in rendered
        assert "{database_context}" not in rendered
        assert "{user_query}" not in rendered

    def test_rendered_prompt_contains_instructions(self):
        """测试渲染后的prompt包含指令"""
        rendered = render_prompt(
            INTENT_ANALYSIS_PROMPT,
            database_context="test",
            user_query="test"
        )

        # 验证关键指令存在
        required_keywords = [
            "analyze",
            "tables",
            "columns",
            "filters",
            "json",
            "intent_type",
            "confidence"
        ]

        for keyword in required_keywords:
            assert keyword.lower() in rendered.lower()

    def test_prompt_with_error_context(self):
        """测试带错误上下文的prompt"""
        base_prompt = render_prompt(
            INTENT_ANALYSIS_PROMPT,
            database_context="test",
            user_query="test"
        )

        error_message = "SQL syntax error near column 'ABC'"
        prompt_with_error = base_prompt + f"\n\nLast attempt failed, error: {error_message}."

        assert "error" in prompt_with_error.lower()
        assert "failed" in prompt_with_error.lower()
        assert error_message in prompt_with_error


class TestSQLGenerationPrompt:
    """测试SQL生成Prompt"""

    def test_prompt_template_structure(self):
        """测试prompt模板结构"""
        assert SQL_GENERATION_PROMPT is not None
        assert len(SQL_GENERATION_PROMPT) > 100
        assert "sql" in SQL_GENERATION_PROMPT.lower()
        assert "generate" in SQL_GENERATION_PROMPT.lower()

    def test_prompt_contains_required_placeholders(self):
        """测试prompt包含必需的占位符"""
        assert "{database_context}" in SQL_GENERATION_PROMPT
        assert "{user_query}" in SQL_GENERATION_PROMPT
        assert "{intent_analysis}" in SQL_GENERATION_PROMPT
        assert "{error_context}" in SQL_GENERATION_PROMPT
        assert "{sqlite_rules}" in SQL_GENERATION_PROMPT

    def test_prompt_rendering_with_all_variables(self):
        """测试完整变量的prompt渲染"""
        variables = {
            "database_context": "Database schema with cost_database table",
            "user_query": "计算26财年HR总费用",
            "intent_analysis": '{"intent_type": "aggregate", "confidence": 0.9}',
            "error_context": "",
            "sqlite_rules": "Use SUM() for aggregation, filter with WHERE clause"
        }

        rendered = render_prompt(SQL_GENERATION_PROMPT, **variables)

        # 验证所有变量都被替换
        for key, value in variables.items():
            assert value in rendered, f"Variable {key} not found in rendered"
            assert "{" + key + "}" not in rendered, f"Placeholder {key} not replaced"

    def test_rendered_prompt_contains_sql_instructions(self):
        """测试渲染后的prompt包含SQL指令"""
        rendered = render_prompt(
            SQL_GENERATION_PROMPT,
            database_context="test schema",
            user_query="test query",
            intent_analysis="{}",
            error_context="",
            sqlite_rules="test rules"
        )

        # 验证SQL生成指令
        required_keywords = [
            "postgresql",
            "generate",
            "valid",
            "sql",
            "where",
            "sum",
            "group by"
        ]

        for keyword in required_keywords:
            assert keyword.lower() in rendered.lower()

    def test_prompt_with_error_retry(self):
        """测试带错误重试的prompt"""
        base_prompt = render_prompt(
            SQL_GENERATION_PROMPT,
            database_context="test",
            user_query="test",
            intent_analysis="{}",
            error_context="",
            sqlite_rules="test rules"
        )

        error_message = "Column 'InvalidCol' does not exist"
        prompt_with_error = base_prompt.replace("error_context\": \"\"",
                                      f"error_context\": \"{error_message}\"")

        assert "error" in prompt_with_error.lower()
        assert "invalidcol" in prompt_with_error.lower()


class TestSQLValidationPrompt:
    """测试SQL验证Prompt"""

    def test_prompt_template_structure(self):
        """测试prompt模板结构"""
        assert SQL_VALIDATION_PROMPT is not None
        assert len(SQL_VALIDATION_PROMPT) > 100
        assert "validate" in SQL_VALIDATION_PROMPT.lower()
        assert "sql" in SQL_VALIDATION_PROMPT.lower()

    def test_prompt_contains_required_placeholders(self):
        """测试prompt包含必需的占位符"""
        assert "{database_context}" in SQL_VALIDATION_PROMPT
        assert "{sql_query}" in SQL_VALIDATION_PROMPT

    def test_prompt_rendering(self):
        """测试prompt渲染"""
        variables = {
            "database_context": "Schema: cost_database table with Year, Function, Amount columns",
            "sql_query": "SELECT SUM(Amount) FROM cost_database WHERE Year=2026 AND Function='HR'"
        }

        rendered = render_prompt(SQL_VALIDATION_PROMPT, **variables)

        # 验证变量被替换
        for key, value in variables.items():
            assert value in rendered

        # 验证SQL查询包含在prompt中
        assert "SUM(Amount)" in rendered
        assert "Year=2026" in rendered
        assert "Function='HR'" in rendered

    def test_rendered_prompt_contains_validation_checks(self):
        """测试渲染后的prompt包含验证检查项"""
        rendered = render_prompt(
            SQL_VALIDATION_PROMPT,
            database_context="test schema",
            sql_query="SELECT * FROM table"
        )

        # 验证验证检查项
        validation_checks = [
            "syntax",
            "table",
            "column",
            "join",
            "where",
            "group by"
        ]

        for check in validation_checks:
            assert check.lower() in rendered.lower()

    def test_prompt_output_format(self):
        """测试prompt输出格式要求"""
        rendered = render_prompt(
            SQL_VALIDATION_PROMPT,
            database_context="test",
            sql_query="test"
        )

        # 验证输出格式说明
        assert "json" in rendered.lower()
        assert "is_valid" in rendered.lower()
        assert "issues" in rendered.lower()
        assert "suggestions" in rendered.lower()


class TestResultReviewPrompt:
    """测试结果审查Prompt"""

    def test_prompt_template_structure(self):
        """测试prompt模板结构"""
        assert RESULT_REVIEW_PROMPT is not None
        assert len(RESULT_REVIEW_PROMPT) > 100
        assert "review" in RESULT_REVIEW_PROMPT.lower()
        assert "result" in RESULT_REVIEW_PROMPT.lower()

    def test_prompt_contains_required_placeholders(self):
        """测试prompt包含必需的占位符"""
        assert "{user_query}" in RESULT_REVIEW_PROMPT
        assert "{sql_query}" in RESULT_REVIEW_PROMPT
        assert "{execution_result}" in RESULT_REVIEW_PROMPT

    def test_prompt_rendering_with_execution_result(self):
        """测试带执行结果的prompt渲染"""
        variables = {
            "user_query": "26财年HR费用是多少？",
            "sql_query": "SELECT SUM(Amount) FROM cost_database WHERE Year=2026 AND Function='HR'",
            "execution_result": "Total: 12,054,383.0"
        }

        rendered = render_prompt(RESULT_REVIEW_PROMPT, **variables)

        # 验证变量被替换
        for key, value in variables.items():
            assert value in rendered

        # 验证关键信息存在
        assert "12,054,383.0" in rendered
        assert "26财年" in rendered
        assert "HR" in rendered

    def test_rendered_prompt_contains_review_criteria(self):
        """测试渲染后的prompt包含审查标准"""
        rendered = render_prompt(
            RESULT_REVIEW_PROMPT,
            user_query="test",
            sql_query="test",
            execution_result="test result"
        )

        # 验证审查标准
        review_criteria = [
            "answers",
            "format",
            "anomalies",
            "confidence",
            "passed"
        ]

        for criterion in review_criteria:
            assert criterion.lower() in rendered.lower()

    def test_prompt_output_format_requirements(self):
        """测试prompt输出格式要求"""
        rendered = render_prompt(
            RESULT_REVIEW_PROMPT,
            user_query="test",
            sql_query="test",
            execution_result="test"
        )

        # 验证输出格式
        assert "json" in rendered.lower()
        assert "passed" in rendered.lower()
        assert "confidence" in rendered.lower()
        assert "issues" in rendered.lower()
        assert "suggestions" in rendered.lower()
        assert "refined_answer" in rendered.lower()


class TestAnswerRefinementPrompt:
    """测试答案优化Prompt"""

    def test_prompt_template_structure(self):
        """测试prompt模板结构"""
        assert ANSWER_REFINEMENT_PROMPT is not None
        assert len(ANSWER_REFINEMENT_PROMPT) > 100

    def test_prompt_contains_required_placeholders(self):
        """测试prompt包含必需的占位符"""
        assert "{user_query}" in ANSWER_REFINEMENT_PROMPT
        assert "{sql_query}" in ANSWER_REFINEMENT_PROMPT
        assert "{execution_result}" in ANSWER_REFINEMENT_PROMPT
        assert "{review_feedback}" in ANSWER_REFINEMENT_PROMPT

    def test_prompt_rendering_with_review_feedback(self):
        """测试带审查反馈的prompt渲染"""
        variables = {
            "user_query": "26财年HR费用是多少？",
            "sql_query": "SELECT SUM(Amount) FROM cost_database WHERE Year=2026 AND Function='HR'",
            "execution_result": "12,054,383.0",
            "review_feedback": "结果准确，置信度高"
        }

        rendered = render_prompt(ANSWER_REFINEMENT_PROMPT, **variables)

        # 验证所有变量被替换
        for key, value in variables.items():
            assert value in rendered

        # 验证审查反馈存在
        assert "结果准确，置信度高" in rendered

    def test_rendered_prompt_contains_refinement_instructions(self):
        """测试渲染后的prompt包含优化指令"""
        rendered = render_prompt(
            ANSWER_REFINEMENT_PROMPT,
            user_query="test",
            sql_query="test",
            execution_result="test result",
            review_feedback="good"
        )

        # 验证优化指令
        refinement_instructions = [
            "clear",
            "concise",
            "natural language",
            "key insights",
            "formatting",
            "specific",
            "numbers"
        ]

        for instruction in refinement_instructions:
            assert instruction.lower() in rendered.lower()

    def test_prompt_answer_structure_requirements(self):
        """测试prompt答案结构要求"""
        rendered = render_prompt(
            ANSWER_REFINEMENT_PROMPT,
            user_query="test",
            sql_query="test",
            execution_result="test",
            review_feedback="test"
        )

        # 验证答案结构要求
        answer_structure = [
            "direct answer",
            "key findings",
            "supporting details",
            "recommendations"
        ]

        for structure in answer_structure:
            assert structure.lower() in rendered.lower()


class TestBusinessQuestionPrompts:
    """测试业务问题Prompt生成"""

    def test_question1_prompt_generation(self):
        """测试Q1的prompt生成"""
        question_en = "What services do IT cost include? And what is the allocation key?"
        question_cn = "IT费用都有些什么服务，这些服务是按什么分摊给业务部门的？"

        # 生成意图分析prompt
        prompt = render_prompt(
            INTENT_ANALYSIS_PROMPT,
            database_context="Schema: cost_database with Function, Cost text, Key columns",
            user_query=question_cn
        )

        # 验证prompt包含问题关键词
        assert "IT" in prompt
        assert "服务" in prompt
        assert "分摊" in prompt
        assert question_cn in prompt

    def test_question2_prompt_generation(self):
        """测试Q2的prompt生成"""
        question = "26财年计划了多少HR费用的预算？"

        # 生成SQL生成prompt
        prompt = render_prompt(
            SQL_GENERATION_PROMPT,
            database_context="Schema: cost_database with Year, Scenario, Function, Amount columns",
            user_query=question,
            intent_analysis='{"intent_type": "aggregate", "confidence": 0.9}',
            error_context="",
            sqlite_rules="Use SUM() for total, filter with WHERE clause"
        )

        # 验证prompt包含问题要素
        assert "26财年" in prompt or "2026" in prompt
        assert "HR" in prompt
        assert "预算" in prompt or "Budget1" in prompt
        assert "SUM" in prompt

    def test_question3_prompt_generation(self):
        """测试Q3的prompt生成（分摊计算）"""
        question = "25财年实际分摊给CT的IT费用是多少？"

        # 生成SQL生成prompt
        prompt = render_prompt(
            SQL_GENERATION_PROMPT,
            database_context="Schema: cost_database and rate_table tables",
            user_query=question,
            intent_analysis='{"intent_type": "allocation", "confidence": 0.9}',
            error_context="",
            sqlite_rules="Use JOIN for tables, multiply amount by rate"
        )

        # 验证prompt包含分摊计算要素
        assert "25财年" in prompt or "2025" in prompt
        assert "IT" in prompt
        assert "CT" in prompt
        assert "分摊" in prompt
        assert "join" in prompt.lower()
        assert "rate" in prompt.lower()

    def test_question4_prompt_generation(self):
        """测试Q4的prompt生成（同比对比）"""
        question = "26财年采购的预算费用和25财年实际数比，变化是什么？"

        # 生成结果审查prompt
        execution_result = """
        FY25 Total: 1,929,340
        FY26 Total: 2,025,807
        Variance: 96,467
        """

        prompt = render_prompt(
            RESULT_REVIEW_PROMPT,
            user_query=question,
            sql_query="SELECT FY25, FY26, Variance FROM comparison",
            execution_result=execution_result
        )

        # 验证prompt包含对比要素
        assert "26财年" in prompt
        assert "25财年" in prompt
        assert "采购" in prompt
        assert "变化" in prompt
        assert "1,929,340" in prompt
        assert "2,025,807" in prompt
        assert "96,467" in prompt

    def test_question5_prompt_generation(self):
        """测试Q5的prompt生成（分摊对比）"""
        question = "26财年预算要分摊给413001的HR费用和25财年实际分摊给XP的HR费用相比，变化是怎么样的？"

        # 生成答案优化prompt
        prompt = render_prompt(
            ANSWER_REFINEMENT_PROMPT,
            user_query=question,
            sql_query="SELECT FY25_Alloc, FY26_Alloc, Variance FROM hr_allocation_comparison",
            execution_result="FY25: 241,362.8, FY26: 216,728.8, Variance: -24,634.0",
            review_feedback="对比结果正确"
        )

        # 验证prompt包含对比要素
        assert "26财年" in prompt
        assert "25财年" in prompt
        assert "413001" in prompt
        assert "HR" in prompt
        assert "分摊" in prompt
        assert "241,362.8" in prompt
        assert "216,728.8" in prompt
        assert "-24,634.0" in prompt


class TestLLMResponseValidation:
    """测试LLM响应格式验证"""

    def test_intent_analysis_response_format(self):
        """测试意图分析响应格式"""
        response = """
        {
          "intent_type": "listing",
          "confidence": 0.95,
          "entities": [
            {"type": "table", "value": "cost_database"},
            {"type": "column", "value": "Function"}
          ],
          "query_type": "simple",
          "filters": [{"column": "Function", "value": "IT", "operator": "="}],
          "groupings": [],
          "aggregations": [],
          "sort_order": null,
          "limit": null,
          "explanation": "用户想要列出IT相关的功能"
        }
        """

        # 解析JSON
        result = json.loads(response)

        # 验证必需字段
        required_fields = [
            "intent_type",
            "confidence",
            "entities",
            "query_type",
            "filters",
            "explanation"
        ]

        for field in required_fields:
            assert field in result

        # 验证数据类型
        assert isinstance(result["confidence"], float)
        assert 0 <= result["confidence"] <= 1
        assert isinstance(result["entities"], list)
        assert isinstance(result["filters"], list)

    def test_sql_validation_response_format(self):
        """测试SQL验证响应格式"""
        valid_response = """
        {
          "is_valid": true,
          "issues": [],
          "suggestions": [],
          "parsed_query": null
        }
        """

        result = json.loads(valid_response)
        assert result["is_valid"] is True
        assert len(result["issues"]) == 0

        invalid_response = """
        {
          "is_valid": false,
          "issues": ["Column 'ABC' does not exist"],
          "suggestions": ["Use existing column names"],
          "parsed_query": "SELECT * FROM valid_table"
        }
        """

        result = json.loads(invalid_response)
        assert result["is_valid"] is False
        assert len(result["issues"]) > 0
        assert len(result["suggestions"]) > 0

    def test_result_review_response_format(self):
        """测试结果审查响应格式"""
        good_response = """
        {
          "passed": true,
          "confidence": 0.92,
          "issues": [],
          "suggestions": [],
          "refined_answer": "查询结果为12,054,383.0元"
        }
        """

        result = json.loads(good_response)
        assert result["passed"] is True
        assert result["confidence"] > 0.8
        assert len(result["issues"]) == 0

        bad_response = """
        {
          "passed": false,
          "confidence": 0.3,
          "issues": ["结果格式不清晰"],
          "suggestions": ["明确金额数值"],
          "refined_answer": null
        }
        """

        result = json.loads(bad_response)
        assert result["passed"] is False
        assert result["confidence"] < 0.5
        assert len(result["issues"]) > 0

    def test_tool_call_response_format(self):
        """测试工具调用响应格式"""
        tool_call_response = """
        {
          "tool_call": "calculate_allocated_costs",
          "parameters": {
            "year": 2025,
            "scenario": "Actual",
            "function": "IT Allocation",
            "target_bl": "CT"
          }
        }
        """

        result = json.loads(tool_call_response)
        assert "tool_call" in result
        assert "parameters" in result
        assert result["tool_call"] == "calculate_allocated_costs"
        assert result["parameters"]["year"] == 2025
        assert result["parameters"]["scenario"] == "Actual"
        assert result["parameters"]["target_bl"] == "CT"


class TestPromptContentQuality:
    """测试Prompt内容质量"""

    def test_intent_analysis_prompt_completeness(self):
        """测试意图分析prompt完整性"""
        prompt = render_prompt(
            INTENT_ANALYSIS_PROMPT,
            database_context="test schema",
            user_query="test query"
        )

        # 验证关键要素
        required_elements = [
            "intent",
            "table",
            "column",
            "filter",
            "group",
            "aggregation",
            "json format",
            "output"
        ]

        found_elements = sum(1 for elem in required_elements if elem.lower() in prompt.lower())
        completeness_ratio = found_elements / len(required_elements)

        # 要求至少80%的关键要素存在
        assert completeness_ratio >= 0.8, \
            f"Prompt completeness is {completeness_ratio*100:.0f}%, expected >= 80%"

    def test_sql_generation_prompt_quality(self):
        """测试SQL生成prompt质量"""
        prompt = render_prompt(
            SQL_GENERATION_PROMPT,
            database_context="test schema",
            user_query="test query",
            intent_analysis="{}",
            error_context="",
            sqlite_rules="test rules"
        )

        # 验证SQL生成关键要素
        sql_quality_elements = [
            "valid sql",
            "schema",
            "where clause",
            "group by",
            "aggregate function",
            "handle null",
            "efficiency"
        ]

        found_elements = sum(1 for elem in sql_quality_elements if elem.lower() in prompt.lower())
        quality_ratio = found_elements / len(sql_quality_elements)

        # 要求至少75%的关键要素存在
        assert quality_ratio >= 0.75, \
            f"SQL generation prompt quality is {quality_ratio*100:.0f}%, expected >= 75%"

    def test_answer_refinement_prompt_clarity(self):
        """测试答案优化prompt清晰度"""
        prompt = render_prompt(
            ANSWER_REFINEMENT_PROMPT,
            user_query="test",
            sql_query="test",
            execution_result="test result",
            review_feedback="test feedback"
        )

        # 验证答案清晰度要素
        clarity_elements = [
            "clear",
            "concise",
            "specific numbers",
            "formatting",
            "avoid jargon",
            "easy to understand"
        ]

        found_elements = sum(1 for elem in clarity_elements if elem.lower() in prompt.lower())
        clarity_ratio = found_elements / len(clarity_elements)

        # 要求至少70%的清晰度要素存在
        assert clarity_ratio >= 0.70, \
            f"Answer refinement prompt clarity is {clarity_ratio*100:.0f}%, expected >= 70%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
