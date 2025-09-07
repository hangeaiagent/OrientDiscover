#!/usr/bin/env python3
"""
数据迁移分析脚本
Analyze existing data structure and generate migration mapping
"""

import json
import sys
import os

# 添加backend目录到Python路径
sys.path.append('/workspace/backend')

from local_attractions_db import local_attractions_db
from global_cities_db import GlobalCitiesDB

def analyze_data_structure():
    """分析现有数据结构"""
    print("=== 数据结构分析 ===")
    
    # 分析本地景点数据
    local_data = local_attractions_db.attractions
    print(f"\n1. LocalAttractionsDB 景点数量: {len(local_data)}")
    print("   样本数据结构:")
    if local_data:
        sample = local_data[0]
        for key, value in sample.items():
            print(f"   - {key}: {type(value).__name__} = {str(value)[:50]}...")
    
    # 分析全球城市数据
    global_db = GlobalCitiesDB()
    global_cities = global_db.get_all_cities()
    print(f"\n2. GlobalCitiesDB 城市数量: {len(global_cities)}")
    
    total_attractions = 0
    for city in global_cities:
        city_key = city['key']
        attractions = global_db.get_city_attractions(city_key)
        city_count = len(attractions)
        total_attractions += city_count
        print(f"   - {city['name']} ({city['country']}): {city_count} 个景点")
    
    print(f"\n   全球景点总数: {total_attractions}")
    
    # 分析字段映射
    print("\n=== 字段映射分析 ===")
    print("本地数据字段 -> Supabase表字段:")
    
    field_mapping = {
        # 景点主表字段映射
        "name": "name",
        "latitude": "location (POINT)",  
        "longitude": "location (POINT)",
        "category": "category",
        "description": "description (多语言内容表)",
        "opening_hours": "opening_hours",
        "ticket_price": "ticket_price", 
        "booking_method": "booking_method",
        "image": "main_image_url",
        "video": "video_url",
        "country": "country",
        "city": "city",
        "address": "address"
    }
    
    for local_field, supabase_field in field_mapping.items():
        print(f"   {local_field:15} -> {supabase_field}")
    
    return {
        "local_attractions": local_data,
        "global_cities": global_cities,
        "global_db": global_db,
        "field_mapping": field_mapping,
        "total_attractions": total_attractions + len(local_data)
    }

def generate_migration_strategy(analysis_result):
    """生成数据迁移策略"""
    print("\n=== 数据迁移策略 ===")
    
    strategy = {
        "tables_to_populate": [
            "spot_attractions",
            "spot_attraction_contents", 
            "spot_attraction_media"
        ],
        "migration_steps": [
            {
                "step": 1,
                "description": "迁移本地北京景点数据到spot_attractions表",
                "source": "local_attractions_db.py",
                "target": "spot_attractions",
                "count": len(analysis_result["local_attractions"])
            },
            {
                "step": 2, 
                "description": "迁移全球城市景点数据到spot_attractions表",
                "source": "global_cities_db.py",
                "target": "spot_attractions", 
                "count": analysis_result["total_attractions"] - len(analysis_result["local_attractions"])
            },
            {
                "step": 3,
                "description": "创建中文描述内容到spot_attraction_contents表",
                "source": "description字段",
                "target": "spot_attraction_contents",
                "language_code": "zh-CN"
            },
            {
                "step": 4,
                "description": "迁移图片和视频URL到spot_attraction_media表",
                "source": "image/video字段", 
                "target": "spot_attraction_media"
            }
        ],
        "data_transformations": [
            {
                "field": "location",
                "transformation": "将latitude/longitude转换为PostGIS POINT格式",
                "example": "ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)"
            },
            {
                "field": "description",
                "transformation": "移动到多语言内容表，设置language_code='zh-CN'",
                "target_table": "spot_attraction_contents"
            },
            {
                "field": "image/video", 
                "transformation": "创建媒体记录，设置media_type和is_primary",
                "target_table": "spot_attraction_media"
            }
        ]
    }
    
    for step in strategy["migration_steps"]:
        print(f"步骤 {step['step']}: {step['description']}")
        print(f"   源: {step['source']}")
        print(f"   目标: {step['target']}")
        if 'count' in step:
            print(f"   数量: {step['count']} 条记录")
        print()
    
    return strategy

def main():
    """主函数"""
    print("开始数据迁移分析...")
    
    # 分析现有数据结构
    analysis_result = analyze_data_structure()
    
    # 生成迁移策略
    strategy = generate_migration_strategy(analysis_result)
    
    # 保存分析结果
    output = {
        "analysis_timestamp": "2024-12-13",
        "data_summary": {
            "local_attractions_count": len(analysis_result["local_attractions"]),
            "global_cities_count": len(analysis_result["global_cities"]),
            "total_attractions_count": analysis_result["total_attractions"]
        },
        "field_mapping": analysis_result["field_mapping"],
        "migration_strategy": strategy
    }
    
    with open('/workspace/migration_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"分析完成！总计需要迁移 {analysis_result['total_attractions']} 个景点")
    print("分析结果已保存到 migration_analysis.json")

if __name__ == "__main__":
    main()