import typer
import os
import json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# 全局配置文件路径：用户家目录下的 .ai_reviewer.json
GLOBAL_CONFIG_PATH = Path.home() / ".ai_review.json"

def get_default_config():
    """默认配置模板"""
    return {
        "api_key": "",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "max_lines": 500,  # 限制 diff 行数，防止浪费 token
        "max_size": 100 # 限制文件大小，单位 KB
    }

def load_full_config():
    """
    按优先级加载配置：
    1. 先读取全局 JSON
    2. 尝试寻找当前目录的 .env (保留作为项目级覆盖)
    3. 合并返回
    """
    conf = get_default_config()

    # 1. 从全局 JSON 加载
    if GLOBAL_CONFIG_PATH.exists():
        try:
            with open(GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                conf.update(user_config)
        except Exception as e:
            typer.secho(f"⚠️ 读取配置文件失败: {e}", fg=typer.colors.YELLOW)

    # 2. 从项目环境变量加载 (优先级最高)
    # 这样你依然可以在特定项目中通过 export 或 .env 临时覆盖设置
    conf["api_key"] = os.getenv("AI_API_KEY", conf["api_key"])
    conf["base_url"] = os.getenv("AI_BASE_URL", conf["base_url"])
    conf["model"] = os.getenv("AI_MODEL", conf["model"])
    conf["max_lines"] = os.getenv("MAX_LINES", conf["max_lines"])
    conf["max_size"] = os.getenv("MAX_SIZE", conf["max_size"])

    return conf
