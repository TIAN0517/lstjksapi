import psycopg2
import pytest
import os

# 資料庫連線配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 35432,
    'database': 'bossjy_huaqiao',
    'user': 'jytian',
    'password': 'ji394su3'
}

@pytest.fixture(scope="module")
def db_connection():
    """建立資料庫連線"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except Exception as e:
        pytest.fail(f"無法建立資料庫連線: {e}")
    finally:
        if conn:
            conn.close()

@pytest.fixture(scope="function")
def db_cursor(db_connection):
    """建立資料庫游標"""
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()

def test_database_connection(db_connection):
    """測試資料庫連線"""
    try:
        cursor = db_connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        assert version is not None
        cursor.close()
    except Exception as e:
        pytest.fail(f"資料庫連線測試失敗: {e}")

def test_create_table(db_cursor, db_connection):
    """測試建立表格"""
    try:
        # 建立測試表格
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 確認表格建立成功
        db_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'test_users'
            );
        """)
        
        exists = db_cursor.fetchone()[0]
        assert exists == True
        
        # 清理測試表格
        db_cursor.execute("DROP TABLE IF EXISTS test_users;")
        db_connection.commit()
    except Exception as e:
        db_connection.rollback()
        pytest.fail(f"建立表格測試失敗: {e}")

def test_crud_operations(db_cursor, db_connection):
    """測試 CRUD 操作"""
    try:
        # 建立測試表格
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                description TEXT
            );
        """)
        
        # Create (新增)
        db_cursor.execute("""
            INSERT INTO test_products (name, price, description) 
            VALUES (%s, %s, %s);
        """, ("測試產品", 99.99, "這是一個測試產品"))
        
        # Read (讀取)
        db_cursor.execute("SELECT * FROM test_products WHERE name = %s;", ("測試產品",))
        product = db_cursor.fetchone()
        assert product is not None
        assert product[1] == "測試產品"
        assert product[2] == 99.99
        
        # Update (更新)
        db_cursor.execute("""
            UPDATE test_products 
            SET price = %s, description = %s 
            WHERE name = %s;
        """, (199.99, "更新後的測試產品", "測試產品"))
        
        db_cursor.execute("SELECT price FROM test_products WHERE name = %s;", ("測試產品",))
        updated_price = db_cursor.fetchone()[0]
        assert updated_price == 199.99
        
        # Delete (刪除)
        db_cursor.execute("DELETE FROM test_products WHERE name = %s;", ("測試產品",))
        db_cursor.execute("SELECT COUNT(*) FROM test_products WHERE name = %s;", ("測試產品",))
        count = db_cursor.fetchone()[0]
        assert count == 0
        
        # 清理測試表格
        db_cursor.execute("DROP TABLE IF EXISTS test_products;")
        db_connection.commit()
    except Exception as e:
        db_connection.rollback()
        pytest.fail(f"CRUD 操作測試失敗: {e}")

def test_transaction_rollback(db_cursor, db_connection):
    """測試交易回滾"""
    try:
        # 建立測試表格
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_transactions (
                id SERIAL PRIMARY KEY,
                value VARCHAR(50) NOT NULL
            );
        """)
        
        # 開始交易
        db_cursor.execute("INSERT INTO test_transactions (value) VALUES ('test1');")
        db_cursor.execute("INSERT INTO test_transactions (value) VALUES ('test2');")
        
        # 故意觸發錯誤
        try:
            db_cursor.execute("INSERT INTO test_transactions (value) VALUES (NULL);")
            db_connection.commit()
        except:
            db_connection.rollback()
        
        # 檢查資料是否已回滾
        db_cursor.execute("SELECT COUNT(*) FROM test_transactions;")
        count = db_cursor.fetchone()[0]
        assert count == 0
        
        # 清理測試表格
        db_cursor.execute("DROP TABLE IF EXISTS test_transactions;")
        db_connection.commit()
    except Exception as e:
        db_connection.rollback()
        pytest.fail(f"交易回滾測試失敗: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])