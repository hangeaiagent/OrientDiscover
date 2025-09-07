-- 地图相册数据库结构设计
-- Database Structure for Map Albums System
-- 创建时间: 2024-12-13

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================
-- 地图相册表 (Map Albums Table)
-- =====================================
CREATE TABLE spot_map_albums (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID REFERENCES users(id) ON DELETE CASCADE,
    creator_type TEXT CHECK (creator_type IN ('system_admin', 'user_self')) DEFAULT 'user_self', -- 创建者类型: 系统管理 | 用户自己
    title TEXT NOT NULL, -- 相册标题
    description TEXT, -- 相册描述
    cover_image TEXT, -- 封面图片URL
    access_level TEXT CHECK (access_level IN ('private', 'public')) DEFAULT 'public', -- 访问级别: 私有 | 公开
    tags TEXT[] DEFAULT '{}', -- 标签数组
    view_count INTEGER DEFAULT 0, -- 浏览次数
    like_count INTEGER DEFAULT 0, -- 点赞次数
    is_recommended BOOLEAN DEFAULT false, -- 是否推荐
    created_at TIMESTAMPTZ DEFAULT now(), -- 创建时间
    updated_at TIMESTAMPTZ DEFAULT now() -- 更新时间
);

-- 创建相册表索引
CREATE INDEX idx_spot_map_albums_creator ON spot_map_albums(creator_id);
CREATE INDEX idx_spot_map_albums_access_level ON spot_map_albums(access_level);
CREATE INDEX idx_spot_map_albums_created_at ON spot_map_albums(created_at DESC);

-- =====================================
-- 景点主表 (Attractions Main Table)
-- =====================================
CREATE TABLE spot_attractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL, -- 景点名称
    location GEOMETRY(Point, 4326) NOT NULL, -- 地理位置坐标
    category TEXT NOT NULL, -- 景点类别
    country TEXT NOT NULL, -- 国家
    city TEXT NOT NULL, -- 城市
    address TEXT, -- 详细地址
    opening_hours TEXT, -- 开放时间
    ticket_price TEXT, -- 门票价格
    booking_method TEXT, -- 预订方式
    main_image_url TEXT, -- 主图片URL
    video_url TEXT, -- 视频URL
    created_at TIMESTAMPTZ DEFAULT now(), -- 创建时间
    updated_at TIMESTAMPTZ DEFAULT now() -- 更新时间
);

-- 创建空间索引和其他索引
CREATE INDEX idx_spot_attractions_location ON spot_attractions USING GIST (location);
CREATE INDEX idx_spot_attractions_category ON spot_attractions(category);
CREATE INDEX idx_spot_attractions_country_city ON spot_attractions(country, city);

-- =====================================
-- 景点多语言内容表 (Attraction Multi-language Content Table)
-- =====================================
CREATE TABLE spot_attraction_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attraction_id UUID REFERENCES spot_attractions(id) ON DELETE CASCADE,
    language_code TEXT NOT NULL, -- 语言代码: 'zh-CN', 'en', 'fr', 'de', 'ja', 'ko', etc.
    name_translated TEXT, -- 翻译后的景点名称
    description TEXT, -- 景点描述
    attraction_introduction TEXT, -- 详细景点介绍
    guide_commentary TEXT, -- 导游词
    created_at TIMESTAMPTZ DEFAULT now(), -- 创建时间
    UNIQUE(attraction_id, language_code)
);

-- 创建多语言内容索引
CREATE INDEX idx_spot_attraction_contents_attraction ON spot_attraction_contents(attraction_id);
CREATE INDEX idx_spot_attraction_contents_language ON spot_attraction_contents(language_code);

