"""数据源工具模块

提供数据源策略的实用工具函数
"""

from typing import Dict, Any, Optional, List
import pandas as pd

from .manager import get_data_source_manager, reset_data_source_manager


def get_current_data_source_info() -> Dict[str, Any]:
    """
    获取当前数据源信息
    
    Returns:
        包含数据源信息的字典
    """
    manager = get_data_source_manager()
    return manager.get_status()


def switch_data_source(strategy_name: str) -> None:
    """
    切换数据源策略
    
    Args:
        strategy_name: 策略名称 (excel, postgresql, auto)
    """
    manager = get_data_source_manager()
    manager.set_strategy(strategy_name)
    print(f"已切换到数据源: {strategy_name}")


def list_available_data_sources() -> List[str]:
    """
    列出所有可用的数据源
    
    """
    manager = get_data_source_manager()
    sources = manager.list_available_strategies()
    
    print("可用的数据源:")
    for i, source in enumerate(sources, 1):
        status = "✓" if manager.is_strategy_available(source) else "✗"
        print(f"  {status} {i}. {source}")
    
    return sources


def load_data_source_data(table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
    """
    从当前数据源加载表数据
    
    Args:
        table_name: 表名
        limit: 限制行数
        
    Returns:
        包含数据的DataFrame
    """
    manager = get_data_source_manager()
    
    if manager.get_strategy_name() == "excel":
        # Excel数据源需要文件路径
        print(f"从Excel加载表: {table_name}")
        return manager.load_data(table_name=table_name, limit=limit)
    else:
        print(f"从PostgreSQL加载表: {table_name}")
        return manager.load_data(table_name=table_name, limit=limit)


def get_data_source_metadata() -> Dict[str, Any]:
    """
    获取当前数据源的元数据
    
    Returns:
        包含元数据的字典
    """
    manager = get_data_source_manager()
    return manager.get_metadata()


def get_data_source_context() -> Dict[str, str]:
    """
    获取当前数据源的上下文信息
    
    Returns:
        包含上下文信息的字典
    """
    manager = get_data_source_manager()
    return manager.get_context()


def execute_data_source_query(query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    在当前数据源中执行查询
    
    Args:
        query: SQL查询语句
        params: 查询参数
        
    Returns:
        包含查询结果的DataFrame
    """
    manager = get_data_source_manager()
    return manager.execute_query(query, params=params)


def get_cost_summary() -> Dict[str, Any]:
    """
    获取成本汇总信息
    
    Returns:
        包含成本汇总的字典
    """
    manager = get_data_source_manager()
    return manager.get_cost_summary()


def get_rate_summary() -> Dict[str, Any]:
    """
    获取费率汇总信息
    
    Returns:
        包含费率汇总的字典
    """
    manager = get_data_source_manager()
    return manager.get_rate_summary()


def calculate_business_allocation(
    business_line: Optional[str] = None,
    key: Optional[str] = None,
    year: Optional[str] = None,
    scenario: Optional[str] = None
) -> pd.DataFrame:
    """
    计算业务分摊
    
    Args:
        business_line: 业务线
        key: 分摊依据
        year: 年份
        scenario: 场景
        
    Returns:
        包含分摊结果的DataFrame
    """
    manager = get_data_source_manager()
    kwargs = {}
    
    if business_line:
        kwargs["business_line"] = business_line
    if key:
        kwargs["key"] = key
    if year:
        kwargs["year"] = year
    if scenario:
        kwargs["scenario"] = scenario
    
    return manager.calculate_allocation(**kwargs)


def display_data_source_status() -> None:
    """
    显示数据源状态
    """
    print("=" * 60)
    print("数据源状态")
    print("=" * 60)
    
    status = get_current_data_source_info()
    
    print(f"当前数据源: {status.get('current_strategy', 'Not set')}")
    print(f"数据源可用: {'是' if status.get('is_available', False) else '否'}")
    print()
    
    print("可用数据源:")
    for source in status.get('available_strategies', []):
        available = '✓' if status.get('is_strategy_available', {}).get(source, False) else '✗'
        print(f"  {available} {source}")
    
    print()
    
    if status.get('is_available', False):
        print("当前数据源不可用，请切换到其他数据源")
    else:
        print(f"数据源类型: {status.get('current_strategy', 'Unknown')}")
        
        try:
            metadata = get_data_source_metadata()
            print(f"数据源: {metadata.get('source_type', 'Unknown')}")
            
            if 'host' in metadata:
                print(f"主机: {metadata.get('host', 'Unknown')}")
            if 'database' in metadata:
                print(f"数据库: {metadata.get('database', 'Unknown')}")
        except Exception as e:
            print(f"获取元数据失败: {e}")
    
    print("=" * 60)


def validate_data_source() -> bool:
    """
    验证当前数据源是否可用
    
    Returns:
        数据源是否可用
    """
    manager = get_data_source_manager()
    return manager.is_available()


def get_table_info(table_name: str) -> Dict[str, Any]:
    """
    获取表信息
    
    Args:
        table_name: 表名
        
    Returns:
        包含表信息的字典
    """
    manager = get_data_source_manager()
    
    info = {
        "table_name": table_name,
        "row_count": manager.get_table_row_count(table_name),
        "is_available": False
    }
    
    if info["row_count"] > 0:
        info["is_available"] = True
    
    return info


def list_all_tables() -> List[str]:
    """
    列出所有可用的表
    
    Returns:
        表名列表
    """
    manager = get_data_source_manager()
    
    try:
        metadata = manager.get_metadata()
        tables = metadata.get("tables", [])
        return [table.get("name", table) for table in tables]
    except Exception:
        return []


def list_available_functions() -> List[str]:
    """
    列出所有可用的功能
    
    Returns:
        功能名称列表
    """
    try:
        context = get_data_source_context()
        return context.get("available_functions", [])
    except Exception:
        return []


def list_available_keys() -> List[str]:
    """
    列出所有可用的分摊依据
    
    Returns:
        分摊依据名称列表
    """
    try:
        context = get_data_source_context()
        return context.get("available_keys", [])
    except Exception:
        return []


def list_available_scenarios() -> List[str]:
    """
    列出所有可用的场景
    
    Returns:
        场景名称列表
    """
    try:
        context = get_data_source_context()
        return context.get("available_scenarios", [])
    except Exception:
        return []


if __name__ == "__main__":
    # 测试代码
    print("Testing data source tools")
    
    display_data_source_status()
    print()
    
    print("列出可用数据源:")
    list_available_data_sources()
    print()
    
    print("列出可用表:")
    tables = list_all_tables()
    for table in tables:
        info = get_table_info(table)
        print(f"  {table}: {info['row_count']} rows, available: {info['is_available']}")
    
    print()
    
    print("列出可用功能:")
    functions = list_available_functions()
    print(f"  {', '.join(functions)}")
    
    print()
    
    print("列出可用Keys:")
    keys = list_available_keys()
    print(f"  {', '.join(keys)}")
    
    print()
    
    print("列出可用场景:")
    scenarios = list_available_scenarios()
    print(f"  {', '.join(scenarios)}")
    
    print()
    
    print("成本汇总:")
    summary = get_cost_summary()
    print(f"  按Function: {len(summary.get('by_function', []))} groups")
    print(f"  按Key: {len(summary.get('by_key', []))} groups")
    print(f"  按月: {len(summary.get('by_month', []))} groups")
    
    print()
    print("费率汇总:")
    rate_summary = get_rate_summary()
    print(f"  按Key: {len(rate_summary.get('by_key', []))} groups")
    print(f"  按业务线: {len(rate_summary.get('by_business_line', []))} groups")
