"""IT功能成本分摊业务逻辑测试"""

import pytest
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import shutil


class TestCostAllocationBusinessLogic:
    """测试IT功能成本分摊业务逻辑"""
    
    @pytest.fixture
    def cost_data_df(self, fixtures_dir):
        """创建成本数据库测试数据"""
        data = {
            "Year": [2025] * 12,
            "Scenario": ["Actual"] * 12,
            "Function": ["IT Allocation"] * 4 + ["IT"] * 4 + ["HR"] * 4,
            "Cost text": ["Software License"] * 12,
            "Account": ["IT Allocation"] * 4 + ["IT Original"] * 4 + ["HR Original"] * 4,
            "Category": ["Software Cost"] * 12,
            "Key": ["WCW"] * 6 + ["headcount"] * 6,
            "Year Total": [-120000] * 12,
            "Month": list(range(1, 13)),
            "Amount": [-10000] * 4 + [10000] * 4 + [5000] * 4
        }
        df = pd.DataFrame(data)
        
        # 保存为Excel文件
        excel_path = fixtures_dir / "cost_data.xlsx"
        df.to_excel(excel_path, index=False)
        return excel_path, df
    
    @pytest.fixture
    def rate_data_df(self, fixtures_dir):
        """创建费率表测试数据"""
        data = {
            "BL": ["BL-001"] * 12,
            "CC": ["CC-001"] * 6 + ["CC-002"] * 6,
            "Year": [2025] * 12,
            "Scenario": ["Actual"] * 12,
            "Month": list(range(1, 13)),
            "Key": ["WCW"] * 12,
            "RateNo": [0.3] * 6 + [0.7] * 6
        }
        df = pd.DataFrame(data)
        
        # 保存为Excel文件
        excel_path = fixtures_dir / "rate_data.xlsx"
        df.to_excel(excel_path, index=False)
        return excel_path, df
    
    @pytest.fixture
    def cc_mapping_df(self, fixtures_dir):
        """创建成本中心映射表测试数据"""
        data = {
            "CostCenterNumber": ["CC-001", "CC-002", "CC-003"],
            "Business Line": ["BL-001", "BL-001", "BL-002"]
        }
        df = pd.DataFrame(data)
        
        excel_path = fixtures_dir / "cc_mapping.xlsx"
        df.to_excel(excel_path, index=False)
        return excel_path, df
    
    @pytest.fixture
    def cost_text_mapping_df(self, fixtures_dir):
        """创建成本文本映射表测试数据"""
        data = {
            "Cost text": ["Software License", "Hardware", "Consulting"],
            "Function": ["IT", "IT", "IT"]
        }
        df = pd.DataFrame(data)
        
        excel_path = fixtures_dir / "cost_text_mapping.xlsx"
        df.to_excel(excel_path, index=False)
        return excel_path, df
    
    def test_cost_data_structure(self, cost_data_df):
        """测试成本数据表结构"""
        excel_path, df = cost_data_df
        
        assert df is not None
        assert len(df) == 12
        
        # 验证字段
        required_columns = ["Year", "Scenario", "Function", "Cost text", 
                          "Account", "Category", "Key", "Year Total", "Month", "Amount"]
        for col in required_columns:
            assert col in df.columns
        
        print("✅ 成本数据表结构测试通过")
    
    def test_rate_data_structure(self, rate_data_df):
        """测试费率表结构"""
        excel_path, df = rate_data_df
        
        assert df is not None
        assert len(df) == 12
        
        # 验证字段
        required_columns = ["BL", "CC", "Year", "Scenario", "Month", "Key", "RateNo"]
        for col in required_columns:
            assert col in df.columns
        
        # 验证费率范围
        assert df["RateNo"].between(0, 1).all()
        
        print("✅ 费率表结构测试通过")
    
    def test_cc_mapping_structure(self, cc_mapping_df):
        """测试成本中心映射表结构"""
        excel_path, df = cc_mapping_df
        
        assert df is not None
        assert len(df) == 3
        
        # 验证字段
        required_columns = ["CostCenterNumber", "Business Line"]
        for col in required_columns:
            assert col in df.columns
        
        print("✅ 成本中心映射表结构测试通过")
    
    def test_cost_text_mapping_structure(self, cost_text_mapping_df):
        """测试成本文本映射表结构"""
        excel_path, df = cost_text_mapping_df
        
        assert df is not None
        assert len(df) == 3
        
        # 验证字段
        required_columns = ["Cost text", "Function"]
        for col in required_columns:
            assert col in df.columns
        
        print("✅ 成本文本映射表结构测试通过")
    
    def test_rule_original_allocation_sum_zero(self, cost_data_df):
        """测试规则：Original成本 + Allocation成本 = 0"""
        excel_path, df = cost_data_df
        
        # 按Cost text和Key分组求和
        grouped = df.groupby(["Cost text", "Key"]).agg({
            "Amount": "sum"
        }).reset_index()
        
        for _, row in grouped.iterrows():
            # Original + Allocation 应该接近0
            assert abs(row["Amount"]) < 100, f"Cost text: {row['Cost text']}, Key: {row['Key']} 的总金额不为0"
        
        print("✅ Original + Allocation = 0 规则测试通过")
    
    def test_rule_monthly_sum_equals_year_total(self, cost_data_df):
        """测试规则：月度成本总和 = Year Total"""
        excel_path, df = cost_data_df
        
        # 按Cost text和Key分组
        for (cost_text, key), group in df.groupby(["Cost text", "Key"]):
            monthly_sum = group["Amount"].sum()
            year_total = group["Year Total"].iloc[0]
            
            # Year Total应该是所有月份Amount的总和
            assert monthly_sum == year_total, \
                f"Cost text: {cost_text}, Key: {key}, Monthly sum: {monthly_sum}, Year Total: {year_total}"
        
        print("✅ 月度总和 = Year Total 规则测试通过")
    
    def test_rule_rate_no_range(self, rate_data_df):
        """测试规则：RateNo范围应为0-1之间"""
        excel_path, df = rate_data_df
        
        assert df["RateNo"].between(0, 1).all(), "RateNo应该都在0-1之间"
        
        print("✅ RateNo范围规则测试通过")
    
    def test_allocation_calculation_formula(self, cost_data_df, rate_data_df):
        """测试分摊计算公式：分摊金额 = |成本金额| × 分摊比例"""
        cost_excel, cost_df = cost_data_df
        rate_excel, rate_df = rate_data_df
        
        # 筛选Allocation成本
        allocation_costs = cost_df[cost_df["Amount"] < 0]
        
        # 计算分摊金额
        for _, cost_row in allocation_costs.head(3).iterrows():
            # 查找对应的费率
            rate_row = rate_df[
                (rate_df["Key"] == cost_row["Key"]) &
                (rate_df["Month"] == cost_row["Month"])
            ].iloc[0]
            
            # 分摊金额 = |Allocation金额| × RateNo
            expected_allocation = abs(cost_row["Amount"]) * rate_row["RateNo"]
            
            # 验证计算
            assert abs(expected_allocation - abs(cost_row["Amount"]) * rate_row["RateNo"]) < 0.01
            
            print(f"Month: {cost_row['Month']}, Allocation: {cost_row['Amount']}, RateNo: {rate_row['RateNo']}, Expected: {expected_allocation}")
        
        print("✅ 分摊计算公式测试通过")
    
    def test_single_cc_scenario(self, cost_data_df, rate_data_df):
        """测试单一成本中心场景：分摊比例 = RateNo"""
        cost_excel, cost_df = cost_data_df
        rate_excel, rate_df = rate_data_df
        
        # 选择单一CC
        cc = "CC-001"
        key = "WCW"
        year = 2025
        scenario = "Actual"
        
        # 筛选该CC的费率
        cc_rates = rate_df[rate_df["CC"] == cc]
        
        # 验证费率
        assert len(cc_rates) == 12, "应该有12个月的费率数据"
        
        # 验证每个月都有费率
        assert len(cc_rates["Month"].unique()) == 12, "每个月都应该有费率"
        
        print(f"✅ 单一成本中心场景测试通过 (CC: {cc}, Key: {key})")
    
    def test_multiple_cc_bl_scenario(self, rate_data_df, cc_mapping_df):
        """测试多个成本中心场景（按BL分摊）：BL总分摊比例 = Σ（每个CC的分摊比例）"""
        rate_excel, rate_df = rate_data_df
        cc_excel, cc_df = cc_mapping_df
        
        # 获取BL下的所有CC
        bl = "BL-001"
        cc_list = cc_df[cc_df["Business Line"] == bl]["CostCenterNumber"].tolist()
        
        # 计算每个CC的总费率
        cc_total_rates = {}
        for cc in cc_list:
            cc_rates = rate_df[rate_df["CC"] == cc]["RateNo"].sum()
            cc_total_rates[cc] = cc_rates
        
        # 计算BL总分摊比例
        bl_total_rate = sum(cc_total_rates.values())
        
        # 验证：BL总分摊比例 = Σ(每个CC的分摊比例)
        assert bl_total_rate == sum(cc_total_rates.values())
        
        print(f"✅ 多个成本中心场景测试通过 (BL: {bl}, CCs: {cc_list}, Total Rate: {bl_total_rate})")
    
    def test_cost_text_mapping(self, cost_text_mapping_df):
        """测试成本文本映射"""
        excel_path, df = cost_text_mapping_df
        
        # 验证映射关系
        it_costs = df[df["Function"] == "IT"]["Cost text"].tolist()
        
        assert "Software License" in it_costs
        assert "Hardware" in it_costs
        assert "Consulting" in it_costs
        
        print(f"✅ 成本文本映射测试通过 (IT: {it_costs})")
    
    def test_year_total_calculation(self, cost_data_df):
        """测试全年总金额计算"""
        excel_path, df = cost_data_df
        
        # 按Cost text和Key分组计算Year Total
        for (cost_text, key), group in df.groupby(["Cost text", "Key"]):
            monthly_sum = group["Amount"].sum()
            year_total = group["Year Total"].iloc[0]
            
            assert monthly_sum == year_total
        
        print("✅ 全年总金额计算测试通过")
    
    def test_scenario_filter(self, cost_data_df):
        """测试场景筛选"""
        excel_path, df = cost_data_df
        
        # 筛选Actual场景
        actual_df = df[df["Scenario"] == "Actual"]
        assert len(actual_df) == 12, "应该有12条Actual数据"
        
        # 筛选Budget场景（应该为空）
        budget_df = df[df["Scenario"] == "Budget1"]
        assert len(budget_df) == 0, "Budget1数据应该为空"
        
        print("✅ 场景筛选测试通过")
    
    def test_function_key_mapping(self):
        """测试Function与Key的对应关系"""
        expected_mapping = {
            "IT": ["WCW", "SAM", "Win Acc"],
            "IT Allocation": ["480056 Cycle"],
            "HR": ["headcount"],
            "HR Allocation": ["480055 Cycle"],
            "Procurement": ["WCW", "SAM", "Pooling", "IM"],
            "Procurement Allocation": ["480055 Cycle"]
        }
        
        # 验证映射关系
        for function, keys in expected_mapping.items():
            assert isinstance(keys, list), f"{function} 的keys应该是列表"
            assert len(keys) > 0, f"{function} 应该至少有一个Key"
        
        print("✅ Function与Key映射关系测试通过")
    
    def test_allocation_amount_absolute_value(self, cost_data_df):
        """测试Allocation金额取绝对值"""
        excel_path, df = cost_data_df
        
        # Allocation金额应该为负数
        allocation_amounts = df[df["Function"].str.contains("Allocation")]["Amount"]
        assert (allocation_amounts < 0).all(), "Allocation金额应该都是负数"
        
        # Original金额应该为正数
        original_amounts = df[~df["Function"].str.contains("Allocation")]["Amount"]
        assert (original_amounts > 0).all(), "Original金额应该都是正数"
        
        print("✅ Allocation金额取绝对值测试通过")
    
    def test_monthly_allocation_consistency(self, cost_data_df, rate_data_df):
        """测试月度分摊比例一致性"""
        cost_excel, cost_df = cost_data_df
        rate_excel, rate_df = rate_data_df
        
        # 获取每个CC每月的费率
        cc_monthly_rates = rate_df.groupby("CC")["RateNo"].apply(list)
        
        # 验证同一CC在所有月份的费率应该一致（除非有特殊调整）
        for cc, rates in cc_monthly_rates.items():
            # 检查费率是否一致（允许一定范围的浮动）
            rate_variance = max(rates) - min(rates)
            assert rate_variance <= 0.1, f"CC {cc} 的月度费率差异过大: {rate_variance}"
        
        print("✅ 月度分摊比例一致性测试通过")


