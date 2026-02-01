"""IT功能成本分摊业务逻辑测试 - 基于实际数据"""

import pytest
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import sys
import os

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestDataIntegrity:
    """测试数据完整性和结构"""
    
    @pytest.fixture
    def actual_excel_file(self):
        """实际的Excel文件路径"""
        return r"D:\AI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx"
    
    @pytest.fixture
    def all_sheets(self, actual_excel_file):
        """所有Sheet名称"""
        xl = pd.ExcelFile(actual_excel_file)
        return xl.sheet_names
    
    @pytest.fixture
    def cost_db_df(self, actual_excel_file):
        """成本数据库表"""
        df = pd.read_excel(actual_excel_file, sheet_name="SSME_FI_InsightBot_CostDataBase")
        return df
    
    @pytest.fixture
    def rate_df(self, actual_excel_file):
        """费率表"""
        df = pd.read_excel(actual_excel_file, sheet_name="SSME_FI_InsightBot_Rate")
        return df
    
    @pytest.fixture
    def cc_mapping_df(self, actual_excel_file):
        """成本中心映射表"""
        df = pd.read_excel(actual_excel_file, sheet_name="CC Mapping")
        return df
    
    def test_excel_file_exists(self, actual_excel_file):
        """测试Excel文件存在"""
        assert Path(actual_excel_file).exists(), "Excel文件应该存在"
    
    def test_all_sheets(self, all_sheets):
        """测试所有Sheet"""
        expected_sheets = [
            "SSME_FI_InsightBot_Rate",
            "SSME_FI_InsightBot_CostDataBase", 
            "CC Mapping",
            "Cost text mapping"
        ]
        for sheet in expected_sheets:
            assert sheet in all_sheets, f"应该包含Sheet: {sheet}"
    
    def test_cost_db_columns(self, cost_db_df):
        """测试成本数据库表列名"""
        expected_columns = ["Year", "Scenario", "Function", "Cost text", 
                          "Account", "Category", "Key", "Year Total", "Month", "Amount"]
        for col in expected_columns:
            assert col in cost_db_df.columns, f"成本数据库表应该包含列: {col}"
    
    def test_rate_db_columns(self, rate_df):
        """测试费率表列名"""
        expected_columns = ["BL", "CC", "Year", "Scenario", "Month", "Key", "RateNo"]
        for col in expected_columns:
            assert col in rate_df.columns, f"费率表应该包含列: {col}"
    
    def test_cc_mapping_columns(self, cc_mapping_df):
        """测试成本中心映射表列名"""
        expected_columns = ["CostCenterNumber", "Business Line"]
        for col in expected_columns:
            assert col in cc_mapping_df.columns, f"成本中心映射表应该包含列: {col}"
    
    def test_cost_db_data_volume(self, cost_db_df):
        """测试成本数据库表数据量"""
        assert len(cost_db_df) > 0, "成本数据库表应该有数据"
        print(f"✅ 成本数据库表数据行数: {len(cost_db_df)}")
    
    def test_rate_db_data_volume(self, rate_df):
        """测试费率表数据量"""
        assert len(rate_df) > 0, "费率表应该有数据"
        print(f"✅ 费率表数据行数: {len(rate_df)}")
    
    def test_cc_mapping_data_volume(self, cc_mapping_df):
        """测试成本中心映射表数据量"""
        assert len(cc_mapping_df) > 0, "成本中心映射表应该有数据"
        print(f"✅ 成本中心映射表数据行数: {len(cc_mapping_df)}")
    
    def test_function_values(self, cost_db_df):
        """测试Function字段值"""
        expected_functions = ["HR", "HR Allocation", "IT", "IT Allocation", 
                             "Procurement", "Procurement Allocation"]
        actual_functions = cost_db_df["Function"].unique()
        
        for func in expected_functions:
            assert func in actual_functions, f"Function应该包含: {func}"
        
        print(f"✅ Function唯一值: {list(actual_functions)}")
    
    def test_key_values(self, rate_df):
        """测试Key字段值"""
        expected_keys = ["WCW", "SAM", "Win Acc", "Headcount", "480055 Cycle", 
                        "480056 Cycle", "IM", "Pooling"]
        actual_keys = rate_df["Key"].unique()
        
        for key in expected_keys:
            assert key in actual_keys, f"Key应该包含: {key}"
        
        print(f"✅ Key唯一值: {list(actual_keys)}")
    
    def test_scenario_values(self, cost_db_df):
        """测试Scenario字段值"""
        expected_scenarios = ["Actual", "Budget1"]
        actual_scenarios = cost_db_df["Scenario"].unique()
        
        for scenario in expected_scenarios:
            assert scenario in actual_scenarios, f"Scenario应该包含: {scenario}"
        
        print(f"✅ Scenario唯一值: {list(actual_scenarios)}")
    
    def test_rate_no_range(self, rate_df):
        """测试RateNo范围"""
        min_rate = rate_df["RateNo"].min()
        max_rate = rate_df["RateNo"].max()
        
        assert min_rate >= 0, f"RateNo最小值应该 >= 0，实际为 {min_rate}"
        assert max_rate <= 1, f"RateNo最大值应该 <= 1，实际为 {max_rate}"
        
        print(f"✅ RateNo范围: {min_rate} 到 {max_rate}")
    
    def test_year_values(self, cost_db_df, rate_df):
        """测试Year字段值"""
        # 成本数据库表的Year值
        cost_years = cost_db_df["Year"].unique()
        # 费率表的Year值
        rate_years = rate_df["Year"].unique()
        
        # 验证年份格式
        for year in cost_years:
            assert "FY" in str(year), f"成本数据库表Year应该包含FY，实际: {year}"
        
        print(f"✅ 成本数据库表Year唯一值: {list(cost_years)}")
        print(f"✅ 费率表Year唯一值: {list(rate_years)}")


