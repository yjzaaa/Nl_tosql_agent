"""数据源配置交互式工具

提供命令行界面来管理和切换数据源
"""

import sys
from pathlib import Path

from config.data_source_config import (
    load_data_source_config,
    apply_data_source_config,
    get_postgresql_connection_string,
    validate_data_source_config,
    switch_data_source,
    get_current_data_source_info,
    test_data_source_connection
)


def show_help():
    """显示帮助信息"""
    print("""
╔═══════════════════════════════════════════════════════╗
║           数据源配置管理工具 v1.0                     ║
╚═══════════════════════════════════════════════════════╝

使用方法:
    python manage_data_source.py [命令] [选项]

命令:
    status                  显示当前数据源状态
    validate               验证数据源配置
    switch <type>           切换数据源
    connect                测试数据源连接
    info                    显示数据源详细信息
    conn-string              获取连接字符串
    init <type>             初始化配置文件
    list                    列出所有表

数据源类型:
    auto                    自动选择（优先级：PostgreSQL > Excel）
    postgresql             PostgreSQL数据库
    excel                  Excel文件

示例:
    python manage_data_source.py status
    python manage_data_source.py switch postgresql
    python manage_data_source.py connect
    python manage_data_source.py conn-string

配置文件: config_postgres.yaml
""")


def cmd_status():
    """显示数据源状态"""
    print("\n" + "=" * 60)
    print("数据源状态")
    print("=" * 60)
    
    try:
        info = get_current_data_source_info("config_postgres.yaml")
        
        print(f"当前数据源: {info.get('current_strategy', 'Not set')}")
        print(f"数据源可用: {'是' if info.get('is_available', False) else '否'}")
        print()
        
        print("可用数据源:")
        for source in info.get('available_strategies', []):
            available = '✓' if info.get('is_strategy_available', {}).get(source, False) else '✗'
            print(f"  {available} {source}")
        
        print()
        
        if info.get('is_available', False):
            print("⚠️  当前数据源不可用，请尝试切换或检查配置")
        else:
            try:
                metadata = info.get('metadata', {})
                print(f"数据源类型: {metadata.get('source_type', 'Unknown')}")
                
                if 'host' in metadata:
                    print(f"主机: {metadata.get('host', 'Unknown')}")
                if 'database' in metadata:
                    print(f"数据库: {metadata.get('database', 'Unknown')}")
                if 'schema' in metadata:
                    print(f"Schema: {metadata.get('schema', 'public')}")
                
            except Exception as e:
                print(f"获取元数据失败: {e}")
        
        print()
        print("提示:")
        print("  使用 'switch' 命令切换数据源")
        print("  使用 'connect' 命令测试连接")
        print("  使用 'list' 命令列出所有表")
        print("  使用 'conn-string' 命令获取连接字符串")
        
    except Exception as e:
        print(f"\n❌ 获取数据源状态失败: {e}")
    
    print("=" * 60)


def cmd_validate():
    """验证数据源配置"""
    print("\n验证数据源配置...")
    print()
    
    config_path = "config_postgres.yaml"
    
    is_valid = validate_data_source_config(config_path)
    
    if is_valid:
        print("✅ 配置文件有效")
        
        config = load_data_source_config(config_path)
        print(f"数据源类型: {config.get('type', 'Not specified')}")
        
        if config.get('type') == 'postgresql':
            pg_config = config.get('postgresql', {})
            print(f"  主机: {pg_config.get('host', 'localhost')}")
            print(f"  端口: {pg_config.get('port', 5432)}")
            print(f"  数据库: {pg_config.get('database', 'cost_allocation')}")
            print(f"  用户: {pg_config.get('user', 'postgres')}")
            print(f"  Schema: {pg_config.get('schema', 'public')}")
            print(f"  连接池大小: {pg_config.get('pool_size', 5)}")
            print(f"  最大连接数: {pg_config.get('max_overflow', 10)}")
        
        elif config.get('type') == 'excel':
            print("Excel数据源配置完成")
        
        if config.get('table_names'):
            print(f"  表名映射:")
            for table_name, mapped_name in config.get('table_names', {}).items():
                print(f"    {mapped_name}: {table_name}")
        
    else:
        print("❌ 配置文件无效")
        print("  请检查 config_postgres.yaml")
        print()
        print("错误原因：")
        print("  - PostgreSQL配置缺少必需字段")
        print("  - 或配置文件格式错误")


