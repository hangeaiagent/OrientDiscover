-- =====================================
-- Spot地图相册系统 - 历史数据清理脚本
-- Historical Data Cleanup Script for Spot Map Albums System
-- =====================================
-- 创建时间: 2024-12-13
-- 版本: v1.0
-- 作者: AI Assistant
-- 
-- 说明: 
-- 本脚本用于完全清理spot_*表中的所有历史迁移数据
-- 解决数据重复插入导致的数据量翻倍问题
-- 
-- ⚠️ 警告: 此脚本将删除所有spot_*表中的数据，请谨慎使用！
-- =====================================

-- 开启事务，确保操作的原子性
BEGIN;

-- =====================================
-- 1. 数据清理前的备份提醒
-- =====================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE '⚠️  数据清理脚本开始执行';
    RAISE NOTICE '⚠️  此操作将删除所有spot_*表中的数据';
    RAISE NOTICE '⚠️  请确保已经备份重要数据';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '清理时间: %', now();
    RAISE NOTICE '===========================================';
END $$;

-- =====================================
-- 2. 清理前数据统计
-- =====================================

DO $$
DECLARE
    attractions_count INTEGER;
    contents_count INTEGER;
    media_count INTEGER;
    albums_count INTEGER;
    album_attractions_count INTEGER;
    embeddings_count INTEGER;
    behaviors_count INTEGER;
BEGIN
    -- 统计清理前的数据量
    SELECT COUNT(*) INTO attractions_count FROM spot_attractions;
    SELECT COUNT(*) INTO contents_count FROM spot_attraction_contents;
    SELECT COUNT(*) INTO media_count FROM spot_attraction_media;
    SELECT COUNT(*) INTO albums_count FROM spot_map_albums;
    SELECT COUNT(*) INTO album_attractions_count FROM spot_album_attractions;
    SELECT COUNT(*) INTO embeddings_count FROM spot_attraction_embeddings;
    SELECT COUNT(*) INTO behaviors_count FROM spot_user_behaviors;
    
    RAISE NOTICE '清理前数据统计:';
    RAISE NOTICE '- spot_attractions: % 条记录', attractions_count;
    RAISE NOTICE '- spot_attraction_contents: % 条记录', contents_count;
    RAISE NOTICE '- spot_attraction_media: % 条记录', media_count;
    RAISE NOTICE '- spot_map_albums: % 条记录', albums_count;
    RAISE NOTICE '- spot_album_attractions: % 条记录', album_attractions_count;
    RAISE NOTICE '- spot_attraction_embeddings: % 条记录', embeddings_count;
    RAISE NOTICE '- spot_user_behaviors: % 条记录', behaviors_count;
    RAISE NOTICE '===========================================';
END $$;

-- =====================================
-- 3. 按依赖关系顺序清理数据
-- =====================================

-- 3.1 清理用户行为数据 (最上层，无外键依赖)
RAISE NOTICE '正在清理用户行为数据...';
DELETE FROM spot_user_behaviors;

-- 3.2 清理向量嵌入数据
RAISE NOTICE '正在清理向量嵌入数据...';
DELETE FROM spot_attraction_embeddings;

-- 3.3 清理相册景点关联数据
RAISE NOTICE '正在清理相册景点关联数据...';
DELETE FROM spot_album_attractions;

-- 3.4 清理相册数据
RAISE NOTICE '正在清理相册数据...';
DELETE FROM spot_map_albums;

-- 3.5 清理景点媒体资源数据
RAISE NOTICE '正在清理景点媒体资源数据...';
DELETE FROM spot_attraction_media;

-- 3.6 清理景点多语言内容数据
RAISE NOTICE '正在清理景点多语言内容数据...';
DELETE FROM spot_attraction_contents;

-- 3.7 清理景点主表数据 (最底层，被其他表引用)
RAISE NOTICE '正在清理景点主表数据...';
DELETE FROM spot_attractions;

-- =====================================
-- 4. 重置序列和自增ID (如果有的话)
-- =====================================

-- 注意：由于我们使用UUID作为主键，不需要重置序列
-- 但如果有其他使用SERIAL类型的字段，可以在这里重置

-- 示例（如果需要）：
-- ALTER SEQUENCE spot_attractions_some_serial_id_seq RESTART WITH 1;

-- =====================================
-- 5. 清理后数据验证
-- =====================================

DO $$
DECLARE
    attractions_count INTEGER;
    contents_count INTEGER;
    media_count INTEGER;
    albums_count INTEGER;
    album_attractions_count INTEGER;
    embeddings_count INTEGER;
    behaviors_count INTEGER;
    total_records INTEGER;
