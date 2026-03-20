import os
import re
import sys
from enum import Enum
from pathlib import Path
from rich.markup import escape

from ai_review.utils import console

# --- 核心配置枚举与映射 ---

class HookType(str, Enum):
    """Git 钩子类型枚举：目前支持提交前 (pre-commit) 和 推送前 (pre-push)"""
    PRE_PUSH = "pre-push"
    PRE_COMMIT = "pre-commit"

# 不同钩子对应的 Git 操作名称映射，用于 UI 提示
HOOK_ACTION_MAP = {
    HookType.PRE_PUSH: "push",
    HookType.PRE_COMMIT: "commit",
}

# 不同钩子触发时，传递给 ai-review review 命令的参数映射
HOOK_PARAM_MAP = {
    HookType.PRE_PUSH: "",           # pre-push 默认评审最后一次提交内容
    HookType.PRE_COMMIT: " --staged", # pre-commit 必须带 --staged 评审暂存区
}

# --- 注入块标记与模板 ---

# 用于在 Shell 脚本中精准识别和定位由本工具生成的代码块
BEGIN_MARKER = "# >>> AI-REVIEW START >>>"
END_MARKER = "# <<< AI-REVIEW END <<<"

# 注入到 .git/hooks 目录下的 Shell 脚本模板
HOOK_CONTENT = f"""
{BEGIN_MARKER}
# AI-Reviewer 自动生成的钩子。若要移除，请删除此区块。
if command -v ai-review >/dev/null 2>&1; then
  # 执行评审，失败（BLOCK）将拦截 [ACTION]
  ai-review review [PARAM]
else
  echo "[AI-Review] 警告: 未找到 ai-review 命令，跳过自动评审。"
fi
{END_MARKER}
"""


def init_cli(hook: HookType = HookType.PRE_PUSH):
    """
    初始化逻辑：将 AI 评审脚本注入到指定的 Git Hook 文件中。
    包含备份现有钩子、处理标记块更新以及设置执行权限等步骤。
    """
    git_dir = Path(".git")

    # 1. 环境校验
    if not git_dir.exists():
        console.print("[bold red]❌ 错误: 当前目录不是 Git 仓库根目录。[/bold red]")
        sys.exit(1)

    hook_path = git_dir / "hooks" / hook.value

    # 2. 根据钩子类型动态填充模板占位符
    action = HOOK_ACTION_MAP.get(hook, "push")
    hook_content = HOOK_CONTENT.replace("[ACTION]", action)
    hook_content = hook_content.replace("[PARAM]", HOOK_PARAM_MAP.get(hook, ""))

    hook_path.parent.mkdir(parents=True, exist_ok=True)

    # 3. 备份与安全处理：如果已存在钩子文件，先创建 .bak 备份
    existing_content = ""
    if hook_path.exists():
        try:
            existing_content = hook_path.read_text(encoding="utf-8")
            backup_path = hook_path.with_suffix(".bak")
            if backup_path.exists():
                backup_path.unlink()
            hook_path.rename(backup_path)
            console.print(f"[dim]已为现有的 {hook.value} 创建备份: {backup_path}[/dim]")
        except PermissionError:
            console.print("[bold red]❌ 权限不足: 无法备份或修改 Git Hook。[/bold red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[yellow]⚠️ 备份失败 ({escape(str(e))})，为安全起见停止自动注入。[/yellow]")
            sys.exit(1)

    # 4. 内容合成逻辑：支持增量更新旧有的标记块
    if BEGIN_MARKER in existing_content and END_MARKER in existing_content:
        # 如果已存在标记块，使用正则表达式将其替换为最新的配置内容
        console.print("[cyan]检测到已存在的 AI-Reviewer 配置，正在执行增量更新...[/cyan]")
        pattern = re.compile(f"{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL)
        new_content = pattern.sub(hook_content.strip(), existing_content)
    else:
        # 如果是首次注入，根据文件是否为空决定是否补全 Shebang 行
        console.print("[cyan]正在注入 AI-Reviewer 到 Git Hook...[/cyan]")
        if not existing_content.strip():
            new_content = "#!/bin/sh\n" + hook_content
        else:
            new_content = existing_content.rstrip() + "\n\n" + hook_content

    # 5. 文件回写与权限授予
    try:
        # 统一使用 LF 换行符以确保在类 Unix 系统中正常执行
        with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_content.strip() + "\n")

        # 在非 Windows 系统上，为钩子脚本赋予可执行权限 (755)
        if os.name != 'nt':
            os.chmod(hook_path, 0o755)

        console.print("[bold green]✅ Git Hook 注入/更新成功！[/bold green]")
        console.print(f"[dim]现在，每次执行 `git {action}` 前，AI 将自动审阅你的代码。[/dim]")

    except Exception as e:
        console.print(f"[bold red]❌ 写入 Hook 文件失败: {escape(str(e))}[/bold red]")
        sys.exit(1)


def remove_cli(hook: HookType = HookType.PRE_PUSH):
    """
    移除逻辑：从指定的 Git Hook 文件中精准剔除 AI-Reviewer 的配置块。
    如果剔除后文件仅剩 Shebang 或为空，则会直接删除该文件。
    """
    git_dir = Path(".git")

    if not git_dir.exists():
        console.print("[bold red]❌ 错误: 当前目录不是 Git 仓库根目录。[/bold red]")
        sys.exit(1)

    hook_path = git_dir / "hooks" / hook.value

    if not hook_path.exists():
        console.print(f"[yellow]⚠️ 未发现 {hook.value} 钩子文件，无需移除。[/yellow]")
        return

    existing_content = hook_path.read_text(encoding="utf-8")

    # 1. 精准块移除逻辑
    if BEGIN_MARKER in existing_content and END_MARKER in existing_content:
        # 匹配并删除整个标记块
        pattern = re.compile(f"{re.escape(BEGIN_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL)
        new_content = pattern.sub("\n", existing_content).strip()
    else:
        # 2. 向下兼容逻辑：如果没有标记块，搜索关键词行进行删除
        target_feature = "ai-review review"

        if target_feature not in existing_content:
            console.print(f"[yellow]⚠️ {hook.value} 钩子文件中未发现 ai-review 的配置，无需移除。[/yellow]")
            return

        lines = existing_content.splitlines()
        new_lines = [line for line in lines if target_feature not in line]
        new_content = "\n".join(new_lines).strip()

    # 3. 脚本清理判断：如果删除后脚本不再具有实质逻辑，则物理删除文件
    is_empty_script = not new_content or (new_content.startswith("#!") and len(new_content.splitlines()) <= 1)

    try:
        if is_empty_script:
            hook_path.unlink()
            console.print(f"[bold green]✅ 已彻底移除不再需要的 {hook.value} 钩子文件。[/bold green]")
        else:
            # 否则仅写回剔除后的内容，并保持 POSIX 换行规范
            hook_path.write_text(new_content + "\n", encoding="utf-8")
            console.print(f"[bold green]✅ 已从 {hook.value} 中成功剔除 ai-review 模块。[/bold green]")
        console.print("[dim]已移除 Git Hook。现在，操作代码前将不再触发 AI 自动审阅。[/dim]")
    except Exception as e:
        console.print(f"[bold red]❌ 移除失败:[/bold red] {escape(str(e))}")