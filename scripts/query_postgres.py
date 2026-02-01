"""查询PostgreSQL数据库并显示统计信息"""

import psycopg2

def main():
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='cost_allocation',
        user='postgres',
        password='123456'
    )
    conn.autocommit = True
    cursor = conn.cursor()

    print('=' * 60)
    print('Database Statistics')
    print('=' * 60)
    print()

    cursor.execute('SELECT COUNT(*) FROM cost_database')
    print(f'Cost Database: {cursor.fetchone()[0]} rows')

    cursor.execute('SELECT COUNT(*) FROM rate_table')
    print(f'Rate Table: {cursor.fetchone()[0]} rows')

    cursor.execute('SELECT COUNT(*) FROM cc_mapping')
    print(f'CC Mapping: {cursor.fetchone()[0]} rows')

    try:
        cursor.execute('SELECT COUNT(*) FROM cost_text_mapping')
        print(f'Cost Text Mapping: {cursor.fetchone()[0]} rows')
    except:
        print(f'Cost Text Mapping: 0 rows (or not created)')

    print()
    print('=' * 60)
    print('Group by Function')
    print('=' * 60)
    print()

    cursor.execute('''
        SELECT 
            function, 
            COUNT(*) as count, 
            SUM(amount) as total 
        FROM cost_database 
        GROUP BY function 
        ORDER BY total DESC
    ''')
    
    for row in cursor.fetchall():
        print(f'  {row[0]:<30} {row[1]:>10} rows, total: {row[2]:>15,.2f}')

    print()
    print('=' * 60)
    print('Group by Key')
    print('=' * 60)
    print()

    cursor.execute('''
        SELECT 
            key, 
            COUNT(*) as count, 
            SUM(amount) as total 
        FROM cost_database 
        GROUP BY key 
        ORDER BY total DESC
    ''')
    
    for row in cursor.fetchall():
        print(f'  {row[0]:<20} {row[1]:>10} rows, total: {row[2]:>15,.2f}')

    print()
    print('=' * 60)
    print('Monthly Summary')
    print('=' * 60)
    print()

    cursor.execute('''
        SELECT 
            month, 
            COUNT(*) as count, 
            SUM(amount) as total 
        FROM cost_database 
        GROUP BY month 
        ORDER BY month
    ''')
    
    for row in cursor.fetchall():
        print(f'  {row[0]:<10} {row[1]:>10} rows, total: {row[2]:>15,.2f}')

    print()
    print('=' * 60)
    print('Allocation vs Original')
    print('=' * 60)
    print()

    cursor.execute('''
        SELECT 
            function,
            SUM(amount) as total
        FROM cost_database
        GROUP BY function
        ORDER BY function
    ''')
    
    for row in cursor.fetchall():
        print(f'  {row[0]:<30} total: {row[1]:>15,.2f}')

    print()
    print('=' * 60)
    print('Rate Summary')
    print('=' * 60)
    print()

    cursor.execute('''
        SELECT 
            key,
            AVG(rate_no) as avg_rate,
            COUNT(*) as count
        FROM rate_table
        GROUP BY key
        ORDER BY avg_rate DESC
    ''')
    
    for row in cursor.fetchall():
        print(f'  {row[0]:<20} avg rate: {row[1]:>10.6f}, count: {row[2]:>10}')

    print()
    print('=' * 60)
    print('Cost Center Count by Business Line')
    print('=' * 60)
    print()

    cursor.execute('''
        SELECT 
            business_line,
            COUNT(*) as count
        FROM cc_mapping
        GROUP BY business_line
        ORDER BY count DESC
    ''')
    
    for row in cursor.fetchall():
        print(f'  {row[0]:<30} {row[1]:>5} cost centers')

    print()
    print('=' * 60)
    print('Sample Cost Data (first 10)')
    print('=' * 60)
    print()

    cursor.execute('''
        SELECT 
            year, 
            month, 
            function, 
            key, 
            amount 
        FROM cost_database 
        ORDER BY ABS(amount) DESC 
        LIMIT 10
    ''')
    
    for row in cursor.fetchall():
        print(f'  Year: {row[0]}, Month: {row[1]}, Function: {row[2]}, Key: {row[3]}, Amount: {row[4]:.2f}')

    print()
    print('=' * 60)
    print('Query Complete')
    print('=' * 60)

    conn.close()

if __name__ == '__main__':
    main()
