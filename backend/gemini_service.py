import os
import base64
import google.generativeai as genai
from PIL import Image
from io import BytesIO
from datetime import datetime
import logging
from typing import Optional, Tuple
import tempfile
from fastapi import UploadFile
import json

# 配置日志
logger = logging.getLogger(__name__)

# 配置 Google Gemini API
GEMINI_API_KEY = "AIzaSyC3fc8-5r4SWOISs0IIduiE4TOvE8-aFC0"
genai.configure(api_key=GEMINI_API_KEY)

class GeminiImageService:
    """Google Gemini 图片生成服务"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        self.output_dir = "backend/generated_images"
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_attraction_prompt(
        self, 
        attraction_name: str, 
        location: str = None,
        category: str = None,
        description: str = None,
        opening_hours: str = None,
        ticket_price: str = None,
        latitude: float = None,
        longitude: float = None
    ) -> str:
        """
        根据景点完整信息生成智能合影提示词
        
        Args:
            attraction_name: 景点名称
            location: 景点位置（城市或国家）
            category: 景点类别
            description: 景点描述
            opening_hours: 开放时间
            ticket_price: 门票价格
            latitude: 纬度
            longitude: 经度
            
        Returns:
            生成的智能提示词
        """
        # 景点特定的提示词模板（保留原有的特定景点）
        attraction_prompts = {
            # 中国景点
            "长城": "让图中的人站在万里长城上，背景是蜿蜒的长城和远山，穿着休闲旅游装，做出胜利的手势，天气晴朗，蓝天白云。保持人脸的原貌不变。",
            "故宫": "让图中的人站在故宫太和殿前，背景是金碧辉煌的宫殿建筑，穿着现代休闲装，自然地微笑，阳光明媚。保持人脸的原貌不变。",
            "天安门": "让图中的人站在天安门广场前，背景是雄伟的天安门城楼，穿着休闲装，自然地站立或做和平手势，蓝天白云。保持人脸的原貌不变。",
            "兵马俑": "让图中的人站在秦始皇兵马俑坑旁，背景是整齐排列的兵马俑军阵，穿着现代装束，表情惊叹，保持人脸的原貌不变。",
            
            # 日本景点
            "富士山": "让图中的人站在富士山前，背景是雪顶的富士山和樱花树，穿着日式休闲装或和服，开心地微笑，春天的氛围。保持人脸的原貌不变。",
            "东京铁塔": "让图中的人站在东京铁塔前，背景是红白相间的铁塔和现代化城市，穿着时尚休闲装，做出拍照姿势。保持人脸的原貌不变。",
            "清水寺": "让图中的人站在京都清水寺前，背景是传统的日式寺庙建筑和红叶，穿着和服或休闲装，优雅地站立。保持人脸的原貌不变。",
            
            # 欧洲景点
            "埃菲尔铁塔": "让图中的人站在埃菲尔铁塔前，背景是标志性的铁塔和塞纳河，穿着优雅的休闲装，浪漫的氛围，黄昏时分。保持人脸的原貌不变。",
            "罗马斗兽场": "让图中的人站在罗马斗兽场前，背景是古老的圆形竞技场，穿着休闲夏装，做出胜利手势，阳光明媚。保持人脸的原貌不变。",
            "大本钟": "让图中的人站在伦敦大本钟前，背景是威斯敏斯特宫和泰晤士河，穿着英伦风格服装，优雅地站立。保持人脸的原貌不变。",
            
            # 美洲景点
            "自由女神像": "让图中的人站在自由女神像前，背景是纽约港和自由女神像，穿着美式休闲装，举起手臂模仿自由女神的姿势。保持人脸的原貌不变。",
            "金门大桥": "让图中的人站在旧金山金门大桥前，背景是红色的大桥和海湾，穿着休闲装，享受海风，夕阳西下。保持人脸的原貌不变。",
            "尼亚加拉瀑布": "让图中的人站在尼亚加拉瀑布观景台，背景是壮观的瀑布和彩虹，穿着防水外套，表情兴奋。保持人脸的原貌不变。",
            
            # 其他著名景点
            "金字塔": "让图中的人站在埃及金字塔前，背景是吉萨金字塔群和狮身人面像，穿着探险装束，沙漠的金色阳光。保持人脸的原貌不变。",
            "泰姬陵": "让图中的人站在印度泰姬陵前，背景是白色大理石的泰姬陵，穿着印度传统服装或休闲装，日出时分。保持人脸的原貌不变。",
            "悉尼歌剧院": "让图中的人站在悉尼歌剧院前，背景是标志性的贝壳形建筑和海港大桥，穿着夏装，阳光灿烂。保持人脸的原貌不变。"
        }
        
        # 查找匹配的景点提示词
        for key, prompt in attraction_prompts.items():
            if key in attraction_name:
                return prompt
        
        # 如果没有找到特定景点，基于详细信息生成智能提示词
        return self._generate_intelligent_prompt(
            attraction_name, location, category, description, 
            opening_hours, ticket_price, latitude, longitude
        )
    
    def _generate_intelligent_prompt(
        self, 
        attraction_name: str, 
        location: str = None,
        category: str = None,
        description: str = None,
        opening_hours: str = None,
        ticket_price: str = None,
        latitude: float = None,
        longitude: float = None
    ) -> str:
        """
        基于景点详细信息生成智能提示词
        """
        prompt_parts = []
        
        # 基础合影描述
        location_str = f"在{location}" if location else ""
        prompt_parts.append(f"让图中的人物与{attraction_name}{location_str}进行完美的合影合成。")
        
        # 根据类别确定背景风格
        if category:
            category_backgrounds = {
                '寺庙': '庄严神圣的寺庙建筑，金碧辉煌的佛殿，古典的东方建筑风格，香火缭绕的神圣氛围',
                '博物馆': '现代化的博物馆建筑外观，展现文化艺术的高雅氛围，知识殿堂的庄重感',
                '公园': '美丽的自然公园景观，绿树成荫，花草繁茂，清新的空气和宁静的环境',
                '古迹': '历史悠久的古代建筑遗迹，斑驳的石墙，深厚的历史文化底蕴',
                '山峰': '雄伟壮观的山峰景色，云雾缭绕，气势磅礴的自然风光',
                '海滩': '碧海蓝天的海滩风光，白沙细软，海浪轻拍，热带度假氛围',
                '城市地标': '标志性的城市建筑，现代化的都市风光，繁华的城市天际线',
                '自然景观': '壮美的自然风光，山川河流，原生态的自然环境',
                '文化景点': '具有当地文化特色的建筑和环境，传统与现代的完美融合',
                '购物': '繁华的商业街区，现代化的购物中心，充满活力的商业氛围',
                '娱乐': '充满活力的娱乐场所，欢乐的游乐设施，热闹的娱乐氛围'
            }
            
            for key, bg_desc in category_backgrounds.items():
                if key in category:
                    prompt_parts.append(f"背景是{bg_desc}。")
                    break
            else:
                prompt_parts.append(f"背景是{attraction_name}的标志性景观和建筑。")
        
        # 根据描述添加具体细节
        if description:
            detail_keywords = {
                '古老': '古朴典雅的建筑风格，历史的厚重感',
                '现代': '现代化的建筑设计，时尚的都市风格',
                '宏伟': '气势恢宏的建筑规模，令人震撼的视觉效果',
                '精美': '精美细致的装饰细节，工艺精湛的艺术价值',
                '壮观': '令人震撼的壮观景象，大自然的鬼斧神工',
                '美丽': '风景如画的美丽环境，赏心悦目的自然风光',
                '历史': '深厚的历史文化氛围，岁月沉淀的文化价值',
                '神圣': '庄严神圣的宗教氛围，虔诚肃穆的精神感受',
                '自然': '原生态的自然环境，天然未雕琢的纯净美感',
                '繁华': '繁华热闹的都市景象，充满活力的现代生活'
            }
            
            for keyword, enhancement in detail_keywords.items():
                if keyword in description:
                    prompt_parts.append(f"展现{enhancement}。")
                    break
        
        # 根据位置添加地域特色服装和氛围
        if location:
            location_styles = {
                '中国': '穿着中式休闲装或具有中国特色的服装，体现东方文化的优雅',
                '日本': '穿着日式休闲装，体现日本文化的精致与和谐',
                '法国': '穿着法式优雅的休闲装，体现法式浪漫与艺术气息',
                '英国': '穿着英伦风格的服装，体现绅士淑女的优雅气质',
                '美国': '穿着美式休闲装，体现自由活力的美式风格',
                '意大利': '穿着意式时尚休闲装，体现地中海的浪漫风情',
                '德国': '穿着简约实用的德式服装，体现严谨与品质',
                '澳大利亚': '穿着轻松的夏装，体现阳光海滩的休闲氛围'
            }
            
            for country, style in location_styles.items():
                if country in location:
                    prompt_parts.append(style)
                    break
            else:
                prompt_parts.append(f"穿着适合{location}当地文化和气候的得体服装")
        else:
            prompt_parts.append("穿着适合旅游的休闲装")
        
        # 添加表情和姿态
        prompt_parts.append("表情自然愉悦，姿态放松自然，展现出旅游的快乐心情。")
        
        # 根据开放时间推断最佳拍摄时间
        time_atmosphere = "阳光明媚的白天"
        if opening_hours:
            if "夜" in opening_hours or "晚" in opening_hours:
                time_atmosphere = "华灯初上的夜晚，灯光璀璨"
            elif "早" in opening_hours:
                time_atmosphere = "清晨的柔和阳光"
            elif "黄昏" in opening_hours or "日落" in opening_hours:
                time_atmosphere = "黄昏时分的金色光线"
        
        prompt_parts.append(f"拍摄时间：{time_atmosphere}，营造温馨浪漫的拍照氛围。")
        
        # 添加技术要求
        prompt_parts.append("图片要求：高清画质，色彩饱和，构图协调，光线自然。")
        prompt_parts.append("特别重要：完全保持人物的面部特征、肤色、发型、体型等所有个人特征不变，只改变服装风格和背景环境。")
        
        return "".join(prompt_parts)
    
    async def generate_attraction_photo(
        self, 
        user_photo: UploadFile,
        attraction_name: str,
        location: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        opening_hours: Optional[str] = None,
        ticket_price: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        custom_prompt: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        生成景点合影照片
        
        Args:
            user_photo: 用户上传的照片
            attraction_name: 景点名称
            location: 景点位置
            category: 景点类别
            description: 景点描述
            opening_hours: 开放时间
            ticket_price: 门票价格
            latitude: 纬度
            longitude: 经度
            custom_prompt: 自定义提示词（可选）
            
        Returns:
            (成功标志, 消息, 生成的图片路径或错误信息)
        """
        try:
            # 读取用户上传的图片
            image_data = await user_photo.read()
            user_image = Image.open(BytesIO(image_data))
            
            # 将图片转换为RGB格式（如果需要）
            if user_image.mode not in ('RGB', 'RGBA'):
                user_image = user_image.convert('RGB')
            
            # 生成提示词
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self.generate_attraction_prompt(
                    attraction_name=attraction_name,
                    location=location,
                    category=category,
                    description=description,
                    opening_hours=opening_hours,
                    ticket_price=ticket_price,
                    latitude=latitude,
                    longitude=longitude
                )
            
            logger.info(f"生成景点合影 - 景点: {attraction_name}, 提示词: {prompt}")
            
            # 调用 Gemini API 生成图片
            contents = [prompt, user_image]
            response = self.model.generate_content(contents)
            
            # 处理响应
            response_dict = response.to_dict()
            
            if "candidates" in response_dict and len(response_dict["candidates"]) > 0:
                parts = response_dict["candidates"][0]["content"]["parts"]
                
                for part in parts:
                    if "inline_data" in part:
                        # 解码base64图像数据
                        image_data = base64.b64decode(part["inline_data"]["data"])
                        
                        # 使用PIL保存图像
                        generated_image = Image.open(BytesIO(image_data))
                        
                        # 生成带时间戳的文件名
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_attraction_name = "".join(c for c in attraction_name if c.isalnum() or c in ('_', '-'))[:30]
                        filename = f"attraction_{safe_attraction_name}_{timestamp}.png"
                        filepath = os.path.join(self.output_dir, filename)
                        
                        # 保存图片
                        generated_image.save(filepath)
                        logger.info(f"✅ 景点合影已生成: {filepath}")
                        
                        # 同时返回base64编码的图片数据，方便前端直接显示
                        buffered = BytesIO()
                        generated_image.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        
                        return True, "景点合影生成成功", {
                            "filepath": filepath,
                            "filename": filename,
                            "base64": f"data:image/png;base64,{img_base64}",
                            "attraction": attraction_name,
                            "prompt": prompt
                        }
            
            return False, "生成失败：API未返回图片数据", None
            
        except Exception as e:
            error_msg = f"生成景点合影时出错: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def get_generated_images(self, limit: int = 10) -> list:
        """
        获取最近生成的图片列表
        
        Args:
            limit: 返回的图片数量限制
            
        Returns:
            图片信息列表
        """
        try:
            images = []
            if os.path.exists(self.output_dir):
                files = os.listdir(self.output_dir)
                image_files = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg'))]
                
                # 按修改时间排序
                image_files.sort(
                    key=lambda x: os.path.getmtime(os.path.join(self.output_dir, x)),
                    reverse=True
                )
                
                for filename in image_files[:limit]:
                    filepath = os.path.join(self.output_dir, filename)
                    images.append({
                        "filename": filename,
                        "filepath": filepath,
                        "created_at": datetime.fromtimestamp(
                            os.path.getmtime(filepath)
                        ).isoformat()
                    })
            
            return images
            
        except Exception as e:
            logger.error(f"获取生成的图片列表时出错: {str(e)}")
            return []

# 创建全局服务实例
gemini_service = GeminiImageService()
