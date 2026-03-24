import time
from pathlib import Path

from rich.markup import escape

from .utils import console


def ensure_gitignore():
    """检查并确保 .ai_review 文件夹在 .gitignore 中"""
    gitignore_path = Path(".gitignore")
    marker = ".ai_review/"

    try:
        # 如果 .gitignore 不存在，创建一个
        if not gitignore_path.exists():
            gitignore_path.write_text(f"{marker}\n", encoding="utf-8")
            return

        content = gitignore_path.read_text(encoding="utf-8")
        if marker not in content:
            # 在末尾添加，确保换行
            with open(gitignore_path, "a", encoding="utf-8") as f:
                if content and not content.endswith("\n"):
                    f.write("\n")
                f.write(f"{marker}\n")
    except Exception as e:
        console.print(f"[yellow]⚠️ 无法更新 .gitignore: {escape(str(e))}[/yellow]")


def save_review_report(content: str):
    """将 AI 评审结果保存到本地文件 """
    try:
        report_dir = Path(".ai_review")
        report_dir.mkdir(exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_path = report_dir / f"report_{timestamp}.md"

        file_path.write_text(content, encoding="utf-8")
        return file_path
    except Exception as e:
        console.print(f"[yellow]⚠️ 报告保存失败: {escape(str(e))}[/yellow]")
        return None