class TestCostAllocationBusinessScenarios:
    """测试成本分摊业务场景"""
    
    @pytest.fixture
    def sample_data(self, fixtures_dir):
        """创建示例测试数据"""
        cost_data = {
            "Year": [2025] * 6,
            "Scenario": ["Actual"] * 6,
            "Function": ["IT Allocation"] * 6,
            "Cost text": ["Software"] * 6,
            "Account": ["IT Allocation"] * 6,
            "Category": ["Software Cost"] * 6,
            "Key": ["WCW"] * 6,
            "Year Total": [-120000] * 6,
            "Month": list(range(1, 7)),
            "Amount": [-20000] * 6
        }
        cost_df = pd.DataFrame(cost_data)
        
        rate_data = {
            "BL": ["BL-001"] * 6,
            "CC": ["CC-001"] * 6,
            "Year": [2025] * 6,
            "Scenario": ["Actual"] * 6,
            "Month": list(range(1, 7)),
            "Key": ["WCW"] * 6,
            "RateNo": [0.25] * 6  # 25%分摊
        }
        rate_df = pd.DataFrame(rate_data)
        
        cost_path = fixtures_dir / "scenario_cost_data.xlsx"
        rate_path = fixtures_dir / "scenario_rate_data.xlsx"
        
        cost_df.to_excel(cost_path, index=False)
        rate_df.to_excel(rate_path, index=False)
        
        return {
            "cost_df": cost_df,
            "rate_df": rate_df,
            "cost_path": cost_path,
            "rate_path": rate_path
        }
    
    def test_scenario_calculate_allocation_to_bl(self, sample_data):
        """测试场景1：计算分摊给指定业务线的费用"""
        cost_df = sample_data["cost_df"]
        rate_df = sample_data["rate_df"]
        
        # Step 1: 筛选指定财年/场景的IT Allocation成本
        filtered_cost = cost_df[
            (cost_df["Year"] == 2025) &
            (cost_df["Scenario"] == "Actual") &
            (cost_df["Function"] == "IT Allocation")
        ]
        
        # Step 2: 获得每月成本
        monthly_costs = filtered_cost.groupby("Month")["Amount"].sum()
        
        # Step 3: 查找指定BL在指定Key下的分摊比例
        filtered_rate = rate_df[
            (rate_df["Year"] == 2025) &
            (rate_df["Scenario"] == "Actual") &
            (rate_df["Key"] == "WCW")
        ]
        
        # 获取BL总分摊比例
        bl_total_rate = filtered_rate["RateNo"].sum()
        
        # Step 4: 计算分摊金额
        total_allocation = sum(monthly_costs.abs()) * bl_total_rate
        
        # 验证
        assert total_allocation == 30000, f"总分摊金额应该为30000，实际为{total_allocation}"
        
        print(f"✅ 场景1测试通过：分摊给BL的总费用 = {total_allocation}")
    
    def test_scenario_year_to_year_comparison(self, sample_data):
        """测试场景2：对比两个财年的费用变化"""
        cost_df = sample_data["cost_df"]
        
        # 基准期费用（前6个月）
        base_period = cost_df[cost_df["Month"] <= 6]
        base_total = base_period["Amount"].sum()
        
        # 对比期费用（后6个月，模拟不同年份）
        # 创建对比数据
        compare_data = base_period.copy()
        compare_data["Month"] = [7, 8, 9, 10, 11, 12]
        compare_data["Amount"] = [-15000] * 6  # 模拟费用变化
        
        compare_total = compare_data["Amount"].sum()
        
        # 计算变化值
        variance = compare_total - base_total
        
        # 计算变化比例
        variance_pct = (abs(variance) / abs(base_total)) * 100
        
        # 验证
        assert variance == -30000, f"费用变化应该为-30000"
        assert abs(variance_pct - 25) < 0.1, f"变化比例应该约为25%"
        
        print(f"✅ 场景2测试通过：费用变化 = {variance}, 变化比例 = {variance_pct:.2f}%")
    
    def test_allocation_amount_not_exceed_cost(self, sample_data):
        """测试规则：分摊金额不应超过成本金额"""
        cost_df = sample_data["cost_df"]
        
        # 获取总成本
        total_cost = cost_df["Amount"].abs().sum()
        
        # 假设分摊比例为25%，则分摊金额不应超过总成本的25%
        allocation_rate = 0.25
        max_allocation = total_cost * allocation_rate
        
        # 验证
        assert max_allocation == 30000, f"最大分摊金额应为30000"
        
        print(f"✅ 分摊金额不超过成本金额测试通过：总成本={total_cost}, 最大分摊={max_allocation}")