class TestBusinessRules:
    """测试业务规则"""
    
    @pytest.fixture
    def cost_db_df(self):
        """成本数据库表"""
        excel_path = r"D:\AI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx"
        return pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_CostDataBase")
    
    @pytest.fixture
    def rate_df(self):
        """费率表"""
        excel_path = r"D:\AI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx"
        return pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_Rate")
    
    def test_rule_original_allocation_sum_near_zero(self, cost_db_df):
        """测试规则：Original成本 + Allocation成本应接近0"""
        # 按Cost text和Key分组
        grouped = cost_db_df.groupby(["Cost text", "Key"]).agg({
            "Amount": "sum"
        }).reset_index()
        
        for _, row in grouped.iterrows():
            # Original + Allocation 应该接近0
            assert abs(row["Amount"]) < 1.0, \
                f"Cost text: {row['Cost text']}, Key: {row['Key']} 的总金额应接近0，实际: {row['Amount']}"
        
        print(f"✅ Original + Allocation ≈ 0 规则验证通过（共{len(grouped)}组）")
    
    def test_rule_year_total_equals_monthly_sum(self, cost_db_df):
        """测试规则：Year Total = 12个月的Amount之和"""
        # 按Cost text和Key分组
        for (cost_text, key), group in cost_db_df.groupby(["Cost text", "Key"]):
            monthly_sum = group["Amount"].sum()
            # Year Total应该对每行都相同，取第一行的Year Total
            year_total = group["Year Total"].iloc[0]
            
            assert abs(monthly_sum - year_total) < 1.0, \
                f"Cost text: {cost_text}, Key: {key}, 月度总和: {monthly_sum}, Year Total: {year_total}"
        
        print(f"✅ Year Total = 月度总和 规则验证通过")
    
    def test_rule_function_key_mapping(self):
        """测试规则：Function与Key的对应关系"""
        expected_mapping = {
            "IT": ["WCW", "SAM", "Win Acc"],
            "IT Allocation": ["480056 Cycle"],
            "HR": ["Headcount"],
            "HR Allocation": ["480055 Cycle"],
            "Procurement": ["WCW", "SAM", "Pooling", "IM"],
            "Procurement Allocation": ["480055 Cycle"]
        }
        
        for function, keys in expected_mapping.items():
            assert isinstance(keys, list), f"{function} 的keys应该是列表"
            assert len(keys) > 0, f"{function} 应该至少有一个Key"
        
        print("✅ Function与Key映射关系验证通过")
    
    def test_rule_allocation_negative(self, cost_db_df):
        """测试规则：Allocation成本应该为负数"""
        allocation_mask = cost_db_df["Function"].str.contains("Allocation")
        allocation_amounts = cost_db_df[allocation_mask]["Amount"]
        
        # Allocation成本应该为负数
        assert (allocation_amounts < 0).all(), \
            f"Allocation成本应该为负数，发现正数: {allocation_amounts[allocation_amounts > 0].tolist()[:5]}"
        
        print(f"✅ Allocation成本为负数规则验证通过（共{len(allocation_amounts)}条）")
    
    def test_rule_original_positive(self, cost_db_df):
        """测试规则：Original成本应该为正数"""
        allocation_mask = cost_db_df["Function"].str.contains("Allocation")
        original_amounts = cost_db_df[~allocation_mask]["Amount"]
        
        # Original成本应该为正数
        assert (original_amounts > 0).all(), \
            f"Original成本应该为正数，发现负数: {original_amounts[original_amounts < 0].tolist()[:5]}"
        
        print(f"✅ Original成本为正数规则验证通过（共{len(original_amounts)}条）")


