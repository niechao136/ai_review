import subprocess

from rich.markup import escape

from .types import ReviewMode


def is_merge_commit(ref: str = "HEAD"):
    try:
        # %P 表示显示所有的父节点哈希值（以空格分隔）
        cmd = ["git", "show", "-s", "--format=%P", ref]
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()

        # 如果拆分后的列表长度 > 1，说明是 Merge 提交
        parents = output.split()
        return len(parents) > 1
    except Exception:
        return False


def get_diff_range(ref: str = "HEAD", mode: ReviewMode = ReviewMode.COMMIT):
    """
    根据用户输入参数确定 Git Diff 的对比范围参数。

    Args:
        ref: 指定的提交引用（如 Commit ID、分支名或 Tag）。
        mode: 评审代码模式：评审提交、评审暂存区 (Staged)、评审本地修改

    Returns:
        list: 传递给 git diff 命令的范围参数列表。
    """
    # 场景 1：如果指定了暂存区模式，直接返回 --cached 参数
    if mode == ReviewMode.STAGED:
        # 用于对比暂存区与最后一次提交 (HEAD) 之间的差异
        return ["--cached"]

    # 场景 2：如果指定了本地修改模式，直接返回 HEAD 参数
    if mode == ReviewMode.LOCAL:
        # 用于对比本地修改与最后一次提交 (HEAD) 之间的差异，无论是否 git add
        return ["HEAD"]

    # 场景 3：评审指定引用及其父节点之间的变更
    try:
        # 尝试通过 rev-parse 检查该引用是否存在父节点（HEAD^）
        subprocess.run(
            ["git", "rev-parse", f"{ref}^"],
            check=True, capture_output=True, text=True
        )
        # 存在父节点，返回对比范围：[父节点, 当前节点]
        return [f"{ref}^", ref]
    except subprocess.CalledProcessError:
        # 场景 3：处理初始提交（没有父节点的情况）
        # 使用 Git 预定义的空目录树 Hash (EMPTY_TREE_HASH) 作为基准进行对比
        return ["4b825dc642cb6eb9a060e54bf8d69288fbee4904", ref]


def get_clean_diff(ref: str = "HEAD", mode: ReviewMode = ReviewMode.COMMIT):
    """
    提取并过滤 Git 变更内容，仅保留有效的文本文件差异。

    该函数执行两步走策略：
    1. 使用 --numstat 分析文件变更统计信息，识别并剔除二进制文件。
    2. 对过滤后的文本文件执行详细的 diff 提取。

    Args:
        ref: 提交引用。
        mode: 评审代码模式：评审提交、评审暂存区 (Staged)、评审本地修改

    Returns:
        tuple: (diff_text, success_flag) 差异文本内容及执行状态。
    """
    try:
        # 检查评审的提交是否是合并提交，如果是则跳过
        if mode == ReviewMode.COMMIT and is_merge_commit(ref=ref):
            return "[yellow]⚠️ 检测到合并提交，跳过重复评审。[/yellow]", False

        # 1. 获取对比范围参数（如 ["--cached"] 或 ["HEAD^", "HEAD"]）
        diff_range = get_diff_range(ref=ref, mode=mode)

        # 2. 获取变更统计信息
        # --numstat 输出：添加行数  删除行数  文件路径
        # --no-renames 强制将重命名操作拆分为“删除旧文件”和“新增新文件”，便于路径处理
        stats_cmd = ["git", "diff"] + diff_range + ["--numstat", "--no-renames", "--", ".", ]

        result = subprocess.run(
            stats_cmd,
            capture_output=True, text=True, check=True,
            encoding="utf-8", errors="replace"
        )
        lines = result.stdout.strip().splitlines()

        # 如果没有任何变更行，返回空字符串
        if not lines:
            return "", True

        valid_files = []
        for line in lines:
            parts = line.split('\t')
            if len(parts) < 3:
                continue

            added, deleted, file_path = parts[0], parts[1], parts[2]

            # 过滤逻辑：Git 在 numstat 中会将二进制文件的行列统计显示为 "-"
            if added == "-" or deleted == "-":
                continue

            valid_files.append(file_path)

        # 如果过滤后没有可评审的文本文件，直接返回
        if not valid_files:
            return "", True

        # 3. 提取最终的详细文本差异内容
        # 仅针对上一步筛选出的有效文本文件列表 (valid_files) 进行 diff
        diff_cmd = ["git", "diff"] + diff_range + ["--no-renames", "--"] + valid_files
        final_diff = subprocess.run(
            diff_cmd,
            capture_output=True, text=True, check=True,
            encoding="utf-8", errors="replace"
        )

        return final_diff.stdout, True

    except subprocess.CalledProcessError as e:
        # 捕获并格式化 Git 命令执行中的标准错误输出
        stderr_msg = e.stderr.decode('utf-8', 'replace') if isinstance(e.stderr, bytes) else e.stderr
        return f"[bold red]❌ Git 命令执行失败: {stderr_msg}[/bold red]", False
    except Exception as e:
        # 捕获逻辑执行中的其他未知异常
        return f"[bold red]❌ 提取 Diff 时发生未知错误: {escape(str(e))}[/bold red]", False