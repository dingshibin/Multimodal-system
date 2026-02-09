import os
from datetime import datetime
# 导入你的模块
from llm.teaching_plan_gen import QwenTeachingPlanGenerator
from lesson_plan.parser import TeachingPlanParser
from prompt.prompt_builder import MultimodalPromptBuilder
from prompt.prompt_saver import PromptSaver
from multimodal.image_wanx import WanXImageGenerator
from multimodal.tts_xunfei import XunfeiTTSGenerator
from multimodal.video_seedance import SeedanceVideoGenerator

# ================= 绝对路径配置 =================
STORAGE_ROOT = 'storage'
LESSON_DB = os.path.join(STORAGE_ROOT, "teaching_db")  # 统一教案库
PROMPT_DB = os.path.join(STORAGE_ROOT, "prompt_db")  # 统一提示词库
OUTPUT_ROOT = os.path.join(STORAGE_ROOT, "output")  # 媒体素材根目录

KEYS = {
    "QWEN": "your-api-key",
    "XUNFEI_APPID": "",
    "XUNFEI_KEY": "",
    "XUNFEI_SECRET": "",
    "ARK_KEY": ""
}


def run_system():
    level = input("请输入学生等级 (如: 三级): ").strip()
    topic = input("请输入教学主题: ").strip()

    # --- 阶段 1: 教案生成 (存入统一教案库) ---
    print("\n[1/4] 正在生成教案并存入统一库...")
    gen = QwenTeachingPlanGenerator(api_key=KEYS["QWEN"], save_dir=LESSON_DB)
    res = gen.generate_teaching_plan(level, topic)
    if not res["success"]: return

    # --- 阶段 2: 解析课文 ---
    parser = TeachingPlanParser(res["teaching_plan"])
    clean_text = parser.extract_lesson_text()

    # --- 阶段 3: 提示词生成 (存入统一提示词库) ---
    print("[2/4] 正在生成提示词并存入统一库...")
    p_builder = MultimodalPromptBuilder(api_key=KEYS["QWEN"])
    p_saver = PromptSaver(base_dir=PROMPT_DB)

    img_prompt = p_builder.generate("image", level, clean_text)
    vid_prompt = p_builder.generate("video", level, clean_text)

    p_saver.save("image", "WanX-2.5", level, clean_text, img_prompt)
    p_saver.save("video", "Seedance", level, clean_text, vid_prompt)

    # --- 阶段 4: 媒体素材生成 (存入独立文件夹) ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 文件夹名：时间_等级_主题
    media_folder_name = f"{timestamp}_{level}_{topic[:10]}"
    current_media_dir = os.path.join(OUTPUT_ROOT, media_folder_name)
    os.makedirs(current_media_dir, exist_ok=True)

    print(f"[3/4] 正在生成多模态素材，保存至: {media_folder_name}")

    # A. 图片
    try:
        wanx = WanXImageGenerator(api_key=KEYS["QWEN"])
        wanx.execute_generation(img_prompt, level, current_media_dir)
    except Exception as e:
        print(f"图片生成失败: {e}")

    # B. 音频
    try:
        tts = XunfeiTTSGenerator(KEYS["XUNFEI_APPID"], KEYS["XUNFEI_KEY"], KEYS["XUNFEI_SECRET"])
        tts.generate(clean_text, level, current_media_dir)
    except Exception as e:
        print(f"音频生成失败: {e}")

    # C. 视频
    try:
        seedance = SeedanceVideoGenerator(api_key=KEYS["ARK_KEY"])
        seedance.execute_generation(vid_prompt, level, current_media_dir)
    except Exception as e:
        print(f"视频生成失败: {e}")

    print(f"\n✅ 流程全部完成！")
    print(f"📄 教案与提示词已汇总至对应数据库。")
    print(f"🎬 多模态素材请查看: {current_media_dir}")


if __name__ == "__main__":

    run_system()
