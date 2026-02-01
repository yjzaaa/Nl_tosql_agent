"""数据源策略模式测试脚本

测试PostgreSQL数据源的完整功能
"""

import sys
import os
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_postgresql_data_source():
    """测试PostgreSQL数据源"""
    print("=" * 60)
    print("测试 1: PostgreSQL数据源基本功能")
    print("=" * 60)
    print()
    
    try:
        from core.data_sources.postgres_source import PostgreSQLDataSource
        
        # 创建PostgreSQL数据源
        pg_source = PostgreSQLDataSource()
        
        # 测试连接字符串
        print("测试连接字符串...")
        conn_string = pg_source._get_connection_string()
        print(f"  连接字符串: {conn_string}")
        print(f"  连接成功: {pg_source.is_available()}")
        print()
        
        # 测试元数据
        print("测试元数据...")
        metadata = pg_source.get_metadata()
        print(f"  数据源类型: {metadata['source_type']}")
        print(f"  主机: {metadata['host']}")
        print(f"  端口: {metadata['port']}")
        print(f"  数据库: {metadata['database']}")
        print(f"  Schema: {metadata['schema']}")
        print(f"  表名: {metadata['tables']}")
        print()
        
        # 测试上下文
        print("测试上下文信息...")
        context = pg_source.get_context()
        print(f"  数据源类型: {context.get('data_source_type')}")
        print(f"  数据库: {context.get('database')}")
        print()
        
        # 检查上下文信息
        if 'available_functions' in context:
            print(f"  可用功能: {', '.join(context.get('available_functions', []))}")
        if 'available_keys' in context:
            print(f"  可用Keys: {', '.join(context.get('available_keys', []))}")
        if 'available_scenarios' in context:
            print(f"  可用场景: {', '.join(context.get('available_scenarios', []))}")
        print()
        
        # 测试表结构
        print("测试表结构...")
        schema_info = pg_source.get_schema_info(['cost_database', 'rate_table'])
        print(schema_info[:500])  # 只显示前500行
        print()
        
        # 测试加载数据
        print("测试加载数据...")
        df_cost = pg_source.load_data('cost_database', limit=5)
        print(f"  Cost Database (前5行）:")
        print(df_cost[['year', 'month', 'function', 'key', 'amount']].to_string(index=False))
        print()
        
        # 测试费率表
        print("测试费率表数据...")
        df_rate = pg_source.load_data('rate_table', limit=5)
        print(f"  Rate Table (前5行）:")
        print(df_rate[['bl', 'cc', 'year', 'month', 'key', 'rate_no']].to_string(index=False))
        print()
        
        print("✅ PostgreSQL数据源测试通过！")
        print()
        
    except Exception as e:
        print(f"❌ PostgreSQL数据源测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print()


def test_data_source_manager():
    """测试数据源管理器"""
    print("=" * 60)
    print("测试 2: 数据源管理器")
    print("=" * 60)
    print()
    
    try:
        from core.data_sources.manager import get_data_source_manager
        
        # 获取管理器
        manager = get_data_source_manager()
        
        # 检查可用策略
        print("测试可用策略...")
        available = manager.list_available_strategies()
        print(f"  可用策略: {', '.join(available)}")
        print()
        
        # 检查当前策略
        current = manager.get_strategy()
        print(f"  当前策略: {current.get_strategy_name() if current else 'None'}")
        print(f"  可用: {manager.is_available()}")
        print()
        
        # 测试获取上下文
        print("测试获取数据源上下文...")
        context = manager.get_context()
        print(f"  数据源类型: {context.get('data_source_type', 'Unknown')}")
        print(f"  数据库: {context.get('database', 'Unknown')}")
        print()
        
        # 测试元数据
        print("测试获取元数据...")
        metadata = manager.get_metadata()
        print(f"  元数据: {metadata}")
        print()
        
        print("✅ 数据源管理器测试通过！")
        print()
        
    except Exception as e:
        print(f"❌ 数据源管理器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print()


def test_data_source_tools():
    """测试数据源工具函数"""
    print("=" * 60)
    print("测试 3: 数据源工具函数")
    print("=" * 60)
    print()
    
    try:
        from core.data_sources.tools import (
            get_current_data_source_info,
            switch_data_source,
            list_available_data_sources,
            load_data_source_data,
            get_data_source_metadata,
            get_data_source_context,
            execute_data_source_query
        )
        
        # 测试显示状态
        print("测试显示数据源状态...")
        display_data_source_status()
        print()
        
        # 测试列出所有数据源
        print("测试列出所有数据源...")
        sources = list_available_data_sources()
        print(f"  可用数据源: {', '.join(sources)}")
        print()
        
        # 测试获取上下文
        print("测试获取数据源上下文...")
        context = get_data_source_context()
        print(f"  数据源类型: {context.get('data_source_type', 'Unknown')}")
        print(f"  数据库: {context.get('database', 'Unknown')}")
        print(f"  可用功能: {', '.join(context.get('available_functions', []))}")
        print()
        
        # 测试列出表
        print("测试列出所有表...")
        tables = list_all_tables()
        print(f"  表名: {', '.join(tables)}")
        print()
        
        # 测试表信息
        for table in tables[:3]:
            info = get_table_info(table)
            print(f"表 {table}: {info.get('row_count', 0)} 行, 可用: {info.get('is_available', False}")
        print()
        
        # 测试成本汇总
        print("测试获取成本汇总...")
        cost_summary = get_cost_summary()
        print(f"  成本汇总: {len(cost_summary.get('by_function', []))} 个功能组")
        print(f"  成本汇总: {len(cost_summary.get('by_key', []))} 个Key组")
        print()
        
        # 测试费率汇总
        print("测试获取费率汇总...")
        rate_summary = get_rate_summary()
        print(f"  费率汇总: {len(rate_summary.get('by_key', []))} 个Key组")
        print(f"  费率汇总: {len(rate_summary.get('by_business_line', []))} 个业务线组")
        print()
        
        print("✅ 数据源工具测试通过！")
        print()
        
    except Exception as e:
        print(f"❌ 数据源工具测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print()


def test_switch_strategy():
    """测试切换数据源"""
    print("=" * 60)
    print("测试 4: 切换数据源")
    print("=" * 60)
    print()
    
    try:
        from core.data_sources.tools import switch_data_source, list_available_data_sources
        
        # 列出所有数据源
        sources = list_available_data_sources()
        print(f"可用数据源: {', '.join(sources)}")
        print()
        
        for source in sources:
            if source not in ['excel', 'postgresql', 'auto']:
                print(f"跳过未知的数据源: {source}")
                continue
            
            print(f"切换到数据源: {source}...")
            switch_data_source(source)
            
            # 验证切换结果
            context = get_data_source_context()
            print(f"  当前数据源: {context.get('data_source_type', 'Unknown')}")
            print(f"  数据库: {context.get('database', 'Unknown')}")
            print()
            
            # 显示状态
            display_data_source_status()
            print()
    
        print("✅ 数据源切换测试通过！")
    except Exception as e:
        print(f"❌ 数据源切换测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print()


def test_sql_execution():
    """测试SQL执行"""
    print("=" * 60)
    print("测试 5: SQL查询执行")
    print("=" * 60)
    print()
    
    try:
        from core.data_sources.tools import execute_data_source_query, get_current_data_source_info
        
        # 显示当前数据源信息
        info = get_current_data_source_info()
        print(f"当前数据源类型: {info.get('current_strategy', 'Not set'}")
        print(f"数据源可用: {info.get('is_available', False)}")
        print()
        
        if not info.get('is_available'):
            print("数据源不可用，尝试切换到postgresql...")
            from core.data_sources.tools import switch_data_source
            switch_data_source("postgresql")
            info = get_current_data_source_info()
        
        if not info.get('is_available'):
            print("切换失败，数据源仍不可用")
            return
        
        print(f"当前数据源: {info.get('current_strategy')}")
        print()
        
        # 测试简单查询
        print("测试简单查询...")
        query = "SELECT * FROM cost_database LIMIT 5"
        print(f"SQL: {query}")
        df = execute_data_source_query(query)
        print(f"查询结果（前5行）:")
        print(df.to_string(index=False))
        print()
        
        # 测试汇总查询
        print("测试汇总查询...")
        summary = get_cost_summary()
        print(f"By Function (前5个）:")
        by_func = summary.get('by_function', [])
        for item in by_func[:5]:
            print(f"  {item['function']}: {item['total_amount']:,.2f}")
        print()
        
    except Exception as e:
        print(f"❌ SQL执行测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print()


def test_business_rules():
    """测试业务规则验证"""
    print("=" * 60)
    print("测试 6: 业务规则验证")
    print("=" * 60)
    print()
    
    try:
        from core.data_sources.tools import get_data_source_context, list_available_functions, list_available_keys, list_available_scenarios
        
        # 获取上下文
        context = get_data_source_context()
        
        print("业务规则验证:")
        print()
        
        # 验证1: Original + Allocation ≈ 0
        cost_summary = get_cost_summary()
        original_total = 0
        allocation_total = 0
        
        for item in cost_summary.get('by_function', []):
            if 'Allocation' not in item['function']:
                original_total += item['total_amount']
            else:
                allocation_total += item['total_amount']
        
        print(f"  Original成本总额: {original_total:,.2f}")
        print(f"  Allocation成本总额: {allocation_total:,.2f}")
        print(f"  差异: {abs(original_total + allocation_total):,.2f}")
        
        if abs(original_total + allocation_total) < 1.0:
            print("✅ 业务规则验证通过：Original + Allocation ≈ 0")
        else:
            print("⚠️  业务规则可能不满足：Original + Allocation ≠ 0")
        print()
        
        # 验证2: Function类型
        print("验证Function类型:")
        functions = list_available_functions()
        print(f"  可用功能: {', '.join(functions)}")
        print()
        
        # 验证3: Key类型
        print("验证Key类型:")
        keys = list_available_keys()
        print(f"  可用Keys: {', '.join(keys)}")
        print()
        
        # 验证4: 场景类型
        print("验证场景类型:")
        scenarios = list_available_scenarios()
        print(f"  可用场景: {', '.join(scenarios)}")
        print()
        
        print("✅ 业务规则验证完成")
        print()
        
    except Exception as e:
        print(f"❌ 业务规则验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print()


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("PostgreSQL数据源策略模式测试套件")
    print("=" * 60)
    print()
    print("开始时间: 2026-02-01")
    print()
    
    # 运行所有测试
    test_postgresql_data_source()
    test_data_source_manager()
    test_data_source_tools()
    test_switch_strategy()
    test_sql_execution()
    test_business_rules()
    
    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)
    print()


if __name__ == "__main__":
    run_all_tests()
