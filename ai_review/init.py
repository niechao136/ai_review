import typer
import os
from pathlib import Path

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

def init_cli():
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