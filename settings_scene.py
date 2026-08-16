"""
肉鸽游戏 - 设置界面（操作设置 + 帧率设置 + 游戏速度）
"""
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BG_COLOR, HIGHLIGHT, GRAY, LIGHT_GRAY, WHITE
from fonts import get_font


class SettingsScene:
    """设置页面：包含操作设置、帧率设置、游戏速度"""

    def __init__(self, game):
        self.game = game
        self.font = get_font(30)
        self.small_font = get_font(24)
        self.title_font = get_font(48)
        self.section_font = get_font(32)

        # 绑定游戏的 controls 字典以便直接修改
        self.controls = game.controls
        self.control_keys = ["up", "down", "left", "right"]
        self.captions = {"up": "向上", "down": "向下", "left": "向左", "right": "向右"}
        # 用于重新绑定按键时的状态
        self.waiting_rebind = None  # None 或 "up"/"down"/"left"/"right"
        # ESC 用于返回菜单
        self.back_key = pygame.K_ESCAPE
        # 帧率选项索引
        self.fps_index = 0
        # 游戏速度选项索引
        self.speed_index = 0

    def _control_name(self, key):
        """将 pygame 按键转为可读名称"""
        name = pygame.key.name(key)
        return name.upper() if name else str(key)

    def _fps_label(self):
        """帧率选项显示文本"""
        opts = self.game.fps_options
        return str(opts[self.fps_index]) if opts[self.fps_index] > 0 else "无限制"

    def _speed_label(self):
        """游戏速度显示文本"""
        return f"{self.game.game_speed:.0f}x"

    def handle_event(self, event):
        # 优先处理按键重绑定
        if self.waiting_rebind is not None:
            if event.type == pygame.KEYDOWN:
                if event.key == self.back_key:
                    self.waiting_rebind = None
                else:
                    self.controls[self.waiting_rebind] = event.key
                    self.waiting_rebind = None
            return

        if event.type == pygame.KEYDOWN and event.key == self.back_key:
            self.game.state = "menu"
            return

        if event.type == pygame.KEYDOWN:
            # 按键绑定：1/2/3/4 设定上下左右
            mapping = {
                pygame.K_1: "up",
                pygame.K_2: "down",
                pygame.K_3: "left",
                pygame.K_4: "right",
            }
            if event.key in mapping:
                self.waiting_rebind = mapping[event.key]
            # 帧率切换：F 键循环切换
            elif event.key == pygame.K_f:
                opts = self.game.fps_options
                self.fps_index = (self.fps_index + 1) % len(opts)
                self.game.fps = opts[self.fps_index]
            # 游戏速度切换：G 键循环切换
            elif event.key == pygame.K_g:
                opts = self.game.game_speed_options
                self.speed_index = (self.speed_index + 1) % len(opts)
                self.game.game_speed = opts[self.speed_index]

        # 鼠标点击帧率/速度按钮
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            fps_btn = pygame.Rect(SCREEN_WIDTH // 2 - 140, 460, 280, 45)
            if fps_btn.collidepoint(mx, my):
                opts = self.game.fps_options
                self.fps_index = (self.fps_index + 1) % len(opts)
                self.game.fps = opts[self.fps_index]
            speed_btn = pygame.Rect(SCREEN_WIDTH // 2 - 140, 545, 280, 45)
            if speed_btn.collidepoint(mx, my):
                opts = self.game.game_speed_options
                self.speed_index = (self.speed_index + 1) % len(opts)
                self.game.game_speed = opts[self.speed_index]

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(BG_COLOR)

        # 标题
        title = self.title_font.render("设置", True, HIGHLIGHT)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 70)))

        # ============ 操作设置区块 ============
        section1 = self.section_font.render("操作设置", True, (120, 180, 255))
        screen.blit(section1, (SCREEN_WIDTH // 2 - 400, 120))

        tip = self.small_font.render("按 1/2/3/4 选中方向键后按新键绑定", True, GRAY)
        screen.blit(tip, (SCREEN_WIDTH // 2 - 400, 158))

        # 方向键绑定
        y_start = 192
        gap = 48
        for action in self.control_keys:
            key_name = self._control_name(self.controls[action])
            idx = self.control_keys.index(action)
            label = f"{self.captions[action]}: [{key_name}]  (按 {idx+1} 重新绑定)"
            text = self.font.render(label, True, HIGHLIGHT if self.waiting_rebind == action else (220, 220, 220))
            screen.blit(text, (SCREEN_WIDTH // 2 - 400, y_start + gap * idx))

        # ============ 帧率设置区块 ============
        section2 = self.section_font.render("帧率设置", True, (120, 220, 120))
        screen.blit(section2, (SCREEN_WIDTH // 2 - 400, 410))

        fps_btn = pygame.Rect(SCREEN_WIDTH // 2 - 140, 440, 280, 45)
        pygame.draw.rect(screen, (50, 50, 60), fps_btn, border_radius=8)
        pygame.draw.rect(screen, (120, 220, 120), fps_btn, width=2, border_radius=8)
        fps_text = self.font.render(f"帧率: {self._fps_label()}", True, (120, 220, 120))
        screen.blit(fps_text, fps_text.get_rect(center=(fps_btn.centerx, fps_btn.centery)))
        fps_hint = self.small_font.render("点击或按 F 切换", True, GRAY)
        screen.blit(fps_hint, fps_hint.get_rect(center=(SCREEN_WIDTH // 2, 495)))

        # ============ 游戏速度区块 ============
        section3 = self.section_font.render("游戏速度", True, (255, 200, 120))
        screen.blit(section3, (SCREEN_WIDTH // 2 - 400, 525))

        speed_btn = pygame.Rect(SCREEN_WIDTH // 2 - 140, 555, 280, 45)
        pygame.draw.rect(screen, (60, 50, 30), speed_btn, border_radius=8)
        pygame.draw.rect(screen, (255, 200, 120), speed_btn, width=2, border_radius=8)
        speed_text = self.font.render(f"速度: {self._speed_label()}", True, (255, 200, 120))
        screen.blit(speed_text, speed_text.get_rect(center=(speed_btn.centerx, speed_btn.centery)))
        speed_hint = self.small_font.render("点击或按 G 切换 (1-10倍)", True, GRAY)
        screen.blit(speed_hint, speed_hint.get_rect(center=(SCREEN_WIDTH // 2, 610)))

        # 底部提示
        hint = self.small_font.render("按 ESC 返回菜单", True, GRAY)
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 45))
