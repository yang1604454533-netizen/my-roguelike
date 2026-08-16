"""
肉鸽游戏 - 菜单界面
"""
import pygame
from settings import *
from fonts import get_font


class Button:
    """简单的菜单按钮"""

    def __init__(self, text, pos, size, font, callback):
        self.text = text
        self.rect = pygame.Rect(pos, size)
        self.font = font
        self.callback = callback
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, screen):
        color = HIGHLIGHT if self.hovered else WHITE
        pygame.draw.rect(screen, MENU_BG, self.rect, border_radius=8)
        pygame.draw.rect(screen, color, self.rect, width=2, border_radius=8)
        text_surf = self.font.render(self.text, True, color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)


class Menu:
    """主菜单"""

    def __init__(self, game):
        self.game = game
        self.font = get_font(32)
        self.title_font = get_font(48)

        # 按钮布局
        btn_w, btn_h = 260, 60
        btn_x = (SCREEN_WIDTH - btn_w) // 2
        start_y = SCREEN_HEIGHT // 2 - 40
        gap = 80

        self.buttons = [
            Button("进入游戏", (btn_x, start_y), (btn_w, btn_h), self.font, self.game.start_new_game),
            Button("读档", (btn_x, start_y + gap), (btn_w, btn_h), self.font, self.game.load_game),
            Button("设置", (btn_x, start_y + gap * 2), (btn_w, btn_h), self.font, self._open_settings),
            Button("退出游戏", (btn_x, start_y + gap * 3), (btn_w, btn_h), self.font, self.game.quit_game),
        ]

    def _open_settings(self):
        self.game.state = "settings"

    def handle_event(self, event):
        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, screen):
        # 标题
        title = self.title_font.render(GAME_TITLE, True, HIGHLIGHT)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 120)))

        # 副标题
        sub = self.font.render("Roguelike Demo", True, GRAY)
        screen.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 180)))

        for btn in self.buttons:
            btn.draw(screen)

        # 底部提示
        tip = self.font.render("WASD 移动 · 菜单点击操作", True, GRAY)
        screen.blit(tip, tip.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)))