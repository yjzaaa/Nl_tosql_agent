# Business Test Cases

本文件记录了 `cost_allocation_test` 技能所覆盖的核心业务测试用例。

## Question 1: IT Service Definition
**Query**: "What services do IT cost include? And what is the allocation key?"
**Expected Logic**:
- Filter `Function = 'IT'`
- Select distinct `Cost text` and `Key`
- 验证是否包含 "7092 GS IT_SW" 等核心服务。

## Question 2: HR Budget Check
**Query**: "What was the HR Cost in FY26 BGT?"
**Expected Logic**:
- Filter `Year='FY26'`, `Scenario='Budget1'`, `Function='HR'`
- Sum `Amount`
- **Target Value**: ~12,054,383

## Question 3: IT Allocation Execution
**Query**: "What was the actual IT cost allocated to CT in FY25?"
**Expected Logic**:
- Join Cost and Rate tables.
- Filter `Year='FY25'`, `Scenario='Actual'`, `Function='IT Allocation'`, `BL='CT'`.
- Calculate `Sum(Amount * Rate)`
- **Target Value**: ~-7,847,136

## Question 4: Procurement Trend
**Query**: "How does Procurement Cost change from FY25 Actual to FY26 BGT?"
**Expected Logic**:
- Compare Sum(Amount) for (FY25, Actual) vs (FY26, Budget1).
- Calculate Diff and Growth Rate.
- **Target Value**: Increase ~96,467 (5%)

## Question 5: HR Allocation Impact
**Query**: "How is the change of HR allocation to 413001 between FY26 BGT and FY25 Actual?"
**Expected Logic**:
- Filter `Function='HR Allocation'`, `CC='413001'`.
- Calculate Allocated Amount (Cost * Rate) for both periods.
- Compare results.
- **Target Value**: Decrease ~24,634 (10.2%)
