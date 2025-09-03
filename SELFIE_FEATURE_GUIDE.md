# 景点合影生成功能使用指南

## 功能概述

本功能允许用户为任何景点生成个人合影照片。用户只需上传自己的照片，系统会使用Google Gemini API将用户与景点背景合成，生成逼真的合影照片。

## 功能特点

✅ **已完成的功能:**
- 在每个景点卡片上添加了"📸 生成合影"按钮
- 支持拖拽和点击上传照片
- 照片预览和更换功能
- 自定义提示词支持
- 基于景点的智能提示词生成
- 生成结果展示和下载
- 响应式设计，支持移动设备
- 完整的错误处理和用户反馈

## 使用方法

### 1. 启动服务

```bash
# 启动后端服务
cd /workspace
python3 start_backend.py

# 启动前端服务（新终端）
python3 -m http.server 8000
```

### 2. 使用步骤

1. **探索景点**: 在主界面设置位置和方向，点击"🧭 开始探索"
2. **选择景点**: 在显示的景点列表中，找到想要合影的景点
3. **生成合影**: 点击景点卡片上的"📸 生成合影"按钮
4. **上传照片**: 
   - 点击上传区域选择照片
   - 或直接拖拽照片到上传区域
   - 支持JPG、PNG格式，建议人脸清晰
5. **自定义提示词**（可选）: 留空将使用景点专用的智能提示词
6. **生成照片**: 点击"🎨 生成合影照片"按钮
7. **下载结果**: 生成完成后可以下载或重新生成

## 技术实现

### 前端 (JavaScript)
- `openSelfieGenerator()`: 打开合影生成界面
- `setupPhotoUpload()`: 设置照片上传功能（支持拖拽）
- `generateAttractionPhoto()`: 调用后端API生成合影
- `showGeneratedPhoto()`: 显示生成结果
- `downloadGeneratedPhoto()`: 下载生成的照片

### 后端 (Python + FastAPI)
- **API端点**: `/api/generate-attraction-photo`
- **服务类**: `GeminiImageService` (gemini_service.py)
- **智能提示词**: 针对不同景点的专门提示词库
- **图片处理**: PIL图像处理和base64编码

### Google Gemini API集成
- **模型**: `gemini-2.5-flash-image-preview`
- **功能**: 图像生成和编辑
- **提示词**: 景点特定的合影提示词，保持人脸特征不变

## 支持的景点类型

系统内置了多种著名景点的专门提示词:

### 中国景点
- 长城、故宫、天安门、兵马俑等

### 国际景点  
- 埃菲尔铁塔、罗马斗兽场、自由女神像
- 富士山、东京铁塔、金门大桥
- 金字塔、泰姬陵、悉尼歌剧院等

### 通用景点
- 对于未预设的景点，系统会生成通用的合影提示词

## 文件结构

```
/workspace/
├── app.js                    # 前端JavaScript代码
├── styles.css                # 包含合影功能的CSS样式
├── index.html                # 主界面HTML
├── backend/
│   ├── main.py              # FastAPI后端主文件
│   ├── gemini_service.py    # Gemini API服务
│   └── generated_images/    # 生成图片存储目录
└── requirements.txt         # Python依赖
```

## 样式类名

- `.photo-upload-modal`: 主模态框
- `.upload-area`: 上传区域
- `.photo-preview`: 照片预览
- `.generate-btn`: 生成按钮
- `.loading-indicator`: 加载动画
- `.result-section`: 结果显示区域

## API接口

### POST /api/generate-attraction-photo

**请求参数:**
- `user_photo`: 用户照片文件 (multipart/form-data)
- `attraction_name`: 景点名称 (string)
- `location`: 景点位置 (string, 可选)
- `custom_prompt`: 自定义提示词 (string, 可选)

**响应格式:**
```json
{
  "success": true,
  "data": {
    "filepath": "backend/generated_images/attraction_xxx.png",
    "filename": "attraction_xxx.png", 
    "base64": "data:image/png;base64,xxx",
    "attraction": "景点名称",
    "prompt": "使用的提示词"
  }
}
```

## 注意事项

1. **API密钥**: 需要有效的Google Gemini API密钥
2. **图片质量**: 建议上传人脸清晰、光线良好的照片
3. **文件大小**: 限制10MB以内的图片文件
4. **生成时间**: 根据图片复杂度，生成时间约10-30秒
5. **存储空间**: 生成的图片会保存在服务器上

## 故障排除

### 常见问题

1. **"请先选择照片"**: 确保已上传照片
2. **"生成失败"**: 检查网络连接和API密钥
3. **"无法连接后端"**: 确保后端服务已启动
4. **上传失败**: 检查图片格式和大小

### 调试方法

1. 打开浏览器开发者工具查看网络请求
2. 检查后端日志输出
3. 验证API密钥是否有效
4. 确认generated_images目录权限

## 更新日志

- ✅ 实现基础合影生成功能
- ✅ 添加拖拽上传支持
- ✅ 集成景点专用提示词库
- ✅ 添加响应式设计
- ✅ 实现结果下载功能

---

🎉 **景点合影生成功能已完全实现并可以使用！**

用户现在可以在任何景点位置点击"📸 生成合影"按钮，上传个人照片，生成专业的景点合影照片。