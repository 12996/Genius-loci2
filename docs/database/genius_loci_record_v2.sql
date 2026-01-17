-- ============================================
-- 地灵 AI 处理结果记录表 (genius_loci_record)
-- ============================================
-- 功能：存储大模型处理结果（对话总结、分类、关键词提取等）
-- 作者：Claude Sonnet 4.5
-- 创建时间：2025-01-17
-- 更新时间：2025-01-17（适配实际表结构）
-- ============================================

-- 创建表
CREATE TABLE IF NOT EXISTS genius_loci_record (
    -- 主键
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- 关联字段
    bubble_id BIGINT NOT NULL COMMENT '关联的气泡/足迹ID（外键）',
    user_id BIGINT NOT NULL COMMENT '关联的用户ID（外键）',

    -- AI处理信息
    ai_process_type TINYINT NOT NULL COMMENT 'AI处理类型（1-内容分类/2-关键词提取/3-互动推荐/4-合规检测/5-对话总结）',
    ai_result TEXT NOT NULL COMMENT 'AI处理结果（JSON格式）',

    -- 时间字段
    process_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'AI处理时间',
    expire_time DATETIME DEFAULT NULL COMMENT '结果过期时间',

    -- 状态字段
    is_effective TINYINT NOT NULL DEFAULT 1 COMMENT '结果是否有效（0-无效/1-有效）',

    -- 模型信息
    model_version VARCHAR(30) NOT NULL COMMENT '调用的大模型版本号',

    -- 索引
    INDEX idx_bubble_id (bubble_id),
    INDEX idx_user_id (user_id),
    INDEX idx_process_type (ai_process_type),
    INDEX idx_process_time (process_time),
    INDEX idx_is_effective (is_effective),

    -- 外键约束（可选，根据实际需求启用）
    FOREIGN KEY (bubble_id) REFERENCES bubble_note(id) ON DELETE CASCADE
) COMMENT='地灵AI处理结果记录表';

-- ============================================
-- AI处理类型说明
-- ============================================
-- 1 - 内容分类：对气泡内容进行分类（如：生活、工作、娱乐等）
-- 2 - 关键词提取：提取内容关键词
-- 3 - 互动推荐：推荐互动方式或回复建议
-- 4 - 合规检测：检测内容是否合规
-- 5 - 对话总结：总结用户与地灵的对话内容（地灵对话专用）

-- ============================================
-- 使用示例
-- ============================================

-- 示例1: 插入对话总结记录
INSERT INTO genius_loci_record (
    bubble_id,
    user_id,
    ai_process_type,
    ai_result,
    model_version
) VALUES (
    123,  -- bubble_id，关联到 bubble_note 表
    1,    -- user_id
    5,    -- ai_process_type = 5 (对话总结)
    '{"summary": "用户表达了对天气的喜悦，地灵回应以温暖的问候。", "emotion": "开心", "turns": 3}',
    'Qwen2.5-7B'  -- model_version
);

-- 示例2: 查询某个气泡的所有AI处理记录
SELECT * FROM genius_loci_record WHERE bubble_id = 123;

-- 示例3: 查询某个用户的所有对话总结
SELECT
    r.*,
    b.content as bubble_content,
    b.gps_longitude,
    b.gps_latitude
FROM genius_loci_record r
JOIN bubble_note b ON r.bubble_id = b.id
WHERE r.user_id = 1
AND r.ai_process_type = 5  -- 对话总结
AND r.is_effective = 1
ORDER BY r.process_time DESC;

-- 示例4: 查询某个位置附近的对话记忆（用于上下文注入）
SELECT
    r.*,
    b.gps_longitude,
    b.gps_latitude,
    ST_Distance(
        b.location,
        ST_SetSRID(ST_MakePoint(120.15507, 30.27408), 4326)::GEOGRAPHY
    ) as distance_meters
FROM genius_loci_record r
JOIN bubble_note b ON r.bubble_id = b.id
WHERE r.ai_process_type = 5  -- 对话总结
AND r.is_effective = 1
AND r.user_id != 1  -- 排除当前用户
AND ST_DWithin(
    b.location,
    ST_SetSRID(ST_MakePoint(120.15507, 30.27408), 4326)::GEOGRAPHY,
    1000  -- 1km
)
ORDER BY distance_meters ASC
LIMIT 1;

-- ============================================
-- 完成提示
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE '地灵 AI 处理结果记录表创建成功！';
    RAISE NOTICE '表名: genius_loci_record';
    RAISE NOTICE 'AI处理类型: 1-分类/2-关键词/3-推荐/4-合规/5-对话总结';
    RAISE NOTICE '===========================================';
END $$;
