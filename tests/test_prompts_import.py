"""Simple test for promts imports"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 测试导入
try:
    # 方法1: 从promts导入
    from promts import get_graph
    print("Method 1 (from promts): SUCCESS")
    
    # 方法2: 从workflow导入
    from workflow import get_graph
    print("Method 2 (from workflow): SUCCESS")
    
    # 方法3: 从promts导入__init__导入
    from promts import __init__
    print("Method 3 (from promts): SUCCESS")
    
    # 方法4: 使用get_graph_function别名
    from promts import get_graph_function
    print("Method 4 (get_graph_function alias): SUCCESS")
    
    print("\n所有导入方法测试通过！")
    
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Test failed: {e}")
