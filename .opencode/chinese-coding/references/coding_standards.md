# 中文编码规范 - 编码标准细则

## 1. 注释规范

### 1.1 函数注释

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    函数简短描述（用一句话说明函数功能）
    
    详细描述（可选，说明函数的工作原理和注意事项）
    
    参数:
        param1: 参数1的描述
        param2: 参数2的描述
        
    返回:
        返回值的描述
        
    异常:
        可能抛出的异常类型和原因
    """
    # 函数实现
    pass
```

### 1.2 类注释

```python
class ClassName(BaseClass):
    """
    类的简短描述（用一句话说明类的用途）
    
    详细描述（可选，说明类的功能和使用场景）
    
    属性:
        attr1: 属性1的描述
        attr2: 属性2的描述
    """
    
    def __init__(self, param: Type):
        """初始化方法描述"""
        pass
```

### 1.3 行内注释

```python
# 解释复杂的逻辑或算法
for item in data_list:
    # 过滤掉空值和无效数据
    if item is not None and item > 0:
        processed.append(item)
```

## 2. 命名规范

### 2.1 变量命名

```python
# 推荐 - 描述性强
total_cost_amount = 10000.0          # 总成本金额
user_query_string = "SELECT * FROM"  # 用户查询字符串
is_validation_passed = True          # 是否校验通过

# 不推荐 - 含义不明
tc = 10000.0
uqs = "SELECT * FROM"
ivp = True
```

### 2.2 函数命名

```python
# 推荐 - 动词+描述
def validate_user_input(user_input: str) -> bool:
    """校验用户输入是否合法"""
    pass

def calculate_tax_amount(base_amount: float, rate: float) -> float:
    """计算税额"""
    pass

def fetch_data_from_database(query: str) -> List[Dict]:
    """从数据库获取数据"""
    pass

# 不推荐
def check(inp):
    pass

def calc(t):
    pass
```

### 2.3 常量命名

```python
# 推荐 - 全大写下划线分隔
MAX_RETRY_COUNT = 3                  # 最大重试次数
DEFAULT_TIMEOUT = 30                 # 默认超时时间
SQL_SELECT_KEYWORDS = ["SELECT"]     # SQL SELECT 关键词

# 不推荐
maxRetry = 3
defaultTimeout = 30
selectKeywords = ["SELECT"]
```

## 3. 代码结构规范

### 3.1 导入顺序

```python
# 1. Python 标准库
import os
import json
from typing import Dict, List, Optional
from datetime import datetime

# 2. 第三方库
import pandas as pd
from langchain_core.messages import BaseMessage

# 3. 项目内部模块
from src.config.settings import Settings
from src.core.llm import get_llm
```

### 3.2 代码块组织

```python
# 类定义（包含所有方法和属性）
class DataProcessor:
    """数据处理器 - 负责数据的读取、清洗和转换"""
    
    # 类属性
    VERSION = "1.0.0"
    
    def __init__(self, config: Dict[str, Any]):
        """初始化处理器配置"""
        self.config = config
        self.data = None
    
    def load_data(self, file_path: str) -> bool:
        """加载数据文件"""
        pass
    
    def process(self) -> pd.DataFrame:
        """执行数据处理"""
        pass


# 工具函数
def validate_file_exists(file_path: str) -> bool:
    """验证文件是否存在"""
    pass


def format_currency(amount: float) -> str:
    """格式化货币金额"""
    pass


# 主入口
if __name__ == "__main__":
    processor = DataProcessor({})
    processor.load_data("data.csv")
```

## 4. 错误处理规范

```python
class BusinessError(Exception):
    """业务异常 - 用于处理业务逻辑错误"""
    
    def __init__(self, message: str, error_code: str = None):
        """初始化异常
        
        参数:
            message: 错误描述
            error_code: 错误代码（可选）
        """
        super().__init__(message)
        self.error_code = error_code


def process_with_error_handling(data: Dict) -> Dict:
    """带错误处理的业务逻辑"""
    try:
        # 业务逻辑
        result = do_processing(data)
        return {"success": True, "data": result}
    except BusinessError as e:
        # 业务异常 - 记录并返回
        return {"success": False, "error": str(e)}
    except Exception as e:
        # 系统异常 - 记录详细日志
        logger.error(f"处理失败: {e}")
        return {"success": False, "error": "系统错误"}
```

## 5. 类型注解规范

```python
from typing import Dict, List, Optional, Union, TypedDict


class UserState(TypedDict):
    """用户状态定义"""
    user_id: str                       # 用户ID
    user_name: str                     # 用户名
    permissions: List[str]             # 权限列表
    preferences: Optional[Dict]        # 用户偏好（可选）


def get_user_info(
    user_id: str,
    include_details: bool = False
) -> Union[UserState, Dict]:
    """获取用户信息
    
    参数:
        user_id: 用户ID
        include_details: 是否包含详细信息
        
    返回:
        用户状态字典或详细信息字典
    """
    pass
```

## 6. 配置文件规范

```python
# 配置常量定义
# 所有配置项应放在文件顶部，便于查找和修改

# 数据库配置
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cost_allocation",
    "pool_size": 5,
}

# LLM 配置
LLM_CONFIG = {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.1,
}

# 业务规则配置
BUSINESS_RULES = {
    "max_allocation_rate": 1.0,
    "min_cost_threshold": 0.01,
}
```
