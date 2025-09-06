#!/usr/bin/env python3
"""
更新关键语言的翻译
只更新最常用的几种语言
"""

import asyncio
import sys
import os
from deepseek_translation_service import deepseek_translation_service

async def update_key_languages():
    """更新关键语言"""
    if not deepseek_translation_service:
        print("❌ DeepSeek翻译服务未初始化")
        return
    
    # 关键语言列表（最常用的）
    key_languages = ['en', 'es', 'fr', 'de', 'ja', 'ko']
    
    print(f"🚀 更新关键语言翻译...")
    
    i18n_directory = "/workspace/i18n/locales"
    source_file = os.path.join(i18n_directory, "zh.json")
    
    success_count = 0
    
    for i, lang_code in enumerate(key_languages, 1):
        print(f"\n[{i}/{len(key_languages)}] 🔄 翻译 {lang_code}")
        
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
                
        except Exception as e:
            print(f"❌ {lang_code} 翻译异常: {e}")
        
        # 添加延迟
        if i < len(key_languages):
            await asyncio.sleep(1)
    
    print(f"\n📊 关键语言翻译完成: {success_count}/{len(key_languages)} 成功")

if __name__ == "__main__":
    asyncio.run(update_key_languages())