-- =====================================
-- 景点媒体资源表 (Attraction Media Resources Table)
-- =====================================
CREATE TABLE spot_attraction_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attraction_id UUID REFERENCES spot_attractions(id) ON DELETE CASCADE,
    media_type TEXT CHECK (media_type IN ('image', 'video', 'audio')) NOT NULL, -- 媒体类型: 图片 | 视频 | 音频
    url TEXT NOT NULL, -- 媒体资源URL
    caption TEXT, -- 媒体说明文字
    is_primary BOOLEAN DEFAULT false, -- 是否为主要媒体
    order_index INTEGER DEFAULT 0, -- 排序索引
    created_at TIMESTAMPTZ DEFAULT now() -- 创建时间
);

-- 创建媒体资源索引
CREATE INDEX idx_spot_attraction_media_attraction ON spot_attraction_media(attraction_id);
CREATE INDEX idx_spot_attraction_media_type ON spot_attraction_media(media_type);
CREATE INDEX idx_spot_attraction_media_order ON spot_attraction_media(attraction_id, order_index);

-- =====================================
-- 相册景点关联表 (Album-Attraction Association Table)
-- =====================================
CREATE TABLE spot_album_attractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    album_id UUID REFERENCES spot_map_albums(id) ON DELETE CASCADE,
    attraction_id UUID REFERENCES spot_attractions(id) ON DELETE CASCADE,
    order_index INTEGER DEFAULT 0, -- 在相册中的排序
    custom_note TEXT, -- 用户自定义备注
    visit_duration INTEGER, -- 建议游览时长(分钟)
    created_at TIMESTAMPTZ DEFAULT now(), -- 创建时间
    UNIQUE(album_id, attraction_id)
);

-- 创建关联表索引
CREATE INDEX idx_spot_album_attractions_album ON spot_album_attractions(album_id);
CREATE INDEX idx_spot_album_attractions_attraction ON spot_album_attractions(attraction_id);
CREATE INDEX idx_spot_album_attractions_order ON spot_album_attractions(album_id, order_index);

-- =====================================
-- 向量存储表 (Vector Storage Table)
-- =====================================
CREATE TABLE spot_attraction_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attraction_id UUID REFERENCES spot_attractions(id) ON DELETE CASCADE,
    language_code TEXT NOT NULL, -- 语言代码
    content_type TEXT CHECK (content_type IN ('description', 'introduction', 'guide_commentary')) NOT NULL, -- 内容类型: 描述 | 介绍 | 导游词
    embedding vector(1536), -- OpenAI Ada-002 embedding dimension
    created_at TIMESTAMPTZ DEFAULT now(), -- 创建时间
    UNIQUE(attraction_id, language_code, content_type)
);

-- 创建向量索引
CREATE INDEX idx_spot_attraction_embeddings_vector ON spot_attraction_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_spot_attraction_embeddings_attraction ON spot_attraction_embeddings(attraction_id);

-- =====================================
-- 用户行为表 (User Behaviors Table)
-- =====================================
CREATE TABLE spot_user_behaviors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    album_id UUID REFERENCES spot_map_albums(id) ON DELETE CASCADE,
    action_type TEXT CHECK (action_type IN ('view', 'like', 'share', 'bookmark')) NOT NULL, -- 行为类型: 查看 | 点赞 | 分享 | 收藏
    created_at TIMESTAMPTZ DEFAULT now() -- 创建时间
);

-- 创建用户行为索引
CREATE INDEX idx_spot_user_behaviors_user ON spot_user_behaviors(user_id);
CREATE INDEX idx_spot_user_behaviors_album ON spot_user_behaviors(album_id);
CREATE INDEX idx_spot_user_behaviors_action ON spot_user_behaviors(action_type);
CREATE INDEX idx_spot_user_behaviors_created ON spot_user_behaviors(created_at DESC);

-- =====================================
-- 行级安全策略 (Row Level Security Policies)
-- =====================================

-- 启用行级安全
ALTER TABLE spot_map_albums ENABLE ROW LEVEL SECURITY;
ALTER TABLE spot_album_attractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE spot_user_behaviors ENABLE ROW LEVEL SECURITY;

