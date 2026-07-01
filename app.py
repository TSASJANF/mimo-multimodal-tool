#!/usr/bin/env python3
"""
MiMo 多媒体理解工具 - 完整版
使用小米 MiMo V2.5 模型分析图片、音频和视频
"""

import os
import sys
import json
import base64
import mimetypes
import time
from pathlib import Path
from typing import Optional, Tuple

import gradio as gr
from openai import OpenAI

# 配置文件路径
CONFIG_FILE = Path(__file__).parent / "config.json"

# 默认配置
DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://api.xiaomimimo.com/v1",
    "model": "mimo-v2.5",
    "max_completion_tokens": 131072
}

# 支持的文件格式
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}
SUPPORTED_VIDEO_FORMATS = {".mp4", ".mov", ".avi", ".wmv"}

# 默认提示词
DEFAULT_PROMPTS = {
    "image": "请详细描述这张图片的内容，包括场景、物体、颜色、文字等所有细节",
    "audio": "请详细描述这个音频的内容，包括说话内容、背景音乐、声音特点等",
    "video": "请详细描述这个视频的内容，包括人物、场景、动作、对话、文字等所有细节"
}


def load_config() -> dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                return {**DEFAULT_CONFIG, **config}
        except Exception as e:
            print(f"加载配置失败: {e}")
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> str:
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return f"✅ 配置已保存到: {CONFIG_FILE}"
    except Exception as e:
        return f"❌ 保存配置失败: {e}"


def get_mime_type(file_path: str) -> str:
    """获取文件的MIME类型"""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    
    ext = Path(file_path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
        ".mp3": "audio/mpeg", ".wav": "audio/wav", ".flac": "audio/flac",
        ".m4a": "audio/mp4", ".ogg": "audio/ogg",
        ".mp4": "video/mp4", ".mov": "video/quicktime",
        ".avi": "video/x-msvideo", ".wmv": "video/x-ms-wmv"
    }
    return mime_map.get(ext, "application/octet-stream")


def file_to_base64(file_path: str) -> str:
    """将文件转换为Base64编码"""
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")


def create_client(api_key: str, base_url: str) -> OpenAI:
    """创建OpenAI客户端，设置较长超时"""
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=1800.0,  # 30分钟超时，流式输出需要更长时间
        max_retries=0
    )


def analyze_image(
    image_source: str,
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
    max_tokens: int,
    source_type: str = "file"
):
    """分析图片 - 流式输出"""
    if not api_key:
        yield "❌ 请先配置API Key"
        return
    
    try:
        client = create_client(api_key, base_url)
        
        if source_type == "url":
            image_url = image_source
        else:
            if not image_source or not os.path.exists(image_source):
                yield "❌ 请选择有效的图片文件"
                return
            base64_data = file_to_base64(image_source)
            mime_type = get_mime_type(image_source)
            image_url = f"data:{mime_type};base64,{base64_data}"
        
        start_time = time.time()
        full_result = ""
        
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are MiMo, an AI assistant developed by Xiaomi."},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            max_completion_tokens=max_tokens,
            stream=True
        )
        
        for chunk in stream:
            try:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        full_result += delta.content
                        yield full_result
            except (IndexError, AttributeError):
                continue
        
        elapsed = time.time() - start_time
        final_result = full_result + f"\n\n{'='*50}\n耗时: {elapsed:.1f}秒"
        yield final_result
    
    except Exception as e:
        yield f"❌ 分析失败: {str(e)}"