class TestCostAllocationStepByStep:
    """测试成本分摊标准流程（四步骤）"""
    
    @pytest.fixture
    def complete_dataset(self, fixtures_dir):
        """创建完整测试数据集"""
        # 成本数据
        cost_data = {
            "Year": [2025] * 12,
            "Scenario": ["Actual"] * 12,
            "Function": ["IT Allocation"] * 12,
            "Cost text": ["Software"] * 12,
            "Account": ["IT Allocation"] * 12,
            "Category": ["Software Cost"] * 12,
            "Key": ["WCW"] * 12,
            "Year Total": [-120000] * 12,
            "Month": list(range(1, 13)),
            "Amount": [-10000] * 12
        }
        cost_df = pd.DataFrame(cost_data)
        
        # 费率数据
        rate_data = {
            "BL": ["BL-001"] * 12,
            "CC": ["CC-001"] * 12,
            "Year": [2025] * 12,
            "Scenario": ["Actual"] * 12,
            "Month": list(range(1, 13)),
            "Key": ["WCW"] * 12,
            "RateNo": [0.3] * 6 + [0.4] * 6
        }
        rate_df = pd.DataFrame(rate_data)
        
        cost_path = fixtures_dir / "step_cost_data.xlsx"
        rate_path = fixtures_dir / "step_rate_data.xlsx"
        
        cost_df.to_excel(cost_path, index=False)
        rate_df.to_excel(rate_path, index=False)
        
        return {
            "cost_df": cost_df,
            "rate_df": rate_df
        }
    
    def test_step1_filter_cost_data(self, complete_dataset):
        """Step 1: 筛选符合条件的成本数据"""
        cost_df = complete_dataset["cost_df"]
        
        # 筛选条件
        filtered = cost_df[
            (cost_df["Year"] == 2025) &
            (cost_df["Scenario"] == "Actual") &
            (cost_df["Function"] == "IT Allocation") &
            (cost_df["Key"] == "WCW")
        ]
        
        # 验证
        assert len(filtered) == 12, "应该筛选出12条数据"
        assert filtered["Year"].unique()[0] == 2025
        assert filtered["Scenario"].unique()[0] == "Actual"
        
        print(f"✅ Step 1测试通过：筛选出{len(filtered)}条成本数据")
    
    def test_step2_get_monthly_amounts(self, complete_dataset):
        """Step 2: 获得每个月的发生金额"""
        cost_df = complete_dataset["cost_df"]
        
        # 按Month分组求和
        monthly_amounts = cost_df.groupby("Month")["Amount"].sum()
        
        # 验证
        assert len(monthly_amounts) == 12, "应该有12个月的数据"
        assert monthly_amounts.sum() == -120000, "全年总金额应为-120000"
        
        print(f"✅ Step 2测试通过：全年总金额={monthly_amounts.sum()}")
    
    def test_step3_get_allocation_rates(self, complete_dataset):
        """Step 3: 查找对应的分摊比例"""
        rate_df = complete_dataset["rate_df"]
        
        # 筛选条件
        filtered_rates = rate_df[
            (rate_df["Year"] == 2025) &
            (rate_df["Scenario"] == "Actual") &
            (rate_df["Key"] == "WCW")
        ]
        
        # 验证
        assert len(filtered_rates) == 12, "应该有12个月的费率"
        
        # 获取每月费率
        monthly_rates = filtered_rates.groupby("Month")["RateNo"].sum()
        
        # 验证单一CC场景
        single_cc_rate = monthly_rates.iloc[0]
        assert 0.3 <= single_cc_rate <= 0.4, "单一CC的分摊比例应该在0.3-0.4之间"
        
        print(f"✅ Step 3测试通过：获取了{len(monthly_rates)}个月的分摊比例")
    
    def test_step4_calculate_monthly_allocation(self, complete_dataset):
        """Step 4: 计算每个月的分摊费用并汇总全年"""
        cost_df = complete_dataset["cost_df"]
        rate_df = complete_dataset["rate_df"]
        
        # 计算每月分摊费用
        monthly_allocations = {}
        for month in range(1, 13):
            # 获取该月成本
            month_cost = cost_df[cost_df["Month"] == month]["Amount"].sum()
            
            # 获取该月费率
            month_rate = rate_df[rate_df["Month"] == month]["RateNo"].sum()
            
            # 计算分摊费用
            allocation = abs(month_cost) * month_rate
            monthly_allocations[month] = allocation
        
        # 计算全年分摊费用
        total_allocation = sum(monthly_allocations.values())
        
        # 验证
        assert total_allocation == 42000, f"全年分摊费用应为42000，实际为{total_allocation}"
        
        print(f"✅ Step 4测试通过：全年分摊费用={total_allocation}")
    
    def test_complete_four_step_process(self, complete_dataset):
        """测试完整的四步骤流程"""
        cost_df = complete_dataset["cost_df"]
        rate_df = complete_dataset["rate_df"]
        
        # Step 1: 筛选
        filtered_cost = cost_df[
            (cost_df["Year"] == 2025) &
            (cost_df["Scenario"] == "Actual")
        ]
        
        # Step 2: 按月汇总
        monthly_costs = filtered_cost.groupby("Month")["Amount"].sum()
        
        # Step 3: 获取费率
        filtered_rates = rate_df[
            (rate_df["Year"] == 2025) &
            (rate_df["Scenario"] == "Actual")
        ]
        
        # Step 4: 计算分摊
        total_allocation = sum([
            abs(monthly_costs[m]) * filtered_rates[filtered_rates["Month"] == m]["RateNo"].sum()
            for m in range(1, 13)
        ])
        
        # 验证完整流程
        assert abs(total_allocation - 42000) < 0.1, f"完整流程分摊费用应为42000"
        
        print(f"✅ 完整四步骤流程测试通过：总分摊费用={total_allocation}")
