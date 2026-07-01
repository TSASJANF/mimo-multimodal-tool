# MiMo 多媒体理解工具

使用小米 MiMo V2.5 模型分析图片、音频和视频的图形化工具。

## 功能特点

- 🖼️ **图片理解**: 分析图片内容，支持描述、分类、OCR等
- 🎵 **音频理解**: 分析音频内容，支持转录、描述、分析等
- 🎬 **视频理解**: 分析视频内容，支持描述、场景分析等
- 💾 **配置管理**: 自动保存API配置，方便下次使用
- 📊 **Token统计**: 显示每次分析的Token使用情况

## 支持的格式

| 类型 | 格式 |
|------|------|
| 图片 | JPG, JPEG, PNG, GIF, WebP, BMP |
| 音频 | MP3, WAV, FLAC, M4A, OGG |
| 视频 | MP4, MOV, AVI, WMV |

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install gradio openai
```

### 2. 获取API Key

1. 访问 [MiMo开放平台](https://platform.xiaomimimo.com/console)
2. 注册并登录账号
3. 在控制台获取API Key

### 3. 运行程序

```bash
python app.py
```

程序启动后会自动打开浏览器，访问 http://localhost:7860

## 使用说明

1. **配置API Key**
   - 在界面上方的配置区域输入您的API Key
   - 点击"保存配置"按钮，配置会自动保存到本地

2. **分析媒体文件**
   - 选择对应的Tab（图片/音频/视频）
   - 点击上传区域选择本地文件
   - 可以自定义分析提示词
   - 点击"分析"按钮

3. **查看结果**
   - 分析结果会显示在右侧
   - 结果包含详细的描述和Token使用统计

## ⚠️ URL分析注意事项

某些URL（如抖音）需要特殊请求头才能访问。MiMo API服务器可能无法直接访问这些URL。

**建议方案：**
1. 先使用下载工具保存视频到本地
2. 然后使用"本地文件"方式上传分析

## 配置文件

配置文件保存在用户主目录下：

```
~/.mimo_multimodal_config.json
```

配置内容：
- `api_key`: API密钥
- `base_url`: API基础URL（默认: https://api.xiaomimimo.com/v1）
- `model`: 模型名称（默认: mimo-v2.5）
- `max_completion_tokens`: 最大输出token数（默认: 131072）

## 示例提示词

### 图片分析
- "请详细描述这张图片的内容"
- "这张图片中有哪些文字？"
- "图片中的场景是什么？"
- "识别图片中的物体并分类"

### 音频分析
- "请转录音频中的对话内容"
- "描述音频的背景音乐"
- "音频中说话人的情绪是什么？"
- "这段音频的主要内容是什么？"

### 视频分析
- "请详细描述这个视频的内容"
- "视频中有哪些人物？他们在做什么？"
- "视频的主要情节是什么？"
- "分析视频的场景和环境"

## 注意事项

1. **文件大小限制**
   - 图片: 最大50MB
   - 音频: 最大100MB
   - 视频: 最大500MB

2. **网络要求**
   - 需要能够访问MiMo API服务器
   - 本地文件会转换为Base64上传

3. **费用说明**
   - API调用会产生费用
   - 费用根据Token使用量计算
   - 详见 [MiMo定价](https://mimo.mi.com/docs/price/pay-as-you-go)

## 常见问题

### Q: 提示"请先配置API Key"
A: 请在配置区域输入有效的API Key并点击保存。

### Q: 分析失败
A: 检查网络连接和API Key是否正确，确保文件格式受支持。

### Q: 程序无法启动
A: 确保已安装所有依赖：`pip install -r requirements.txt`

## 技术栈

- **Gradio**: Web界面框架
- **OpenAI Python SDK**: API调用
- **MiMo V2.5**: 小米多模态AI模型

## 许可证

MIT License