def cmd_switch(strategy_name: str):
    """切换数据源"""
    print(f"\n切换数据源为: {strategy_name}")
    print()
    
    try:
        switch_data_source(strategy_name, "config_postgres.yaml")
    except Exception as e:
        print(f"\n❌ 切换失败: {e}")
        print("\n尝试手动切换:")
        print("  检查配置文件: config_postgres.yaml")
        print("  验证配置: python manage_data_source.py validate")
        print("  重试切换: python manage_data_source.py switch postgresql")


def cmd_connect():
    """测试数据源连接"""
    print("\n测试数据源连接...")
    print()
    
    is_connected = test_data_source_connection("config_postgres.yaml")
    
    if is_connected:
        print("\n✅ 数据源连接成功")
        
        info = get_current_data_source_info("config_postgres.yaml")
        if info.get('is_available'):
            try:
                metadata = info.get('metadata', {})
                if metadata.get('source_type') == 'postgresql':
                    print(f"\nPostgreSQL信息:")
                    print(f"  主机: {metadata.get('host', 'Unknown')}")
                    print(f"  数据库: {metadata.get('database', 'Unknown')}")
                    print(f"  Schema: {metadata.get('schema', 'public')}")
            except Exception as e:
                print(f"获取元数据失败: {e}")
    else:
        print("\n❌ 数据源连接失败")
        print("\n可能的原因:")
        print("   PostgreSQL服务未运行")
        print("  连接信息配置错误")
        print("  防火墙阻止连接")
        print()
        print("解决方法:")
        print("   1. 检查PostgreSQL服务状态")
        print("   2. 检查配置文件: config_postgres.yaml")
        print("   3. 验证连接信息")
        print("   4. 重试测试: python manage_data_source.py connect")


def cmd_info():
    """显示数据源详细信息"""
    print("\n数据源详细信息")
    print("=" * 60)
    print()
    
    try:
        info = get_current_data_source_info("config_postgres.yaml")
        
        print("当前数据源状态:")
        print(f"  类型: {info.get('current_strategy', 'Not set')}")
        print(f"  可用: {'是' if info.get('is_available', False) else '否'}")
        print()
        
        metadata = info.get('metadata', {})
        print("元数据:")
        print(f"  数据源类型: {metadata.get('source_type', 'Unknown')}")
        
        if metadata.get('source_type') == 'postgresql':
            print(f"  主机: {metadata.get('host', 'Unknown')}")
            print(f"  端口: {metadata.get('port', 'Unknown')}")
            print(f"  数据库: {metadata.get('database', 'Unknown')}")
            print(f"  Schema: {metadata.get('schema', 'public')}")
            print(f"  用户: {metadata.get('user', 'Unknown')}")
            print()
            print("可用的表:")
            tables = metadata.get("tables", [])
            for table in tables:
                print(f"  - {table.get('name', table)}")
        
        elif metadata.get('source_type') == 'excel':
            print("  Excel文件路径: {metadata.get('file_path', 'Not specified')}")
            print()
            print("可用的表:")
            tables = metadata.get("tables", [])
            for table in tables:
                print(f"  - {table.get('name', table)}")
        
        print()
        print("上下文信息:")
        context = info.get("context", {})
        print(f"  可用功能: {', '.join(context.get('available_functions', []))}")
        print(f"  可用Key: {', '.join(context.get('available_keys', []))}")
        print(f"  可用场景: {', '.join(context.get('available_scenarios', []))}")
        
    except Exception as e:
        print(f"\n❌ 获取数据源信息失败: {e}")
    
    print("=" * 60)


def cmd_conn_string():
    """显示连接字符串"""
    print("\n连接字符串")
    print("=" * 60)
    print()
    
    try:
        conn_string = get_postgresql_connection_string("config_postgres.yaml")
        
        print(f"PostgreSQL连接字符串:")
        print(f"  {conn_string}")
        print()
        print("连接示例:")
        print(f"  Python: psycopg2.connect('{conn_string}')")
        print(f"  SQLAlchemy: create_engine('{conn_string}')")
        print(f"  命令行: D:\\postgres\\bin\\psql.exe '{conn_string}'")
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 获取连接字符串失败: {e}")