-- 相册访问策略
CREATE POLICY "users_can_view_public_albums" ON spot_map_albums -- 用户可以查看公开相册
    FOR SELECT USING (access_level = 'public');

CREATE POLICY "users_can_manage_own_albums" ON spot_map_albums -- 用户可以管理自己的相册
    FOR ALL USING (auth.uid() = creator_id);

-- 相册景点关联策略
CREATE POLICY "can_view_public_album_attractions" ON spot_album_attractions -- 可以查看公开相册的景点
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM spot_map_albums 
            WHERE id = album_id AND (access_level = 'public' OR creator_id = auth.uid())
        )
    );

-- 用户行为策略
CREATE POLICY "users_can_manage_own_behaviors" ON spot_user_behaviors -- 用户可以管理自己的行为记录
    FOR ALL USING (auth.uid() = user_id);

-- =====================================
-- 触发器函数 (Trigger Functions)
-- =====================================

-- 更新时间戳触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建更新时间戳触发器
CREATE TRIGGER update_spot_map_albums_updated_at BEFORE UPDATE ON spot_map_albums
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_spot_attractions_updated_at BEFORE UPDATE ON spot_attractions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================
-- 视图 (Views)
-- =====================================

-- 相册详情视图 (包含统计信息)
CREATE VIEW spot_album_details AS
SELECT 
    ma.*,
    COUNT(aa.id) as attraction_count,
    COALESCE(ub_stats.total_views, 0) as total_views,
    COALESCE(ub_stats.total_likes, 0) as total_likes
FROM spot_map_albums ma
LEFT JOIN spot_album_attractions aa ON ma.id = aa.album_id
LEFT JOIN (
    SELECT 
        album_id,
        COUNT(CASE WHEN action_type = 'view' THEN 1 END) as total_views,
        COUNT(CASE WHEN action_type = 'like' THEN 1 END) as total_likes
    FROM spot_user_behaviors 
    GROUP BY album_id
) ub_stats ON ma.id = ub_stats.album_id
GROUP BY ma.id, ub_stats.total_views, ub_stats.total_likes;

-- 景点详情视图 (包含多语言内容)
CREATE VIEW spot_attraction_details AS
SELECT 
    a.*,
    ac.language_code,
    ac.name_translated,
    ac.description as translated_description,
    ac.attraction_introduction,
    ac.guide_commentary,
    COUNT(am.id) as media_count
FROM spot_attractions a
LEFT JOIN spot_attraction_contents ac ON a.id = ac.attraction_id
LEFT JOIN spot_attraction_media am ON a.id = am.attraction_id
GROUP BY a.id, ac.language_code, ac.name_translated, ac.description, ac.attraction_introduction, ac.guide_commentary;

-- =====================================
-- 示例数据插入 (Sample Data)
-- =====================================

-- 注意：这里假设已经有users表，如果没有需要先创建
-- CREATE TABLE IF NOT EXISTS users (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     email TEXT UNIQUE NOT NULL,
--     created_at TIMESTAMPTZ DEFAULT now()
-- );

-- 插入示例数据的注释说明
-- 实际使用时，请根据具体需求插入真实数据

COMMENT ON TABLE spot_map_albums IS '地图相册表 - 存储用户创建的景点相册信息';
COMMENT ON TABLE spot_attractions IS '景点主表 - 存储景点的基本信息和地理位置';
COMMENT ON TABLE spot_attraction_contents IS '景点多语言内容表 - 存储景点的多语言描述和介绍';
COMMENT ON TABLE spot_attraction_media IS '景点媒体资源表 - 存储景点的图片、视频等媒体资源';
COMMENT ON TABLE spot_album_attractions IS '相册景点关联表 - 定义相册与景点的关联关系';
COMMENT ON TABLE spot_attraction_embeddings IS '向量存储表 - 存储景点内容的向量嵌入，用于AI搜索';
COMMENT ON TABLE spot_user_behaviors IS '用户行为表 - 记录用户对相册的各种操作行为';