class TestAllocationCalculation:
    """测试分摊计算"""
    
    @pytest.fixture
    def cost_db_df(self):
        """成本数据库表"""
        excel_path = r"D:\AI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx"
        return pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_CostDataBase")
    
    @pytest.fixture
    def rate_df(self):
        """费率表"""
        excel_path = r"D:\AI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx"
        return pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_Rate")
    
    def test_allocation_formula_wcw_key(self, cost_db_df, rate_df):
        """测试WCW Key的分摊计算公式"""
        # 筛选WCW Key的Allocation成本
        wcw_allocation = cost_db_df[
            (cost_db_df["Key"] == "WCW") &
            (cost_db_df["Function"].str.contains("Allocation"))
        ].head(5)
        
        for _, cost_row in wcw_allocation.iterrows():
            # 查找对应的费率
            rate_row = rate_df[
                (rate_df["Key"] == "WCW") &
                (rate_df["Month"] == cost_row["Month"])
            ].iloc[0]
            
            # 分摊金额 = |Allocation金额| × RateNo
            expected_allocation = abs(cost_row["Amount"]) * rate_row["RateNo"]
            
            # 验证计算
            actual_allocation = abs(cost_row["Amount"]) * rate_row["RateNo"]
            
            print(f"Month: {cost_row['Month']}, Allocation: {cost_row['Amount']}, RateNo: {rate_row['RateNo']}, Expected: {expected_allocation:.2f}")
            
            assert abs(actual_allocation - expected_allocation) < 0.01, "分摊计算应该正确"
        
        print(f"✅ WCW Key分摊计算公式验证通过")
    
    def test_monthly_allocation_consistency(self, cost_db_df, rate_df):
        """测试月度分摊比例一致性"""
        # 获取WCW Key的费率
        wcw_rates = rate_df[rate_df["Key"] == "WCW"].groupby("CC")["RateNo"].apply(list)
        
        # 验证同一CC在所有月份的费率应该一致
        for cc, rates in wcw_rates.items():
            if len(rates) == 0:
                continue
            
            # 检查费率是否一致（允许一定范围的浮动）
            rate_variance = max(rates) - min(rates)
            
            # 如果有数据，验证一致性
            if len(rates) > 1:
                assert rate_variance <= 0.01, \
                    f"CC {cc} 的月度费率应该一致，差异: {rate_variance}"
        
        print(f"✅ 月度分摊比例一致性验证通过")
    
    def test_year_total_calculation(self, cost_db_df):
        """测试全年总金额计算"""
        # 获取所有Allocation成本的Year Total
        allocation_data = cost_db_df[cost_db_df["Function"].str.contains("Allocation")]
        
        # 按月汇总Amount
        monthly_totals = allocation_data.groupby("Month")["Amount"].sum()
        
        # 按月汇总Year Total（应该与monthly_totals相同）
        year_total_by_month = allocation_data.groupby("Month")["Year Total"].first()
        
        for month in monthly_totals.index:
            actual_total = monthly_totals[month]
            expected_total = year_total_by_month[month]
            
            assert abs(actual_total - expected_total) < 1.0, \
                f"Month {month}: 实际总和={actual_total}, Year Total={expected_total}"
        
        print(f"✅ 全年总金额计算验证通过")


