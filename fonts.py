"""
肉鸽游戏 - 字体工具
自动从系统常见中文字体路径中寻找可用的字体
"""
import os
import pygame


# 常见中文字体路径（按优先级排序）
CANDIDATE_FONTS = [
    # 微软雅黑
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyh.ttf",
    # 等线
    r"C:\Windows\Fonts\Deng.ttf",
    r"C:\Windows\Fonts\Dengb.ttf",
    # 宋体
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\simsun.ttf",
    r"C:\Windows\Fonts\SimsunExtG.ttf",
    # 黑体
    r"C:\Windows\Fonts\simhei.ttf",
    # 楷体
    r"C:\Windows\Fonts\simkai.ttf",
]

_font_path_cache = None


def find_chinese_font():
    """寻找系统中文字体文件路径，找不到返回 None"""
    global _font_path_cache
    if _font_path_cache is not None:
        return _font_path_cache

    for path in CANDIDATE_FONTS:
        if os.path.exists(path):
            _font_path_cache = path
            return path
    _font_path_cache = None
    return None


def get_font(size, bold=False):
    """
    获取支持中文的字体
    优先使用系统中文字体，找不到则回退 pygame 默认字体
    """
    path = find_chinese_font()
    if path:
        try:
            return pygame.font.Font(path, size)
        except Exception:
            pass
    # 回退：pygame 默认字体（不含中文，仅英文）
    return pygame.font.Font(None, size)


def has_chinese_font():
    """是否找到了中文字体"""
    return find_chinese_font() is not None