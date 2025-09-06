"""
DeepSeek 翻译服务
基于DeepSeek大模型的多语言翻译服务，支持动态内容翻译
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import aiohttp
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

class DeepSeekTranslationService:
    """DeepSeek翻译服务类"""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
        
        self.api_base_url = "https://api.deepseek.com/v1"
        self.chat_endpoint = f"{self.api_base_url}/chat/completions"
        
        # 模型配置
        self.model_config = {
            "chat": {
                "model": "deepseek-chat",
                "temperature": 0.3,  # 较低温度确保翻译一致性
                "max_tokens": 4000,
                "top_p": 0.7
            },
            "reasoner": {
                "model": "deepseek-reasoner", 
                "temperature": 0.3,
                "max_tokens": 4000,
                "top_p": 0.7
            }
        }
        
        # 支持的语言映射
        self.supported_languages = {
            'en': {'name': 'English', 'native': 'English'},
            'zh': {'name': 'Chinese', 'native': '中文'},
            'es': {'name': 'Spanish', 'native': 'Español'},
            'fr': {'name': 'French', 'native': 'Français'},
            'de': {'name': 'German', 'native': 'Deutsch'},
            'ja': {'name': 'Japanese', 'native': '日本語'},
            'ko': {'name': 'Korean', 'native': '한국어'},
            'it': {'name': 'Italian', 'native': 'Italiano'},
            'pt': {'name': 'Portuguese', 'native': 'Português'},
            'ru': {'name': 'Russian', 'native': 'Русский'},
            'ar': {'name': 'Arabic', 'native': 'العربية'},
            'hi': {'name': 'Hindi', 'native': 'हिन्दी'},
            'tr': {'name': 'Turkish', 'native': 'Türkçe'},
            'nl': {'name': 'Dutch', 'native': 'Nederlands'},
            'he': {'name': 'Hebrew', 'native': 'עברית'},
            'bg': {'name': 'Bulgarian', 'native': 'Български'}
        }
        
        # 翻译缓存
        self.translation_cache = {}
        self.cache_max_size = 1000
        
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # 测试简单的翻译请求
                test_payload = {
                    "model": self.model_config["chat"]["model"],
                    "messages": [
                        {
                            "role": "user", 
                            "content": "Translate 'Hello' to Chinese"
                        }
                    ],
                    "max_tokens": 50,
                    "temperature": 0.3
                }
                
                async with session.post(
                    self.chat_endpoint, 
                    headers=headers, 
                    json=test_payload,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "api_accessible": True,
                            "message": "DeepSeek API连接正常"
                        }
                    else:
                        return {
                            "status": "error",
                            "api_accessible": False,
                            "message": f"API返回错误状态: {response.status}"
                        }
                        
        except Exception as e:
            logger.error(f"DeepSeek健康检查失败: {e}")
            return {
                "status": "error",
                "api_accessible": False,
                "message": f"连接失败: {str(e)}"
            }
    
    def _create_translation_prompt(self, text: str, source_lang: str, target_lang: str, context: Optional[str] = None) -> str:
        """创建翻译提示词"""
        source_name = self.supported_languages.get(source_lang, {}).get('native', source_lang)
        target_name = self.supported_languages.get(target_lang, {}).get('native', target_lang)
        
        prompt = f"""你是一个专业的多语言翻译专家。请将以下{source_name}文本翻译成{target_name}。

翻译要求：
1. 保持原文的语义和语调
2. 符合目标语言的表达习惯
3. 保持专业术语的准确性
4. 如果是界面文本，保持简洁明了
5. 保持格式不变（如有占位符{{}}等）