BEGIN
    -- 统计清理后的数据量
    SELECT COUNT(*) INTO attractions_count FROM spot_attractions;
    SELECT COUNT(*) INTO contents_count FROM spot_attraction_contents;
    SELECT COUNT(*) INTO media_count FROM spot_attraction_media;
    SELECT COUNT(*) INTO albums_count FROM spot_map_albums;
    SELECT COUNT(*) INTO album_attractions_count FROM spot_album_attractions;
    SELECT COUNT(*) INTO embeddings_count FROM spot_attraction_embeddings;
    SELECT COUNT(*) INTO behaviors_count FROM spot_user_behaviors;
    
    total_records := attractions_count + contents_count + media_count + 
                    albums_count + album_attractions_count + embeddings_count + behaviors_count;
    
    RAISE NOTICE '===========================================';
    RAISE NOTICE '清理后数据统计:';
    RAISE NOTICE '- spot_attractions: % 条记录', attractions_count;
    RAISE NOTICE '- spot_attraction_contents: % 条记录', contents_count;
    RAISE NOTICE '- spot_attraction_media: % 条记录', media_count;
    RAISE NOTICE '- spot_map_albums: % 条记录', albums_count;
    RAISE NOTICE '- spot_album_attractions: % 条记录', album_attractions_count;
    RAISE NOTICE '- spot_attraction_embeddings: % 条记录', embeddings_count;
    RAISE NOTICE '- spot_user_behaviors: % 条记录', behaviors_count;
    RAISE NOTICE '===========================================';
    RAISE NOTICE '总计剩余记录: % 条', total_records;
    
    -- 验证清理是否完全
    IF total_records = 0 THEN
        RAISE NOTICE '✅ 数据清理完成！所有spot_*表已清空';
    ELSE
        RAISE WARNING '⚠️ 数据清理可能不完整，仍有 % 条记录', total_records;
    END IF;
    
    RAISE NOTICE '===========================================';
END $$;

-- =====================================
-- 6. 重建表统计信息
-- =====================================

RAISE NOTICE '正在重建表统计信息...';

-- 更新表统计信息，优化后续查询性能
ANALYZE spot_attractions;
ANALYZE spot_attraction_contents;
ANALYZE spot_attraction_media;
ANALYZE spot_map_albums;
ANALYZE spot_album_attractions;
ANALYZE spot_attraction_embeddings;
ANALYZE spot_user_behaviors;

-- =====================================
-- 7. 验证表结构完整性
-- =====================================

RAISE NOTICE '正在验证表结构完整性...';

-- 验证所有spot_*表是否存在
DO $$
DECLARE
    table_names TEXT[] := ARRAY[
        'spot_attractions',
        'spot_attraction_contents', 
        'spot_attraction_media',
        'spot_map_albums',
        'spot_album_attractions',
        'spot_attraction_embeddings',
        'spot_user_behaviors'
    ];
    table_name TEXT;
    table_exists BOOLEAN;
BEGIN
    RAISE NOTICE '验证表结构:';
    
    FOREACH table_name IN ARRAY table_names
    LOOP
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = table_name
        ) INTO table_exists;
        
        IF table_exists THEN
            RAISE NOTICE '✅ 表 % 存在', table_name;
        ELSE
            RAISE WARNING '❌ 表 % 不存在', table_name;
        END IF;
    END LOOP;
END $$;

-- =====================================
-- 8. 验证索引完整性
-- =====================================

RAISE NOTICE '正在验证索引完整性...';

-- 检查重要索引是否存在
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename LIKE 'spot_%'
ORDER BY tablename, indexname;

-- =====================================
-- 9. 验证外键约束
-- =====================================

RAISE NOTICE '正在验证外键约束...';

-- 检查外键约束是否完整
SELECT 
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu 
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name LIKE 'spot_%'
ORDER BY tc.table_name, tc.constraint_name;

-- =====================================
-- 10. 清理完成通知
-- =====================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE '🎉 数据清理脚本执行完成！';
    RAISE NOTICE '完成时间: %', now();
    RAISE NOTICE '===========================================';
    RAISE NOTICE '清理结果:';
    RAISE NOTICE '✅ 所有spot_*表数据已清空';
    RAISE NOTICE '✅ 表结构保持完整';
    RAISE NOTICE '✅ 索引和约束正常';
    RAISE NOTICE '✅ 统计信息已更新';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '现在可以重新执行数据迁移脚本';
    RAISE NOTICE '或开始添加新的数据';
    RAISE NOTICE '===========================================';
END $$;

-- 提交事务
COMMIT;

-- =====================================
-- 11. 可选：创建数据清理记录表
-- =====================================

-- 记录清理操作历史（可选）
CREATE TABLE IF NOT EXISTS spot_data_cleanup_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cleanup_type TEXT NOT NULL DEFAULT 'full_cleanup',
    cleanup_timestamp TIMESTAMPTZ DEFAULT now(),
    cleanup_description TEXT,
    executed_by TEXT DEFAULT current_user,
    cleanup_status TEXT DEFAULT 'completed'
);

-- 插入本次清理记录
INSERT INTO spot_data_cleanup_log (
    cleanup_type,
    cleanup_description,
    cleanup_status
) VALUES (
    'historical_data_cleanup',
    '清理所有spot_*表中的历史迁移数据，解决数据重复问题',
    'completed'
);

-- =====================================
-- 使用说明和注意事项
-- =====================================

/*
使用说明:
1. 在执行此脚本前，请确保已备份重要数据
2. 此脚本将完全清空所有spot_*表的数据
3. 表结构、索引、约束将保持不变
4. 执行后可以重新运行数据迁移脚本

执行方式:
方式1: 通过Supabase Dashboard SQL编辑器
- 复制此脚本内容到SQL编辑器
- 点击执行按钮

方式2: 通过psql命令行
psql -h db.uobwbhvwrciaxloqdizc.supabase.co -U postgres -d postgres -f 02历史数据迁移脚本数据清理0907.sql

注意事项:
- 此操作不可逆，请谨慎执行
- 建议在测试环境先验证
- 如有疑问请先备份数据库
- 执行前请确认当前数据库连接正确

清理范围:
- spot_attractions (景点主表)
- spot_attraction_contents (景点多语言内容)
- spot_attraction_media (景点媒体资源)
- spot_map_albums (地图相册)
- spot_album_attractions (相册景点关联)
- spot_attraction_embeddings (向量嵌入)
- spot_user_behaviors (用户行为)
*/