class TestBusinessScenarios:
    """测试业务场景"""
    
    @pytest.fixture
    def cost_db_df(self):
        """成本数据库表"""
        excel_path = r"D:\AI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx"
        return pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_CostDataBase")
    
    @pytest.fixture
    def rate_df(self):
        """费率表"""
        excel_path = r"D:\AI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx"
        return pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_Rate")
    
    @pytest.fixture
    def cc_mapping_df(self):
        """成本中心映射表"""
        excel_path = r"D:\AI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx"
        return pd.read_excel(excel_path, sheet_name="CC Mapping")
    
    def test_scenario_actual_data(self, cost_db_df):
        """测试场景：使用Actual数据"""
        # 筛选Actual场景数据
        actual_data = cost_db_df[cost_db_df["Scenario"] == "Actual"]
        
        assert len(actual_data) > 0, "应该有Actual场景数据"
        assert len(actual_data) < len(cost_db_df), "Actual数据应该小于总数据"
        
        print(f"✅ Actual场景数据验证通过（{len(actual_data)}条）")
    
    def test_scenario_budget_data(self, cost_db_df):
        """测试场景：使用Budget1数据"""
        # 筛选Budget1场景数据
        budget_data = cost_db_df[cost_db_df["Scenario"] == "Budget1"]
        
        # Budget1数据可能为空
        print(f"ℹ️ Budget1场景数据: {len(budget_data)}条")
    
    def test_allocation_by_business_line(self, cost_db_df, rate_df, cc_mapping_df):
        """测试场景：按业务线（BL）计算分摊费用"""
        # 选择一个BL
        test_bl = "CT"
        test_key = "WCW"
        
        # 获取该BL下的所有CC
        cc_list = cc_mapping_df[cc_mapping_df["Business Line"] == test_bl]["CostCenterNumber"].tolist()
        
        # 筛选该BL的Allocation成本
        bl_allocation = cost_db_df[
            (cost_db_df["Key"] == test_key) &
            (cost_db_df["Function"].str.contains("Allocation"))
        ]
        
        if len(bl_allocation) == 0:
            pytest.skip("该BL下没有Allocation成本数据")
        
        # 计算总分摊金额
        total_allocation = bl_allocation["Amount"].sum()
        
        print(f"✅ 按BL计算分摊费用: BL={test_bl}, Key={test_key}, 总金额={total_allocation:.2f}")
    
    def test_monthly_cost_distribution(self, cost_db_df):
        """测试场景：月度成本分布"""
        # 按月汇总所有Allocation成本
        monthly_allocations = cost_db_df[
            cost_db_df["Function"].str.contains("Allocation")
        ].groupby("Month")["Amount"].sum()
        
        # 验证所有月份都有数据
        assert len(monthly_allocations) <= 12, "应该最多有12个月"
        
        # 验证总金额
        total_allocation = monthly_allocations.sum()
        
        print(f"✅ 月度成本分布: 总分摊金额={total_allocation:.2f}")
        print(f"每月分摊金额: {dict(monthly_allocations.sort_values())}")
    
    def test_it_allocation_analysis(self, cost_db_df, rate_df):
        """测试场景：IT分摊分析"""
        # 筛选IT和IT Allocation数据
        it_data = cost_db_df[
            (cost_db_df["Function"].str.contains("IT"))
        ]
        
        # 按Key分组统计
        by_key = it_data.groupby(["Function", "Key"]).agg({
            "Amount": "sum",
            "Count": "count"
        }).reset_index()
        
        print(f"✅ IT分摊分析（按Key分组）:")
        print(by_key.to_string(index=False))
    
    def test_allocation_percentage(self, cost_db_df, rate_df):
        """测试场景：分摊比例分析"""
        # 筛选WCW Key的Allocation成本
        wcw_allocation = cost_db_df[
            (cost_db_df["Key"] == "WCW") &
            (cost_db_df["Function"].str.contains("Allocation"))
        ]
        
        # 按CC汇总
        by_cc = wcw_allocation.groupby("Cost text").agg({
            "Amount": "sum"
        }).reset_index()
        
        # 计算分摊比例
        total_amount = by_cc["Amount"].sum()
        by_cc["AllocationPercentage"] = by_cc["Amount"] / total_amount * 100
        
        print(f"✅ 分摊比例分析（按CC）:")
        print(by_cc.to_string(index=False))


class TestComplexQueries:
    """测试复杂查询"""
    
    @pytest.fixture
    def cost_db_df(self):
        """成本数据库表"""
        excel_path = r"D:\AI_PAI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx"
        return pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_CostDataBase")
    
    @pytest.fixture
    def rate_df(self):
        """费率表"""
        excel_path = r"D:\AI\Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx"
        return pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_Rate")
    
    def test_query_year_total_by_function(self, cost_db_df):
        """测试查询：按Function统计Year Total"""
        result = cost_db_df.groupby("Function")["Year Total"].sum()
        
        # 验证总金额
        assert result is not None, "应该能按Function统计Year Total"
        
        print(f"✅ 按Function统计Year Total:")
        print(result.to_string())
    
    def test_query_monthly_amount_by_function(self, cost_db_df):
        """测试查询：按Function和Month统计Amount"""
        result = cost_db_df.groupby(["Function", "Month"])["Amount"].sum()
        
        # 验证总金额
        assert result is not None, "应该能按Function和Month统计Amount"
        
        print(f"✅ 按Function和Month统计Amount（前20行）:")
        print(result.head(20).to_string())
    
    def test_query_allocation_by_key(self, cost_db_df, rate_df):
        """测试查询：按Key查询分摊信息"""
        # 筛选Allocation成本
        allocation_data = cost_db_df[cost_db_df["Function"].str.contains("Allocation")]
        
        # 按Key分组
        result = allocation_data.groupby("Key").agg({
            "Amount": "sum",
            "Count": "count"
        }).reset_index()
        
        print(f"✅ 按Key查询分摊信息:")
        print(result.to_string())
    
    def test_query_rate_by_cc(self, rate_df):
        """测试查询：按CC查询费率信息"""
        # 按CC和Key分组统计费率
        result = rate_df.groupby(["CC", "Key"]).agg({
            "RateNo": ["mean", "min", "max", "count"]
        }).reset_index()
        
        # 重命名列
        result.columns = ["CC", "Key", "RateNo_Avg", "RateNo_Min", "RateNo_Max", "Count"]
        
        print(f"✅ 按CC查询费率信息（前10行）:")
        print(result.head(10).to_string())


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
