import re
from typing import Dict


class TeachingPlanParser:
    """
    教案解析器：从教案中提取纯净的课文及其他教学要素
    """

    def __init__(self, teaching_plan_text: str):
        self.text = teaching_plan_text

    def extract_lesson_text(self) -> str:
        """
        提取标记内的纯净课文内容
        """
        # 尝试匹配标记内的内容
        tag_pattern = r"【课文开始】([\s\S]*?)【课文结束】"
        match = re.search(tag_pattern, self.text)
        if match:
            return match.group(1).strip()

        # 如果模型没有生成标记，降级使用标题匹配逻辑（兼容性处理）
        fallback_pattern = r"（二）课文([\s\S]*?)（三）语法"
        match = re.search(fallback_pattern, self.text)
        return match.group(1).strip() if match else ""

    def extract_vocab(self) -> str:
        pattern = r"（一）生词([\s\S]*?)（二）课文"
        match = re.search(pattern, self.text)
        return match.group(1).strip() if match else ""

    def parse(self) -> Dict[str, str]:
        return {
            "lesson_text": self.extract_lesson_text(),
            "vocabulary": self.extract_vocab()
        }