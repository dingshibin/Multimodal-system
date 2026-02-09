import json
import os
from datetime import datetime


class PromptSaver:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save(self, task_type: str, model_name: str, student_level: str, lesson_text: str, pure_prompt: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{timestamp}_{task_type}_{model_name}.json"
        save_path = os.path.join(self.base_dir, file_name)

        data = {
            "metadata": {
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "student_level": student_level,
                "task": task_type,
                "engine": model_name
            },
            "payload": {
                "lesson_source": lesson_text,
                "prompt": pure_prompt  # 这里就是提取后的纯净内容
            }
        }

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return save_path