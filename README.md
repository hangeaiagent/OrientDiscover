# 🧭 方向探索派对智能工具

一款集娱乐、教育和社交于一体的方向探索工具，让用户在旅行中通过简单的方向指向，发现世界的奇妙与未知。

## ✨ 功能特性

### 核心功能
- 🧭 **方向检测**: 使用设备传感器获取用户面对的方向
- 📍 **地理定位**: 结合GPS获取用户当前位置
- 🌍 **大圆航线计算**: 基于用户位置和方向，计算地球表面最短路径
- 📏 **分段距离取样**: 支持自定义分段距离（50km/100km/200km）
- 🏛️ **地点信息展示**: 显示路径上的地点卡片，包含图片和趣味介绍

### 模式切换
- 🌟 **现代模式**: 显示当前地点的现代信息
- 📜 **过去模式**: 显示100年前该地点的历史事件
- 🚀 **未来模式**: AI生成未来场景（彩蛋功能）

### 设置选项
- 📐 分段距离调整（50km/100km/200km）
- ⚡ 速度设置（默认120km/h）
- 🎛️ 模式切换界面

## 🛠️ 技术架构

### 前端技术
- **HTML5**: 现代化响应式界面
- **CSS3**: 美观的渐变背景和动画效果
- **JavaScript**: 
  - DeviceOrientationEvent API (方向检测)
  - Geolocation API (位置获取)
  - Fetch API (与后端通信)

### 后端技术
- **Python FastAPI**: 轻量级高性能API框架
- **GeographicLib**: 精确的大圆航线计算
- **Pydantic**: 数据验证和序列化
- **CORS支持**: 跨域请求处理

### 数据存储
- 静态JSON格式地点数据
- 包含坐标、名称、图片和介绍
- 支持多时间模式数据

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 现代浏览器（支持地理位置和设备方向API）
- 网络连接（用于图片加载）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd direction-exploration-party
```

2. **启动后端服务**
```bash
python start_backend.py
```
后端服务将在 http://localhost:8000 启动

3. **启动前端服务**
```bash
python start_frontend.py
```
前端服务将在 http://localhost:3000 启动，浏览器会自动打开

### 使用说明

1. **授权权限**: 首次使用时需要授权地理位置和设备方向权限
2. **获取位置**: 点击"刷新位置"获取当前GPS坐标
3. **调整设置**: 点击设置按钮调整分段距离和模式
4. **开始探索**: 面向想要探索的方向，点击"开始探索"
5. **查看结果**: 浏览生成的地点卡片，了解路径上的有趣地点

## 📱 设备兼容性

### 支持的浏览器
- ✅ Safari (iOS/macOS) - 完整支持
- ✅ Chrome (Android/Desktop) - 完整支持
- ✅ Firefox (Android/Desktop) - 部分支持
- ⚠️ Edge (Desktop) - 部分支持

### 设备要求
- 📱 移动设备: 支持陀螺仪和磁力计的智能手机
- 💻 桌面设备: 可使用模拟方向功能进行测试

## 🔧 开发说明

### 项目结构
```
direction-exploration-party/
├── index.html              # 主页面
├── styles.css              # 样式文件
├── app.js                  # 前端逻辑
├── backend/
│   └── main.py            # 后端API服务
├── requirements.txt        # Python依赖
├── start_backend.py       # 后端启动脚本
├── start_frontend.py      # 前端启动脚本
└── README.md              # 项目说明
```

### API端点
- `POST /api/explore` - 探索方向
- `GET /api/places/{time_mode}` - 获取地点数据
- `GET /api/health` - 健康检查
- `GET /docs` - API文档

### 调试功能
在浏览器控制台中可以使用以下调试函数：
```javascript
// 模拟方向（用于桌面测试）
simulateHeading(90); // 设置为东方

// 查看调试信息
debugInfo();
```

## 🎯 未来规划

### 短期目标
- [ ] 集成真实的地理数据API
- [ ] 添加更多历史数据
- [ ] 优化移动端体验
- [ ] 添加离线模式

### 长期目标
- [ ] AI生成动态内容
- [ ] 社交分享功能
- [ ] 多语言支持
- [ ] 增强现实(AR)集成

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📄 许可证

MIT License - 详见LICENSE文件

## 🙏 致谢

- [GeographicLib](https://geographiclib.sourceforge.io/) - 地理计算库
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [Unsplash](https://unsplash.com/) - 高质量图片资源

---

**享受探索世界的乐趣！** 🌍✨