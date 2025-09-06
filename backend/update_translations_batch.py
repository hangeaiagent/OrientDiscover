#!/usr/bin/env python3
"""
批量更新翻译脚本
分批处理语言文件，避免超时问题
"""

import asyncio
import sys
import os
from deepseek_translation_service import deepseek_translation_service

async def update_languages_batch():
    """批量更新语言文件，每次处理一个"""
    if not deepseek_translation_service:
        print("❌ DeepSeek翻译服务未初始化")
        return
    
    # 获取支持的语言
    supported_languages = deepseek_translation_service.get_supported_languages()
    target_languages = [lang for lang in supported_languages.keys() if lang != "zh"]
    
    print(f"🚀 开始批量更新 {len(target_languages)} 种语言...")
    
    i18n_directory = "/workspace/i18n/locales"
    source_file = os.path.join(i18n_directory, "zh.json")
    
    success_count = 0
    failed_languages = []
    
    for i, lang_code in enumerate(target_languages, 1):
        lang_info = supported_languages[lang_code]
        print(f"\n[{i}/{len(target_languages)}] 🔄 翻译 {lang_code}: {lang_info['native']}")
        
        try:
            success, error = await deepseek_translation_service.translate_i18n_file(
                source_file, lang_code, "zh", 
                os.path.join(i18n_directory, f"{lang_code}.json")
            )
            
            if success:
                print(f"✅ {lang_code} 翻译完成")
                success_count += 1
            else:
                print(f"❌ {lang_code} 翻译失败: {error}")
                failed_languages.append((lang_code, error))
                
        except Exception as e:
            print(f"❌ {lang_code} 翻译异常: {e}")
            failed_languages.append((lang_code, str(e)))
        
        # 添加延迟避免API限制
        if i < len(target_languages):
            print("⏳ 等待 2 秒...")
            await asyncio.sleep(2)
    
    print(f"\n📊 批量翻译完成:")
    print(f"   ✅ 成功: {success_count}")
    print(f"   ❌ 失败: {len(failed_languages)}")
    
    if failed_languages:
        print(f"\n❌ 失败的语言:")
        for lang_code, error in failed_languages:
            lang_info = supported_languages.get(lang_code, {})
            print(f"   - {lang_code} ({lang_info.get('native', lang_code)}): {error}")

if __name__ == "__main__":
    asyncio.run(update_languages_batch())