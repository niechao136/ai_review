import typer
from typing import Optional

from .config import config_cli
from .hook import get_status, init_cli, remove_cli
from .review import review_code
from .types import HookType, ReviewMode
from .utils import console

app = typer.Typer()


@app.command()
def init(
    hook: HookType = typer.Argument(
        HookType.PRE_PUSH,
        help="指定挂载的 Git Hook 类型 (pre-push 或 pre-commit 或 all)"
    )
):
    """
    安装：将 AI 评审逻辑注入到本地 Git 钩子中。默认为 pre-push，也可通过参数设置为 pre-commit 或 all。
    """
    if hook == HookType.ALL:
        tasks = [item for item in HookType if item != HookType.ALL]
    else:
        tasks = [hook]
    for task in tasks:
        init_cli(hook=task)


@app.command()
def remove(
    hook: HookType = typer.Argument(
        HookType.PRE_PUSH,
        help="指定需要卸载的 Git Hook 类型 (pre-push 或 pre-commit 或 all)"
    )
):
    """
    卸载：从当前项目移除指定的 AI 评审钩子配置。默认为 pre-push，也可通过参数设置为 pre-commit 或 all。
    """
    if hook == HookType.ALL:
        tasks = [item for item in HookType if item != HookType.ALL]
    else:
        tasks = [hook]
    for task in tasks:
        remove_cli(hook=task)


@app.command()
def status():
    """
    查看当前项目的 AI 评审钩子安装状态。
    """
    get_status()


@app.command(name="config")
def config(
    key: Optional[str] = typer.Argument(None, help="配置项键名 (e.g. api_key, model, base_url)"),
    value: Optional[str] = typer.Argument(None, help="要设置的配置值"),
    list_all: bool = typer.Option(False, "--list", "-l", help="列出当前所有全局配置")
):
    """
    配置：管理全局 AI 评审参数（API Key、模型名称等）。
    """
    config_cli(key=key, value=value, list_all=list_all)


@app.command()
def review(
    ref: str = typer.Argument(
        "HEAD",
        help="指向特定的提交、分支或标签。若使用 --staged 则此参数失效。"
    ),
    staged: bool = typer.Option(
        False, "--staged", "-s",
        help="开启暂存区模式：仅评审已 git add 但未 commit 的变更"
    ),
    local: bool = typer.Option(
        False, "--local", "-l",
        help="开启本地修改模式：仅评审所有未 commit 的变更"
    )
):
    """
    评审：手动触发 AI 代码审计。支持指定历史提交或当前暂存区。
    """
    if staged:
        if local:
            console.print("[yellow]⚠️  警告: 检测到 --staged 参数，将忽略指定的 --local 参数，转而评审暂存区。[/yellow]")
        if ref != "HEAD":
            console.print("[yellow]⚠️  警告: 检测到 --staged 参数，将忽略指定的引用 '%s'，转而评审暂存区。[/yellow]" % ref)
        mode = ReviewMode.STAGED
        console.print("[dim]ℹ️  模式：暂存区 (Staged) 增量审计[/dim]")
        review_code(ref="HEAD", mode=mode)
    elif local:
        if ref != "HEAD":
            console.print("[yellow]⚠️  警告: 检测到 --local 参数，将忽略指定的引用 '%s'，转而评审本地修改。[/yellow]" % ref)
        mode = ReviewMode.LOCAL
        console.print("[dim]ℹ️  模式：本地修改审计[/dim]")
        review_code(ref="HEAD", mode=mode)
    else:
        mode = ReviewMode.COMMIT
        mode_desc = "最后一次提交 (HEAD)" if ref == "HEAD" else f"提交节点 {ref}"
        console.print(f"[dim]ℹ️  模式：{mode_desc} 审计[/dim]")
        review_code(ref=ref, mode=mode)