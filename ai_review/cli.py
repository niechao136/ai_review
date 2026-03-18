import typer
import os
import json
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional
from .config import load_full_config, GLOBAL_CONFIG_PATH
from .review import review_code

load_dotenv()

app = typer.Typer()

# 定义唯一的标记，用于识别我们的代码块
BEGIN_MARKER = "# >>> AI-REVIEW START >>>"
END_MARKER = "# <<< AI-REVIEW END <<<"
HOOK_CONTENT = f"""
{BEGIN_MARKER}
# 自动生成的 AI 评审钩子，请勿手动修改标记行
if command -v ai-review >/dev/null 2>&1; then
  ai-review review
else
  echo "警告: 未找到 ai-review 命令，跳过 AI 评审。"
fi
{END_MARKER}
"""

@app.command()
def init():
    """将 AI 评审钩子注入到当前项目的 .git 文件夹下"""
    git_dir = Path(".git")

    if not git_dir.exists():
        typer.secho("❌ 错误: 当前目录不是 Git 仓库。", fg=typer.colors.RED)
        raise typer.Exit(1)

    hook_path = git_dir / "hooks" / "pre-push"

    # 确保 hooks 目录存在
    hook_path.parent.mkdir(parents=True, exist_ok=True)

    existing_content = ""
    if hook_path.exists():
        existing_content = hook_path.read_text(encoding="utf-8")
        # 备份原文件（以防万一）
        backup_path = hook_path.with_suffix(".bak")
        hook_path.replace(backup_path)
        typer.echo(f"已创建备份: {backup_path}")

    if BEGIN_MARKER in existing_content and END_MARKER in existing_content:
        # 情况 A: 已经存在区块，进行替换更新
        typer.echo("检测到已存在的 AI-Reviewer 区块，正在更新内容...")
        import re
        pattern = re.compile(f"{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL)
        new_content = pattern.sub(HOOK_CONTENT.strip(), existing_content)
    else:
        # 情况 B: 不存在区块，追加到末尾
        typer.echo("正在注入新的 AI-Reviewer 区块...")
        # 如果是新文件，记得加 Shebang
        prefix = "#!/bin/sh\n" if not existing_content else existing_content + "\n"
        new_content = prefix + HOOK_CONTENT

    with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content.strip() + "\n")

    # 授予执行权限 (仅限 Unix 系统，Windows 下 Git 会自动处理)
    if os.name != 'nt':
        os.chmod(hook_path, 0o755)

    typer.secho("✅ Git Hook 注入/更新成功！", fg=typer.colors.GREEN, bold=True)


@app.command()
def config(
    key: Optional[str] = typer.Argument(None, help="配置项名称 (如 api_key, model)"),
    value: Optional[str] = typer.Argument(None, help="要设置的值"),
    list_all: bool = typer.Option(False, "--list", "-l", help="列出所有配置")
):
    """管理配置信息，用法类似 git config"""
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


@app.command()
def review():
    """
    🚀 核心指令：执行 AI 自动代码评审。

    逻辑流程:
    1. 自动提取 Git 变更：对比 HEAD 与 HEAD~1 (或暂存区)。
    2. 智能过滤：剔除二进制文件、大文件及 node_modules 等干扰项。
    3. 调用 AI：将清理后的 Diff 发送至配置的大模型 (如 DeepSeek/GPT)。
    4. 风险评估：解析 AI 回复中的 [DECISION] 指令。

    拦截机制:
    若 AI 返回 [DECISION: BLOCK]，则程序以状态码 1 退出，从而拦截 Git Push。
    """
    review_code()