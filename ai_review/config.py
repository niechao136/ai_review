import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.markup import escape

from .utils import console

# 全局配置文件路径：存储于用户 home 目录下的隐藏 JSON 文件
GLOBAL_CONFIG_PATH = Path.home() / ".ai_review.json"


def get_default_config() -> dict:
    """
    获取项目支持的标准配置模板。

    Returns:
        dict: 包含 api_key, base_url, model, proxy 的初始字典。
    """
    return {
        "api_key": "",
        "base_url": "",
        "model": "",
        "proxy": ""
    }


def load_full_config() -> dict:
    """
    按优先级从多个源合并加载配置信息。
    优先级从低到高依次为：默认值 -> 全局 JSON 文件 -> 项目 .env 文件 -> 系统环境变量。

    Returns:
        dict: 合并后的最终配置字典。
    """
    conf = get_default_config()

    # 1. 加载全局持久化配置 (JSON)
    if GLOBAL_CONFIG_PATH.exists():
        try:
            with open(GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                conf.update(user_config)
        except Exception as e:
            console.print(f"[yellow]⚠️ 读取配置文件失败: {escape(str(e))}[/yellow]")

    # 2. 加载当前工作目录下的项目级配置 (.env)
    dotenv_path = Path.cwd() / ".env"
    if dotenv_path.exists():
        # override=True 确保 .env 中的内容可以覆盖之前的 JSON 配置
        load_dotenv(dotenv_path=dotenv_path, override=True)

    # 3. 读取系统环境变量，拥有最高优先级
    conf["api_key"] = os.getenv("AI_API_KEY", conf.get("api_key"))
    conf["base_url"] = os.getenv("AI_BASE_URL", conf.get("base_url"))
    conf["model"] = os.getenv("AI_MODEL", conf.get("model"))
    conf["proxy"] = os.getenv("AI_PROXY", conf.get("proxy"))

    return conf


def config_cli(key: Optional[str] = None, value: Optional[str] = None, list_all: bool = False):
    """
    配置管理功能的 CLI 逻辑实现，支持查询、设置及列表展示。

    Args:
        key: 配置项名称。
        value: 需要设置的新值。
        list_all: 是否展示所有已配置的内容。
    """
    conf = load_full_config()

    # 场景 1: 展示所有配置项（含 API Key 脱敏处理）
    if list_all:
        console.print("[bold cyan]当前配置列表:[/bold cyan]")
        for k, v in conf.items():
            display_v = v
            # 对敏感信息进行脱敏：保留前 8 位和后 4 位
            if k == "api_key" and v:
                display_v = f"{v[:8]}...{v[-4:]}" if len(v) > 12 else "******"
            console.print(f"  [yellow]{k:10}[/yellow] = [white]{display_v}[/white]")
        return

    # 场景 2: 未提供任何参数时的用法提示
    if key is None:
        console.print("[yellow]用法:[/yellow] ai-review config [key] [value] 或 ai-review config --list")
        return

    # 场景 3: 查询单个配置项的值
    if value is None:
        if key in conf:
            display_v = conf[key]
            # 查询单个项时对 api_key 同样进行脱敏显示
            if key == "api_key" and conf[key]:
                display_v = f"{conf[key][:8]}...{conf[key][-4:]}" if len(conf[key]) > 12 else "******"
            console.print(f"[cyan]{key}[/cyan] = [white]{display_v}[/white]")
        else:
            console.print(f"[bold red]❌ 未找到配置项: {key}[/bold red]")
        return

    # 场景 4: 写入/更新配置项
    # 验证键名是否属于标准配置范畴
    if key not in conf and key not in get_default_config():
        console.print(f"[yellow]⚠️ [bold]{key}[/bold] 不是标准配置项。[/yellow]")
        return

    # 更新字典并持久化到 JSON 文件
    conf[key] = value
    try:
        with open(GLOBAL_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(conf, f, indent=4, ensure_ascii=False)
        console.print(f"[bold green]✅ 已成功设置 [magenta]{key}[/magenta][/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ 写入配置失败: {escape(str(e))}[/bold red]")