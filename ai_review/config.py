import json
import os
from pathlib import Path

from dotenv import load_dotenv

from ai_review.utils import console

# 全局配置文件路径：用户家目录下的 .ai_review.json
GLOBAL_CONFIG_PATH = Path.home() / ".ai_review.json"


def get_default_config():
    """默认配置模板"""
    return {
        "api_key": "",
        "base_url": "",
        "model": "",
        "proxy": ""
    }


def load_full_config():
    """
    按优先级加载配置：1. 全局 JSON -> 2. 项目 .env -> 3. 系统环境变量
    """
    conf = get_default_config()

    # 1. 从全局 JSON 加载
    if GLOBAL_CONFIG_PATH.exists():
        try:
            with open(GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                conf.update(user_config)
        except Exception as e:
            console.print(f"[yellow]⚠️ 读取配置文件失败: {e}[/yellow]")

    # 2. 从项目 .env 加载 (作为项目级覆盖)
    dotenv_path = Path.cwd() / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=True)
        # 仅在调试或明确需要时显示，降低 Git Hook 运行时的视觉噪音
        # console.print(f"[dim]✅ Loaded .env from: {dotenv_path}[/dim]")

    # 3. 环境变量覆盖 (优先级最高)
    conf["api_key"] = os.getenv("AI_API_KEY", conf.get("api_key"))
    conf["base_url"] = os.getenv("AI_BASE_URL", conf.get("base_url"))
    conf["model"] = os.getenv("AI_MODEL", conf.get("model"))
    conf["proxy"] = os.getenv("AI_PROXY", conf.get("proxy"))

    return conf


def config_cli(key: str = None, value: str = None, list_all: bool = False):
    """配置管理逻辑实现"""
    conf = load_full_config()

    # 场景 1: 列出所有配置内容
    if list_all:
        console.print("[bold cyan]当前配置列表:[/bold cyan]")
        for k, v in conf.items():
            # 对 API Key 进行脱敏显示
            display_v = v
            if k == "api_key" and v:
                display_v = f"{v[:8]}...{v[-4:]}" if len(v) > 12 else "******"

            console.print(f"  [yellow]{k:10}[/yellow] = [white]{display_v}[/white]")
        return

    # 场景 2: 没有任何参数
    if key is None:
        console.print("[yellow]用法:[/yellow] ai-review config \[key] \[value] 或 ai-review config --list")
        return

    # 场景 3: 只有 Key -> 查询操作
    if value is None:
        if key in conf:
            display_v = conf[key]
            # 如果是查询 api_key，仍然显示脱敏结果，除非用户确实需要原文
            if key == "api_key" and conf[key]:
                display_v = f"{conf[key][:8]}...{conf[key][-4:]}" if len(conf[key]) > 12 else "******"
            console.print(f"[cyan]{key}[/cyan] = [white]{display_v}[/white]")
        else:
            console.print(f"[bold red]❌ 未找到配置项: {key}[/bold red]")
        return

    # 场景 4: 写入操作
    # 检查是否为有效配置项
    if key not in conf and key not in get_default_config():
        console.print(f"[yellow]⚠️ [bold]{key}[/bold] 不是标准配置项。[/yellow]")
        return

    conf[key] = value
    try:
        with open(GLOBAL_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(conf, f, indent=4, ensure_ascii=False)
        console.print(f"[bold green]✅ 已成功设置 [magenta]{key}[/magenta][/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ 写入配置失败: {e}[/bold red]")