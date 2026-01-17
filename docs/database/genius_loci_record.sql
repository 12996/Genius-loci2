-- ============================================
-- 地灵对话记忆表 (genius_loci_record)
-- ============================================
-- 功能：存储用户与地灵的对话摘要记忆
-- 作者：Claude Sonnet 4.5
-- 创建时间：2025-01-17
-- ============================================

-- 创建表
CREATE TABLE IF NOT EXISTS genius_loci_record (
    -- 主键
    id BIGSERIAL PRIMARY KEY,

    -- 用户关联
    user_id BIGINT NOT NULL,

    -- 会话标识（同一轮对话的多条记录共享同一个 session_id）
    session_id VARCHAR(100) NOT NULL,

    -- 对话内容摘要（由 LLM 总结，保留关键信息和情感变化）
    ai_result TEXT NOT NULL,

    -- 地理位置信息
    gps_longitude DECIMAL(10, 7) NOT NULL,
    gps_latitude DECIMAL(10, 7) NOT NULL,

    -- 时间戳
    create_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    CONSTRAINT gps_longitude_check CHECK (gps_longitude BETWEEN -180 AND 180),
    CONSTRAINT gps_latitude_check CHECK (gps_latitude BETWEEN -90 AND 90)
);

-- ============================================
-- 创建索引（优化查询性能）
-- ============================================

-- PostGIS 地理位置索引（如果启用了 PostGIS 扩展）
-- 需要先启用扩展: CREATE EXTENSION IF NOT EXISTS postgis;

-- 添加地理位置列（PostGIS）
DO $$
BEGIN
    -- 检查 postgis 扩展是否可用
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') THEN
        -- 添加地理列（如果不存在）
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'genius_loci_record'
            AND column_name = 'location'
        ) THEN
            ALTER TABLE genius_loci_record ADD COLUMN location GEOGRAPHY(POINT, 4326);

            -- 基于现有坐标创建地理点
            UPDATE genius_loci_record
            SET location = ST_SetSRID(ST_MakePoint(gps_longitude, gps_latitude), 4326)::GEOGRAPHY;

            -- 创建地理索引
            CREATE INDEX idx_genius_loci_location ON genius_loci_record USING GIST (location);
        END IF;
    END IF;
END $$;

-- 用户 ID 索引
CREATE INDEX IF NOT EXISTS idx_genius_loci_user_id ON genius_loci_record(user_id);

-- 会话 ID 索引
CREATE INDEX IF NOT EXISTS idx_genius_loci_session_id ON genius_loci_record(session_id);

-- 创建时间索引（用于查询最近记录）
CREATE INDEX IF NOT EXISTS idx_genius_loci_create_time ON genius_loci_record(create_time DESC);

-- 复合索引（用户+时间，用于查询某用户最近的记忆）
CREATE INDEX IF NOT EXISTS idx_genius_loci_user_time ON genius_loci_record(user_id, create_time DESC);

-- ============================================
-- 添加注释
-- ============================================

COMMENT ON TABLE genius_loci_record IS '地灵对话记忆表：存储用户与地灵的对话摘要';
COMMENT ON COLUMN genius_loci_record.id IS '主键';
COMMENT ON COLUMN genius_loci_record.user_id IS '用户ID';
COMMENT ON COLUMN genius_loci_record.session_id IS '会话标识（同一轮对话的多条记录共享）';
COMMENT ON COLUMN genius_loci_record.ai_result IS '对话内容摘要（由 LLM 生成，包含事情经过和情感变化）';
COMMENT ON COLUMN genius_loci_record.gps_longitude IS '经度';
COMMENT ON COLUMN genius_loci_record.gps_latitude IS '纬度';
COMMENT ON COLUMN genius_loci_record.create_time IS '创建时间';
COMMENT ON COLUMN genius_loci_record.location IS 'PostGIS 地理位置点（如果启用 PostGIS）';

-- ============================================
-- 启用 Row Level Security (RLS) - 可选
-- ============================================

ALTER TABLE genius_loci_record ENABLE ROW LEVEL SECURITY;

-- 创建策略：用户只能读取自己的记录
CREATE POLICY "Users can read own records"
    ON genius_loci_record FOR SELECT
    USING (user_id = current_setting('request.jwt.claim.user_id')::BIGINT);

-- 创建策略：用户可以插入自己的记录
CREATE POLICY "Users can insert own records"
    ON genius_loci_record FOR INSERT
    WITH CHECK (user_id = current_setting('request.jwt.claim.user_id')::BIGINT);

-- ============================================
-- 完成提示
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE '地灵对话记忆表创建成功！';
    RAISE NOTICE '表名: genius_loci_record';
    RAISE NOTICE '===========================================';
END $$;
