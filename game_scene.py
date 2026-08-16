"""
肉鸽游戏 - 游戏场景
"""
import pygame
import json
import random
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, BG_COLOR, GRID_COLOR,
                      PLAYER_SPEED, PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_COLOR,
                      GRASS_DARK, GRASS_LIGHT, DIRT_COLOR, TILE_SIZE, MAP_SEED,
                      DASH_DISTANCE, DASH_SPEED_FACTOR, DASH_COLOR, PLAYER_HP,
                      WHITE, GRAY, LIGHT_GRAY, HIGHLIGHT, FIRE_RATE,
                      ATTACK_SPEED_MIN, ATTACK_SPEED_MAX,
                      BULLET_COUNT_MIN, BULLET_COUNT_MAX,
                      BULLET_SIZE, BULLET_SIZE_BONUS_MIN, BULLET_SIZE_BONUS_MAX,
                      GRASS_COLORS, EGG_STAY_TIME_DEFAULT, KILLS_PER_LEVEL, LOW_HP_THRESHOLD)
from fonts import get_font
from input_helper import is_physical_key_down, disable_ime
from combat_system import CombatSystem


class GameScene:
    """游戏主场景 - 无限地图 + 相机跟随 + 战斗"""

    def __init__(self, game, save_data=None):
        self.game = game
        # 玩家在世界坐标中的位置（左上角）
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT // 2
        self.camera_x = 0
        self.camera_y = 0

        # 当前按下的按键集合
        self._pressed = set()

        # 双击方向键计时器（用于冲刺技能）
        self._last_key_time = 0
        self._last_key = None
        self._double_tap_ms = 250  # 双击判定时间

        # 冲刺状态（平滑移动过程）
        self.dash_remaining = 0.0   # 剩余冲刺距离（像素）
        self.dash_dir_x = 0         # 冲刺方向
        self.dash_dir_y = 0
        self.dash_speed = 1200      # 冲刺速度（像素/秒）

        # 碰撞冷却计时（防止一帧内多次扣血）
        self._hit_cooldown = 0.0

        # 升级状态
        self.is_level_up = False
        self._level_up_options = []       # 三个选项，如 ["攻击", "生命", "移速"]
        self._level_up_desc = []          # 对应描述
        self._level_up_funcs = []         # 对应回调函数

        # GM 控制面板状态
        self.gm_active = False
        self._gm_input = ""               # 当前输入的数值字符串
        self._gm_selected_index = 0       # 当前选中的属性索引
        self._gm_props = ["伤害", "移速", "射速", "弹量", "穿透", "弹射", "生命", "暴击率", "暴击伤害", "奖励间隔", "洗脑概率", "屏障范围", "屏障频率", "生命回复", "自动攻击"]

        # 自动攻击开关（默认开）
        self.auto_attack = True

        # 闪烁格子奖励：每分钟随机一个格子闪烁 3 秒，踩到获得升级
        self.bonus_tile = None           # 闪烁格子 (tx, ty)
        self.bonus_tile_timer = 0.0      # 闪烁剩余时间
        self.bonus_spawn_timer = 0.0     # 每分钟触发计时器
        self.bonus_notice = ""           # 提示文字
        self.bonus_notice_timer = 0.0

        # 背景色系：每次进入场景随机选一个色系（同色系深浅变化）
        self.bg_palette, self.scene_name = self._pick_bg_palette()
        # 加载当前场景的瓦片素材
        try:
            import assets_manager
            self.scene_tile = assets_manager.load_scene_tile(self.scene_name)
        except Exception:
            self.scene_tile = None
        self.player_color_override = None   # 角色对比色覆盖（接近背景时用互补色）
        self.enemy_color_overrides = {}     # 敌人颜色覆盖

        # 加载角色/敌人素材
        try:
            import assets_manager
            self.player_sprite = assets_manager.load_character()
            self.enemy_sprite = assets_manager.load_enemy_sprite()
        except Exception:
            self.player_sprite = None
            self.enemy_sprite = None

        # 进入游戏时关闭中文输入法
        disable_ime()

        # 战斗系统
        self.combat = CombatSystem(self.player_x, self.player_y)
        self.combat.player.x = self.player_x
        self.combat.player.y = self.player_y
        # 击杀升级回调
        self.combat.on_kill_callback = self._on_trigger_level_up

        # 应用背景对比色调整
        self._apply_bg_contrast()

        # 玩家是否死亡
        self.is_dead = False

        if save_data:
            self.load_from_data(save_data)

    def load_from_data(self, save_data):
        """从存档数据加载"""
        try:
            data = json.loads(save_data)
            self.player_x = data.get("player_x", SCREEN_WIDTH // 2)
            self.player_y = data.get("player_y", SCREEN_HEIGHT // 2)
            p = self.combat.player
            p.hp = data.get("hp", PLAYER_HP)
            p.max_hp = data.get("max_hp", PLAYER_HP)
            p.damage = data.get("damage", 1)
            p.level = data.get("level", 1)
            p.kill_count = data.get("kill_count", 0)
            p.speed_bonus = data.get("speed_bonus", 0.0)
            p.fire_rate_bonus = data.get("fire_rate_bonus", 0.0)
            p.bullet_count = data.get("bullet_count", 1)
            p.pierce = data.get("pierce", 0)
            p.bullet_size_bonus = data.get("bullet_size_bonus", 0.0)
            p.bounce = data.get("bounce", 0)
            p.lifesteal = data.get("lifesteal", 0.0)
            p.crit_rate = data.get("crit_rate", 0.05)
            p.crit_damage = data.get("crit_damage", 2.0)
            p.brainwash_chance = data.get("brainwash_chance", 0.01)
            p.barrier_enabled = data.get("barrier_enabled", False)
            p.barrier_radius = data.get("barrier_radius", 2)
            p.barrier_freq = data.get("barrier_freq", 1.0)
            p.explosion_enabled = data.get("explosion_enabled", False)
            p.explosion_radius = data.get("explosion_radius", 1)
            p.knockback_enabled = data.get("knockback_enabled", False)
            p.knockback_dist = data.get("knockback_dist", 1)
            self.combat.player.x = self.player_x
            self.combat.player.y = self.player_y
        except (json.JSONDecodeError, TypeError):
            pass

    def get_save_data(self):
        """获取当前存档数据"""
        p = self.combat.player
        return json.dumps({
            "player_x": self.player_x,
            "player_y": self.player_y,
            "hp": p.hp,
            "max_hp": p.max_hp,
            "damage": p.damage,
            "level": p.level,
            "kill_count": p.kill_count,
            "speed_bonus": p.speed_bonus,
            "fire_rate_bonus": p.fire_rate_bonus,
            "bullet_count": p.bullet_count,
            "pierce": p.pierce,
            "bullet_size_bonus": p.bullet_size_bonus,
            "bounce": p.bounce,
            "lifesteal": p.lifesteal,
            "crit_rate": p.crit_rate,
            "crit_damage": p.crit_damage,
            "brainwash_chance": p.brainwash_chance,
            "barrier_enabled": p.barrier_enabled,
            "barrier_radius": p.barrier_radius,
            "barrier_freq": p.barrier_freq,
            "explosion_enabled": p.explosion_enabled,
            "explosion_radius": p.explosion_radius,
            "knockback_enabled": p.knockback_enabled,
            "knockback_dist": p.knockback_dist,
        })

    def _on_trigger_level_up(self):
        import random
        import math
        self.is_level_up = True
        p = self.combat.player

        # 预先计算随机值，让玩家在面板上直接看到具体数值
        as_val = random.randint(10, 100)                      # 攻速 +X%
        bc_val = random.randint(1, 5)                         # 子弹 +X
        bs_val = random.randint(10, 100)                      # 子弹大小 +X%
        # 攻速实际加成量（百分比转小数）
        as_bonus = as_val / 100.0
        bs_bonus = bs_val / 100.0
        cr_val = random.randint(5, 20)                        # 暴击率 +X%
        cd_val = random.randint(5, 20)                        # 暴击伤害 +X%
        cr_bonus = cr_val / 100.0
        cd_bonus = cd_val / 100.0

        # 当前属性显示
        current_fire_rate = FIRE_RATE * (1 + p.fire_rate_bonus)
        current_speed = int(PLAYER_SPEED * (1 + p.speed_bonus))
        current_bullet_size = int(BULLET_SIZE * (1 + p.bullet_size_bonus))
        pierce_desc = "穿透 +1"
        bounce_desc = "弹射 +1"
        lifesteal_state = f"{p.lifesteal*100:.0f}%" if p.lifesteal > 0 else "未开启"

        # 候选项（名称，描述，回调函数）
        pool = [
            ("攻击",  f"子弹伤害 +2",  p.upgrade_attack),
            ("生命",  f"生命上限 +2",   p.upgrade_hp),
            ("移速",  f"移速 +10%", p.upgrade_speed),
            ("攻速",  f"射击速度 +{as_val}%",
             lambda v=as_bonus: p.upgrade_attack_speed(v)),
            ("弹量",  f"子弹 +{bc_val}",
             lambda v=bc_val: p.upgrade_bullet_count(v)),
            ("穿透",  pierce_desc, p.upgrade_pierce),
            ("子弹大小", f"子弹大小 +{bs_val}%",
             lambda v=bs_bonus: p.upgrade_bullet_size(v)),
            ("弹射",  bounce_desc, p.upgrade_bounce),
            ("吸血",  f"吸血概率 +10%", p.upgrade_lifesteal),
            ("暴击率",  f"暴击率 +{cr_val}%",
             lambda v=cr_bonus: p.upgrade_crit_rate(v)),
            ("暴击伤害", f"暴击伤害 +{cd_val}%",
             lambda v=cd_bonus: p.upgrade_crit_damage(v)),
            ("洗脑",  f"洗脑概率 +1%", p.upgrade_brainwash),
            ("生命回复", f"每秒回血 +1", p.upgrade_regen),
            ("爆炸",  f"子弹命中爆炸，范围+1格" if p.explosion_enabled else "子弹命中引发爆炸", p.upgrade_explosion),
            ("击退",  f"子弹击退敌人，距离+1格" if p.knockback_enabled else "子弹击退敌人1格", p.upgrade_knockback),
            ("召唤",  f"每10秒召唤一只十二生肖", p.upgrade_summon),
        ]

        # 召唤开启后追加召唤强化选项
        if p.summon_enabled:
            import random as _r
            sa_val = _r.randint(10, 50)  # 攻速 +10%~50%
            sm_val = _r.randint(10, 20)  # 移速 +10%~20%
            sd_val = _r.randint(10, 20)  # 持续时间 +10%~20%
            pool.append(("召唤攻速", f"召唤物攻速 +{sa_val}%", lambda v=sa_val/100.0: p.upgrade_summon_atk_speed(v)))
            pool.append(("召唤移速", f"召唤物移速 +{sm_val}%", lambda v=sm_val/100.0: p.upgrade_summon_move_speed(v)))
            pool.append(("召唤时长", f"召唤物持续时间 +{sd_val}%", lambda v=sd_val/100.0: p.upgrade_summon_duration(v)))

        # 屏障解锁后才有范围/频率选项
        if p.barrier_enabled:
            pool.append(("屏障范围", f"屏障范围 +1格", p.upgrade_barrier_radius))
            pool.append(("屏障频率", f"屏障频率翻倍", p.upgrade_barrier_freq))
        else:
            pool.append(("屏障解锁", "获得能量屏障", p.upgrade_barrier_radius))

        # 过滤：暴击率满/吸血满不再出现；穿透 与 (击退/弹射/爆炸) 互斥
        # 拥有击退/弹射/爆炸任一 → 不出穿透；选了穿透 → 不出这三项
        has_pierce = p.pierce > 0
        has_knockback_chain = p.knockback_enabled or p.bounce > 0 or p.explosion_enabled
        pool = [opt for opt in pool if not (
            (opt[0] == "暴击率" and p.crit_rate >= 1.0) or
            (opt[0] == "吸血" and p.lifesteal >= 1.0) or
            (opt[0] == "穿透" and has_knockback_chain) or
            (opt[0] in ("击退", "弹射", "爆炸") and has_pierce) or
            (opt[0] == "召唤" and p.summon_enabled)
        )]

        # 随机选 3 个不同的选项（关键新机制加权，更容易出现）
        # 权重：召唤/爆炸/击退/屏障解锁 等未解锁核心项提高出现概率
        weights = []
        for opt in pool:
            name = opt[0]
            if name == "召唤" and not p.summon_enabled:
                weights.append(4)  # 召唤未解锁时高权重
            elif name == "屏障解锁":
                weights.append(3)
            elif name in ("爆炸", "击退") and not (
                name == "爆炸" and p.explosion_enabled
            ) and not (name == "击退" and p.knockback_enabled):
                weights.append(3)
            else:
                weights.append(1)
        chosen = random.choices(pool, weights=weights, k=3)
        # 去重（choices 可能重复）
        chosen_unique = []
        seen_names = set()
        for c in chosen:
            if c[0] not in seen_names:
                chosen_unique.append(c)
                seen_names.add(c[0])
        # 如果去重后不足 3 个，从剩余补充
        if len(chosen_unique) < 3:
            for opt in pool:
                if opt[0] not in seen_names and len(chosen_unique) < 3:
                    chosen_unique.append(opt)
                    seen_names.add(opt[0])
        chosen = chosen_unique[:3]

        self._level_up_options = [c[0] for c in chosen]
        self._level_up_desc = [c[1] for c in chosen]
        self._level_up_funcs = [c[2] for c in chosen]
    def _apply_level_up(self, index):
        """应用选中的升级"""
        if 0 <= index < len(self._level_up_funcs):
            self._level_up_funcs[index]()
        self.is_level_up = False
        self._level_up_options = []
        self._level_up_desc = []
        self._level_up_funcs = []
        # 清空按键状态，防止选完后自动往一个方向跑
        self._pressed.clear()
        self._last_key_time = 0
        self._last_key = None

    def _handle_levelup_click(self, mouse_pos):
        """处理升级面板的鼠标点击"""
        mx, my = mouse_pos
        for i in range(3):
            y = 280 + i * 90 - 30  # box top
            if y <= my <= y + 80:
                self._apply_level_up(i)
                break

    # ================== GM 功能 ==================

    def _gm_get_value(self, prop_index):
        """获取指定 GM 属性的当前值"""
        p = self.combat.player
        if prop_index == 0:
            return p.damage
        elif prop_index == 1:
            return int(PLAYER_SPEED * (1 + p.speed_bonus))
        elif prop_index == 2:
            return FIRE_RATE * (1 + p.fire_rate_bonus)
        elif prop_index == 3:
            return p.bullet_count
        elif prop_index == 4:
            return p.pierce
        elif prop_index == 5:
            return p.bounce
        elif prop_index == 6:
            return p.max_hp
        elif prop_index == 7:
            return p.crit_rate
        elif prop_index == 8:
            return p.crit_damage
        elif prop_index == 9:
            return self.bonus_spawn_timer
        elif prop_index == 10:
            return p.brainwash_chance
        elif prop_index == 11:
            return p.barrier_radius
        elif prop_index == 12:
            return p.barrier_freq
        elif prop_index == 13:
            return 1 if p.regen else 0
        elif prop_index == 14:
            return 1 if self.auto_attack else 0
        return 0

    def _gm_set_value(self, prop_index, value):
        """设置指定 GM 属性的值（立即生效）"""
        p = self.combat.player
        if prop_index == 0:
            p.damage = max(1, int(value))
        elif prop_index == 1:
            # 移速：基础 300，设置后 speed_bonus = value/300 - 1
            speed = max(50, int(value))
            p.speed_bonus = speed / PLAYER_SPEED - 1.0
        elif prop_index == 2:
            # 射速：fire_rate_bonus = value/FIRE_RATE - 1
            rate = max(0.5, float(value))
            p.fire_rate_bonus = rate / FIRE_RATE - 1.0
        elif prop_index == 3:
            p.bullet_count = max(1, int(value))
        elif prop_index == 4:
            p.pierce = max(0, int(value))
        elif prop_index == 5:
            p.bounce = max(0, int(value))
        elif prop_index == 6:
            p.max_hp = max(1, int(value))
            p.hp = min(p.hp, p.max_hp)
        elif prop_index == 7:
            # 暴击率：输入百分数（如 50 = 50%）
            p.crit_rate = max(0.0, min(1.0, float(value) / 100.0))
        elif prop_index == 8:
            # 暴击伤害：输入百分数（如 300 = 300%）
            p.crit_damage = max(1.0, float(value) / 100.0)
        elif prop_index == 9:
            # 奖励格子刷新间隔（秒）
            self.bonus_spawn_timer = max(0.0, float(value))
        elif prop_index == 10:
            # 洗脑概率：输入百分数（如 5 = 5%）
            p.brainwash_chance = max(0.0, min(1.0, float(value) / 100.0))
        elif prop_index == 11:
            # 屏障范围：整数（格）
            p.barrier_enabled = True
            p.barrier_radius = max(1, int(value))
        elif prop_index == 12:
            # 屏障频率：浮点数
            p.barrier_enabled = True
            p.barrier_freq = max(0.1, float(value))
        elif prop_index == 13:
            # 生命回复：1开 0关
            p.regen = int(value) > 0
        elif prop_index == 14:
            # 自动攻击：1开 0关
            self.auto_attack = int(value) > 0

    def _gm_apply(self):
        """应用 GM 输入（解析数值并设置）"""
        try:
            value = float(self._gm_input)
            self._gm_set_value(self._gm_selected_index, value)
        except (ValueError, TypeError):
            pass
        self._gm_input = ""

    def handle_gm_event(self, event):
        """处理 GM 面板的键盘输入"""
        if event.type == pygame.KEYDOWN:
            # 数字键（主键盘 0-9）
            if pygame.K_0 <= event.key <= pygame.K_9:
                self._gm_input += chr(event.key)
            # 小键盘数字键（显式映射，keycode 不连续）
            else:
                kp_map = {
                    pygame.K_KP0: "0", pygame.K_KP1: "1", pygame.K_KP2: "2",
                    pygame.K_KP3: "3", pygame.K_KP4: "4", pygame.K_KP5: "5",
                    pygame.K_KP6: "6", pygame.K_KP7: "7", pygame.K_KP8: "8",
                    pygame.K_KP9: "9",
                }
                if event.key in kp_map:
                    self._gm_input += kp_map[event.key]
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self._gm_input += "-"
                elif event.key in (pygame.K_PERIOD, pygame.K_KP_PERIOD):
                    self._gm_input += "."
                elif event.key == pygame.K_BACKSPACE:
                    self._gm_input = self._gm_input[:-1]
                elif event.key == pygame.K_UP:
                    self._gm_selected_index = (self._gm_selected_index - 1) % 15
                    self._gm_input = ""
                elif event.key == pygame.K_DOWN:
                    self._gm_selected_index = (self._gm_selected_index + 1) % 15
                    self._gm_input = ""
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._gm_apply()
                elif event.key == pygame.K_ESCAPE:
                    self.gm_active = False
                    self._gm_input = ""
                elif event.key == pygame.K_F1:
                    self.gm_active = False
                    self._gm_input = ""

    def _try_dash(self, direction_key):
        """尝试触发冲刺（双击方向键）"""
        import pygame
        current_time = pygame.time.get_ticks()
        
        if self._last_key == direction_key:
            # 同方向再按，检查是否在双击时间窗口内
            if self._last_key_time > 0 and (current_time - self._last_key_time) < self._double_tap_ms:
                # 双击成功，执行冲刺
                self._last_key_time = 0
                self._last_key = None
                
                # 计算冲刺方向
                dx, dy = 0, 0
                if direction_key == self.game.controls["up"]:
                    dy = -1
                elif direction_key == self.game.controls["down"]:
                    dy = 1
                elif direction_key == self.game.controls["left"]:
                    dx = -1
                elif direction_key == self.game.controls["right"]:
                    dx = 1
                
                # 设置冲刺状态（位移距离 = DASH_DISTANCE * TILE_SIZE，由 update 平滑移动）
                self.dash_remaining = DASH_DISTANCE * TILE_SIZE
                self.dash_dir_x = dx
                self.dash_dir_y = dy
                return True
        
        # 记录本次按键时间（作为第一次按下）
        self._last_key_time = current_time
        self._last_key = direction_key
        return False

    # ================== 闪烁格子奖励 ==================

    def _update_bonus_tile(self, dt):
        """每分钟随机一个格子闪烁 3 秒，踩到获得升级"""
        # 每分钟生成闪烁格子
        self.bonus_spawn_timer += dt
        if self.bonus_spawn_timer >= 60:
            self.bonus_spawn_timer -= 60
            # 在玩家附近随机选一个格子（可见范围）
            cx = int(self.player_x // TILE_SIZE)
            cy = int(self.player_y // TILE_SIZE)
            self.bonus_tile = (cx + random.randint(-3, 3), cy + random.randint(-3, 3))
            self.bonus_tile_timer = 3.0  # 闪烁 3 秒

        # 闪烁计时
        if self.bonus_tile is not None:
            self.bonus_tile_timer -= dt
            # 玩家踩到闪烁格子
            tx = int(self.player_x // TILE_SIZE)
            ty = int(self.player_y // TILE_SIZE)
            if self.bonus_tile == (tx, ty):
                self.bonus_notice = "踩到奖励格子！获得免费升级！"
                self.bonus_notice_timer = 2.0
                self.bonus_tile = None
                self._on_trigger_level_up()
            elif self.bonus_tile_timer <= 0:
                # 3 秒超时，格子恢复正常
                self.bonus_tile = None

        # 提示文字计时
        if self.bonus_notice_timer > 0:
            self.bonus_notice_timer -= dt
            if self.bonus_notice_timer <= 0:
                self.bonus_notice = ""

    def handle_event(self, event):
        """处理事件"""
        # 死亡状态
        if self.is_dead:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.state = "menu"
            return

        # GM 面板激活时：优先处理 GM 输入
        if self.gm_active:
            self.handle_gm_event(event)
            return

        # F1 打开/关闭 GM 面板
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.gm_active = True
            self._gm_input = ""
            self._pressed.clear()
            disable_ime()  # 关闭输入法，防止数字键被拦截
            return

        # 升级状态：只处理 1/2/3 选择、R 重置、ESC 取消
        if self.is_level_up:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self._apply_level_up(0)
                elif event.key == pygame.K_2:
                    self._apply_level_up(1)
                elif event.key == pygame.K_3:
                    self._apply_level_up(2)
                elif event.key == pygame.K_r:
                    # 重置：重新生成 3 个升级项
                    self._on_trigger_level_up()
                elif event.key == pygame.K_ESCAPE:
                    self._apply_level_up(0)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                reset_rect = pygame.Rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT - 110, 160, 40)
                if reset_rect.collidepoint(mx, my):
                    self._on_trigger_level_up()  # 重置选项
                else:
                    self._handle_levelup_click(event.pos)
            return

        if event.type == pygame.KEYDOWN:
            self._pressed.add(event.key)
            if event.key == pygame.K_ESCAPE:
                self._pressed.clear()
                self.game.state = "menu"
            elif event.key == pygame.K_F5:
                self.game.save_game()
            elif event.key == pygame.K_F2:
                self.auto_attack = not self.auto_attack
            elif event.key == pygame.K_g:
                # 游戏速度循环切换（1-10倍）
                opts = self.game.game_speed_options
                idx = opts.index(self.game.game_speed) if self.game.game_speed in opts else 0
                idx = (idx + 1) % len(opts)
                self.game.game_speed = opts[idx]
            else:
                # 检查是否触发冲刺
                controls = self.game.controls
                if event.key == controls["up"]:
                    self._try_dash(controls["up"])
                elif event.key == controls["down"]:
                    self._try_dash(controls["down"])
                elif event.key == controls["left"]:
                    self._try_dash(controls["left"])
                elif event.key == controls["right"]:
                    self._try_dash(controls["right"])
        elif event.type == pygame.KEYUP:
            self._pressed.discard(event.key)

    def update(self, dt):
        """游戏逻辑更新"""
        if self.is_dead:
            return

        # GM 面板打开时暂停游戏
        if self.gm_active:
            self.camera_x = self.player_x + PLAYER_WIDTH / 2 - SCREEN_WIDTH / 2
            self.camera_y = self.player_y + PLAYER_HEIGHT / 2 - SCREEN_HEIGHT / 2
            return

        # 升级界面只暂停玩家控制和敌人靠近，但仍更新子弹、动画
        if self.is_level_up:
            # 敌人在升级期间冻结，让玩家从容选择
            self.camera_x = self.player_x + PLAYER_WIDTH / 2 - SCREEN_WIDTH / 2
            self.camera_y = self.player_y + PLAYER_HEIGHT / 2 - SCREEN_HEIGHT / 2
            return

        # --- 玩家移动 ---
        dx, dy = 0, 0
        controls = self.game.controls

        # 优先用事件跟踪，若为空用物理按键兜底
        if not self._pressed:
            if is_physical_key_down(controls["up"]):
                dy -= 1
            if is_physical_key_down(controls["down"]):
                dy += 1
            if is_physical_key_down(controls["left"]):
                dx -= 1
            if is_physical_key_down(controls["right"]):
                dx += 1
        else:
            if controls["up"] in self._pressed:
                dy -= 1
            if controls["down"] in self._pressed:
                dy += 1
            if controls["left"] in self._pressed:
                dx -= 1
            if controls["right"] in self._pressed:
                dx += 1

        # 归一化斜向移动
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        # 升级后实际速度 = 基础 * (1 + bonus)，向下取整
        speed = int(PLAYER_SPEED * (1 + self.combat.player.speed_bonus))

        # 冲刺平滑移动（优先于普通移动）
        if self.dash_remaining > 0:
            dash_move = self.dash_speed * dt
            self.player_x += self.dash_dir_x * dash_move
            self.player_y += self.dash_dir_y * dash_move
            self.dash_remaining -= dash_move
            if self.dash_remaining <= 0:
                self.dash_remaining = 0
        else:
            # 更新玩家位置（普通移动）
            self.player_x += dx * speed * dt
            self.player_y += dy * speed * dt
        self.combat.player.x = self.player_x
        self.combat.player.y = self.player_y

        # 相机跟随玩家
        self.camera_x = self.player_x + PLAYER_WIDTH / 2 - SCREEN_WIDTH / 2
        self.camera_y = self.player_y + PLAYER_HEIGHT / 2 - SCREEN_HEIGHT / 2

        # --- 闪烁格子奖励 ---
        self._update_bonus_tile(dt)

        # 战斗系统同步自动攻击开关
        self.combat.auto_attack = self.auto_attack
        self.combat.update(dt, self.player_x, self.player_y)

        # 玩家碰撞检测（带冷却，防止连续扣血）
        self._hit_cooldown -= dt
        if self._hit_cooldown <= 0:
            collided, enemy = self.combat.check_player_collision(self.player_x, self.player_y)
            if collided:
                # 敌人攻击（含暴击判定）
                if hasattr(enemy, 'get_attack_damage'):
                    damage, is_crit = enemy.get_attack_damage()
                else:
                    damage, is_crit = getattr(enemy, 'attack', 1), False
                self.combat.player.take_damage(damage)
                # 玩家受击伤害跳字（红色）
                from combat_system import DamageText
                self.combat.damage_texts.append(DamageText(
                    self.player_x + PLAYER_WIDTH / 2,
                    self.player_y - 10,
                    str(damage),
                    is_crit
                ))
                self._hit_cooldown = 0.5  # 0.5 秒内不再重复扣血
                if self.combat.player.hp <= 0:
                    self.is_dead = True

    def draw(self, screen):
        """绘制场景"""
        screen.fill(BG_COLOR)
        self._draw_grid(screen)
        self.combat.draw(screen, self.camera_x, self.camera_y)

        # 绘制玩家（优先用素材，无素材时回退矩形）
        screen_x = self.player_x - self.camera_x
        screen_y = self.player_y - self.camera_y
        if self.player_sprite is not None and not self.is_dead:
            screen.blit(self.player_sprite, (screen_x, screen_y))
        else:
            if self.is_dead:
                player_color = (100, 100, 100)
            elif self.player_color_override is not None:
                player_color = self.player_color_override
            else:
                player_color = PLAYER_COLOR
            pygame.draw.rect(screen, player_color,
                             (screen_x, screen_y, PLAYER_WIDTH, PLAYER_HEIGHT))

        # 玩家头顶红色血条
        p = self.combat.player
        bar_w = PLAYER_WIDTH
        bar_h = 6
        hp_ratio = max(0, p.hp) / p.max_hp
        bar_x = screen_x
        bar_y = screen_y - 10
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, (220, 50, 50), (bar_x, bar_y, bar_w * hp_ratio, bar_h))

        # 等级进度条（最上方，只有进度条没有文字）
        font = get_font(22)
        p = self.combat.player
        gt = self.combat.game_time
        speed_now = int(PLAYER_SPEED * (1 + p.speed_bonus))
        fr = FIRE_RATE * (1 + p.fire_rate_bonus)
        lifesteal_str = f"{p.lifesteal*100:.0f}%"
        minutes = int(gt // 60)
        seconds = int(gt % 60)
        max_tier = self.combat._get_max_tier()
        egg_info = ""
        if self.bonus_tile is not None:
            egg_info = f"奖励格子 {self.bonus_tile_timer:.1f}s"

        kills_in_level = p.kill_count % KILLS_PER_LEVEL
        level_progress = kills_in_level / KILLS_PER_LEVEL
        level_bar_x = 15
        level_bar_y = 15
        level_bar_w = 180
        level_bar_h = 10
        pygame.draw.rect(screen, (40, 40, 50), (level_bar_x, level_bar_y, level_bar_w, level_bar_h))
        pygame.draw.rect(screen, (80, 200, 255), (level_bar_x, level_bar_y, int(level_bar_w * level_progress), level_bar_h))

        # HUD 文字从经验条下方开始

        # 垂直排列的 HUD 行（每行一个属性，从 y=30 开始）
        hud_lines = [
            f"位置: ({int(self.player_x)}, {int(self.player_y)})",
            f"生命: {p.hp}/{p.max_hp}",
            f"等级: {p.level}",
            f"击杀: {p.kill_count}",
            f"伤害: {p.damage}",
            f"移速: {speed_now}",
            f"射速: {fr:.1f}/秒",
            f"弹量: {p.bullet_count}",
            f"穿透: {p.pierce}",
            f"暴击率: {p.crit_rate*100:.0f}%",
            f"暴击伤害: {p.crit_damage*100:.0f}%",
            f"吸血: {lifesteal_str}",
            f"弹射: {p.bounce}",
            f"子弹大小: {(1+p.bullet_size_bonus)*100:.0f}%",
            f"时间: {minutes:02d}:{seconds:02d}",
            f"敌人强度: {max_tier}",
        ]
        if egg_info:
            hud_lines.append(egg_info)

        for i, line in enumerate(hud_lines):
            y = 35 + i * 22
            color = (255, 220, 120) if i == len(hud_lines) - 1 and egg_info else (255, 255, 255)
            surf = font.render(line, True, color)
            screen.blit(surf, (15, y))


        # 濒血红色边缘闪烁（血量低于 10%）
        p = self.combat.player
        if not self.is_dead and p.hp / p.max_hp < LOW_HP_THRESHOLD:
            # 用脉冲闪烁
            import math as _math
            blink = (_math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2  # 0~1
            alpha = int(40 + 80 * blink)
            edge = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            # 边缘红色框
            thickness = 8 + int(10 * blink)
            pygame.draw.rect(edge, (255, 0, 0, alpha), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), thickness)
            screen.blit(edge, (0, 0))

        if self.is_dead:
            # 死亡提示
            big_font = get_font(72)
            death_text = big_font.render("你死了", True, (255, 80, 80))
            screen.blit(death_text, death_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))
            tip_font = get_font(28)
            tip = tip_font.render("按 ESC 返回菜单 · 再进来吧", True, (220, 220, 220))
            screen.blit(tip, tip.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)))
        else:
            hint = font.render("WASD 移动 · 双击方向冲刺 · ESC 返回菜单 · F5 存档", True, (210, 210, 210))
            screen.blit(hint, (15, SCREEN_HEIGHT - 40))

        # 升级面板（居中弹窗）
        if self.is_level_up:
            # 半透明背景
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            # 标题
            title_font = get_font(48)
            title = title_font.render("选择升级", True, HIGHLIGHT)
            screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 180)))

            # 三个选项
            option_font = get_font(32)
            for i, (opt, desc) in enumerate(zip(self._level_up_options, self._level_up_desc)):
                y = 280 + i * 90
                # 选项框（加高，容纳两行文字）
                box_rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, y - 30, 440, 80)
                # 选项框
                pygame.draw.rect(screen, (40, 40, 50), box_rect, border_radius=8)
                pygame.draw.rect(screen, (100, 100, 120), box_rect, width=2, border_radius=8)
                # 编号（垂直居中靠左）
                num_surf = option_font.render(f"{i+1}.", True, WHITE)
                screen.blit(num_surf, (box_rect.x + 12, box_rect.y + 20))
                # 选项名（黄字，第一行）
                opt_surf = option_font.render(opt, True, HIGHLIGHT)
                screen.blit(opt_surf, (box_rect.x + 60, box_rect.y + 8))
                # 描述（灰字，第二行，拉开间距）
                desc_surf = font.render(desc, True, LIGHT_GRAY)
                screen.blit(desc_surf, (box_rect.x + 60, box_rect.y + 50))

            # 提示
            tip_font = get_font(24)
            tip = tip_font.render("按 1/2/3 选择 · ESC 默认选第一项 · R 键重置选项", True, GRAY)
            screen.blit(tip, tip.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)))

            # 重置按钮（刷新 3 个升级项）
            reset_rect = pygame.Rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT - 110, 160, 40)
            pygame.draw.rect(screen, (60, 50, 30), reset_rect, border_radius=6)
            pygame.draw.rect(screen, (200, 160, 60), reset_rect, width=2, border_radius=6)
            reset_text = tip_font.render("重置选项", True, (220, 190, 80))
            screen.blit(reset_text, reset_text.get_rect(center=reset_rect.center))

        # 奖励提示文字（屏幕中央上方，层级高于升级面板和GM面板）
        if self.bonus_notice:
            notice_font = get_font(40)
            notice_surf = notice_font.render(self.bonus_notice, True, (80, 255, 80))
            screen.blit(notice_surf, notice_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)))

        # GM 控制面板（F1 开启）
        if self.gm_active:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            title_font = get_font(48)
            title = title_font.render("GM 控制面板 (F1 退出)", True, HIGHLIGHT)
            screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 100)))

            btn_font = get_font(28)
            input_font = pygame.font.Font(None, 36)

            for i, prop in enumerate(self._gm_props):
                # 分两列：左列 0-5, 右列 6-10
                col = 0 if i < 6 else 1
                row = i if i < 6 else i - 6
                y = 140 + row * 60
                x = 60 if col == 0 else 660
                # 背景框
                frame = pygame.Rect(x, y - 10, 560, 50)
                pygame.draw.rect(screen, (40, 40, 50), frame, border_radius=6)
                pygame.draw.rect(screen, (100, 100, 120), frame, width=2, border_radius=6)

                # 当前值高亮选中项
                current_val = self._gm_get_value(i)
                if i == self._gm_selected_index:
                    val_color = (255, 255, 100)
                else:
                    val_color = WHITE

                # 属性名/当前值/输入框
                name = btn_font.render(prop, True, WHITE)
                screen.blit(name, (frame.x + 15, frame.y + 8))

                # 值显示（暴击率/伤害/洗脑以百分比显示）
                if i in (7, 8, 10):
                    val_str = f"{current_val*100:.0f}%"
                elif i == 2 or i == 12:
                    val_str = f"{current_val:.1f}"
                else:
                    val_str = str(int(current_val))
                val = btn_font.render(f"当前: {val_str}", True, val_color)
                screen.blit(val, (frame.x + 200, frame.y + 8))

                # 输入框（只有选中的那一行显示输入框）
                if i == self._gm_selected_index:
                    if self._gm_input:
                        input_txt = f"新值: {self._gm_input}"
                    else:
                        input_txt = "输入后按回车确认"
                    input_surf = input_font.render(input_txt, True, (255, 255, 100))
                    screen.blit(input_surf, (frame.x + 400, frame.y + 20))
                else:
                    # 非选中项显示 "←" 箭头提示
                    inactive_font = get_font(22)
                    hint_surf = inactive_font.render("按↑↓选中", True, (60, 60, 70))
                    screen.blit(hint_surf, (frame.x + 400, frame.y + 22))

            tip = btn_font.render("↑↓ 切换属性 · 目标输入框输入数值 · 回车确认 · ESC 退出", True, GRAY)
            screen.blit(tip, tip.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)))

    def _pick_bg_palette(self):
        """随机选择一个背景色系和场景（RGB, 场景名）"""
        palettes = [
            ((70, 120, 200), "水域"),   # 蓝系 → 水域
            ((60, 150, 90), "草原"),    # 绿系 → 草原
            ((200, 80, 80), "熔岩"),    # 红系 → 熔岩
            ((160, 80, 180), "墓地"),   # 紫系 → 墓地
            ((210, 140, 60), "沙漠"),   # 橙系 → 沙漠
            ((70, 160, 160), "雪地"),   # 青系 → 雪地
            ((190, 110, 150), "地牢"),  # 粉系 → 地牢
            ((150, 130, 70), "星空"),   # 棕/土黄系 → 星空
        ]
        return random.choice(palettes)

    def _color_distance(self, c1, c2):
        """计算两个 RGB 颜色的距离（越小越接近）"""
        return abs(c1[0] - c2[0]) + abs(c1[1] - c2[1]) + abs(c1[2] - c2[2])

    def _contrast_color(self, color):
        """返回颜色的互补色（RGB 取反）"""
        return (255 - color[0], 255 - color[1], 255 - color[2])

    def _apply_bg_contrast(self):
        """根据背景色系调整角色/敌人颜色，保证对比度"""
        bg = self.bg_palette
        # 角色颜色
        player_c = PLAYER_COLOR
        if self._color_distance(player_c, bg) < 200:
            self.player_color_override = self._contrast_color(player_c)
        else:
            self.player_color_override = None
        # 敌人各色系颜色（tier 0-5 + 精英 + 弓箭手）
        enemy_overrides = {}
        from combat_system import ENEMY_TIER_COLORS, ELITE_COLOR, ARCHER_COLOR
        from settings import ENEMY_TIER_COLORS as TIER, ELITE_COLOR as ELITE, ARCHER_COLOR as ARCHER
        all_colors = {}
        for i, c in enumerate(TIER):
            all_colors[f"tier{i}"] = c
        all_colors["elite"] = ELITE
        all_colors["archer"] = ARCHER
        for key, c in all_colors.items():
            if self._color_distance(c, bg) < 200:
                enemy_overrides[key] = self._contrast_color(c)
        self.enemy_color_overrides = enemy_overrides
        # 通知战斗系统应用颜色覆盖
        if self.combat:
            self.combat.apply_enemy_colors(enemy_overrides)
            self.combat.player_contrast_color = self.player_color_override

    def _draw_grid(self, screen):
        """绘制程序化无限地图背景（同色系深浅变化的格子）"""
        def tile_hash(tx, ty, salt):
            h = (tx * 374761393 + ty * 668265263 + salt * 69069) & 0x7FFFFFFF
            h = (h ^ (h >> 13)) * 1274126177 & 0x7FFFFFFF
            h = h ^ (h >> 16)
            return h

        left_tile = int(self.camera_x // TILE_SIZE) - 1
        right_tile = int((self.camera_x + SCREEN_WIDTH) // TILE_SIZE) + 1
        top_tile = int(self.camera_y // TILE_SIZE) - 1
        bottom_tile = int((self.camera_y + SCREEN_HEIGHT) // TILE_SIZE) + 1

        # 场景瓦片素材
        tile = self.scene_tile
        base_r, base_g, base_b = self.bg_palette

        for ty in range(top_tile, bottom_tile + 1):
            for tx in range(left_tile, right_tile + 1):
                world_x = tx * TILE_SIZE
                world_y = ty * TILE_SIZE
                screen_x = world_x - self.camera_x
                screen_y = world_y - self.camera_y

                h = tile_hash(tx, ty, MAP_SEED)
                if tile is not None:
                    # 用场景瓦片素材，轻微明暗变化增强立体感
                    screen.blit(tile, (screen_x, screen_y))
                    shade = 0.85 + (h % 3) * 0.08
                    if shade != 1.0:
                        overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        overlay.fill((0, 0, 0, 0))
                        if shade < 1:
                            overlay.fill((0, 0, 0, int((1 - shade) * 40)))
                        screen.blit(overlay, (screen_x, screen_y))
                else:
                    # 无素材时回退纯色
                    base = (base_r, base_g, base_b)
                    pygame.draw.rect(screen, base,
                                     (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

                # 格子线（浅色，不遮挡素材）
                pygame.draw.line(screen, (0, 0, 0, 0),
                                 (screen_x, screen_y),
                                 (screen_x + TILE_SIZE, screen_y), 1)
                pygame.draw.line(screen, (0, 0, 0, 0),
                                 (screen_x, screen_y),
                                 (screen_x, screen_y + TILE_SIZE), 1)

                # 闪烁奖励格子（绿色闪烁）
                if self.bonus_tile == (tx, ty):
                    import time as _t
                    blink = (int(_t.time() * 8) % 2 == 0)
                    if blink:
                        glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        glow.fill((0, 255, 0, 120))
                        screen.blit(glow, (screen_x, screen_y))
                    else:
                        pygame.draw.rect(screen, (0, 180, 0),
                                         (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 4)
