import sys
import io
from rich.console import Console

# 1. 重新包装标准输出流
# 在 Windows 环境下，强制 sys.stdout 使用 UTF-8 编码
# errors="replace" 是关键：遇到无法显示的字符（如 ✅）会替换为 ? 而非报错崩溃
if sys.platform == "win32":
    # 检查是否已经是包装过的流，避免重复包装
    if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )
    if not isinstance(sys.stderr, io.TextIOWrapper) or sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer,
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )

# 2. 初始化 Rich Console
# 现在 Rich 会自动使用我们修复过的 sys.stdout
console = Console(
    # force_terminal 确保在 PyCharm 等 IDE 的控制台中也能显示颜色
    force_terminal=True if sys.platform == "win32" else None,
    # 显式指定使用包装后的流
    file=sys.stdout,
    # 针对旧版 Windows 控制台的特殊处理
    legacy_windows=True if sys.platform == "win32" else None
)