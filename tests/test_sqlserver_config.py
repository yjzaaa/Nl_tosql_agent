import sys
import os

# 添加项目根目录到 sys.path
sys.path.append(os.getcwd())

from src.core.data_sources.manager import get_data_source_manager
from src.config.settings import get_config

def test_config_structure():
    print("Testing Config Structure...")
    config = get_config()
    print(f"Data Source Type: {config.data_source.type}")
    print(f"MSSQL Host (Default): {config.data_source.mssql_host}")
    print(f"MSSQL Driver (Default): {config.data_source.mssql_driver}")

def test_manager_detection():
    print("\nTesting Manager Detection...")
    manager = get_data_source_manager()
    strategies = manager.list_available_strategies()
    print(f"Available Strategies: {strategies}")
    
    # 尝试切换到 sqlserver (预期失败，因为没装 pyodbc)
    try:
        if "sqlserver" in strategies:
            manager.set_strategy("sqlserver")
            print("Successfully set strategy to sqlserver")
        else:
            print("sqlserver strategy not available (likely missing pyodbc)")
    except Exception as e:
        print(f"Error setting strategy: {e}")

if __name__ == "__main__":
    test_config_structure()
    test_manager_detection()
