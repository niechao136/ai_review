import typer
import os
import json
from dotenv import load_dotenv
from pathlib import Path

# 全局配置文件路径：用户家目录下的 .ai_reviewer.json
GLOBAL_CONFIG_PATH = Path.home() / ".ai_review.json"

def get_default_config():
    """默认配置模板"""
    return {
        "api_key": "",
        "base_url": "",
        "model": "",
        "proxy": "",
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
    dotenv_path = Path.cwd() / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=True)
        # 调试用：执行 ai-review review 时能看到是否加载成功
        typer.echo(f"✅ Loaded .env from: {dotenv_path}")
    else:
        typer.echo(f"⚠️ No .env found at: {dotenv_path}")
        pass
    conf["api_key"] = os.getenv("AI_API_KEY", conf["api_key"])
    conf["base_url"] = os.getenv("AI_BASE_URL", conf["base_url"])
    conf["model"] = os.getenv("AI_MODEL", conf["model"])
    conf["proxy"] = os.getenv("AI_PROXY", conf["proxy"])
    conf["max_lines"] = os.getenv("MAX_LINES", conf["max_lines"])
    conf["max_size"] = os.getenv("MAX_SIZE", conf["max_size"])

    return conf

def config_cli(key: str = None, value: str = None, list_all: bool = False):
    conf = load_full_config()

    # 场景 1: 列出所有配置内容
    if list_all:
        for k, v in conf.items():
            # 使用 Rich 或者简单的 print
            typer.echo(f"{k} = {v}")
        return

    # 场景 2: 没有任何参数，显示帮助
    if key is None:
        typer.echo("用法: ai-review config [key] [value] 或 ai-review config --list")
        raise typer.Exit()

    # 场景 3: 只有 Key，没有 Value -> 查询操作
    if value is None:
        if key in conf:
            typer.echo(conf[key])
        else:
            typer.secho(f"❌ 未找到配置项: {key}", fg=typer.colors.RED)
        return

    # 场景 4: Key 和 Value 都有 -> 写入操作
    # 这里可以做一层简单的校验
    valid_keys = conf.keys()
    if key not in valid_keys:
        typer.confirm(f"⚠️ {key} 不是预设配置项，确认要添加吗？", abort=True)

    conf[key] = value
    with open(GLOBAL_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(conf, f, indent=4, ensure_ascii=False)

    typer.secho(f"✅ 已设置 {key} 为 {value}", fg=typer.colors.GREEN)