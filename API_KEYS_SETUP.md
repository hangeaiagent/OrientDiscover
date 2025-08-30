# 🔑 API密钥配置指南

为了使用真实数据功能，你需要申请以下免费API密钥：

## 🌍 OpenWeatherMap Geocoding API（可选）

**用途**: 获取地理位置信息
**费用**: 免费（每月1000次调用）

### 申请步骤：
1. 访问 [OpenWeatherMap](https://openweathermap.org/api)
2. 注册免费账户
3. 在Dashboard中获取API Key
4. 设置环境变量：
   ```bash
   export OPENWEATHER_API_KEY="your_api_key_here"
   ```

## 📸 Unsplash API（可选）

**用途**: 获取高质量地点图片
**费用**: 免费（每小时50次调用）

### 申请步骤：
1. 访问 [Unsplash Developers](https://unsplash.com/developers)
2. 注册开发者账户
3. 创建新应用获取Access Key
4. 设置环境变量：
   ```bash
   export UNSPLASH_API_KEY="your_access_key_here"
   ```

## 🗺️ 当前使用的免费API

### Nominatim OpenStreetMap API
- **用途**: 反向地理编码，获取地点名称
- **费用**: 完全免费
- **限制**: 每秒1次请求
- **无需API密钥**

### Wikipedia API
- **用途**: 获取地点描述信息
- **费用**: 完全免费
- **无需API密钥**

## 🚀 快速开始（无需API密钥）

即使不配置API密钥，真实数据功能也能正常工作：

1. **地点名称**: 使用OpenStreetMap的Nominatim API
2. **地点描述**: 使用Wikipedia API获取摘要
3. **地点图片**: 使用默认占位符图片

## 🔧 环境变量设置

### macOS/Linux:
```bash
# 临时设置（当前会话）
export OPENWEATHER_API_KEY="your_key"
export UNSPLASH_API_KEY="your_key"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export OPENWEATHER_API_KEY="your_key"' >> ~/.zshrc
echo 'export UNSPLASH_API_KEY="your_key"' >> ~/.zshrc
source ~/.zshrc
```

### Windows:
```cmd
# 临时设置
set OPENWEATHER_API_KEY=your_key
set UNSPLASH_API_KEY=your_key

# 永久设置（系统环境变量）
setx OPENWEATHER_API_KEY "your_key"
setx UNSPLASH_API_KEY "your_key"
```

## 📊 数据源对比

| 功能 | 演示数据 | 真实数据 |
|------|----------|----------|
| 地点数量 | 18个预定义城市 | 全球所有地点 |
| 地点名称 | 固定城市名 | 真实地理名称 |
| 地点描述 | 手工编写 | Wikipedia摘要 |
| 地点图片 | 固定Unsplash图片 | 相关主题图片 |
| 响应速度 | 极快 | 稍慢（需API调用） |
| 网络依赖 | 无 | 需要网络连接 |
| 缓存机制 | 无 | 自动缓存减少API调用 |

## 🎯 推荐使用方式

1. **开发测试**: 使用演示数据，快速验证功能
2. **真实体验**: 使用真实数据，获得准确的地理信息
3. **生产环境**: 配置API密钥，获得最佳用户体验

## 🔍 故障排除

### 真实数据返回空结果
- 检查网络连接
- 确认API服务正常运行
- 查看后端日志了解详细错误

### API调用失败
- 检查API密钥是否正确设置
- 确认API配额是否用完
- 检查API服务状态

### 缓存问题
- 删除 `backend/data_cache.json` 文件重新获取数据
- 重启后端服务清除内存缓存
