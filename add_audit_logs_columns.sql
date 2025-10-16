-- 添加缺失的列到audit_logs表
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS username VARCHAR(100);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS tenant VARCHAR(50);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS endpoint VARCHAR(255);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS method VARCHAR(10);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS status VARCHAR(20);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS response_time FLOAT;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs(tenant);
CREATE INDEX IF NOT EXISTS idx_audit_logs_status ON audit_logs(status);