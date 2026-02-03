# 中文编码规范 - 命名约定

## 1. 通用命名原则

### 1.1 清晰性优先

```python
# 推荐 - 名称清晰表达意图
monthly_revenue_total = 50000.0       # 月度总收入
user_authentication_status = True     # 用户认证状态

# 不推荐 - 缩写过度，难以理解
mrt = 50000.0
uas = True
```

### 1.2 长度适中

```python
# 推荐 - 长度适中，既不太长也不太短
data_source = "postgresql"            # 数据源
query_result = df.to_dict()           # 查询结果

# 不推荐 - 过短
ds = "postgresql"
qr = df.to_dict()

# 不推荐 - 过长
the_data_source_that_we_are_connected_to = "postgresql"
the_final_result_of_the_query_execution_returned_as_dataframe = df.to_dict()
```

## 2. 命名风格

### 2.1 变量命名 - snake_case

```python
# 常规变量
user_name = "张三"
order_amount = 1500.0
is_active = True

# 集合类型（使用复数或集合后缀）
user_list = [1, 2, 3]                 # 用户列表
data_dict = {"key": "value"}          # 数据字典
item_set = {1, 2, 3}                  # 项目集合

# 标志位
has_error = False                     # 是否有错误
is_enabled = True                     # 是否启用
need_validation = True                # 是否需要校验
```

### 2.2 常量命名 - UPPER_SNAKE_CASE

```python
# 数值常量
MAX_RETRY_COUNT = 3                   # 最大重试次数
DEFAULT_TIMEOUT = 30                  # 默认超时
PI_VALUE = 3.14159                    # 圆周率

# 字符串常量
DATABASE_DRIVER = "postgresql"        # 数据库驱动
ERROR_PREFIX = "[ERROR]"              # 错误前缀
SQL_SELECT = "SELECT"                 # SQL 关键词

# 集合常量
VALID_STATUS_CODES = [200, 201, 202]  # 有效状态码
ALLOWED_OPERATIONS = ["create", "read"]  # 允许操作
```

### 2.3 函数命名 - snake_case + 动词

```python
# 获取类
def get_user_info(user_id: str) -> Dict:
    """获取用户信息"""
    pass

def fetch_data_from_db(query: str) -> pd.DataFrame:
    """从数据库获取数据"""
    pass

def retrieve_config(key: str) -> Any:
    """检索配置项"""
    pass

# 检查类
def validate_input(data: Dict) -> bool:
    """校验输入数据"""
    pass

def check_permission(user_id: str, resource: str) -> bool:
    """检查权限"""
    pass

def is_valid_email(email: str) -> bool:
    """验证邮箱格式"""
    pass

# 执行类
def execute_query(sql: str) -> List[Dict]:
    """执行查询"""
    pass

def process_payment(order_id: str, amount: float) -> bool:
    """处理支付"""
    pass

def generate_report(data: pd.DataFrame) -> str:
    """生成报表"""
    pass

# 转换类
def convert_to_currency(amount: float) -> str:
    """转换为货币格式"""
    pass

def format_date(timestamp: int) -> str:
    """格式化日期"""
    pass

def serialize_to_json(obj: Any) -> str:
    """序列化为 JSON"""
    pass
```

### 2.4 类命名 - PascalCase

```python
class DataProcessor:
    """数据处理器"""
    pass

class UserAuthenticationManager:
    """用户认证管理器"""
    pass

class CostAllocationCalculator:
    """成本分摊计算器"""
    pass

class SQLQueryBuilder:
    """SQL 查询构建器"""
    pass

class ResultFormatter:
    """结果格式化器"""
    pass
```

### 2.5 私有成员命名

```python
class DataManager:
    """数据管理器"""
    
    def __init__(self):
        # 私有属性（单下划线前缀）
        self._connection = None       # 数据库连接
        self._cache = {}              # 缓存字典
        
    def _establish_connection(self):
        """建立数据库连接（私有方法）"""
        pass
    
    def _get_from_cache(self, key: str) -> Any:
        """从缓存获取数据（私有方法）"""
        pass
```

## 3. 特定领域命名

### 3.1 数据库相关

```python
# 表名常量
COST_DATABASE_TABLE = "SSME_FI_InsightBot_CostDataBase"
RATE_TABLE = "SSME_FI_InsightBot_Rate"

# 字段名
cost_amount_field = "Amount"
allocation_key_field = "Allocation Key"
function_name_field = "Function"

# 查询相关
sql_query = "SELECT * FROM table"     # SQL 查询语句
query_parameters = {"year": "FY26"}    # 查询参数
result_set = []                        # 结果集
```

### 3.2 业务逻辑相关

```python
# 成本分摊
cost_amount = 10000.0                  # 成本金额
allocation_rate = 0.5                  # 分摊系数
allocated_amount = 5000.0              # 分摊金额

# 预算相关
budget_amount = 100000.0               # 预算金额
actual_amount = 80000.0                # 实际金额
budget_variance = 20000.0              # 预算差异

# 统计相关
total_count = 100                      # 总数量
average_value = 50.0                   # 平均值
running_total = []                     # 累计值列表
```

### 3.3 状态和标志

```python
# 处理状态
is_processing = False                  # 是否正在处理
has_completed = True                   # 是否已完成
is_pending_review = False              # 待审核

# 验证状态
is_valid = True                        # 是否有效
validation_passed = True               # 校验通过
error_occurred = False                 # 是否发生错误

# 数据状态
is_empty = False                       # 是否为空
is_dirty = False                       # 是否有未保存的更改
is_stale = False                       # 数据是否过期
```

## 4. 避免的命名模式

### 4.1 避免单字母名称（循环变量除外）

```python
# 不推荐
d = {"key": "value"}
n = 100

# 推荐
data_dict = {"key": "value"}
item_count = 100

# 循环变量可以使用单字母
for i in range(10):
    pass
```

### 4.2 避免 Python 关键字

```python
# 不推荐
class = "my_class"         # 使用 class_ 替代
list_items = []            # 使用 list_values 替代

# 推荐
class_name = "my_class"
list_items = []
```

### 4.3 避免魔法数字

```python
# 不推荐
if status == 1:    # 1 是什么意思？
    pass

# 推荐 - 使用具名常量
STATUS_ACTIVE = 1
STATUS_INACTIVE = 2

if status == STATUS_ACTIVE:
    pass
```