def analyze_audio(
    audio_source: str,
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
    max_tokens: int,
    source_type: str = "file"
):
    """分析音频 - 流式输出"""
    if not api_key:
        yield "❌ 请先配置API Key"
        return
    
    try:
        client = create_client(api_key, base_url)
        
        if source_type == "url":
            audio_data = audio_source
        else:
            if not audio_source or not os.path.exists(audio_source):
                yield f"❌ 音频文件不存在: {audio_source}"
                return
            
            # 检查文件大小
            file_size = os.path.getsize(audio_source)
            print(f"[DEBUG] 音频文件: {audio_source}, 大小: {file_size} bytes")
            
            if file_size == 0:
                yield "❌ 音频文件为空"
                return
            
            # 检查文件扩展名
            ext = Path(audio_source).suffix.lower()
            print(f"[DEBUG] 文件扩展名: {ext}")
            
            if ext not in SUPPORTED_AUDIO_FORMATS:
                yield f"❌ 不支持的音频格式: {ext}\n支持的格式: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
                return
            
            # 读取文件内容
            with open(audio_source, 'rb') as f:
                audio_bytes = f.read()
            
            print(f"[DEBUG] 读取文件成功, {len(audio_bytes)} bytes")
            
            base64_data = base64.b64encode(audio_bytes).decode('utf-8')
            mime_type = get_mime_type(audio_source)
            audio_data = f"data:{mime_type};base64,{base64_data}"
            print(f"[DEBUG] MIME类型: {mime_type}, Base64长度: {len(base64_data)}")
        
        start_time = time.time()
        full_result = ""
        
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are MiMo, an AI assistant developed by Xiaomi."},
                {
                    "role": "user",
                    "content": [
                        {"type": "input_audio", "input_audio": {"data": audio_data}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            max_completion_tokens=max_tokens,
            stream=True
        )
        
        for chunk in stream:
            try:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        full_result += delta.content
                        yield full_result
            except (IndexError, AttributeError) as e:
                # 跳过有问题的chunk
                continue
        
        elapsed = time.time() - start_time
        final_result = full_result + f"\n\n{'='*50}\n耗时: {elapsed:.1f}秒"
        yield final_result
    
    except IndexError as e:
        yield f"❌ 音频格式不兼容，请尝试其他音频文件\n错误详情: {str(e)}"
    except Exception as e:
        yield f"❌ 分析失败: {str(e)}"


def analyze_video(
    video_source: str,
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
    max_tokens: int,
    fps: float = 2.0,
    media_resolution: str = "default",
    source_type: str = "file"
):
    """分析视频 - 流式输出"""
    if not api_key:
        yield "❌ 请先配置API Key"
        return
    
    try:
        client = create_client(api_key, base_url)
        
        if source_type == "url":
            video_url = video_source
            print(f"[DEBUG] 视频URL: {video_url}")
        else:
            if not video_source or not os.path.exists(video_source):
                yield "❌ 请选择有效的视频文件"
                return
            file_size = os.path.getsize(video_source)
            print(f"[DEBUG] 视频文件: {video_source}, 大小: {file_size} bytes")
            base64_data = file_to_base64(video_source)
            mime_type = get_mime_type(video_source)
            video_url = f"data:{mime_type};base64,{base64_data}"
            print(f"[DEBUG] MIME类型: {mime_type}, Base64长度: {len(base64_data)}")
        
        start_time = time.time()
        full_result = ""
        
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are MiMo, an AI assistant developed by Xiaomi."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "video_url",
                            "video_url": {"url": video_url},
                            "fps": fps,
                            "media_resolution": media_resolution
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            max_completion_tokens=max_tokens,
            stream=True
        )
        
        for chunk in stream:
            try:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        full_result += delta.content
                        yield full_result
            except (IndexError, AttributeError):
                continue
        
        elapsed = time.time() - start_time
        final_result = full_result + f"\n\n{'='*50}\n耗时: {elapsed:.1f}秒"
        yield final_result
    
    except ConnectionError as e:
        yield f"❌ 网络连接错误: {str(e)}\n\n建议：尝试使用较小的视频文件或降低帧率(FPS)"
    except Exception as e:
        error_msg = str(e)
        if "incomplete chunked read" in error_msg:
            yield f"❌ 连接中断: API服务器提前关闭了连接\n\n可能原因：\n1. 视频文件过大\n2. 网络不稳定\n3. 服务器超时\n\n建议：\n1. 尝试使用较小的视频文件\n2. 降低FPS参数\n3. 稍后重试"
        else:
            yield f"❌ 分析失败: {error_msg}"


def create_ui():
    """创建Gradio界面"""
    config = load_config()
    
    with gr.Blocks(title="MiMo 多媒体理解工具") as app:
        gr.Markdown("# 🎨 MiMo 多媒体理解工具\n使用小米 MiMo V2.5 模型分析图片、音频和视频")
        
        # 配置区域
        with gr.Accordion("⚙️ 配置设置", open=not config.get("api_key")):
            with gr.Row():
                api_key_input = gr.Textbox(
                    label="API Key",
                    value=config.get("api_key", ""),
                    type="password",
                    placeholder="请输入您的 MiMo API Key",
                    scale=3
                )
                save_config_btn = gr.Button("💾 保存配置", scale=1, variant="secondary")
            
            with gr.Row():
                base_url_input = gr.Textbox(
                    label="API Base URL",
                    value=config.get("base_url", "https://api.xiaomimimo.com/v1"),
                    scale=2
                )
                model_input = gr.Textbox(
                    label="模型名称",
                    value=config.get("model", "mimo-v2.5"),
                    scale=1
                )
                max_tokens_input = gr.Slider(
                    label="最大输出Token",
                    minimum=256,
                    maximum=131072,
                    value=config.get("max_completion_tokens", 131072),
                    step=1024,
                    scale=1
                )
            
            config_status = gr.Textbox(label="配置状态", interactive=False)
        
        # 主功能区域
        with gr.Tabs():
            # ==================== 图片理解Tab ====================
            with gr.Tab("🖼️ 图片理解"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 输入")
                        image_source_type = gr.Radio(
                            label="图片来源",
                            choices=["本地文件", "远程URL"],
                            value="本地文件"
                        )
                        image_file_input = gr.Image(label="选择图片", type="filepath", visible=True)
                        image_url_input = gr.Textbox(
                            label="图片URL",
                            placeholder="https://example.com/image.jpg",
                            visible=False
                        )
                        image_prompt = gr.Textbox(
                            label="分析提示词",
                            value=DEFAULT_PROMPTS["image"],
                            lines=3
                        )
                        image_btn = gr.Button("🔍 分析图片", variant="primary", size="lg")
                        image_status = gr.Textbox(label="状态", value="", interactive=False)
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 输出")
                        image_output = gr.Markdown(label="分析结果")
                
                def toggle_image_input(source_type):
                    return (
                        gr.update(visible=source_type == "本地文件"),
                        gr.update(visible=source_type == "远程URL")
                    )
                
                image_source_type.change(
                    fn=toggle_image_input,
                    inputs=[image_source_type],
                    outputs=[image_file_input, image_url_input]
                )
            
            # ==================== 音频理解Tab ====================
            with gr.Tab("🎵 音频理解"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 输入")
                        audio_source_type = gr.Radio(
                            label="音频来源",
                            choices=["本地文件", "远程URL"],
                            value="本地文件"
                        )
                        audio_file_input = gr.Audio(label="选择音频", type="filepath", visible=True)
                        audio_url_input = gr.Textbox(
                            label="音频URL",
                            placeholder="https://example.com/audio.mp3",
                            visible=False
                        )
                        audio_prompt = gr.Textbox(
                            label="分析提示词",
                            value=DEFAULT_PROMPTS["audio"],
                            lines=3
                        )
                        audio_btn = gr.Button("🔍 分析音频", variant="primary", size="lg")
                        audio_status = gr.Textbox(label="状态", value="", interactive=False)
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 输出")
                        audio_output = gr.Markdown(label="分析结果")
                
                def toggle_audio_input(source_type):
                    return (
                        gr.update(visible=source_type == "本地文件"),
                        gr.update(visible=source_type == "远程URL")
                    )
                
                audio_source_type.change(
                    fn=toggle_audio_input,
                    inputs=[audio_source_type],
                    outputs=[audio_file_input, audio_url_input]
                )
            
            # ==================== 视频理解Tab ====================
            with gr.Tab("🎬 视频理解"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 输入")
                        video_source_type = gr.Radio(
                            label="视频来源",
                            choices=["本地文件", "远程URL"],
                            value="本地文件"
                        )
                        video_file_input = gr.Video(label="选择视频", visible=True)
                        video_url_input = gr.Textbox(
                            label="视频URL",
                            placeholder="https://example.com/video.mp4",
                            visible=False
                        )
                        video_prompt = gr.Textbox(
                            label="分析提示词",
                            value=DEFAULT_PROMPTS["video"],
                            lines=3
                        )
                        
                        gr.Markdown("### ⚙️ 视频参数")
                        with gr.Row():
                            video_fps = gr.Slider(
                                label="抽帧率 (FPS)",
                                minimum=0.1,
                                maximum=10.0,
                                value=2.0,
                                step=0.1,
                                info="每秒抽取的帧数，越高越精细，Token消耗越多"
                            )
                            video_resolution = gr.Radio(
                                label="分辨率档次",
                                choices=["default", "max"],
                                value="default",
                                info="default: 平衡效果与效率; max: 最高分辨率"
                            )
                        
                        video_btn = gr.Button("🔍 分析视频", variant="primary", size="lg")
                        video_status = gr.Textbox(label="状态", value="", interactive=False)
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 输出")
                        video_output = gr.Markdown(label="分析结果")
                
                def toggle_video_input(source_type):
                    return (
                        gr.update(visible=source_type == "本地文件"),
                        gr.update(visible=source_type == "远程URL")
                    )
                
                video_source_type.change(
                    fn=toggle_video_input,
                    inputs=[video_source_type],
                    outputs=[video_file_input, video_url_input]
                )
        
        # 使用说明
        with gr.Accordion("📖 使用说明", open=False):
            gr.Markdown("""
            ### 支持的格式
            | 类型 | 格式 |
            |------|------|
            | 图片 | JPG, JPEG, PNG, GIF, WebP, BMP |
            | 音频 | MP3, WAV, FLAC, M4A, OGG |
            | 视频 | MP4, MOV, AVI, WMV |
            
            ### 视频参数说明
            - **FPS (抽帧率)**: 范围 [0.1, 10]，默认 2
            - **分辨率档次**: `default` 或 `max`
            
            ### 获取API Key
            请访问 [MiMo开放平台](https://platform.xiaomimimo.com/console)
            """)
        
        # ==================== 事件处理 ====================
        def on_save_config(api_key, base_url, model, max_tokens):
            config = {
                "api_key": api_key,
                "base_url": base_url,
                "model": model,
                "max_completion_tokens": int(max_tokens)
            }
            return save_config(config)
        
        def on_analyze_image(source_type, file_path, url, prompt, api_key, base_url, model, max_tokens):
            # 先返回状态
            yield "", "⏳ 正在分析图片，请稍候..."
            if source_type == "远程URL":
                if not url:
                    yield "❌ 请输入图片URL", ""
                    return
                gen = analyze_image(url, prompt, api_key, base_url, model, int(max_tokens), "url")
            else:
                if not file_path:
                    yield "❌ 请选择图片文件", ""
                    return
                gen = analyze_image(file_path, prompt, api_key, base_url, model, int(max_tokens), "file")
            
            for result in gen:
                yield result, "⏳ 正在分析..."
            yield result, "✅ 分析完成"
        
        def on_analyze_audio(source_type, file_path, url, prompt, api_key, base_url, model, max_tokens):
            yield "", "⏳ 正在分析音频，请稍候..."
            if source_type == "远程URL":
                if not url:
                    yield "❌ 请输入音频URL", ""
                    return
                gen = analyze_audio(url, prompt, api_key, base_url, model, int(max_tokens), "url")
            else:
                if not file_path:
                    yield "❌ 请选择音频文件", ""
                    return
                gen = analyze_audio(file_path, prompt, api_key, base_url, model, int(max_tokens), "file")
            
            for result in gen:
                yield result, "⏳ 正在分析..."
            yield result, "✅ 分析完成"
        
        def on_analyze_video(source_type, file_path, url, prompt, api_key, base_url, model, max_tokens, fps, resolution):
            yield "", "⏳ 正在分析视频，请稍候..."
            if source_type == "远程URL":
                if not url:
                    yield "❌ 请输入视频URL", ""
                    return
                gen = analyze_video(url, prompt, api_key, base_url, model, int(max_tokens), fps, resolution, "url")
            else:
                if not file_path:
                    yield "❌ 请选择视频文件", ""
                    return
                gen = analyze_video(file_path, prompt, api_key, base_url, model, int(max_tokens), fps, resolution, "file")
            
            for result in gen:
                yield result, "⏳ 正在分析..."
            yield result, "✅ 分析完成"
        
        # 绑定事件
        save_config_btn.click(
            fn=on_save_config,
            inputs=[api_key_input, base_url_input, model_input, max_tokens_input],
            outputs=[config_status]
        )
        
        image_btn.click(
            fn=on_analyze_image,
            inputs=[image_source_type, image_file_input, image_url_input, image_prompt,
                    api_key_input, base_url_input, model_input, max_tokens_input],
            outputs=[image_output, image_status]
        )
        
        audio_btn.click(
            fn=on_analyze_audio,
            inputs=[audio_source_type, audio_file_input, audio_url_input, audio_prompt,
                    api_key_input, base_url_input, model_input, max_tokens_input],
            outputs=[audio_output, audio_status]
        )
        
        video_btn.click(
            fn=on_analyze_video,
            inputs=[video_source_type, video_file_input, video_url_input, video_prompt,
                    api_key_input, base_url_input, model_input, max_tokens_input,
                    video_fps, video_resolution],
            outputs=[video_output, video_status]
        )
    
    return app


def main():
    """主函数"""
    print("=" * 50)
    print("MiMo 多媒体理解工具")
    print("=" * 50)
    print(f"配置文件: {CONFIG_FILE}")
    
    try:
        import gradio
        import openai
        print(f"Gradio版本: {gradio.__version__}")
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("请运行: pip install gradio openai")
        sys.exit(1)
    
    app = create_ui()
    app.queue()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True,
        show_error=True,
        theme=gr.themes.Soft()
    )


if __name__ == "__main__":
    main()
