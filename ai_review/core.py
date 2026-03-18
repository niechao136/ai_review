import subprocess
import os


def get_clean_diff(max_filesize_kb: int = 100):
    """
    智能提取 Git 变更：
    1. 自动识别并剔除二进制文件（图片、模型、压缩包等）
    2. 自动剔除超过大小限制的文本文件（防止大日志或数据文件）
    3. 支持忽略特定路径
    """
    try:
        # 1. 获取变更统计 (--numstat)
        # 输出格式：增加行数  删除行数  文件路径
        # 对于二进制文件，增加/删除行数会显示为 "-"
        stats_cmd = [
            "git", "diff", "HEAD~1", "HEAD",
            "--numstat",
            "--",
            ".",
            ":!node_modules/*",
            ":!venv/*",
            ":!.env*",
            ":!*.lock"
        ]

        result = subprocess.run(stats_cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().splitlines()

        if not lines:
            return ""

        valid_files = []
        for line in lines:
            parts = line.split('\t')
            if len(parts) < 3:
                continue

            added, deleted, file_path = parts[0], parts[1], parts[2]

            # --- 智能过滤逻辑 ---

            # A. 过滤二进制文件 (Git 会将二进制文件的统计记为 "-")
            if added == "-" or deleted == "-":
                continue

            # B. 过滤已删除的文件 (评审逻辑通常只关注新增/修改)
            if not os.path.exists(file_path):
                continue

            # C. 过滤超大文本文件 (例如意外提交的 1MB 日志)
            file_size_kb = os.path.getsize(file_path) / 1024
            if file_size_kb > max_filesize_kb:
                # 可以在终端打印一行提示，让用户知道这个文件被跳过了
                continue

            valid_files.append(file_path)

        if not valid_files:
            return ""

        # 2. 提取最终的文本差异
        # 使用 --unified=3 (默认) 保留上下文，方便 AI 理解代码逻辑
        diff_cmd = ["git", "diff", "HEAD~1", "HEAD", "--"] + valid_files
        final_diff = subprocess.run(diff_cmd, capture_output=True, text=True, check=True)

        return final_diff.stdout

    except subprocess.CalledProcessError as e:
        return f"❌ Git 命令执行失败: {e.stderr}"
    except Exception as e:
        return f"❌ 提取 Diff 时发生未知错误: {str(e)}"


def get_staged_diff(max_filesize_kb: int = 100):
    """
    可选：如果你想在 commit 之前（暂存区）进行评审，只需把命令改为 --cached
    """
    # 逻辑同上，只需将 "HEAD~1", "HEAD" 替换为 "--cached"
    pass