"""
        
        if context:
            prompt += f"上下文信息：{context}\n\n"
            
        prompt += f"原文（{source_name}）：{text}\n\n请直接返回翻译结果，不要包含任何解释："
        
        return prompt
    
    async def translate_text(
        self, 
        text: str, 
        target_lang: str, 
        source_lang: str = "zh",
        context: Optional[str] = None,
        use_cache: bool = True
    ) -> Tuple[bool, str, Optional[str]]:
        """
        翻译单个文本
        
        Args:
            text: 要翻译的文本
            target_lang: 目标语言代码
            source_lang: 源语言代码，默认为中文
            context: 上下文信息
            use_cache: 是否使用缓存
            
        Returns:
            Tuple[成功状态, 错误信息, 翻译结果]
        """
        if not text or not text.strip():
            return True, "", ""
        
        # 检查缓存
        cache_key = f"{source_lang}_{target_lang}_{hash(text)}"
        if use_cache and cache_key in self.translation_cache:
            logger.debug(f"使用缓存翻译: {text[:50]}...")
            return True, "", self.translation_cache[cache_key]
        
        try:
            prompt = self._create_translation_prompt(text, source_lang, target_lang, context)
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model_config["chat"]["model"],
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self.model_config["chat"]["temperature"],
                    "max_tokens": self.model_config["chat"]["max_tokens"],
                    "top_p": self.model_config["chat"]["top_p"]
                }
                
                async with session.post(
                    self.chat_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"DeepSeek API错误 {response.status}: {error_text}")
                        return False, f"API请求失败: {response.status}", None
                    
                    result = await response.json()
                    
                    if 'choices' not in result or not result['choices']:
                        return False, "API返回格式错误", None
                    
                    translated_text = result['choices'][0]['message']['content'].strip()
                    
                    # 保存到缓存
                    if use_cache:
                        self.translation_cache[cache_key] = translated_text
                        if len(self.translation_cache) > self.cache_max_size:
                            # 删除最旧的缓存项
                            oldest_key = next(iter(self.translation_cache))
                            del self.translation_cache[oldest_key]
                    
                    logger.info(f"翻译成功: {text[:30]}... -> {translated_text[:30]}...")
                    return True, "", translated_text
                    
        except asyncio.TimeoutError:
            logger.error("翻译请求超时")
            return False, "请求超时", None
        except Exception as e:
            logger.error(f"翻译失败: {e}")
            return False, f"翻译错误: {str(e)}", None
    
    async def translate_json_structure(
        self, 
        json_data: Dict[str, Any], 
        target_lang: str, 
        source_lang: str = "zh",
        context: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        翻译JSON结构中的所有文本
        
        Args:
            json_data: 要翻译的JSON数据
            target_lang: 目标语言代码
            source_lang: 源语言代码
            context: 上下文信息
            
        Returns:
            Tuple[成功状态, 错误信息, 翻译后的JSON数据]
        """
        try:
            translated_data = {}
            
            for key, value in json_data.items():
                if isinstance(value, dict):
                    # 递归翻译嵌套对象
                    success, error, translated_value = await self.translate_json_structure(
                        value, target_lang, source_lang, context
                    )
                    if not success:
                        return False, error, None
                    translated_data[key] = translated_value
                    
                elif isinstance(value, str):
                    # 翻译字符串值
                    success, error, translated_text = await self.translate_text(
                        value, target_lang, source_lang, context
                    )
                    if not success:
                        logger.warning(f"翻译失败 {key}: {error}")
                        translated_data[key] = value  # 使用原文
                    else:
                        translated_data[key] = translated_text
                else:
                    # 保持非字符串值不变
                    translated_data[key] = value
            
            return True, "", translated_data
            
        except Exception as e:
            logger.error(f"翻译JSON结构失败: {e}")
            return False, f"翻译JSON结构错误: {str(e)}", None
    
    async def batch_translate_texts(
        self, 
        texts: List[str], 
        target_lang: str, 
        source_lang: str = "zh",
        context: Optional[str] = None,
        batch_size: int = 10
    ) -> Dict[str, str]:
        """
        批量翻译文本列表
        
        Args:
            texts: 要翻译的文本列表
            target_lang: 目标语言代码
            source_lang: 源语言代码
            context: 上下文信息
            batch_size: 批处理大小
            
        Returns:
            Dict[原文, 译文] 映射
        """
        results = {}
        
        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_tasks = []
            
            for text in batch_texts:
                task = self.translate_text(text, target_lang, source_lang, context)
                batch_tasks.append(task)
            
            # 并发执行批次
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for text, result in zip(batch_texts, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"批量翻译异常: {text[:30]}... - {result}")
                    results[text] = text  # 使用原文
                else:
                    success, error, translated = result
                    if success:
                        results[text] = translated
                    else:
                        logger.warning(f"批量翻译失败: {text[:30]}... - {error}")
                        results[text] = text  # 使用原文
            
            # 添加延迟避免API限制
            await asyncio.sleep(0.1)
        
        return results
    
    async def translate_i18n_file(
        self, 
        source_file_path: str, 
        target_lang: str, 
        source_lang: str = "zh",
        output_file_path: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        翻译i18n文件
        
        Args:
            source_file_path: 源文件路径
            target_lang: 目标语言代码
            source_lang: 源语言代码
            output_file_path: 输出文件路径，如果为None则覆盖原文件
            
        Returns:
            Tuple[成功状态, 错误信息]
        """
        try:
            # 读取源文件
            with open(source_file_path, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
            
            logger.info(f"开始翻译文件: {source_file_path} -> {target_lang}")
            
            # 翻译内容
            success, error, translated_data = await self.translate_json_structure(
                source_data, target_lang, source_lang, 
                context=f"这是一个Web应用的国际化文件，包含界面文本"
            )
            
            if not success:
                return False, error
            
            # 确定输出文件路径
            if output_file_path is None:
                output_file_path = source_file_path
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            
            # 写入翻译结果
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(translated_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"翻译完成: {output_file_path}")
            return True, ""
            
        except FileNotFoundError:
            return False, f"源文件不存在: {source_file_path}"
        except json.JSONDecodeError as e:
            return False, f"JSON格式错误: {str(e)}"
        except Exception as e:
            logger.error(f"翻译文件失败: {e}")
            return False, f"翻译文件错误: {str(e)}"
    
    async def update_all_i18n_files(
        self, 
        i18n_directory: str = "/workspace/i18n/locales",
        source_lang: str = "zh"
    ) -> Dict[str, Tuple[bool, str]]:
        """
        更新所有i18n文件，使其与源语言文件保持一致
        
        Args:
            i18n_directory: i18n文件目录
            source_lang: 源语言代码
            
        Returns:
            Dict[语言代码, Tuple[成功状态, 错误信息]]
        """
        results = {}
        
        try:
            source_file = os.path.join(i18n_directory, f"{source_lang}.json")
            
            if not os.path.exists(source_file):
                error_msg = f"源语言文件不存在: {source_file}"
                logger.error(error_msg)
                return {"error": (False, error_msg)}
            
            # 获取所有目标语言
            target_languages = [lang for lang in self.supported_languages.keys() if lang != source_lang]
            
            # 并发翻译所有语言
            tasks = []
            for target_lang in target_languages:
                target_file = os.path.join(i18n_directory, f"{target_lang}.json")
                task = self.translate_i18n_file(source_file, target_lang, source_lang, target_file)
                tasks.append((target_lang, task))
            
            # 执行所有翻译任务
            for target_lang, task in tasks:
                try:
                    success, error = await task
                    results[target_lang] = (success, error)
                    if success:
                        logger.info(f"✅ {target_lang} 翻译完成")
                    else:
                        logger.error(f"❌ {target_lang} 翻译失败: {error}")
                except Exception as e:
                    results[target_lang] = (False, f"翻译异常: {str(e)}")
                    logger.error(f"❌ {target_lang} 翻译异常: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"批量更新i18n文件失败: {e}")
            return {"error": (False, f"批量更新失败: {str(e)}")}
    
    def get_supported_languages(self) -> Dict[str, Dict[str, str]]:
        """获取支持的语言列表"""
        return self.supported_languages.copy()
    
    def clear_cache(self):
        """清空翻译缓存"""
        self.translation_cache.clear()
        logger.info("翻译缓存已清空")

# 创建全局翻译服务实例
try:
    deepseek_translation_service = DeepSeekTranslationService()
    logger.info("DeepSeek翻译服务初始化成功")
except Exception as e:
    logger.error(f"DeepSeek翻译服务初始化失败: {e}")
    deepseek_translation_service = None