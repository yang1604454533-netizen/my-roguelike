"""
肉鸽游戏 - 游戏主控制类
"""
import pygame
from settings import *
from menu import Menu
from game_scene import GameScene
from save_load import SaveLoad
from settings_scene import SettingsScene
from fonts import get_font


class Game:
    """游戏主控制 - 状态机管理"""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.font = get_font(28)
        self.title_font = get_font(48)

        # 状态: "menu", "playing", "settings"
        self.state = "menu"

        # 帧率设置（默认无上限，可选 60/120/144/180/240/无限制）
        self.fps = 0  # 0 = 无限制（默认）
        self.fps_options = [60, 120, 144, 180, 240, 0]  # 0 = 无限制

        # 游戏速度倍率（1-10 倍，加速/慢放）
        self.game_speed = 1.0
        self.game_speed_options = [1.0, 2.0, 3.0, 5.0, 10.0]

        # 实时帧率统计
        self.current_fps = 0
        self._fps_counter = 0
        self._fps_timer = 0.0

        # 加载默认设置
        self.controls = self._load_default_controls()

        # 各场景实例（settings_scene需controls初始化后才能创建）
        self.menu = Menu(self)
        self.settings_scene = SettingsScene(self)
        self.save_load = SaveLoad()

        # 当前游戏场景（进入游戏时创建）
        self.game_scene = None

        # 后台预生成嘲讽池（启动时，菜单停留期间完成，进游戏不卡）
        try:
            import threading
            from combat_system import _global_taunt_pool
            import ai_assistant
            def _preload_taunts():
                try:
                    if ai_assistant.AI_ENABLED:
                        taunts = ai_assistant.get_taunts_batch(20)
                        _global_taunt_pool.extend(taunts)
                except Exception:
                    pass
            t = threading.Thread(target=_preload_taunts, daemon=True)
            t.start()
        except Exception:
            pass

    def _load_default_controls(self):
        """默认操作设置 WASD"""
        return {
            "up": pygame.K_w,
            "down": pygame.K_s,
            "left": pygame.K_a,
            "right": pygame.K_d,
        }

    def start_new_game(self):
        """开始新游戏"""
        self.game_scene = GameScene(self)
        self.state = "playing"

    def load_game(self):
        """读档"""
        save_data = self.save_load.load()
        if save_data:
            self.game_scene = GameScene(self, save_data)
            self.state = "playing"
            return True
        return False

    def save_game(self):
        """存档"""
        if self.game_scene:
            data = self.game_scene.get_save_data()
            self.save_load.save(data)

    def back_to_menu(self):
        """返回菜单"""
        self.state = "menu"
        self.game_scene = None

    def quit_game(self):
        """退出游戏"""
        pygame.quit()
        import sys
        sys.exit(0)

    def run(self):
        """主循环"""
        running = True
        while running:
            # 使用帧率设置（0 = 无限制）
            if self.fps > 0:
                real_dt = self.clock.tick(self.fps) / 1000.0
            else:
                real_dt = self.clock.tick() / 1000.0

            # 游戏逻辑时间（受游戏速度倍率影响，1-10 倍）
            dt = real_dt * self.game_speed

            # 实时帧率统计（每 0.5 秒真实时间更新一次）
            self._fps_counter += 1
            self._fps_timer += real_dt
            if self._fps_timer >= 0.5:
                self.current_fps = int(self._fps_counter / self._fps_timer)
                self._fps_counter = 0
                self._fps_timer = 0.0

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue

                if self.state == "menu":
                    self.menu.handle_event(event)
                elif self.state == "playing":
                    self.game_scene.handle_event(event)
                elif self.state == "settings":
                    self.settings_scene.handle_event(event)

            # 更新
            if self.state == "menu":
                self.menu.update(dt)
            elif self.state == "playing":
                self.game_scene.update(dt)
            elif self.state == "settings":
                self.settings_scene.update(dt)

            # 绘制
            self.screen.fill(BG_COLOR)
            if self.state == "menu":
                self.menu.draw(self.screen)
            elif self.state == "playing":
                self.game_scene.draw(self.screen)
            elif self.state == "settings":
                self.settings_scene.draw(self.screen)

            # 右上角实时帧率显示（所有界面）
            fps_font = get_font(22)
            fps_text = fps_font.render(f"FPS: {self.current_fps}", True, (120, 220, 120))
            self.screen.blit(fps_text, (SCREEN_WIDTH - fps_text.get_width() - 15, 12))
            # 游戏速度显示（非 1 倍时显示）
            if self.game_speed != 1.0:
                speed_text = fps_font.render(f"速度: {self.game_speed:.0f}x", True, (255, 200, 120))
                self.screen.blit(speed_text, (SCREEN_WIDTH - speed_text.get_width() - 15, 38))

            pygame.display.flip()

        pygame.quit()
