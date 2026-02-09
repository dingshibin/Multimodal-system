from openai import OpenAI
import os
import json
from typing import Dict, Any
from datetime import datetime


class QwenTeachingPlanGenerator:
    """
    国际中文教学教案生成模块（Qwen）
    输入：学生等级 + 话题 / 文本
    输出：结构化教学教案（文本）+ JSON 入库
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = "qwen3-max",
        temperature: float = 0.7,
        top_p: float = 0.3,
        save_dir: str = r"storage\teaching_db"
    ):
        # ========= API Key =========
        if api_key is None:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if api_key is None:
                raise ValueError("未检测到 DASHSCOPE_API_KEY，请设置环境变量或直接传入")

        # ========= Client =========
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    # =====================================================
    # 教案生成主函数
    # =====================================================
    def generate_teaching_plan(
        self,
        student_level: str,
        content: str,
        save: bool = True
    ) -> Dict[str, Any]:

        system_prompt = """你是一名优秀的国际中文教师，具有优秀的教学组织能力和教案撰写能力。
你必须严格按照规定结构撰写教案，不得缺项，不得合并栏目。

教案结构如下：

一、教学目标
（一）知识目标
（二）技能目标
（三）情感与文化目标

二、教学内容
（一）生词（包括拼音、词性、英文释义、例句）
（二）课文
    - 若输入内容为完整文本，请直接以输入内容作为课文，不能修改
    - 若输入内容为话题，请围绕话题生成课文，并使用【课文开始】【课文结束】标记
    - 对话体课文需明确交际场景
（三）语法（包括：中文解释、英文解释、例句、练习）
（四）汉字（与主题和生词相关）
（五）文化（与主题相关）

三、教学重点与难点
（一）教学重点
（二）教学难点

四、教学步骤（45分钟）
五、教学方法
"""

        user_prompt = f"""
本次课程的学生汉语水平为：{student_level}。
输入内容为：{content}。

请根据学生汉语水平和输入内容，
撰写一份可直接用于数字化国际中文教学的详细、完整教案。
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
                temperature=self.temperature,
                top_p=self.top_p
            )

            teaching_plan_text = completion.choices[0].message.content

            result = {
                "success": True,
                "student_level": student_level,
                "input_content": content,
                "teaching_plan": teaching_plan_text,
                "usage": {
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens
                },
                "model": self.model,
                "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            if save:
                self._save_teaching_plan(result)

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "student_level": student_level,
                "input_content": content
            }

    # =====================================================
    # 教案保存
    # =====================================================
    def _save_teaching_plan(self, result: Dict[str, Any]) -> None:
        safe_level = result["student_level"].replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_level}_teaching_plan_{timestamp}.json"
        path = os.path.join(self.save_dir, filename)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n✓ 教案已保存至：{path}")


# =====================================================
# 命令行交互入口
# =====================================================
def interactive_input() -> Dict[str, str]:
    print("\n========== 国际中文教学教案生成系统 ==========\n")

    # 学生等级
    while True:
        level = input("请输入学生汉语水平（如：一级 / 二级 / 三级 / 中级 / 高级）：").strip()
        if level:
            break
        print("⚠️ 学生水平不能为空，请重新输入。")

    # 内容类型提示
    print("\n请输入教学内容：")
    print("👉 可以是【话题】（如：在中国餐馆点菜）")
    print("👉 也可以是【完整课文文本】")
    print("👉 输入完成后，单独输入一行 END 结束\n")

    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)

    content = "\n".join(lines).strip()

    if not content:
        raise ValueError("教学内容不能为空")

    return {
        "student_level": level,
        "content": content
    }


# =====================================================
# 主程序
# =====================================================
if __name__ == "__main__":

    QWEN_API_KEY = ""

    generator = QwenTeachingPlanGenerator(
        api_key=QWEN_API_KEY,
        model="qwen3-max",
        temperature=0.7,
        top_p=0.3,
        save_dir=r"\storage\teaching_plan"
    )

    try:
        user_input = interactive_input()

        result = generator.generate_teaching_plan(
            student_level=user_input["student_level"],
            content=user_input["content"],
            save=True
        )

        if result["success"]:
            print("\n========== 教案生成成功 ==========\n")
            print(result["teaching_plan"])
        else:
            print("\n❌ 教案生成失败：")
            print(result["error"])

    except Exception as e:
        print(f"\n❌ 程序错误：{e}")

