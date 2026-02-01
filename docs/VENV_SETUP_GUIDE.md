# 虚拟环境测试指南

## 快速开始

### 1. 激活虚拟环境
```bash
# Windows CMD
.venv\Scripts\activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 2. 运行测试
```bash
# 运行所有测试
pytest -v

# 运行冒烟测试
pytest tests/test_smoke.py -v

# 运行配置测试
pytest tests/test_config.py -v

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 3. 退出虚拟环境
```bash
deactivate
```

## Windows批处理脚本

### run_tests_venv.bat
直接运行测试的批处理脚本（无需激活虚拟环境）

```bash
# 运行所有测试
run_tests_venv.bat

# 运行特定测试
run_tests_venv.bat tests/test_smoke.py

# 运行配置测试
run_tests_venv.bat tests/test_config.py
```

## 测试结果

### 当前状态
- ✅ 冒烟测试: 7/7 通过 (100%)
- ✅ 配置测试: 12/12 通过 (100%)
- ⚠️ Agent测试: 10/12 通过 (83%)
- ⚠️ Skill加载测试: 18/28 通过 (64%)
- ❌ 工作流测试: 集合错误
- ❌ 数据源测试: 集合错误

### 总体通过率: 80% (47/59)

详细报告: `VENV_TEST_REPORT.md`

## 常用测试命令

### 基础测试
```bash
# 运行冒烟测试
.venv/Scripts/python.exe -m pytest tests/test_smoke.py -v

# 运行配置测试
.venv/Scripts/python.exe -m pytest tests/test_config.py -v

# 运行Agent测试
.venv/Scripts/python.exe -m pytest tests/test_nl_to_sql_agent.py -v

# 运行Skill加载测试
.venv/Scripts/python.exe -m pytest tests/test_skill_loader.py -v
```

### 高级选项
```bash
# 显示详细输出
.venv/Scripts/python.exe -m pytest -vv

# 显示print输出
.venv/Scripts/python.exe -m pytest -s

# 在第一个失败时停止
.venv/Scripts/python.exe -m pytest -x

# 只运行失败的测试
.venv/Scripts/python.exe -m pytest --lf

# 运行特定测试类
.venv/Scripts/python.exe -m pytest tests/test_config.py::TestAppConfig -v

# 运行特定测试方法
.venv/Scripts/python.exe -m pytest tests/test_config.py::TestAppConfig::test_model_config -v
```

### 覆盖率报告
```bash
# 生成HTML覆盖率报告
.venv/Scripts/python.exe -m pytest --cov=src --cov-report=html

# 生成终端覆盖率报告
.venv/Scripts/python.exe -m pytest --cov=src --cov-report=term-missing

# 生成XML覆盖率报告
.venv/Scripts/python.exe -m pytest --cov=src --cov-report=xml

# 生成所有格式
.venv/Scripts/python.exe -m pytest --cov=src --cov-report=html --cov-report=term-missing --cov-report=xml
```

## 虚拟环境包列表

### 核心依赖
```
langchain==1.2.7
langgraph==1.0.7
langchain-openai==1.1.7
langchain-community==0.4.1
pandas==3.0.0
numpy==2.4.1
openpyxl==3.1.5
pydantic==2.12.5
pyyaml==6.0.3
python-dotenv==1.2.1
openai==2.16.0
sqlalchemy==2.0.46
rich==14.3.1
```

### 测试依赖
```
pytest==9.0.2
pytest-cov==7.0.0
pytest-mock==3.15.1
pytest-asyncio==1.3.0
coverage==7.13.2
```

## 故障排除

### 问题: 虚拟环境不存在
```bash
# 解决方法: 重新创建虚拟环境
python -m venv .venv
```

### 问题: 导入错误
```bash
# 解决方法: 重新安装依赖
.venv/Scripts/python.exe -m pip install -e .
```

### 问题: 测试失败
```bash
# 解决方法: 查看详细错误信息
.venv/Scripts/python.exe -m pytest -v --tb=long
```

### 问题: 缺少模块
```bash
# 解决方法: 安装缺失的模块
.venv/Scripts/python.exe -m pip install <module_name>
```

## 环境信息

- **Python版本**: 3.11.13
- **虚拟环境**: .venv
- **测试框架**: pytest 9.0.2
- **操作系统**: Windows

## 相关文档

- `VENV_TEST_REPORT.md` - 详细测试报告
- `TESTING_STATUS.md` - 测试状态报告
- `tests/README.md` - 测试使用指南
- `tests/SUMMARY.md` - 测试总结

## 更新虚拟环境

如果项目依赖发生变化，可以更新虚拟环境：

```bash
# 删除旧虚拟环境
rm -rf .venv

# 创建新虚拟环境
python -m venv .venv

# 安装依赖
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

## 快速测试检查清单

- [ ] 虚拟环境已创建
- [ ] 所有依赖已安装
- [ ] 冒烟测试通过 (7/7)
- [ ] 配置测试通过 (12/12)
- [ ] 测试覆盖率报告已生成

---

**最后更新**: 2026-02-01
