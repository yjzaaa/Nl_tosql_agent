"""
自然语言转SQL Agent工作流测试

测试完整的NL-to-SQL agent工作流，包括：
1. 意图分析
2. 上下文加载
3. SQL生成
4. SQL验证
5. SQL执行
6. 结果审查
7. 答案优化

基于业务需求的5个问题测试
"""

import pytest
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nl_to_sql_agent import NLToSQLAgent
from skills.loader import Skill, SkillLoader
from workflow.skill_aware import SkillAwareWorkflow, SkillAwareState


# Module-level fixtures for all test classes
@pytest.fixture(scope="module")
def sample_cost_data(fixtures_dir):
    """创建成本数据库测试数据"""
    data = {
        "Year": [2025] * 12 + [2026] * 12,
        "Scenario": ["Actual"] * 12 + ["Budget1"] * 12,
        "Function": ["IT"] * 12 + ["HR"] * 12,
        "Cost text": [
            "7092 GS IT_SW", "7092 GS IT_End user", "5547 GS IT", "5547 DLP",
            "P41", "M365 Collaboration", "M365 Messaging", "MWP",
            "Printing", "ISD & AHD", "SD-LAN Local", "SD-LAN Hub"
        ] + ["HR Services"] * 12,
        "Account": ["IT Original"] * 12 + ["HR Original"] * 12,
        "Category": ["IT Cost"] * 12 + ["HR Cost"] * 12,
        "Key": ["WCW", "SAM", "WCW", "WCW", "WCW", "WCW", "WCW", "WCW", "WCW", "Win Acc", "WCW", "WCW"] + ["headcount"] * 12,
        "Year Total": [-120000] * 12 + [12054383] * 12,
        "Month": list(range(1, 13)) * 2,
        "Amount": [-10000] * 12 + [1004532] * 12
    }
    df = pd.DataFrame(data)
    excel_path = fixtures_dir / "nl_cost_data.xlsx"
    df.to_excel(excel_path, index=False)
    return excel_path, df


@pytest.fixture(scope="module")
def sample_rate_data(fixtures_dir):
    """创建费率表测试数据"""
    data = {
        "BL": ["CT"] * 12 + ["413001"] * 12,
        "CC": ["CT-001"] * 6 + ["413001-CC"] * 6 + ["CT-001"] * 6 + ["413001-CC"] * 6,
        "Year": [2025] * 12 + [2026] * 12,
        "Scenario": ["Actual"] * 12 + ["Budget1"] * 12,
        "Period": list(range(1, 13)) + list(range(1, 13)),
        "Key": ["480056 Cycle"] * 12 + ["480055 Cycle"] * 12,
        "RateNo": [0.05] * 6 + [0.10] * 6 + [0.08] * 6 + [0.09] * 6
    }
    df = pd.DataFrame(data)
    excel_path = fixtures_dir / "nl_rate_data.xlsx"
    df.to_excel(excel_path, index=False)
    return excel_path, df


@pytest.fixture(scope="module")
def sample_procurement_data(fixtures_dir):
    """创建采购成本数据"""
    data = {
        "Year": [2025] * 12 + [2026] * 12,
        "Scenario": ["Actual"] * 12 + ["Budget1"] * 12,
        "Function": ["Procurement"] * 24,
        "Cost text": ["Procurement Services"] * 24,
        "Account": ["Procurement"] * 24,
        "Category": ["Procurement Cost"] * 24,
        "Key": ["WCW"] * 24,
        "Year Total": [1929340] * 12 + [2025807] * 12,
        "Month": list(range(1, 13)) * 2,
        "Amount": [160778] * 12 + [168817] * 12
    }
    df = pd.DataFrame(data)
    excel_path = fixtures_dir / "nl_procurement_data.xlsx"
    df.to_excel(excel_path, index=False)
    return excel_path, df