def cmd_init(source_type: str):
    """初始化配置文件"""
    print(f"\n初始化配置文件: {source_type}")
    print()
    
    if source_type not in ['auto', 'postgresql', 'excel']:
        print(f"❌ 无效的数据源类型: {source_type}")
        print("  有效类型: auto, postgresql, excel")
        return
    
    # 创建默认配置
    if source_type == 'postgresql':
        config_content = """# PostgreSQL 配置文件
# 此文件包含PostgreSQL数据源的连接配置

# PostgreSQL连接配置
postgresql:
  type: postgresql
  
  # 数据库连接信息
  host: localhost
  port: 5432
  database: cost_allocation
  user: postgres
  password: "123456"
  schema: public
  
  # 连接池配置
  pool_size: 5
  max_overflow: 10
  pool_timeout: 30
  pool_recycle: 3600
  
  # 超时配置
  connect_timeout: 10
  statement_timeout: 30
  
  # 连接重试
  max_retries: 3
  retry_delay: 1

# Excel配置（备用）
excel:
  type: excel
  file_paths:
    cost_database: ""
    rate_table: ""
    cc_mapping: ""
    cost_text_mapping: ""

# 数据源选择策略
data_source_strategy: auto

# 默认表名映射
table_names:
  cost_database: cost_database
  rate_table: rate_table
  cc_mapping: cc_mapping
  cost_text_mapping: cost_text_mapping

# 数据源优先级
data_source_priority:
  postgresql: 1
  excel: 2
"""
        
        config_file = "config_postgres.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ 已创建配置文件: {config_file}")
        print("\n下一步:")
        print("   1. 验证配置: python manage_data_source.py validate")
        print("  2. 测试连接: python manage_data_source.py connect")
        print("  3. 切换数据源: python manage_data_source.py switch postgresql")
        print("  4. 查看状态: python manage_data_source.py status")
        print("  5. 查看信息: python manage_data_source.py info")
    
    elif source_type == 'excel':
        print("Excel配置使用默认配置")
        print("  请确保配置Excel文件路径")
        print("  在config_postgres.yaml中配置file_paths")


def cmd_list():
    """列出所有表"""
    print("\n数据表列表")
    print("=" * 60)
    print()
    
    try:
        from core.data_sources.tools import list_all_tables, get_table_info
        
        tables = list_all_tables()
        
        if not tables:
            print("未找到任何表")
            return
        
        for i, table in enumerate(tables, 1):
            info = get_table_info(table)
            available = '✓' if info.get('is_available', False) else '✗'
            count = info.get('row_count', 0)
            
            print(f"{available} {i}. {table} ({count} rows)")
        
        print()
        print(f"总计: {len(tables)} 个表")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 列出表失败: {e}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == 'help' or command == '-h' or command == '--help':
        show_help()
    
    elif command == 'status':
        cmd_status()
    
    elif command == 'validate' or command == 'val':
        cmd_validate()
    
    elif command == 'switch':
        if len(sys.argv) < 3:
            print("错误: 请指定数据源类型")
            print("用法: python manage_data_source.py switch <type>")
            print()
            print("数据源类型:")
            print("  auto      - 自动选择（默认）")
            print("  postgresql - PostgreSQL数据库")
            print("  excel     - Excel文件")
            return
        
        cmd_switch(sys.argv[2])
    
    elif command == 'connect' or command == 'conn' or command == 'test':
        cmd_connect()
    
    elif command == 'info' or command == 'i':
        cmd_info()
    
    elif command == 'conn-string' or command == 'cs':
        cmd_conn_string()
    
    elif command == 'init':
        if len(sys.argv) < 3:
            print("错误: 请指定初始化的数据源类型")
            print("用法: python manage_data_source.py init <type>")
            print()
            print("数据源类型:")
            print("  auto      - 自动选择（默认）")
            print("  postgresql - PostgreSQL数据库（推荐）")
            print("  excel     - Excel文件")
            return
        
        cmd_init(sys.argv[2])
    
    elif command == 'list' or command == 'ls':
        cmd_list()
    
    else:
        print(f"未知命令: {command}")
        print("使用 'help' 或 '-h' 查看帮助信息")


if __name__ == "__main__":
    main()
