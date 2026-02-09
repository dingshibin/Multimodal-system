import os
import time
import requests
import json
from datetime import datetime
from volcenginesdkarkruntime import Ark


class SeedanceVideoGenerator:
    """
    豆包 Seedance 文生视频模块 (基于火山引擎 Ark SDK)
    """

    def __init__(self, api_key: str):
        self.client = Ark(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key
        )
        self.model_id = "doubao-seedance-1-5-pro-251215"

    def generate_from_prompt_file(self, json_path: str, output_dir: str):
        """
        从提示词库 JSON 读取并生成视频
        """
        if not os.path.exists(json_path):
            print(f"❌ 未找到文件: {json_path}")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        pure_prompt = data["payload"]["prompt"]
        student_level = data["metadata"]["student_level"]

        return self.execute_generation(pure_prompt, student_level, output_dir)

    def execute_generation(self, prompt: str, level: str, output_dir: str):
        """
        核心逻辑：提交任务 -> 异步轮询 -> 下载保存
        """
        os.makedirs(output_dir, exist_ok=True)
        # 补充视频参数：5秒时长、固定摄像机、水印
        full_prompt = f"{prompt} --duration 5 --camerafixed false --watermark true"

        try:
            print(f"🚀 正在向 Seedance 提交视频生成任务...")
            create_result = self.client.content_generation.tasks.create(
                model=self.model_id,
                content=[{"type": "text", "text": full_prompt}]
            )
            task_id = create_result.id
            print(f"🆔 任务创建成功，ID: {task_id}")

            # 轮询状态
            start_time = time.time()
            while True:
                if time.time() - start_time > 900:  # 15分钟超时
                    print(f"⌛ 视频生成超时。")
                    return None

                get_result = self.client.content_generation.tasks.get(task_id=task_id)
                status = get_result.status

                if status == "succeeded":
                    # 解析 URL
                    video_url = self._parse_url(get_result)
                    if video_url:
                        timestamp = datetime.now().strftime("%H%M%S")
                        save_path = os.path.join(output_dir, f"{level}_{timestamp}.mp4")
                        self._download_video(video_url, save_path)
                        return save_path
                    break
                elif status == "failed":
                    print(f"❌ 视频任务失败: {get_result.error}")
                    break
                else:
                    print(f"⏳ 视频处理中({status})... 15秒后重试")
                    time.sleep(15)
        except Exception as e:
            print(f"❌ Seedance 模块异常: {e}")
            return None

    def _parse_url(self, get_result):
        """解析 API 返回的复杂对象结构"""
        try:
            video_url = get_result.content.video_url
            if hasattr(video_url, 'url'):
                return video_url.url
            return video_url if isinstance(video_url, str) else None
        except:
            return None

    def _download_video(self, url, save_path):
        try:
            response = requests.get(url, stream=True, timeout=60)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✅ 视频已保存: {save_path}")
        except Exception as e:
            print(f"❌ 下载视频异常: {e}")