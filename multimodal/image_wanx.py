import os
import requests
import json
from http import HTTPStatus
from dashscope import ImageSynthesis
import dashscope


class WanXImageGenerator:
    """
    通义万相 WanX-2.5 文生图模块
    """

    def __init__(self, api_key: str = None):
        # 设置 API Key
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        dashscope.api_key = self.api_key
        # 设置基础 URL
        dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

    def generate_from_prompt_file(self, json_path: str, output_dir: str):
        """
        从你之前生成的 Prompt JSON 文件中读取并生成图片
        """
        if not os.path.exists(json_path):
            print(f"❌ 找不到提示词文件: {json_path}")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 根据之前的 PromptSaver 结构提取数据
        pure_prompt = data["payload"]["prompt"]
        student_level = data["metadata"]["student_level"]
        task_type = data["metadata"]["task"]

        print(f"正在为 [{student_level}] 生成 {task_type} 图片...")
        self.execute_generation(pure_prompt, student_level, output_dir)

    def execute_generation(self, prompt: str, level: str, output_dir: str):
        """
        执行模型调用与保存
        """
        os.makedirs(output_dir, exist_ok=True)

        try:
            rsp = ImageSynthesis.call(
                model="wan2.5-t2i-preview",  # 确保使用最新的预览版或正式版
                prompt=prompt,
                n=1,
                size='1280*1280',
                prompt_extend=True,
                watermark=False
            )

            if rsp.status_code == HTTPStatus.OK:
                image_url = rsp.output.results[0].url
                # 文件命名：等级_时间戳.png
                from datetime import datetime
                timestamp = datetime.now().strftime("%H%M%S")
                save_path = os.path.join(output_dir, f"{level}_{timestamp}.png")

                self._download_image(image_url, save_path)
                return save_path
            else:
                print(f"❌ WanX 生成失败: {rsp.message}")
                return None
        except Exception as e:
            print(f"❌ WanX 异常: {e}")
            return None

    def _download_image(self, url: str, save_path: str):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ 图片已保存至: {save_path}")
            else:
                print(f"❌ 下载失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ 下载异常: {e}")