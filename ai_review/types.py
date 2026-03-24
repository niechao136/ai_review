from enum import Enum


class HookType(str, Enum):
    """Git 钩子类型枚举：目前支持提交前 (pre-commit) 、 推送前 (pre-push) 以及全部"""
    PRE_PUSH = "pre-push"
    PRE_COMMIT = "pre-commit"
    ALL = "all"


class ReviewMode(str, Enum):
    """评审代码模式枚举：目前支持评审提交、评审暂存区 (Staged)、评审本地修改"""
    COMMIT = "commit"
    STAGED = "staged"
    LOCAL = "local"