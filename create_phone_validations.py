import psycopg2
from datetime import datetime

try:
    conn = psycopg2.connect('postgresql://jytian:ji394su3@postgres:5432/bossjy_huaqiao')
    cursor = conn.cursor()
    
    # 创建phone_validations表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phone_validations (
            id SERIAL PRIMARY KEY,
            phone_number VARCHAR(20) NOT NULL,
            country_code VARCHAR(5),
            validation_type VARCHAR(50) NOT NULL DEFAULT 'basic',
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            validation_result JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER REFERENCES users(id),
            metadata JSONB
        );
    """)
    
    # 创建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_phone_validations_phone ON phone_validations(phone_number);
        CREATE INDEX IF NOT EXISTS idx_phone_validations_status ON phone_validations(status);
        CREATE INDEX IF NOT EXISTS idx_phone_validations_user ON phone_validations(user_id);
    """)
    
    # 创建更新时间触发器
    cursor.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    cursor.execute("""
        CREATE TRIGGER update_phone_validations_updated_at 
            BEFORE UPDATE ON phone_validations 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    conn.commit()
    print("✓ phone_validations表创建成功")
    
    # 验证表是否创建成功
    cursor.execute("""
        SELECT COUNT(*) FROM phone_validations
    """)
    count = cursor.fetchone()[0]
    print(f"✓ phone_validations表当前记录数: {count}")
    
    conn.close()
except Exception as e:
    print(f"错误: {e}")
    if conn:
        conn.rollback()