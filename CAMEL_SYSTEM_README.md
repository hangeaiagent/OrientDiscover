# CAMEL多智能体旅游导航系统

## 🌟 项目简介

基于CAMEL框架的多智能体协作系统，实现一句话生成旅游导航图相册的功能。系统集成了向量数据库、多智能体协作、媒体资源管理等先进技术，为用户提供智能化的旅游规划服务。

## 🏗️ 系统架构

### 核心组件

1. **多智能体系统 (CAMEL Framework)**
   - **需求分析师**: 解析用户输入，提取关键旅游信息
   - **景点搜索专家**: 基于需求搜索匹配景点
   - **内容创作者**: 生成详细介绍和导游词
   - **媒体管理员**: 获取和管理图片视频资源
   - **相册组织者**: 整合信息生成最终相册

2. **向量数据库 (pgvector + Supabase)**
   - 文本向量化和语义搜索
   - 景点内容的向量索引
   - 相似度匹配和推荐

3. **媒体资源管理**
   - 多源图片搜索 (Unsplash, Pexels)
   - 云存储集成 (AWS S3, 本地存储)
   - 图片优化和处理

4. **Web界面**
   - 简洁的一句话输入界面
   - 实时处理状态显示
   - 美观的相册展示

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository_url>
cd workspace

# 安装依赖
pip install -r requirements.txt
```

### 2. 环境配置

创建 `.env` 文件并配置以下变量：

```env
# OpenAI API (必需)
OPENAI_API_KEY=your_openai_api_key

# Supabase 配置 (必需)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_DB_URL=postgresql://user:password@host:port/database

# 图片搜索API (可选)
UNSPLASH_ACCESS_KEY=your_unsplash_key
PEXELS_API_KEY=your_pexels_key

# 云存储配置 (可选)
CLOUD_STORAGE_TYPE=local  # 或 aws_s3
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET=your_bucket_name

# 本地存储路径
LOCAL_STORAGE_PATH=/workspace/media_storage
```

### 3. 数据库初始化

如果使用向量数据库功能：

```bash
# 初始化向量表结构
python -c "
import asyncio
from backend.vector_database import get_vector_database

async def init():
    vector_db = get_vector_database()
    await vector_db.initialize_vector_tables()

asyncio.run(init())
"
```

### 4. 启动系统

#### 方式一：一键启动
```bash
python start_camel_system.py
```

#### 方式二：手动启动
```bash
# 启动后端API
python backend/main.py

# 打开Web界面
open album_generator.html
```

### 5. 系统测试

```bash
# 运行完整测试
python test_camel_system.py

# 测试单个组件
python -c "
import asyncio
from backend.album_orchestrator import get_album_orchestrator

async def test():
    orchestrator = get_album_orchestrator()
    result = await orchestrator.generate_album_from_prompt('我想去北京看故宫')
    print(result)

asyncio.run(test())
"
```

## 📖 API文档

### 核心端点

#### 1. 一句话生成相册
```http
POST /api/generate-album
Content-Type: application/json

{
  "user_prompt": "我想去北京体验传统文化，看故宫、长城",
  "user_id": "user_123",
  "language": "zh-CN"
}
```

#### 2. 快速景点推荐
```http
GET /api/quick-recommendations?latitude=39.9042&longitude=116.4074&interests=历史文化,传统建筑&limit=5
```

#### 3. 向量相似度搜索
```http
POST /api/vector-search
Content-Type: application/json

