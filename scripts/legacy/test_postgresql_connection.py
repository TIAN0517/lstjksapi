import psycopg2
import asyncio
import asyncpg

def test_psycopg2_connection():
    """測試 psycopg2 連接"""
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=35432,
            user="jytian",
            password="ji394su3",
            database="bossjy_huaqiao"
        )
        print("psycopg2 連接成功")
        conn.close()
        return True
    except Exception as e:
        print(f"psycopg2 連接失敗: {e}")
        return False

async def test_asyncpg_connection():
    """測試 asyncpg 連接"""
    try:
        conn = await asyncpg.connect(
            host="127.0.0.1",
            port=35432,
            user="jytian",
            password="ji394su3",
            database="bossjy_huaqiao"
        )
        print("asyncpg 連接成功")
        await conn.close()
        return True
    except Exception as e:
        print(f"asyncpg 連接失敗: {e}")
        return False

def test_psql_command():
    """測試 psql 命令行連接"""
    import subprocess
    try:
        # 嘗試執行 psql 命令
        result = subprocess.run([
            'psql', 
            '-h', '127.0.0.1', 
            '-p', '35432', 
            '-U', 'jytian', 
            '-d', 'bossjy_huaqiao',
            '-c', 'SELECT version();'
        ], 
        capture_output=True, 
        text=True,
        timeout=10
        )
        
        if result.returncode == 0:
            print("psql 命令行連接成功")
            return True
        else:
            print(f"psql 命令行連接失敗: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("psql 命令行連接超時")
        return False
    except FileNotFoundError:
        print("未找到 psql 命令，請確保 PostgreSQL 已正確安裝")
        return False
    except Exception as e:
        print(f"psql 命令行連接出錯: {e}")
        return False

if __name__ == "__main__":
    print("測試 PostgreSQL 連接...")
    
    # 測試 psycopg2
    print("\n1. 測試 psycopg2 連接:")
    test_psycopg2_connection()
    
    # 測試 asyncpg
    print("\n2. 測試 asyncpg 連接:")
    asyncio.run(test_asyncpg_connection())
    
    # 測試 psql 命令行
    print("\n3. 測試 psql 命令行連接:")
    test_psql_command()