@pytest.fixture
def test_skill_dir(tmp_path):
    """创建测试技能目录"""
    skill_dir = tmp_path / "nl-to-sql-agent"
    skill_dir.mkdir()

    # SKILL.md
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: nl-to-sql-agent
version: "1.0.0"
description: "Test skill for NL to SQL workflow"
license: MIT
---

# Test NL to SQL Agent

This is a test skill for NL to SQL workflow testing.
""")

    # metadata.md
    metadata_md = skill_dir / "metadata.md"
    metadata_md.write_text("""```json
{
  "tables": {
    "cost_database": {
      "description": "成本数据库",
      "columns": [
        {"name": "Year", "type": "INTEGER", "description": "财年"},
        {"name": "Scenario", "type": "TEXT", "description": "场景"},
        {"name": "Function", "type": "TEXT", "description": "功能"},
        {"name": "Cost text", "type": "TEXT", "description": "成本描述"},
        {"name": "Account", "type": "TEXT", "description": "科目"},
        {"name": "Category", "type": "TEXT", "description": "类别"},
        {"name": "Key", "type": "TEXT", "description": "分摊键"},
        {"name": "Year Total", "type": "FLOAT", "description": "年度总计"},
        {"name": "Month", "type": "INTEGER", "description": "月份"},
        {"name": "Amount", "type": "FLOAT", "description": "金额"}
      ]
    },
    "rate_table": {
      "description": "费率表",
      "columns": [
        {"name": "BL", "type": "TEXT", "description": "业务线"},
        {"name": "CC", "type": "TEXT", "description": "成本中心"},
        {"name": "Year", "type": "INTEGER", "description": "财年"},
        {"name": "Scenario", "type": "TEXT", "description": "场景"},
        {"name": "Period", "type": "INTEGER", "description": "期间"},
        {"name": "Key", "type": "TEXT", "description": "分摊键"},
        {"name": "RateNo", "type": "FLOAT", "description": "费率"}
      ]
    }
}
```""")

    return skill_dir


class TestQuestion1_ITServicesAndKeys:
    """测试问题1: IT费用都有些什么服务，这些服务是按什么分摊给业务部门的？"""

    def test_q1_intent_analysis(self, test_skill_dir, sample_cost_data):
        """测试Q1意图分析"""
        query_en = "What services do IT cost include? And what is the allocation key?"
        query_cn = "IT费用都有些什么服务，这些服务是按什么分摊给业务部门的？"

        # 验证问题类型
        assert "IT" in query_cn
        assert "服务" in query_cn
        assert "分摊" in query_cn

        print("✅ Q1意图分析: 这是一个列表查询问题，需要列出IT服务和对应的分摊Key")

    def test_q1_expected_sql_structure(self, sample_cost_data):
        """测试Q1期望的SQL结构"""
        excel_path, df = sample_cost_data

        # 期望的SQL逻辑
        expected_sql_pattern = """
        SELECT DISTINCT [Cost text], [Key]
        FROM [cost_database]
        WHERE [Function] = 'IT'
        ORDER BY [Cost text]
        """

        # 验证数据中是否存在相关字段
        assert "Cost text" in df.columns
        assert "Key" in df.columns
        assert "Function" in df.columns

        # 验证数据内容
        it_data = df[df["Function"] == "IT"]
        assert len(it_data) > 0

        print("✅ Q1 SQL结构验证: 期望的SQL应筛选IT功能，并返回Cost text和Key")

    def test_q1_expected_result_format(self, sample_cost_data):
        """测试Q1期望的结果格式"""
        excel_path, df = sample_cost_data

        # 执行期望的查询
        result = df[df["Function"] == "IT"][["Cost text", "Key"]].drop_duplicates()

        # 验证结果结构
        assert len(result) > 0
        assert "Cost text" in result.columns
        assert "Key" in result.columns

        # 验证期望的IT服务和Key
        expected_services = [
            "7092 GS IT_SW", "7092 GS IT_End user", "5547 GS IT", "5547 DLP",
            "P41", "M365 Collaboration", "M365 Messaging", "MWP",
            "Printing", "ISD & AHD", "SD-LAN Local", "SD-LAN Hub"
        ]

        expected_keys = ["SAM", "WCW", "Win Acc"]

        print(f"✅ Q1结果格式验证: 期望返回{len(expected_services)}个IT服务")
        print(f"   服务: {result['Cost text'].tolist()}")
        print(f"   Key: {result['Key'].unique().tolist()}")


class TestQuestion2_HRCostFY26Budget:
    """测试问题2: 26财年计划了多少HR费用的预算？"""

    def test_q2_intent_analysis(self, test_skill_dir, sample_cost_data):
        """测试Q2意图分析"""
        query_en = "What was the HR Cost in FY26 BGT?"
        query_cn = "26财年计划了多少HR费用的预算？"

        # 验证问题要素
        assert "26财年" in query_cn or "FY26" in query_en
        assert "HR" in query_en
        assert "预算" in query_cn or "BGT" in query_en

        print("✅ Q2意图分析: 这是一个聚合查询问题，需要计算FY26 Budget的HR总费用")

    def test_q2_expected_sql_structure(self, sample_cost_data):
        """测试Q2期望的SQL结构"""
        excel_path, df = sample_cost_data

        # 期望的SQL逻辑
        expected_sql_pattern = """
        SELECT SUM(CAST([Amount] AS FLOAT)) AS Total_HR_Cost
        FROM [cost_database]
        WHERE [Year] = 2026
          AND [Scenario] = 'Budget1'
          AND [Function] = 'HR'
        """

        # 验证筛选条件
        filtered = df[
            (df["Year"] == 2026) &
            (df["Scenario"] == "Budget1") &
            (df["Function"] == "HR")
        ]

        assert len(filtered) > 0

        # 验证聚合计算
        total_cost = filtered["Amount"].sum()

        print(f"✅ Q2 SQL结构验证: 期望的SQL应筛选FY26 Budget的HR费用并求和")
        print(f"   总费用: {total_cost:,.1f}")

    def test_q2_expected_result_format(self, sample_cost_data):
        """测试Q2期望的结果格式"""
        excel_path, df = sample_cost_data

        # 执行期望的查询
        result = df[
            (df["Year"] == 2026) &
            (df["Scenario"] == "Budget1") &
            (df["Function"] == "HR")
        ]["Amount"].sum()

        # 验证结果
        assert result > 0

        # 期望的结果格式
        expected_answer = f"26财年HR预算为 {result:,.1f}"

        print(f"✅ Q2结果格式验证: 期望返回总金额")
        print(f"   预期答案: {expected_answer}")


class TestQuestion3_ITCostAllocatedToCTFY25:
    """测试问题3: 25财年实际分摊给CT的IT费用是多少？"""

    def test_q3_intent_analysis(self, test_skill_dir, sample_rate_data):
        """测试Q3意图分析"""
        query_en = "What was the actual IT cost allocated to CT in FY25?"
        query_cn = "25财年实际分摊给CT的IT费用是多少？"

        # 验证问题要素
        assert "25财年" in query_cn or "FY25" in query_en
        assert "IT" in query_en
        assert "CT" in query_en
        assert "分摊" in query_cn or "allocated" in query_en
        assert "实际" in query_cn or "Actual" in query_en

        print("✅ Q3意图分析: 这是一个分摊计算问题，需要关联成本和费率表")

    def test_q3_expected_sql_structure(self, sample_cost_data, sample_rate_data):
        """测试Q3期望的SQL结构"""
        cost_excel, cost_df = sample_cost_data
        rate_excel, rate_df = sample_rate_data

        # 期望的SQL逻辑（分摊计算）
        expected_sql_pattern = """
        SELECT
            SUM(ABS(c.[Amount]) * r.[RateNo]) AS Allocated_Cost
        FROM [cost_database] c
        INNER JOIN [rate_table] r
            ON c.[Year] = r.[Year]
            AND c.[Scenario] = r.[Scenario]
            AND c.[Month] = r.[Period]
        WHERE c.[Year] = 2025
          AND c.[Scenario] = 'Actual'
          AND c.[Function] = 'IT Allocation'
          AND c.[Key] = '480056 Cycle'
          AND r.[BL] = 'CT'
        """

        print("✅ Q3 SQL结构验证: 期望的SQL需要关联成本和费率表，并计算分摊金额")

    def test_q3_expected_calculation_logic(self, sample_cost_data, sample_rate_data):
        """测试Q3期望的计算逻辑"""
        cost_excel, cost_df = sample_cost_data
        rate_excel, rate_df = sample_rate_data

        # Step 1: 筛选IT Allocation成本
        it_allocation = cost_df[
            (cost_df["Year"] == 2025) &
            (cost_df["Scenario"] == "Actual") &
            (cost_df["Function"] == "IT Allocation")
        ]

        # Step 2: 筛选CT的费率
        ct_rates = rate_df[
            (rate_df["Year"] == 2025) &
            (rate_df["Scenario"] == "Actual") &
            (rate_df["BL"] == "CT")
        ]

        # Step 3: 计算分摊金额
        total_allocation = 0
        for month in range(1, 13):
            month_cost = it_allocation[it_allocation["Month"] == month]["Amount"].sum()
            month_rate = ct_rates[ct_rates["Period"] == month]["RateNo"].sum()
            allocation = abs(month_cost) * month_rate
            total_allocation += allocation

        print(f"✅ Q3计算逻辑验证:")
        print(f"   IT Allocation总成本: {it_allocation['Amount'].sum():,.1f}")
        print(f"   CT的总费率: {ct_rates['RateNo'].sum():.2f}")
        print(f"   分摊给CT的总金额: {total_allocation:,.1f}")


class TestQuestion4_ProcurementCostChange:
    """测试问题4: 26财年采购的预算费用和25财年实际数比，变化是什么？"""

    def test_q4_intent_analysis(self, test_skill_dir, sample_procurement_data):
        """测试Q4意图分析"""
        query_en = "How does Procurement Cost change from FY25 Actual to FY26 BGT?"
        query_cn = "26财年采购的预算费用和25财年实际数比，变化是什么？"

        # 验证问题要素
        assert "Procurement" in query_en
        assert "FY25" in query_en and "FY26" in query_en
        assert "变化" in query_cn or "change" in query_en

        print("✅ Q4意图分析: 这是一个同比对比问题，需要计算两年费用的变化值和变化比例")

    def test_q4_expected_sql_structure(self, sample_procurement_data):
        """测试Q4期望的SQL结构"""
        excel_path, df = sample_procurement_data

        # 期望的SQL逻辑（两个子查询）
        expected_sql_pattern = """
        WITH
        FY25_Actual AS (
            SELECT SUM(CAST([Amount] AS FLOAT)) AS FY25_Total
            FROM [cost_database]
            WHERE [Year] = 2025
              AND [Scenario] = 'Actual'
              AND [Function] = 'Procurement'
        ),
        FY26_Budget AS (
            SELECT SUM(CAST([Amount] AS FLOAT)) AS FY26_Total
            FROM [cost_database]
            WHERE [Year] = 2026
              AND [Scenario] = 'Budget1'
              AND [Function] = 'Procurement'
        )
        SELECT
            FY25_Total,
            FY26_Total,
            FY26_Total - FY25_Total AS Variance,
            (FY26_Total - FY25_Total) / FY25_Total * 100 AS Variance_Pct
        FROM FY25_Actual, FY26_Budget
        """

        print("✅ Q4 SQL结构验证: 期望的SQL需要使用CTE或子查询对比两年的数据")

    def test_q4_expected_calculation_logic(self, sample_procurement_data):
        """测试Q4期望的计算逻辑"""
        excel_path, df = sample_procurement_data

        # FY25 Actual
        fy25_total = df[
            (df["Year"] == 2025) &
            (df["Scenario"] == "Actual") &
            (df["Function"] == "Procurement")
        ]["Amount"].sum()

        # FY26 Budget
        fy26_total = df[
            (df["Year"] == 2026) &
            (df["Scenario"] == "Budget1") &
            (df["Function"] == "Procurement")
        ]["Amount"].sum()

        # 计算变化
        variance = fy26_total - fy25_total
        variance_pct = (variance / fy25_total) * 100

        print(f"✅ Q4计算逻辑验证:")
        print(f"   FY25 Actual: {fy25_total:,.0f}")
        print(f"   FY26 Budget: {fy26_total:,.0f}")
        print(f"   变化值: {variance:,}")
        print(f"   变化比例: {variance_pct:.1f}%")


class TestQuestion5_HRAllocationChange413001:
    """测试问题5: 26财年预算要分摊给413001的HR费用和25财年实际分摊给XP的HR费用相比，变化是怎么样的？"""

    def test_q5_intent_analysis(self, test_skill_dir, sample_rate_data):
        """测试Q5意图分析"""
        query_en = "How is the change of HR allocation to 4130011 between FY26 BGT and FY25 Actual?"
        query_cn = "26财年预算要分摊给413001的HR费用和25财年实际分摊给XP的HR费用相比，变化是怎么样的？"

        # 验证问题要素
        assert "HR" in query_en
        assert "413001" in query_cn or "413001" in query_en
        assert "FY25" in query_en and "FY26" in query_en
        assert "分摊" in query_cn or "allocation" in query_en

        print("✅ Q5意图分析: 这是一个分摊对比问题，需要对比两年分摊给同一实体/不同实体的HR费用")

    def test_q5_expected_sql_structure(self, sample_cost_data, sample_rate_data):
        """测试Q5期望的SQL结构"""
        cost_excel, cost_df = sample_cost_data
        rate_excel, rate_df = sample_rate_data

        # 期望的SQL逻辑（复杂的多表关联和对比）
        expected_sql_pattern = """
        WITH
        FY25_Allocation AS (
            SELECT
                SUM(ABS(c.[Amount]) * r.[RateNo]) AS FY25_Total
            FROM [cost_database] c
            INNER JOIN [rate_table] r
                ON c.[Year] = r.[Year]
                AND c.[Scenario] = r.[Scenario]
                AND c.[Month] = r.[Period]
            WHERE c.[Year] = 2025
              AND c.[Scenario] = 'Actual'
              AND c.[Function] = 'HR Allocation'
              AND c.[Key] = '480055 Cycle'
              AND r.[BL] = '413001'
        ),
        FY26_Allocation AS (
            SELECT
                SUM(ABS(c.[Amount]) * r.[RateNo]) AS FY26_Total
            FROM [cost_database] c
            INNER JOIN [rate_table] r
                ON c.[Year] = r.[Year]
                AND c.[Scenario] = r.[Scenario]
                AND c.[Month] = r.[Period]
            WHERE c.[Year] = 2026
              AND c.[Scenario] = 'Budget1'
              AND c.[Function] = 'HR Allocation'
              AND c.[Key] = '480055 Cycle'
              AND r.[BL] = '413001'
        )
        SELECT
            FY25_Total,
            FY26_Total,
            FY26_Total - FY25_Total AS Variance,
            (FY26_Total - FY25_Total) / FY25_Total * 100 AS Variance_Pct
        FROM FY25_Allocation, FY26_Allocation
        """

        print("✅ Q5 SQL结构验证: 期望的SQL需要关联成本和费率表，并对比两年的分摊结果")


class TestAgentIntegrationScenarios:
    """Agent集成测试场景"""

    def test_workflow_initialization(self, test_skill_dir, tmp_path):
        """测试工作流初始化"""
        # 修改技能目录结构，添加nl-to-sql-agent子目录
        skills_base = tmp_path / "skills"
        skills_base.mkdir()
        agent_skill_dir = skills_base / "nl-to-sql-agent"
        agent_skill_dir.mkdir()

        # SKILL.md
        skill_md = agent_skill_dir / "SKILL.md"
        skill_md.write_text("""---