{
  "query": "北京历史文化景点",
  "latitude": 39.9042,
  "longitude": 116.4074,
  "radius_km": 50,
  "limit": 10
}
```

#### 4. 系统健康检查
```http
GET /api/camel-health
```

### 完整API文档
启动系统后访问: http://localhost:8001/docs

## 🎯 功能特性

### 智能需求理解
- 自然语言处理
- 意图识别和信息提取
- 多维度需求分析

### 智能景点推荐
- 基于向量相似度的语义搜索
- 地理位置和兴趣匹配
- 多数据源景点信息整合

### 内容智能生成
- 个性化景点介绍
- 生动的导游解说词
- 实用的游览建议

### 媒体资源管理
- 多平台图片搜索
- 自动图片优化
- 云存储集成

### 相册智能组织
- 路线规划优化
- 时间安排合理化
- 预算估算

## 🔧 技术栈

- **后端框架**: FastAPI
- **AI框架**: CAMEL, OpenAI GPT-4
- **向量数据库**: pgvector + Supabase
- **数据库**: PostgreSQL + Supabase
- **媒体处理**: Pillow, aiohttp
- **前端**: HTML5 + CSS3 + JavaScript
- **部署**: Uvicorn, Docker (可选)

## 📊 系统监控

### 健康检查端点
- `/api/health` - 基础服务状态
- `/api/camel-health` - CAMEL系统状态
- `/api/spot/health` - 数据库连接状态

### 日志系统
```bash
# 查看系统日志
tail -f backend.log

# 查看特定组件日志
grep "需求分析师" backend.log
```

### 性能指标
- 相册生成响应时间
- 向量搜索查询速度
- 媒体资源获取成功率

## 🛠️ 开发指南

### 添加新的智能体

1. 在 `backend/camel_agents.py` 中创建新的智能体类：

```python
class NewAgent(BaseAgent):
    def __init__(self):
        system_prompt = "你的系统提示词..."
        super().__init__(
            role_name="新智能体",
            role_description="描述",
            system_prompt=system_prompt
        )
    
    async def custom_method(self, input_data):
        # 实现自定义方法
        pass
```

2. 在编排器中集成新智能体：

```python
# 在 album_orchestrator.py 中
self.new_agent = NewAgent()
```

### 扩展向量搜索

```python
# 在 vector_database.py 中添加新的搜索方法
async def custom_search(self, query, filters):
    # 实现自定义搜索逻辑
    pass
```

### 添加新的媒体源

```python
# 在 media_service_enhanced.py 中
async def _search_new_source(self, query, count):
    # 实现新媒体源搜索
    pass
```

## 🐛 故障排除

### 常见问题

1. **API密钥错误**
   ```
   解决方案: 检查.env文件中的API密钥配置
   ```

2. **数据库连接失败**
   ```
   解决方案: 验证Supabase配置和网络连接
   ```

3. **向量搜索失败**
   ```
   解决方案: 确保pgvector扩展已安装并初始化
   ```

4. **媒体资源获取失败**
   ```
   解决方案: 检查图片API配置或使用默认图片
   ```

### 调试模式

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 单步调试智能体
from backend.camel_agents import RequirementAnalyst
analyst = RequirementAnalyst()
result = await analyst.analyze_user_input("测试输入")
```

## 📈 性能优化

### 并发处理
- 智能体并行执行
- 异步API调用
- 批量数据处理

### 缓存策略
- 向量搜索结果缓存
- 媒体资源缓存
- API响应缓存

### 资源管理
- 连接池管理
- 内存使用优化
- 临时文件清理

## 🔒 安全考虑

- API密钥安全存储
- 用户输入验证和过滤
- 数据传输加密
- 访问权限控制

## 📝 更新日志

### v1.0.0 (当前版本)
- ✅ 实现CAMEL多智能体框架
- ✅ 集成向量数据库搜索
- ✅ 媒体资源管理系统
- ✅ Web界面和API端点
- ✅ 系统测试和监控

### 计划功能
- 🔄 多语言支持扩展
- 🔄 移动端适配
- 🔄 用户账户系统
- 🔄 社交分享功能
- 🔄 离线模式支持

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 支持

如有问题或建议，请：
- 创建 Issue
- 发送邮件至 support@example.com
- 查看文档 [Wiki](wiki_url)

---

**🎉 感谢使用CAMEL多智能体旅游导航系统！祝您旅途愉快！**