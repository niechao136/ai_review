import os
import re
import sys
from pathlib import Path

from ai_review.utils import console

# 定义唯一的标记，用于识别我们的代码块
BEGIN_MARKER = "# >>> AI-REVIEW START >>>"
END_MARKER = "# <<< AI-REVIEW END <<<"

# 优化 Hook 内容：增加更清晰的提示，并确保 shell 环境兼容
HOOK_CONTENT = f"""
{BEGIN_MARKER}
# AI-Reviewer 自动生成的钩子。若要移除，请删除此区块。
if command -v ai-review >/dev/null 2>&1; then
  # 执行评审，失败（BLOCK）将拦截 push
  ai-review review
else
  echo "[AI-Review] 警告: 未找到 ai-review 命令，跳过自动评审。"
fi
{END_MARKER}
"""


def init_cli():
    git_dir = Path(".git")

    if not git_dir.exists():
        console.print("[bold red]❌ 错误: 当前目录不是 Git 仓库根目录。[/bold red]")
        sys.exit(1)

    hook_path = git_dir / "hooks" / "pre-push"

    # 确保 hooks 目录存在
    hook_path.parent.mkdir(parents=True, exist_ok=True)

    existing_content = ""
    if hook_path.exists():
        try:
            existing_content = hook_path.read_text(encoding="utf-8")
            # 备份原文件
            backup_path = hook_path.with_suffix(".bak")
            # 兼容 Windows 的文件替换
            if backup_path.exists():
                backup_path.unlink()
            hook_path.rename(backup_path)
            console.print(f"[dim]已为现有的 pre-push 创建备份: {backup_path}[/dim]")
        except PermissionError:
            console.print("[bold red]❌ 权限不足: 无法备份或修改 Git Hook。[/bold red]")
            console.print("[yellow]提示: 请尝试以管理员身份运行，或手动检查 .git/hooks 权限。[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[yellow]⚠️ 备份失败 ({e})，为安全起见停止自动注入。[/yellow]")
            sys.exit(1)

    # 逻辑优化：判断是否需要注入或更新
    if BEGIN_MARKER in existing_content and END_MARKER in existing_content:
        console.print("[cyan]检测到已存在的 AI-Reviewer 配置，正在执行增量更新...[/cyan]")
        pattern = re.compile(f"{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL)
        new_content = pattern.sub(HOOK_CONTENT.strip(), existing_content)
    else:
        console.print("[cyan]正在注入 AI-Reviewer 到 Git Hook...[/cyan]")
        # 如果是新文件或空文件，必须添加 Shebang 行
        if not existing_content.strip():
            new_content = "#!/bin/sh\n" + HOOK_CONTENT
        else:
            new_content = existing_content.rstrip() + "\n\n" + HOOK_CONTENT

    try:
        # 强制使用 LF 换行符，这是 Git Hook (Shell 脚本) 的标准
        with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_content.strip() + "\n")

        # 授予执行权限 (非 Windows 系统)
        if os.name != 'nt':
            os.chmod(hook_path, 0o755)

        console.print("[bold green]✅ Git Hook 注入/更新成功！[/bold green]")
        console.print("[dim]现在，每次执行 `git push` 前，AI 将自动审阅你的代码。[/dim]")

    except Exception as e:
        console.print(f"[bold red]❌ 写入 Hook 文件失败: {e}[/bold red]")
        sys.exit(1)


def remove_cli():
    """从当前项目的 .git/hooks/pre-push 中移除 ai-review 配置"""
    git_dir = Path(".git")

    if not git_dir.exists():
        console.print("[bold red]❌ 错误: 当前目录不是 Git 仓库根目录。[/bold red]")
        sys.exit(1)

    hook_path = git_dir / "hooks" / "pre-push"

    if not hook_path.exists():
        console.print("[yellow]⚠️ 未发现 pre-push 钩子文件，无需移除。[/yellow]")
        return

    existing_content = hook_path.read_text(encoding="utf-8")

    if BEGIN_MARKER in existing_content and END_MARKER in existing_content:
        pattern = re.compile(f"{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL)
        new_content = pattern.sub("\n", existing_content).strip()
    else:
        target_feature = "ai-review review"

        if target_feature not in existing_content:
            console.print("[yellow]⚠️ pre-push 钩子文件中未发现 ai-review 的配置，无需移除。[/yellow]")
            return

        lines = existing_content.splitlines()
        new_lines = [line for line in lines if target_feature not in line]
        new_content = "\n".join(new_lines).strip()

    # 决定是回写还是彻底删除
    is_empty_script = not new_content or new_content.startswith("#!") and len(new_content.splitlines()) <= 1

    try:
        if is_empty_script:
            hook_path.unlink()
            console.print("[bold green]✅ 已彻底移除不再需要的 pre-push 钩子文件。[/bold green]")
        else:
            # 保证文件以一个换行符结尾，符合 POSIX 标准
            hook_path.write_text(new_content + "\n", encoding="utf-8")
            console.print("[bold green]✅ 已从 pre-push 中成功剔除 ai-review 模块。[/bold green]")
        console.print("[dim]已移除 Git Hook。现在，推送代码前将不再触发 AI 自动审阅。[/dim]")
    except Exception as e:
        console.print(f"[bold red]❌ 移除失败:[/bold red] {str(e)}")