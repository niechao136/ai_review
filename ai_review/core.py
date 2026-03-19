import subprocess
import os


def get_clean_diff(ref: str = "HEAD", max_filesize_kb: float = 100.0):
    """
    智能提取 Git 变更：
    1. 自动识别并剔除二进制文件（图片、模型、压缩包等）
    2. 自动剔除超过大小限制的文本文件（防止大日志或数据文件）
    3. 支持忽略特定路径
    """
    try:
        max_filesize_kb = float(max_filesize_kb)
    except (ValueError, TypeError):
        max_filesize_kb = 100.0  # 转换失败时的兜底值
    try:
        # 如果能解析出 ref^，说明有父节点
        subprocess.run(["git", "rev-parse", f"{ref}^"], check=True, capture_output=True)
        has_parent = True
    except subprocess.CalledProcessError:
        has_parent = False
    if has_parent:
        base_ref = f"{ref}^"
    else:
        # 如果是初始提交，对比“空树” (Magic Hash for empty tree)
        # 这会让 git diff 列出该提交中的所有文件内容
        base_ref = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    target_ref = ref
    try:
        # 1. 获取变更统计 (--numstat)
        # 输出格式：增加行数  删除行数  文件路径
        # 对于二进制文件，增加/删除行数会显示为 "-"
        stats_cmd = [
            "git", "diff", base_ref, target_ref,
            "--numstat",
            "--",
            ".",
            ":!node_modules/*",
            ":!venv/*",
            ":!.env*",
            ":!*.lock"
        ]

        result = subprocess.run(stats_cmd, capture_output=True, text=True, check=True, encoding="utf-8", errors="replace")
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
        diff_cmd = ["git", "diff", base_ref, target_ref, "--"] + valid_files
        final_diff = subprocess.run(diff_cmd, capture_output=True, text=True, check=True, encoding="utf-8", errors="replace")

        return final_diff.stdout, True

    except subprocess.CalledProcessError as e:
        stderr_msg = e.stderr.decode('utf-8', 'replace') if isinstance(e.stderr, bytes) else e.stderr
        return f"❌ Git 命令执行失败: {stderr_msg}", False
    except Exception as e:
        return f"❌ 提取 Diff 时发生未知错误: {str(e)}", False