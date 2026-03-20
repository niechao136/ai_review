import typer
from typing import Optional
from .config import config_cli
from .hook import init_cli, remove_cli
from .review import review_code

app = typer.Typer()

@app.command()
def init():
    """将 AI 评审钩子注入到当前项目的 .git 文件夹下"""
    init_cli()


@app.command()
def remove():
    """将 AI 评审钩子从当前项目移除"""
    remove_cli()


@app.command()
def config(
    key: Optional[str] = typer.Argument(None, help="配置项名称 (如 api_key, model)"),
    value: Optional[str] = typer.Argument(None, help="要设置的值"),
    list_all: bool = typer.Option(False, "--list", "-l", help="列出所有配置")
):
    """管理配置信息，用法类似 git config"""
    config_cli(key=key, value=value, list_all=list_all)


@app.command()
def review(
    ref: str = typer.Argument("HEAD", help="要检查的提交 ID、分支名或 Tag（默认为最后一次提交 HEAD）")
):
    """核心指令：执行 AI 自动代码评审。支持对比指定提交：ai-review review <commit_id>"""
    review_code(ref)