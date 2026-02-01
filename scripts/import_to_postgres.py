"""
将Excel数据导入到PostgreSQL数据库的脚本

功能：
1. 读取Excel文件中的数据
2. 连接PostgreSQL数据库
3. 创建表结构
4. 导入数据

使用方法：
    python import_to_postgres.py --excel <excel_path> --db <database_url>

示例：
    python import_to_postgres.py --excel "D:\path\to\data.xlsx" --db "postgresql://user:password@localhost:5432/cost_allocation"
"""

import pandas as pd
import argparse
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Float, Integer, Numeric
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_table_schemas(engine):
    """创建数据库表结构"""
    
    # 成本数据库表
    cost_db_schema = """
    CREATE TABLE IF NOT EXISTS cost_database (
        id SERIAL PRIMARY KEY,
        year VARCHAR(10),
        scenario VARCHAR(50),
        function VARCHAR(100),
        cost_text VARCHAR(500),
        account VARCHAR(200),
        category VARCHAR(200),
        key VARCHAR(100),
        year_total NUMERIC(18, 2),
        month VARCHAR(20),
        amount NUMERIC(18, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_cost_year ON cost_database(year);
    CREATE INDEX IF NOT EXISTS idx_cost_scenario ON cost_database(scenario);
    CREATE INDEX IF NOT EXISTS idx_cost_function ON cost_database(function);
    CREATE INDEX IF NOT EXISTS idx_cost_key ON cost_database(key);
    """
    
    # 费率表
    rate_schema = """
    CREATE TABLE IF NOT EXISTS rate_table (
        id SERIAL PRIMARY KEY,
        bl VARCHAR(100),
        cc VARCHAR(50),
        year VARCHAR(10),
        scenario VARCHAR(50),
        month VARCHAR(20),
        key VARCHAR(100),
        rate_no NUMERIC(10, 6),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_rate_year ON rate_table(year);
    CREATE INDEX IF NOT EXISTS idx_rate_scenario ON rate_table(scenario);
    CREATE INDEX IF NOT EXISTS idx_rate_month ON rate_table(month);
    CREATE INDEX IF NOT EXISTS idx_rate_key ON rate_table(key);
    CREATE INDEX IF NOT EXISTS idx_rate_bl ON rate_table(bl);
    CREATE INDEX IF NOT EXISTS idx_rate_cc ON rate_table(cc);
    """
    
    # 成本中心映射表
    cc_mapping_schema = """
    CREATE TABLE IF NOT EXISTS cc_mapping (
        id SERIAL PRIMARY KEY,
        cost_center_number VARCHAR(50) UNIQUE,
        business_line VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_cc_bl ON cc_mapping(business_line);
    """
    
    # 成本文本映射表
    cost_text_mapping_schema = """
    CREATE TABLE IF NOT EXISTS cost_text_mapping (
        id SERIAL PRIMARY KEY,
        cost_text VARCHAR(500) UNIQUE,
        function VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # 创建所有表
    with engine.connect() as conn:
        logger.info("Creating cost_database table...")
        conn.execute(text(cost_db_schema))
        
        logger.info("Creating rate_table...")
        conn.execute(text(rate_schema))
        
        logger.info("Creating cc_mapping...")
        conn.execute(text(cc_mapping_schema))
        
        logger.info("Creating cost_text_mapping...")
        conn.execute(text(cost_text_mapping_schema))
        
        conn.commit()
    
    logger.info("All tables created successfully!")


def import_excel_to_postgres(excel_path, database_url):
    """将Excel数据导入到PostgreSQL"""
    
    logger.info(f"Reading Excel file: {excel_path}")
    
    # 读取Excel文件
    xl = pd.ExcelFile(excel_path)
    logger.info(f"Available sheets: {xl.sheet_names}")
    
    # 创建数据库引擎
    engine = create_engine(database_url)
    
    try:
        # 创建表结构
        create_table_schemas(engine)
        
        # 导入成本数据库表
        if "SSME_FI_InsightBot_CostDataBase" in xl.sheet_names:
            logger.info("Importing SSME_FI_InsightBot_CostDataBase...")
            cost_df = pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_CostDataBase")
            
            # 重命名列以匹配数据库表
            cost_df.columns = [
                'year', 'scenario', 'function', 'cost_text', 'account',
                'category', 'key', 'year_total', 'month', 'amount'
            ]
            
            # 转换数据类型
            cost_df['year_total'] = pd.to_numeric(cost_df['year_total'], errors='coerce')
            cost_df['amount'] = pd.to_numeric(cost_df['amount'], errors='coerce')
            
            # 导入数据库
            cost_df.to_sql('cost_database', engine, if_exists='append', index=False)
            logger.info(f"Imported {len(cost_df)} rows to cost_database")
        
        # 导入费率表
        if "SSME_FI_InsightBot_Rate" in xl.sheet_names:
            logger.info("Importing SSME_FI_InsightBot_Rate...")
            rate_df = pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_Rate")
            
            # 重命名列
            rate_df.columns = ['bl', 'cc', 'year', 'scenario', 'month', 'key', 'rate_no']
            
            # 转换数据类型
            rate_df['rate_no'] = pd.to_numeric(rate_df['rate_no'], errors='coerce')
            
            # 导入数据库
            rate_df.to_sql('rate_table', engine, if_exists='append', index=False)
            logger.info(f"Imported {len(rate_df)} rows to rate_table")
        
        # 导入成本中心映射表
        if "CC Mapping" in xl.sheet_names:
            logger.info("Importing CC Mapping...")
            cc_df = pd.read_excel(excel_path, sheet_name="CC Mapping")
            
            # 重命名列
            cc_df.columns = ['cost_center_number', 'business_line']
            
            # 导入数据库
            cc_df.to_sql('cc_mapping', engine, if_exists='append', index=False)
            logger.info(f"Imported {len(cc_df)} rows to cc_mapping")
        
        # 导入成本文本映射表
        if "Cost text mapping" in xl.sheet_names:
            logger.info("Importing Cost text mapping...")
            text_df = pd.read_excel(excel_path, sheet_name="Cost text mapping")
            
            # 清理数据（跳过空行和标题行）
            text_df = text_df.dropna(subset=['Cost text'])
            text_df = text_df[text_df['Cost text'] != 'Cost text']
            
            # 重命名列
            text_df.columns = ['cost_text', 'function']
            
            # 导入数据库
            text_df.to_sql('cost_text_mapping', engine, if_exists='append', index=False)
            logger.info(f"Imported {len(text_df)} rows to cost_text_mapping")
        
        logger.info("All data imported successfully!")
        
        # 显示导入统计
        display_import_stats(engine)
        
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        raise


def display_import_stats(engine):
    """显示导入统计信息"""
    
    logger.info("\n=== Import Statistics ===")
    
    with engine.connect() as conn:
        # 成本数据库表统计
        result = conn.execute(text("SELECT COUNT(*) FROM cost_database"))
        logger.info(f"Cost database rows: {result.scalar()}")
        
        # 费率表统计
        result = conn.execute(text("SELECT COUNT(*) FROM rate_table"))
        logger.info(f"Rate table rows: {result.scalar()}")
        
        # 成本中心映射表统计
        result = conn.execute(text("SELECT COUNT(*) FROM cc_mapping"))
        logger.info(f"CC mapping rows: {result.scalar()}")
        
        # 成本文本映射表统计
        result = conn.execute(text("SELECT COUNT(*) FROM cost_text_mapping"))
        logger.info(f"Cost text mapping rows: {result.scalar()}")
        
        # 按Function分组统计
        result = conn.execute(text("""
            SELECT function, COUNT(*) as count 
            FROM cost_database 
            GROUP BY function 
            ORDER BY count DESC
        """))
        logger.info("\nRows by function:")
        for row in result:
            logger.info(f"  {row[0]}: {row[1]}")
        
        # 按Key分组统计
        result = conn.execute(text("""
            SELECT key, COUNT(*) as count 
            FROM cost_database 
            GROUP BY key 
            ORDER BY count DESC
        """))
        logger.info("\nRows by key:")
        for row in result:
            logger.info(f"  {row[0]}: {row[1]}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Import Excel data to PostgreSQL")
    parser.add_argument("--excel", required=True, help="Path to Excel file")
    parser.add_argument("--db", required=True, help="PostgreSQL database URL")
    parser.add_argument("--create-db", action="store_true", help="Create database if not exists")
    
    args = parser.parse_args()
    
    # 检查Excel文件
    excel_path = Path(args.excel)
    if not excel_path.exists():
        logger.error(f"Excel file not found: {excel_path}")
        sys.exit(1)
    
    logger.info(f"Starting import from: {excel_path}")
    logger.info(f"Target database: {args.db}")
    
    try:
        import_excel_to_postgres(str(excel_path), args.db)
        logger.info("\n✅ Import completed successfully!")
    except Exception as e:
        logger.error(f"\n❌ Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