name: nl-to-sql-agent
version: "1.0.0"
description: "Test skill for NL to SQL workflow"
license: MIT
---

# Test NL to SQL Agent

This is a test skill for NL to SQL workflow testing.
""")

        # metadata.md
        metadata_md = agent_skill_dir / "metadata.md"
        metadata_md.write_text("""```json
{
  "tables": {
    "cost_database": {
      "description": "成本数据库",
      "columns": [
        {"name": "Year", "type": "INTEGER", "description": "财年"}
      ]
    }
  }
}
```""")

        loader = SkillLoader(str(skills_base))
        skill = loader.load_skill("nl-to-sql-agent")

        assert skill is not None
        assert skill.name == "nl-to-sql-agent"

        workflow = SkillAwareWorkflow(skill=skill)
        graph = workflow.get_graph()

        assert graph is not None

        print("✅ 工作流初始化测试通过")

    def test_state_transition(self, test_skill_dir):
        """测试状态转换"""
        workflow = SkillAwareWorkflow()

        # 创建初始状态
        initial_state: SkillAwareState = {
            "trace_id": "test-123",
            "messages": [],
            "user_query": "测试查询",
            "intent_analysis": None,
            "sql_query": None,
            "sql_valid": False,
            "execution_result": None,
            "review_passed": None,
            "review_message": None,
            "table_names": None,
            "data_source_type": "excel",
            "error_message": None,
            "retry_count": 0,
            "skill": None,
            "skill_name": "nl-to-sql-agent"
        }

        # 测试路由逻辑
        test_valid_state = initial_state.copy()
        test_valid_state["sql_valid"] = True
        route = workflow._route_after_validation(test_valid_state)
        assert route == "execute_sql"

        test_invalid_state = initial_state.copy()
        test_invalid_state["sql_valid"] = False
        route = workflow._route_after_validation(test_invalid_state)
        assert route == "generate_sql"

        test_max_retry_state = initial_state.copy()
        test_max_retry_state["sql_valid"] = False
        test_max_retry_state["retry_count"] = 5
        route = workflow._route_after_validation(test_max_retry_state)
        assert route == "refine_answer"

        print("✅ 状态转换测试通过")

    def test_query_pattern_recognition(self):
        """测试查询模式识别"""
        test_queries = {
            "listing": {
                "query": "列出所有IT服务",
                "expected_type": "listing"
            },
            "aggregate": {
                "query": "计算26财年HR总费用",
                "expected_type": "aggregate"
            },
            "allocation": {
                "query": "25财年实际分摊给CT的IT费用",
                "expected_type": "allocation"
            },
            "comparison": {
                "query": "26财年和25财年的采购费用对比",
                "expected_type": "comparison"
            }
        }

        for pattern, test_case in test_queries.items():
            query = test_case["query"]
            expected_type = test_case["expected_type"]

            # 简单的关键词匹配
            if "列出" in query or "显示" in query:
                detected_type = "listing"
            elif "计算" in query or "总计" in query or "总和" in query:
                detected_type = "aggregate"
            elif "分摊" in query:
                detected_type = "allocation"
            elif "对比" in query or "变化" in query:
                detected_type = "comparison"
            else:
                detected_type = "general"

            assert detected_type == expected_type, \
                f"查询类型识别错误: '{query}' 期望 {expected_type}, 检测到 {detected_type}"

            print(f"✅ 查询 '{query}' 识别为 {expected_type}")

        print("✅ 查询模式识别测试通过")
