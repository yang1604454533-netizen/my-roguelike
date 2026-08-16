"""
肉鸽游戏 - 主入口
"""
import sys
import os
import pygame
from game import Game


def main():
    pygame.init()

    # 设置窗口图标
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.exists(icon_path):
        try:
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
        except Exception:
            pass

    game = Game()
    game.run()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
