"""
肉鸽游戏 - 存档 / 读档系统
"""
import os
import json
from settings import SAVE_FILE


class SaveLoad:
    """存档 / 读档系统"""

    @staticmethod
    def load():
        """加载存档，返回字符串或 None"""
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    return f.read()
            except OSError:
                return None
        return None

    @staticmethod
    def save(data):
        """保存存档"""
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                f.write(data)
            return True
        except OSError:
            return False