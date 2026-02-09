import os
import re  # 必须导入正则模块
from openai import OpenAI
from typing import Dict, Any

class MultimodalPromptBuilder:
    """
    多模态提示词生成模块
    利用 Qwen 模型为文生图 (WanX) 和 文生视频 (Seedance) 生成专业提示词
    """

    def __init__(self, api_key: str, model: str = "qwen3-max"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.model = model

    def _clean_prompt(self, raw_text: str) -> str:
        """
        最小改动：添加提取逻辑，抓取【提示词开始】与【提示词结束】之间的数据
        """
        pattern = r"【提示词开始】([\s\S]*?)【提示词结束】"
        match = re.search(pattern, raw_text)
        if match:
            return match.group(1).strip()
        return raw_text.strip()  # 如果模型没按格式给标记，则返回全部内容以防报错

    def generate(self, task_type: str, student_level: str, lesson_text: str) -> str:
        if task_type == "image":
            system_prompt = (
                """你是一名优秀的国际中文教师，你也是一名优秀的提示词写作专家，可以为文生图大模型写出清晰、完整的提示词。
            提示词具体要求是：
            1. 提示词公式：内容主体（课文内容场景）+ 话题内容 + 图片风格 + 分辨率和比例。使用【提示词开始】【提示词结束】作为提示词实际内容的标记。
            2. 所有图片的分辨率要求：不得低于150dpi。
            3. 色彩要求：彩色图片的颜色数不低于真彩（16位），灰度图片的灰度级不低于128级。"""
            )
        else:  # video
            system_prompt = (
                """你是一名优秀的国际中文教师，你也是一名优秀的提示词写作专家，可以为文生视频大模型写出清晰、完整的提示词。
                提示词具体要求是：
                1. 提示词公式为：内容主体+场景空间+运动/变化+镜头运动+美感氛围。使用【提示词开始】【提示词结束】作为提示词实际内容的标记。
                2.镜头稳定无抖动，横屏拍摄，音画同步，人物清晰。动画色彩造型和谐、帧与帧之间关联性强，静止画面时间不超过5秒钟。彩色视频每帧图片颜色数不低于256色，黑白不低于128级。
                3.音频与视频有良好同步，音频中要完整包含课文内容。"""
            )

        user_prompt = f"学生等级：{student_level}\n课文内容：{lesson_text}\n\n请根据上述内容生成最适合教学的{task_type}提示词。"

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            raw_content = completion.choices[0].message.content
            # 这里的 self._clean_prompt 现在已经定义好了
            return self._clean_prompt(raw_content)
        except Exception as e:
            return f"Error: {str(e)}"