#!/usr/bin/env python3
"""
多语言翻译工具
使用DeepSeek大模型翻译和更新所有i18n语言文件
"""

import asyncio
import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deepseek_translation_service import deepseek_translation_service

def load_json_file(file_path: str) -> Dict[str, Any]:
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载文件失败 {file_path}: {e}")
        return {}

def save_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """保存JSON文件"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ 保存文件失败 {file_path}: {e}")
        return False

def count_json_keys(data: Dict[str, Any], prefix: str = "") -> int:
    """递归统计JSON中的键数量"""
    count = 0
    for key, value in data.items():
        if isinstance(value, dict):
            count += count_json_keys(value, f"{prefix}{key}.")
        else:
            count += 1
    return count

def compare_json_structures(source: Dict[str, Any], target: Dict[str, Any], path: str = "") -> list:
    """比较两个JSON结构的差异"""
    missing_keys = []
    
    for key, value in source.items():
        current_path = f"{path}.{key}" if path else key
        
        if key not in target:
            missing_keys.append(current_path)
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            missing_keys.extend(compare_json_structures(value, target[key], current_path))
        elif isinstance(value, dict) and not isinstance(target.get(key), dict):
            missing_keys.append(current_path)
    
    return missing_keys

async def translate_single_language(source_file: str, target_lang: str, source_lang: str = "zh"):
    """翻译单个语言文件"""
    if not deepseek_translation_service:
        print("❌ DeepSeek翻译服务未初始化")
        return False
    
    i18n_dir = os.path.dirname(source_file)
    target_file = os.path.join(i18n_dir, f"{target_lang}.json")
    
    print(f"🔄 开始翻译 {source_lang} -> {target_lang}")
    
    success, error = await deepseek_translation_service.translate_i18n_file(
        source_file, target_lang, source_lang, target_file
    )
    
    if success:
        print(f"✅ {target_lang} 翻译完成")
        return True
    else:
        print(f"❌ {target_lang} 翻译失败: {error}")
        return False

async def update_all_languages(i18n_directory: str, source_lang: str = "zh"):
    """更新所有语言文件"""
    if not deepseek_translation_service:
        print("❌ DeepSeek翻译服务未初始化")
        return
    
    print(f"🚀 开始批量更新多语言文件...")
    print(f"📁 目录: {i18n_directory}")
    print(f"🌐 源语言: {source_lang}")
    
    # 检查源文件
    source_file = os.path.join(i18n_directory, f"{source_lang}.json")
    if not os.path.exists(source_file):
        print(f"❌ 源文件不存在: {source_file}")
        return
    
    source_data = load_json_file(source_file)
    source_keys = count_json_keys(source_data)
    print(f"📊 源文件包含 {source_keys} 个翻译键")
    
    # 获取支持的语言
    supported_languages = deepseek_translation_service.get_supported_languages()
    target_languages = [lang for lang in supported_languages.keys() if lang != source_lang]
    
    print(f"🔤 将翻译到以下 {len(target_languages)} 种语言:")
    for lang in target_languages:
        lang_info = supported_languages[lang]
        print(f"   - {lang}: {lang_info['native']} ({lang_info['name']})")
    
    # 执行翻译
    results = await deepseek_translation_service.update_all_i18n_files(i18n_directory, source_lang)
    
    # 统计结果
    successful = sum(1 for success, _ in results.values() if success)
    failed = len(results) - successful
    
    print(f"\n📈 翻译结果统计:")
    print(f"   ✅ 成功: {successful}")
    print(f"   ❌ 失败: {failed}")
    
    # 详细结果
    print(f"\n📋 详细结果:")
    for lang, (success, error) in results.items():
        if success:
            print(f"   ✅ {lang}: 翻译完成")
        else:
            print(f"   ❌ {lang}: {error}")

async def check_translation_completeness(i18n_directory: str, source_lang: str = "zh"):
    """检查翻译完整性"""
    print(f"🔍 检查翻译完整性...")
    
    source_file = os.path.join(i18n_directory, f"{source_lang}.json")
    if not os.path.exists(source_file):
        print(f"❌ 源文件不存在: {source_file}")
        return
    
    source_data = load_json_file(source_file)
    source_keys = count_json_keys(source_data)
    
    print(f"📊 源文件 ({source_lang}.json): {source_keys} 个键")
    
    # 检查所有语言文件
    if not deepseek_translation_service:
        print("❌ DeepSeek翻译服务未初始化")
        return
        
    supported_languages = deepseek_translation_service.get_supported_languages()
    
    incomplete_files = []
    
    for lang_code, lang_info in supported_languages.items():
        if lang_code == source_lang:
            continue
            
        target_file = os.path.join(i18n_directory, f"{lang_code}.json")
        
        if not os.path.exists(target_file):
            print(f"❌ {lang_code}: 文件不存在")
            incomplete_files.append(lang_code)
            continue
        
        target_data = load_json_file(target_file)
        target_keys = count_json_keys(target_data)
        
        # 检查缺失的键
        missing_keys = compare_json_structures(source_data, target_data)
        
        if missing_keys:
            print(f"⚠️  {lang_code}: {target_keys}/{source_keys} 键 (缺失 {len(missing_keys)} 个)")
            incomplete_files.append(lang_code)
            # 显示前几个缺失的键
            for key in missing_keys[:5]:
                print(f"     - {key}")
            if len(missing_keys) > 5:
                print(f"     ... 还有 {len(missing_keys) - 5} 个")
        else:
            print(f"✅ {lang_code}: {target_keys}/{source_keys} 键 (完整)")
    
    if incomplete_files:
        print(f"\n⚠️  发现 {len(incomplete_files)} 个不完整的语言文件:")
        for lang in incomplete_files:
            lang_info = supported_languages.get(lang, {})
            print(f"   - {lang}: {lang_info.get('native', lang)}")
        print(f"\n💡 建议运行翻译更新命令修复")
    else:
        print(f"\n✅ 所有语言文件都是完整的！")

async def test_translation_service():
    """测试翻译服务"""
    print("🧪 测试DeepSeek翻译服务...")
    
    if not deepseek_translation_service:
        print("❌ DeepSeek翻译服务未初始化")
        return
    
    # 健康检查
    health = await deepseek_translation_service.health_check()
    print(f"🏥 健康检查: {health['status']}")
    if health['status'] != 'healthy':
        print(f"❌ {health['message']}")
        return
    
    # 测试简单翻译
    test_text = "你好，世界！"
    success, error, result = await deepseek_translation_service.translate_text(
        test_text, "en", "zh"
    )
    
    if success:
        print(f"✅ 翻译测试成功:")
        print(f"   原文: {test_text}")
        print(f"   译文: {result}")
    else:
        print(f"❌ 翻译测试失败: {error}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="多语言翻译工具")
    parser.add_argument("--action", choices=["check", "update", "translate", "test"], 
                       default="check", help="执行的操作")
    parser.add_argument("--i18n-dir", default="/workspace/i18n/locales", 
                       help="i18n文件目录")
    parser.add_argument("--source-lang", default="zh", help="源语言代码")
    parser.add_argument("--target-lang", help="目标语言代码（仅用于单个翻译）")
    
    args = parser.parse_args()
    
    print("🌍 多语言翻译工具")
    print("=" * 50)
    
    if args.action == "test":
        asyncio.run(test_translation_service())
    elif args.action == "check":
        asyncio.run(check_translation_completeness(args.i18n_dir, args.source_lang))
    elif args.action == "update":
        asyncio.run(update_all_languages(args.i18n_dir, args.source_lang))
    elif args.action == "translate":
        if not args.target_lang:
            print("❌ 单个翻译需要指定 --target-lang 参数")
            return
        source_file = os.path.join(args.i18n_dir, f"{args.source_lang}.json")
        asyncio.run(translate_single_language(source_file, args.target_lang, args.source_lang))
    
    print("=" * 50)
    print("🎉 操作完成")

if __name__ == "__main__":
    main()