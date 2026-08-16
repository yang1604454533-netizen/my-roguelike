"""
肉鸽游戏 - 战斗系统
包含：玩家血量、敌人血量、子弹、自动攻击、无限敌人生成
"""
import math
import random
import time
import pygame
from zodiac_pixels import ZODIAC_PIXELS, ZODIAC_COLORS
from fonts import get_font
try:
    import ai_assistant
except ImportError:
    ai_assistant = None

# 全局嘲讽池（Game 启动时后台预填）
_global_taunt_pool = []

from settings import (ENEMY_SIZE, ENEMY_SPEED_FACTOR, ENEMY_COLOR,
                      ENEMY_TIER_COLORS, ENEMY_TIER_STATS,
                      BULLET_SIZE, BULLET_SPEED_FACTOR, BULLET_RANGE_FACTOR,
                      BULLET_COLOR, FIRE_RATE, AUTO_ATTACK_RANGE,
                      PLAYER_SPEED, PLAYER_WIDTH, PLAYER_HEIGHT,
                      ENEMY_SPAWN_INTERVAL, ENEMY_SPAWN_DIST_MIN,
                      ENEMY_SPAWN_DIST_MAX, ENEMY_HP_MIN, ENEMY_HP_MAX,
                      PLAYER_HP, BULLET_DAMAGE, KILLS_PER_LEVEL,
                      PLAYER_HP_BONUS, SPEED_BONUS_PCT,
                      ATTACK_SPEED_MIN, ATTACK_SPEED_MAX,
                      BULLET_COUNT_MIN, BULLET_COUNT_MAX, PIERCE_BONUS,
                      BULLET_SIZE_BONUS_MIN, BULLET_SIZE_BONUS_MAX,
                      BOUNCE_COUNT, LIFESTEAL_CHANCE, LIFESTEAL_PITY, LIFESTEAL_HEAL,
                      CRIT_RATE_DEFAULT, CRIT_DAMAGE_DEFAULT,
                      CRIT_RATE_MIN, CRIT_RATE_MAX, CRIT_DMG_MIN, CRIT_DMG_MAX,
                      DAMAGE_TEXT_LIFETIME, DAMAGE_TEXT_COLOR, CRIT_TEXT_COLOR,
                      CRIT_TEXT_SIZE, DAMAGE_TEXT_SIZE,
                      BRAINWASH_CHANCE, BRAINWASH_DURATION, BRAINWASH_COLOR, BRAINWASH_SIZE,
                      BARRIER_RADIUS, BARRIER_DAMAGE, BARRIER_COLOR, BARRIER_ALPHA,
                      BARRIER_RADIUS_BONUS, BARRIER_FREQ_BONUS,
                      REGEN_AMOUNT, ENEMY_EMPTY_REFRESH,
                      EXPLOSION_RADIUS, EXPLOSION_RADIUS_BONUS, EXPLOSION_COLOR, EXPLOSION_DURATION, EXPLOSION_STUN,
                      LOW_HP_THRESHOLD, KNOCKBACK_DISTANCE, KNOCKBACK_BONUS,
                      ELITE_SPAWN_INTERVAL, ELITE_SIZE_MULT, ELITE_HP_MULT,
                      ELITE_ATK_MULT, ELITE_SPD_MULT, ELITE_COLOR,
                      ARCHER_COLOR, ARCHER_SIZE, ARCHER_HP, ARCHER_SPEED,
                      ARCHER_ATTACK_RANGE, ARCHER_FLEE_RANGE, ARCHER_FIRE_INTERVAL,
                      ARCHER_ARROW_DAMAGE, ARCHER_ARROW_SPEED, ARCHER_ARROW_COLOR,
                      SPECIAL_ENEMY_INTERVAL, SPECIAL_ENEMY_HP_MULT, SPECIAL_ENEMY_SPD_MULT,
                      SPECIAL_ENEMY_ATK_MULT, SPECIAL_ENEMY_CRIT_MULT,
                      SPECIAL_ENEMY_BARRIER_MULT, SPECIAL_ENEMY_BARRIER_DAMAGE,
                      SUMMON_INTERVAL, SUMMON_DURATION, SUMMON_SPEED,
                      SUMMON_SIZE, SUMMON_ATTACK, SUMMON_KNOCKBACK, SUMMON_ZODIAC,
                      SUMMON_SHOOTERS, SUMMON_BULLET_COLORS,
                      SUMMON_ATTACK_SPD_MIN, SUMMON_ATTACK_SPD_MAX,
                      SUMMON_MOVE_SPD_MIN, SUMMON_MOVE_SPD_MAX,
                      SUMMON_DURATION_MIN, SUMMON_DURATION_MAX,
                      ENEMY_GROWTH_RATE, ENEMY_STAT_GROWTH, ENEMY_STAT_GROWTH_INTERVAL)


class Bullet:
    """子弹 - 支持穿透、大小、弹射，飞行固定距离后消失"""

    def __init__(self, x, y, dir_x, dir_y, pierce=0, size=BULLET_SIZE, bounce=0):
        self.x = x
        self.y = y
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.speed = PLAYER_SPEED * BULLET_SPEED_FACTOR
        self.range_left = PLAYER_SPEED * BULLET_RANGE_FACTOR  # 射程（像素）
        self.width = size
        self.height = size
        self.pierce = pierce          # 剩余穿透次数（0=击中后消失）
        self.bounce = bounce          # 剩余弹射次数
        self.color = BULLET_COLOR     # 子弹颜色（默认玩家黄色，召唤物可覆盖）
        self.damage = None            # 子弹伤害（None 时用玩家当前伤害）
        self.is_summon = False        # 是否为召唤物发射的子弹
        self.alive = True

    def update(self, dt):
        """更新子弹位置"""
        move = self.speed * dt
        self.x += self.dir_x * move
        self.y += self.dir_y * move
        self.range_left -= move

        # 超出射程则销毀
        if self.range_left <= 0:
            self.alive = False

    def get_rect(self):
        """返回碰撞矩形"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera_x, camera_y):
        sx = self.x - camera_x
        sy = self.y - camera_y
        pygame.draw.ellipse(screen, self.color,
                            (sx, sy, self.width, self.height))


class DamageText:
    """伤害跳字 - 显示 0.5 秒后消失"""

    def __init__(self, x, y, text, is_crit=False):
        self.x = x
        self.y = y
        self.text = text
        self.is_crit = is_crit
        self.lifetime = DAMAGE_TEXT_LIFETIME
        self.elapsed = 0.0
        self.owner_id = None    # 归属敌人 id（用于同敌人跳字替换）
        # 根据伤害值动态计算字号（伤害越大字号越大）
        self.font_size = self._calc_font_size(text, is_crit)

    @staticmethod
    def _calc_font_size(text, is_crit):
        """根据伤害数值动态计算字号"""
        try:
            value = abs(int(float(text)))
        except (ValueError, TypeError):
            value = 0
        if is_crit:
            base = CRIT_TEXT_SIZE
        else:
            base = DAMAGE_TEXT_SIZE
        # 每 10 倍伤害放大 6px（对数缩放），上限 72
        size = base
        if value >= 10:
            digits = len(str(value))
            size = base + (digits - 1) * 6
        return min(size, 72)

    def update(self, dt):
        """更新生命周期"""
        self.elapsed += dt
        self.y -= 30 * dt  # 向上飘
        return self.elapsed < self.lifetime  # 返回是否仍存活

    def draw(self, screen, camera_x, camera_y):
        # 根据暴击选择字体和颜色（数字用默认字体，避免中文字体放大成方块）
        if self.is_crit:
            font = pygame.font.Font(None, self.font_size)
            color = CRIT_TEXT_COLOR
            outline = (0, 0, 0)  # 暴击加黑色描边，任何背景都清晰
        else:
            font = pygame.font.Font(None, self.font_size)
            color = DAMAGE_TEXT_COLOR
            outline = None
        sx = self.x - camera_x
        sy = self.y - camera_y
        surf = font.render(self.text, True, color)
        if outline is not None:
            # 黑色描边（渲染4个偏移副本）
            o = 1
            for dx, dy in [(-o,0),(o,0),(0,-o),(0,o)]:
                outline_surf = font.render(self.text, True, outline)
                screen.blit(outline_surf, (sx+dx, sy+dy))
        screen.blit(surf, (sx, sy))


class Explosion:
    """爆炸特效 - 橙色扩散圆，0.3 秒后消失"""

    def __init__(self, x, y, radius_px):
        self.x = x
        self.y = y
        self.max_radius = radius_px
        self.lifetime = EXPLOSION_DURATION
        self.elapsed = 0.0
        self.custom_color = None    # 自定义颜色（召唤物爆炸用其颜色）

    def update(self, dt):
        self.elapsed += dt
        return self.elapsed < self.lifetime

    def draw(self, screen, camera_x, camera_y):
        progress = self.elapsed / self.lifetime
        r = int(self.max_radius * progress)
        sx = self.x - camera_x
        sy = self.y - camera_y
        surf = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
        fade = 1 - progress
        # 放射状爆炸：外圈火焰环 + 放射线，不是实心色块
        if self.custom_color is not None:
            base = self.custom_color
            bright = (min(255, base[0]+60), min(255, base[1]+60), min(255, base[2]+60))
            # 外圈环（细）
            pygame.draw.circle(surf, (*bright, int(220 * fade)), (r + 5, r + 5), r, width=4)
            # 内圈环
            pygame.draw.circle(surf, (*base, int(180 * fade)), (r + 5, r + 5), int(r * 0.6), width=3)
            # 放射线（星芒）
            for i in range(8):
                ang = i * math.pi / 4
                ex = (r + 5) + math.cos(ang) * r
                ey = (r + 5) + math.sin(ang) * r
                ix = (r + 5) + math.cos(ang) * r * 0.3
                iy = (r + 5) + math.sin(ang) * r * 0.3
                pygame.draw.line(surf, (*bright, int(200 * fade)), (ix, iy), (ex, ey), 3)
        else:
            # 默认火焰色：外圈环 + 放射线 + 中心亮
            outer = (255, 110, 30)
            inner = (255, 230, 150)
            pygame.draw.circle(surf, (*outer, int(220 * fade)), (r + 5, r + 5), r, width=5)
            pygame.draw.circle(surf, (*outer, int(160 * fade)), (r + 5, r + 5), int(r * 0.6), width=3)
            pygame.draw.circle(surf, (*inner, int(200 * fade)), (r + 5, r + 5), int(r * 0.25))
            for i in range(10):
                ang = i * math.pi / 5
                ex = (r + 5) + math.cos(ang) * r
                ey = (r + 5) + math.sin(ang) * r
                ix = (r + 5) + math.cos(ang) * r * 0.25
                iy = (r + 5) + math.sin(ang) * r * 0.25
                pygame.draw.line(surf, (*outer, int(200 * fade)), (ix, iy), (ex, ey), 4)
        screen.blit(surf, (sx - r - 5, sy - r - 5))


class BigText:
    """大文字特效 - 1 秒后消失"""

    def __init__(self, x, y, text, color=(255, 50, 50)):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = 1.0
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt
        self.y -= 20 * dt  # 向上飘
        return self.elapsed < self.lifetime

    def draw(self, screen, camera_x, camera_y):
        size = 48
        font = pygame.font.Font(None, size)
        font.set_bold(True)
        surf = font.render(self.text, True, self.color)
        sx = self.x - camera_x - surf.get_width() / 2
        sy = self.y - camera_y - surf.get_height() / 2
        screen.blit(surf, (sx, sy))


class Enemy:
    """敌人 - 分多个 tier，属性（攻击/生命/速度/大小）按倍率增强，颜色由浅至深"""

    def __init__(self, x, y, tier=None, elite=False):
        self.x = x
        self.y = y
        self.elite = elite
        # 随机 tier（0~5），权重分布：基础敌人更多
        if tier is None:
            weights = [30, 25, 20, 15, 7, 3]  # tier 0 最多，tier 5 最少
            tier = random.choices(range(6), weights=weights)[0]
        self.tier = tier

        # 从配置取该 tier 的属性倍率 (攻击, 生命, 速度, 尺寸)
        atk_mult, hp_mult, spd_mult, size_mult = ENEMY_TIER_STATS[tier]

        # 基础属性
        self.base_atk = 1                  # 基础攻击力
        self.attack = int(self.base_atk * atk_mult)   # 攻击力（碰撞扣血）
        self.hp = int(random.randint(ENEMY_HP_MIN, ENEMY_HP_MAX) * hp_mult)
        self.max_hp = self.hp
        self.speed = PLAYER_SPEED * ENEMY_SPEED_FACTOR * spd_mult
        self.width = int(ENEMY_SIZE * size_mult)
        self.height = int(ENEMY_SIZE * size_mult)
        # 颜色（由浅至深）
        self.color = ENEMY_TIER_COLORS[tier]

        # 嘲讽气泡
        self.taunt_text = ""            # 当前气泡文本
        self.taunt_timer = 0.0          # 气泡显示计时
        self.taunt_cooldown = 0.0   # 首次进入画面立即嘲讽，之后每5秒一次
        self._taunt_font = None         # 气泡字体（懒加载）
        self.taunt_used = set()         # 该敌人用过的嘲讽语（避免重复）

        # 敌人素材（懒加载）
        self._enemy_img = None

        # 精英怪强化
        if elite:
            self.width = int(self.width * ELITE_SIZE_MULT)
            self.height = int(self.height * ELITE_SIZE_MULT)
            self.hp = int(self.hp * ELITE_HP_MULT)
            self.max_hp = self.hp
            self.attack = int(self.attack * ELITE_ATK_MULT)
            # 精英移速 = 角色初始移速 × 1.1（固定值，不随角色移速变化）
            self.speed = PLAYER_SPEED * ELITE_SPD_MULT
            self.color = ELITE_COLOR
        self.alive = True
        self.flash_timer = 0.0     # 受击闪烁计时器
        self.stun_timer = 0.0      # 爆炸停顿计时器
        self.knockback_vx = 0.0    # 击退速度（平滑移动）
        self.knockback_vy = 0.0
        # 敌人默认暴击属性
        self.crit_rate = 0.05      # 默认暴击率 5%
        self.crit_damage = 2.0     # 默认暴击伤害 200%
        self.crit_color = (255, 80, 80)  # 敌人暴击时伤害跳字红色

    def get_attack_damage(self):
        """计算攻击玩家的伤害（含暴击判定）"""
        if random.random() < self.crit_rate:
            return int(self.attack * self.crit_damage), True
        return self.attack, False

    def apply_growth(self, game_time):
        """按游戏时间强化敌人属性：每 2 分钟攻击/生命 +10%"""
        stages = int(game_time // ENEMY_STAT_GROWTH_INTERVAL)
        if stages <= 0:
            return
        mult = (1 + ENEMY_STAT_GROWTH) ** stages
        # 保证至少 +1（避免基础值小被 int 吃掉）
        self.attack = max(self.attack + 1, int(self.attack * mult))
        self.hp = max(self.hp + 1, int(self.hp * mult))
        self.max_hp = self.hp

    def take_damage(self, damage):
        """受到伤害"""
        self.hp -= damage
        self.flash_timer = 0.25    # 受击后闪烁 0.25 秒（更明显）
        if self.hp <= 0:
            self.alive = False

    def stun(self, duration):
        """爆炸停顿"""
        self.stun_timer = max(self.stun_timer, duration)

    def apply_knockback(self, dir_x, dir_y, distance):
        """施加击退（平滑移动），精英怪免疫"""
        if self.elite:
            return
        # 击退速度 = 距离 * 10（让 0.1 秒内完成，用衰减）
        self.knockback_vx += dir_x * distance * 15
        self.knockback_vy += dir_y * distance * 15

    def update(self, dt, player_x, player_y):
        """朝玩家方向移动（含平滑击退）"""
        if self.flash_timer > 0:
            self.flash_timer -= dt
        # 嘲讽气泡计时
        if self.taunt_timer > 0:
            self.taunt_timer -= dt
        if self.taunt_cooldown > 0:
            self.taunt_cooldown -= dt
        # 击退移动（衰减）
        if self.knockback_vx != 0 or self.knockback_vy != 0:
            self.x += self.knockback_vx * dt
            self.y += self.knockback_vy * dt
            # 衰减
            decay = 1 - min(1, dt * 12)
            self.knockback_vx *= decay
            self.knockback_vy *= decay
            if abs(self.knockback_vx) < 1 and abs(self.knockback_vy) < 1:
                self.knockback_vx = 0
                self.knockback_vy = 0
        # 停顿期间不移动
        if self.stun_timer > 0:
            self.stun_timer -= dt
            return
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def distance_to(self, target_x, target_y):
        """距离目标的距离"""
        dx = self.x - target_x
        dy = self.y - target_y
        return math.sqrt(dx * dx + dy * dy)

    def draw(self, screen, camera_x, camera_y):
        sx = self.x - camera_x
        sy = self.y - camera_y
        # 优先用敌人素材（懒加载，缩放到敌人尺寸）
        if self._enemy_img is None:
            try:
                import assets_manager
                base_img = assets_manager.load_image(assets_manager.ENEMY_SPRITE)
                if base_img is not None:
                    frame = base_img.subsurface((0, 0, 32, 32)).copy()
                    self._enemy_img = pygame.transform.scale(frame, (self.width, self.height))
            except Exception:
                self._enemy_img = None
        if self._enemy_img is not None:
            screen.blit(self._enemy_img, (sx, sy))
        else:
            # 回退：椭圆
            draw_color = self.color
            pygame.draw.ellipse(screen, draw_color,
                                (sx, sy, self.width, self.height))
        # 受击白色爆炸效果（在敌人中心，小范围扩散）
        if self.flash_timer > 0:
            cx = sx + self.width / 2
            cy = sy + self.height / 2
            # 白色小圆扩散（随 flash_timer 衰减）
            progress = 1 - (self.flash_timer / 0.25)
            r = int(self.width * (0.15 + 0.35 * progress))
            glow = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            alpha = int(180 * (1 - progress))
            pygame.draw.circle(glow, (255, 255, 255, alpha), (r + 2, r + 2), r)
            screen.blit(glow, (cx - r - 2, cy - r - 2))
        # 眼睛
        eye_size = max(3, int(self.width * 0.12))
        pygame.draw.circle(screen, (255, 255, 255),
                           (sx + self.width * 0.3, sy + self.height * 0.3), eye_size)
        pygame.draw.circle(screen, (255, 255, 255),
                           (sx + self.width * 0.7, sy + self.height * 0.3), eye_size)
        # 血条
        if self.hp < self.max_hp:
            bar_w = self.width
            bar_h = 5
            hp_ratio = max(0, self.hp) / self.max_hp
            pygame.draw.rect(screen, (80, 80, 80),
                             (sx, sy - 8, bar_w, bar_h))
            pygame.draw.rect(screen, (220, 220, 0),
                             (sx, sy - 8, bar_w * hp_ratio, bar_h))
        # 嘲讽气泡
        if self.taunt_timer > 0 and self.taunt_text:
            if self._taunt_font is None:
                self._taunt_font = get_font(16)
            bubble_font = self._taunt_font
            text_surf = bubble_font.render(self.taunt_text, True, (30, 30, 30))
            bw = text_surf.get_width() + 12
            bh = text_surf.get_height() + 6
            bx = sx + self.width / 2 - bw / 2
            by = sy - 12 - bh
            pygame.draw.rect(screen, (255, 255, 255), (bx, by, bw, bh), border_radius=4)
            pygame.draw.rect(screen, (60, 60, 60), (bx, by, bw, bh), width=1, border_radius=4)
            # 小三角尾巴
            pygame.draw.polygon(screen, (255, 255, 255),
                                [(bx + bw / 2 - 3, by + bh), (bx + bw / 2 + 3, by + bh),
                                 (bx + bw / 2, by + bh + 4)])
            screen.blit(text_surf, (bx + 6, by + 3))


class Archer(Enemy):
    """弓箭手 - 远程敌人，保持距离射击，玩家靠近时逃跑"""

    def __init__(self, x, y):
        super().__init__(x, y, tier=0)
        self.width = ARCHER_SIZE
        self.height = ARCHER_SIZE
        self.hp = ARCHER_HP
        self.max_hp = ARCHER_HP
        self.speed = ARCHER_SPEED
        self.attack = 1
        self.color = ARCHER_COLOR
        self.fire_cooldown = 0.0

    def update(self, dt, player_x, player_y):
        """保持距离射击，玩家靠近就逃跑"""
        if self.flash_timer > 0:
            self.flash_timer -= dt
        # 击退（继承）
        if self.knockback_vx != 0 or self.knockback_vy != 0:
            self.x += self.knockback_vx * dt
            self.y += self.knockback_vy * dt
            decay = 1 - min(1, dt * 12)
            self.knockback_vx *= decay
            self.knockback_vy *= decay
        if self.stun_timer > 0:
            self.stun_timer -= dt
            return

        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > 0:
            if dist < ARCHER_FLEE_RANGE:
                # 玩家太近 → 逃跑后退
                self.x -= (dx / dist) * self.speed * dt
                self.y -= (dy / dist) * self.speed * dt
            elif dist > ARCHER_ATTACK_RANGE:
                # 玩家太远 → 靠近（但不超过攻击距离）
                self.x += (dx / dist) * self.speed * dt
                self.y += (dy / dist) * self.speed * dt
            # 在攻击范围内不移动，只射击

    def get_fire_direction(self, player_x, player_y):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist == 0:
            return 1, 0
        return dx / dist, dy / dist

    def draw(self, screen, camera_x, camera_y):
        """弓箭手形象：绿色三角形（箭头指向玩家）"""
        sx = self.x - camera_x
        sy = self.y - camera_y
        cx = sx + self.width / 2
        cy = sy + self.height / 2
        # 画一个绿色圆底 + 弓标记
        pygame.draw.ellipse(screen, self.color, (sx, sy, self.width, self.height))
        # 弓形（弧形）
        pygame.draw.arc(screen, (80, 120, 60), (sx - 5, sy - 5, self.width + 10, self.height + 10), 0, math.pi, 3)
        # 眼睛
        eye_size = 3
        pygame.draw.circle(screen, (255, 255, 255), (sx + self.width * 0.35, sy + self.height * 0.3), eye_size)
        pygame.draw.circle(screen, (255, 255, 255), (sx + self.width * 0.65, sy + self.height * 0.3), eye_size)
        # 血条
        if self.hp < self.max_hp:
            bar_w = self.width
            bar_h = 4
            hp_ratio = max(0, self.hp) / self.max_hp
            pygame.draw.rect(screen, (80, 80, 80), (sx, sy - 7, bar_w, bar_h))
            pygame.draw.rect(screen, (220, 220, 0), (sx, sy - 7, bar_w * hp_ratio, bar_h))


class Arrow:
    """弓箭手箭矢 - 三角形，按攻击方向旋转，穿透敌人直到击中玩家"""

    def __init__(self, x, y, dir_x, dir_y):
        self.x = x
        self.y = y
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.speed = ARCHER_ARROW_SPEED
        self.damage = ARCHER_ARROW_DAMAGE
        self.alive = True

    def update(self, dt):
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt

    def get_rect(self):
        return pygame.Rect(self.x - 5, self.y - 5, 10, 10)

    def draw(self, screen, camera_x, camera_y):
        sx = self.x - camera_x
        sy = self.y - camera_y
        # 三角形顶点朝攻击方向
        angle = math.atan2(self.dir_y, self.dir_x)
        size = 8
        tip = (sx + math.cos(angle) * size, sy + math.sin(angle) * size)
        back1 = (sx + math.cos(angle + 2.5) * size * 0.6, sy + math.sin(angle + 2.5) * size * 0.6)
        back2 = (sx + math.cos(angle - 2.5) * size * 0.6, sy + math.sin(angle - 2.5) * size * 0.6)
        pygame.draw.polygon(screen, ARCHER_ARROW_COLOR, [tip, back1, back2])


# ============ 5 种特殊敌人（不同形状） ============

class TankEnemy(Enemy):
    """血厚敌人 - 生命 5 倍，方形"""
    def __init__(self, x, y):
        super().__init__(x, y, tier=random.randint(0, 5))
        self.hp = self.hp * SPECIAL_ENEMY_HP_MULT
        self.max_hp = self.hp
        self.speed = PLAYER_SPEED * SPECIAL_ENEMY_SPD_MULT
        self.color = (120, 160, 220)  # 蓝灰
    def draw(self, screen, camera_x, camera_y):
        sx = self.x - camera_x; sy = self.y - camera_y
        pygame.draw.rect(screen, self.color, (sx, sy, self.width, self.height))
        if self.flash_timer > 0:
            pygame.draw.rect(screen, (255, 255, 255), (sx, sy, self.width, self.height), 3)
        # 血条
        if self.hp < self.max_hp:
            r = max(0, self.hp) / self.max_hp
            pygame.draw.rect(screen, (80,80,80), (sx, sy-6, self.width, 4))
            pygame.draw.rect(screen, (0, 200, 0), (sx, sy-6, self.width*r, 4))


class SpeedEnemy(Enemy):
    """快速敌人 - 移速 0.9 倍（角色初始），菱形"""
    def __init__(self, x, y):
        super().__init__(x, y, tier=random.randint(0, 5))
        self.speed = PLAYER_SPEED * SPECIAL_ENEMY_SPD_MULT
        self.color = (255, 220, 80)  # 亮黄
    def draw(self, screen, camera_x, camera_y):
        sx = self.x - camera_x; sy = self.y - camera_y
        cx = sx + self.width/2; cy = sy + self.height/2
        pts = [(cx, sy), (sx+self.width, cy), (cx, sy+self.height), (sx, cy)]
        pygame.draw.polygon(screen, self.color, pts)
        if self.flash_timer > 0:
            pygame.draw.polygon(screen, (255,255,255), pts, 3)


class StrongEnemy(Enemy):
    """高攻敌人 - 攻击 5 倍，星形"""
    def __init__(self, x, y):
        super().__init__(x, y, tier=random.randint(0, 5))
        self.attack = self.attack * SPECIAL_ENEMY_ATK_MULT
        self.speed = PLAYER_SPEED * SPECIAL_ENEMY_SPD_MULT
        self.color = (255, 90, 90)  # 亮红
    def draw(self, screen, camera_x, camera_y):
        sx = self.x - camera_x; sy = self.y - camera_y
        cx = sx + self.width/2; cy = sy + self.height/2
        r = self.width/2
        pts = []
        for i in range(5):
            ang1 = -math.pi/2 + i*2*math.pi/5
            ang2 = ang1 + math.pi/5
            pts.append((cx + r*math.cos(ang1), cy + r*math.sin(ang1)))
            pts.append((cx + r*0.4*math.cos(ang2), cy + r*0.4*math.sin(ang2)))
        pygame.draw.polygon(screen, self.color, pts)
        if self.flash_timer > 0:
            pygame.draw.polygon(screen, (255,255,255), pts, 2)


class CritEnemy(Enemy):
    """高暴击敌人 - 暴击率 5 倍（25%），六边形"""
    def __init__(self, x, y):
        super().__init__(x, y, tier=random.randint(0, 5))
        self.crit_rate = self.crit_rate * SPECIAL_ENEMY_CRIT_MULT  # 25%
        self.speed = PLAYER_SPEED * SPECIAL_ENEMY_SPD_MULT
        self.color = (200, 120, 255)  # 紫色
    def draw(self, screen, camera_x, camera_y):
        sx = self.x - camera_x; sy = self.y - camera_y
        cx = sx + self.width/2; cy = sy + self.height/2
        r = self.width/2
        pts = []
        for i in range(6):
            ang = -math.pi/2 + i*2*math.pi/6
            pts.append((cx + r*math.cos(ang), cy + r*math.sin(ang)))
        pygame.draw.polygon(screen, self.color, pts)
        if self.flash_timer > 0:
            pygame.draw.polygon(screen, (255,255,255), pts, 2)


class BarrierEnemy(Enemy):
    """屏障敌人 - 自带屏障（2倍范围，每秒1伤害），移速0.9倍，圆形+光环"""
    def __init__(self, x, y):
        super().__init__(x, y, tier=random.randint(0, 5))
        self.speed = PLAYER_SPEED * SPECIAL_ENEMY_SPD_MULT
        self.barrier_radius = BARRIER_RADIUS * SPECIAL_ENEMY_BARRIER_MULT * 80  # 像素
        self.barrier_damage = SPECIAL_ENEMY_BARRIER_DAMAGE
        self._barrier_timer = 0.0
        self.color = (120, 220, 255)  # 亮青
    def update(self, dt, player_x, player_y):
        # 屏障对玩家造成伤害
        px = player_x + PLAYER_WIDTH/2
        py = player_y + PLAYER_HEIGHT/2
        dist = math.sqrt((self.x-self.x)**2 + (self.y-self.y)**2)
        self._barrier_timer += dt
        # 调用父类移动逻辑
        super().update(dt, player_x, player_y)
    def draw(self, screen, camera_x, camera_y):
        sx = self.x - camera_x; sy = self.y - camera_y
        cx = sx + self.width/2; cy = sy + self.height/2
        # 外层屏障光环
        pygame.draw.circle(screen, (120, 220, 255), (int(cx), int(cy)), self.barrier_radius, 3)
        pygame.draw.circle(screen, (120, 220, 255), (int(cx), int(cy)), self.barrier_radius - 3, 1)
        # 本体（圆形）
        pygame.draw.circle(screen, self.color, (int(cx), int(cy)), int(self.width/2))
        if self.flash_timer > 0:
            pygame.draw.circle(screen, (255,255,255), (int(cx), int(cy)), int(self.width/2), 3)
        # 血条
        if self.hp < self.max_hp:
            r = max(0, self.hp) / self.max_hp
            pygame.draw.rect(screen, (80,80,80), (sx, sy-6, self.width, 4))
            pygame.draw.rect(screen, (0, 200, 0), (sx, sy-6, self.width*r, 4))


SPECIAL_ENEMY_TYPES = [TankEnemy, SpeedEnemy, StrongEnemy, CritEnemy, BarrierEnemy]


class Ally:
    """友军 - 被洗脑的敌人，攻击敌方，与玩家免伤，持续 30 秒，移速+50%"""

    def __init__(self, x, y, attack_power=1):
        self.x = x
        self.y = y
        self.width = int(ENEMY_SIZE * BRAINWASH_SIZE)
        self.height = int(ENEMY_SIZE * BRAINWASH_SIZE)
        self.speed = PLAYER_SPEED * ENEMY_SPEED_FACTOR * 1.5  # 移速 +50%
        self.attack = attack_power      # 友军攻击力
        self.lifetime = BRAINWASH_DURATION  # 剩余存活时间
        self.alive = True

    def update(self, dt, player_x, player_y, enemies):
        """优先朝最近敌人攻击，无敌人时跟随玩家"""
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
            return

        # 1) 优先找最近的敌人
        nearest_enemy = None
        min_d = float('inf')
        for en in enemies:
            if not en.alive:
                continue
            d = self.distance_to(en.x, en.y)
            if d < min_d:
                min_d = d
                nearest_enemy = en

        if nearest_enemy is not None:
            # 朝敌人移动（撞上去造成伤害由 CombatSystem 处理）
            dx = nearest_enemy.x - self.x
            dy = nearest_enemy.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.x += (dx / dist) * self.speed * dt
                self.y += (dy / dist) * self.speed * dt
        else:
            # 2) 没敌人时跟随玩家
            dx = player_x - self.x
            dy = player_y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 120:
                if dist > 0:
                    self.x += (dx / dist) * self.speed * dt
                    self.y += (dy / dist) * self.speed * dt
            elif dist < 60:
                if dist > 0:
                    self.x -= (dx / dist) * self.speed * dt * 0.5
                    self.y -= (dy / dist) * self.speed * dt * 0.5

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def distance_to(self, target_x, target_y):
        dx = self.x - target_x
        dy = self.y - target_y
        return math.sqrt(dx * dx + dy * dy)

    def draw(self, screen, camera_x, camera_y):
        """绘制友军（浅蓝色，带箭头标记表示友军）"""
        sx = self.x - camera_x
        sy = self.y - camera_y
        pygame.draw.ellipse(screen, BRAINWASH_COLOR,
                            (sx, sy, self.width, self.height))
        # 眼睛
        eye_size = max(3, int(self.width * 0.12))
        pygame.draw.circle(screen, (30, 30, 30),
                           (sx + self.width * 0.3, sy + self.height * 0.3), eye_size)
        pygame.draw.circle(screen, (30, 30, 30),
                           (sx + self.width * 0.7, sy + self.height * 0.3), eye_size)
        # 剩余时间条（青色）
        bar_w = self.width
        bar_h = 5
        ratio = max(0, self.lifetime) / BRAINWASH_DURATION
        pygame.draw.rect(screen, (60, 60, 60),
                         (sx, sy - 8, bar_w, bar_h))
        pygame.draw.rect(screen, (80, 220, 255),
                         (sx, sy - 8, bar_w * ratio, bar_h))


class Summon:
    """召唤物（十二生肖）- 碰撞伤害，持续 20 秒，最多同时 2 只"""

    def __init__(self, x, y, zodiac_name, attack=1):
        self.x = x
        self.y = y
        self.zodiac = zodiac_name        # 生肖名（鼠/牛/虎...）
        self.width = SUMMON_SIZE
        self.height = SUMMON_SIZE
        self.speed = SUMMON_SPEED
        self.attack = attack
        self.lifetime = SUMMON_DURATION
        self.alive = True
        # 是否为射击型（发射子弹、跟随角色）
        self.is_shooter = zodiac_name in SUMMON_SHOOTERS
        self.bullet_color = SUMMON_BULLET_COLORS.get(zodiac_name, (200, 200, 200))
        self.fire_cooldown = 0.0        # 射击型开火冷却
        # 生肖对应颜色
        zodiac_colors = {
            "鼠": (150, 150, 150), "牛": (139, 119, 80), "虎": (220, 160, 40),
            "兔": (240, 220, 240), "龙": (80, 200, 120), "蛇": (100, 180, 80),
            "马": (180, 130, 80), "羊": (230, 230, 230), "猴": (170, 120, 60),
            "鸡": (220, 180, 60), "狗": (160, 120, 70), "猪": (240, 180, 180),
        }
        self.color = zodiac_colors.get(zodiac_name, (200, 200, 200))
        self.attack_cooldown = 0.0    # 攻击冷却（攻速加成影响）
        self.attack_interval = 0.5    # 基础攻击间隔 0.5 秒

    def update(self, dt, enemies, player_x, player_y):
        """射击型：跟随角色身边；近战型：画面内有敌人就攻击，无则回角色身边"""
        # SUMMON_DURATION=0 表示永久存在，否则倒计时
        if SUMMON_DURATION > 0:
            self.lifetime -= dt
            if self.lifetime <= 0:
                self.alive = False
                return
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt

        if self.is_shooter:
            # 射击型：始终在角色身边（保持 80~120px 距离）
            dx = player_x - self.x
            dy = player_y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 120:
                if dist > 0:
                    self.x += (dx / dist) * self.speed * dt
                    self.y += (dy / dist) * self.speed * dt
            elif dist < 60:
                if dist > 0:
                    self.x -= (dx / dist) * self.speed * dt * 0.5
                    self.y -= (dy / dist) * self.speed * dt * 0.5
            return

        # 近战型：只找画面内敌人（以玩家为中心 700x420 范围），无则回玩家身边待命
        nearest = None
        min_d = float('inf')
        for en in enemies:
            if not en.alive:
                continue
            # 只在画面内（玩家视野范围）找敌人
            if abs(en.x - player_x) > 700 or abs(en.y - player_y) > 420:
                continue
            d = self.distance_to(en.x, en.y)
            if d < min_d:
                min_d = d
                nearest = en
        if nearest is not None:
            # 朝画面内敌人移动
            dx = nearest.x - self.x
            dy = nearest.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.x += (dx / dist) * self.speed * dt
                self.y += (dy / dist) * self.speed * dt
        else:
            # 画面内无敌人，回到玩家身边待命（保持 80~120px 距离）
            dx = player_x - self.x
            dy = player_y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 150:
                if dist > 0:
                    self.x += (dx / dist) * self.speed * dt
                    self.y += (dy / dist) * self.speed * dt
            elif dist < 60:
                if dist > 0:
                    self.x -= (dx / dist) * self.speed * dt * 0.5
                    self.y -= (dy / dist) * self.speed * dt * 0.5

    def distance_to(self, x, y):
        return math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera_x, camera_y):
        sx = self.x - camera_x
        sy = self.y - camera_y
        # 像素风渲染：12x12 网格，每格放大
        pixel_size = self.width / 12.0
        pattern = ZODIAC_PIXELS.get(self.zodiac, ZODIAC_PIXELS["鼠"])
        palette = ZODIAC_COLORS.get(self.zodiac, ZODIAC_COLORS["鼠"])
        color_map = {
            "B": palette.get("B", self.color),
            "D": palette.get("D", (60, 60, 60)),
            "W": (255, 255, 255),
            "R": palette.get("R", (220, 50, 50)),
            "Y": palette.get("Y", (250, 220, 100)),
        }
        for row_i, row in enumerate(pattern):
            for col_i, ch in enumerate(row):
                if ch == ".":
                    continue
                color = color_map.get(ch)
                if color is None:
                    continue
                px = sx + col_i * pixel_size
                py = sy + row_i * pixel_size
                pygame.draw.rect(screen, color,
                                 (px, py, pixel_size + 0.5, pixel_size + 0.5))
        # 剩余时间条
        bar_w = self.width
        ratio = max(0, self.lifetime) / SUMMON_DURATION
        pygame.draw.rect(screen, (60, 60, 60), (sx, sy - 8, bar_w, 4))
        pygame.draw.rect(screen, (150, 200, 255), (sx, sy - 8, bar_w * ratio, 4))


class Player:
    """玩家 - 带血量、等级、击杀计数、攻击速度/子弹数量/穿透等升级属性"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = PLAYER_HP
        self.max_hp = PLAYER_HP
        self.damage = BULLET_DAMAGE   # 子弹伤害（升级可增加）
        self.level = 1                # 等级
        self.kill_count = 0           # 击杀计数
        self.speed_bonus = 0.0         # 移速加成（累计百分比）
        # 新升级属性
        self.fire_rate_bonus = 0.0     # 攻击速度加成（累计百分比，0=默认）
        self.bullet_count = 1          # 单次射击子弹数（默认 1）
        self.pierce = 0                # 子弹穿透次数（0=不可穿透）
        self.bullet_size_bonus = 0.0   # 子弹大小加成（累计百分比）
        self.bounce = 0                # 子弹弹射次数（0=不弹射）
        self.lifesteal = 0.0           # 吸血概率（0=无，0.1=10%，1.0=100%）
        self._lifesteal_counter = 0    # 假概率计数
        self.brainwash_chance = BRAINWASH_CHANCE  # 初始洗脑概率 0%
        # 能量屏障属性
        self.barrier_enabled = False               # 是否有屏障（首次升级后开启）
        self.barrier_radius = BARRIER_RADIUS       # 屏障范围（格）
        self.barrier_freq = 1.0                    # 屏障攻击频率倍率
        self.barrier_damage = BARRIER_DAMAGE       # 屏障伤害
        self.regen = False                         # 是否开启生命回复
        self._regen_timer = 0.0                    # 回血计时器
        self.knockback_enabled = False            # 是否开启击退
        self.knockback_dist = KNOCKBACK_DISTANCE  # 击退距离（格）
        self.explosion_enabled = False             # 是否开启爆炸
        self.explosion_radius = EXPLOSION_RADIUS    # 爆炸范围（格）
        # 暴击属性
        self.crit_rate = CRIT_RATE_DEFAULT      # 暴击率（默认5%）
        self.crit_damage = CRIT_DAMAGE_DEFAULT  # 暴击伤害倍率（默认200% = 2倍）
        # 召唤属性
        self.summon_enabled = False             # 是否开启召唤
        self.summon_atk_bonus = 0.0             # 召唤物攻速加成
        self.summon_speed_bonus = 0.0           # 召唤物移速加成
        self.summon_duration_bonus = 0.0        # 召唤物持续时间加成

    def roll_crit(self):
        """判定本次攻击是否暴击"""
        return random.random() < self.crit_rate

    def get_damage_with_crit(self):
        """返回 (伤害值, 是否暴击)"""
        if self.roll_crit():
            return int(self.damage * self.crit_damage), True
        return self.damage, False

    def upgrade_crit_rate(self, amount):
        """升级暴击率：+amount（小数）"""
        self.crit_rate += amount

    def upgrade_crit_damage(self, amount):
        """升级暴击伤害：+amount（小数，如0.05=+5%）"""
        self.crit_damage += amount

    def take_damage(self, damage):
        """受到伤害"""
        self.hp -= damage
        if self.hp <= 0:
            return True  # 死亡
        return False

    def heal(self, amount):
        """恢复血量"""
        self.hp = min(self.max_hp, self.hp + amount)

    def on_kill(self):
        """击杀敌人时调用，返回是否触发升级"""
        self.kill_count += 1
        if self.kill_count % KILLS_PER_LEVEL == 0:
            self.level += 1  # 升级
            return True
        return False

    def upgrade_attack(self):
        """升级攻击：子弹伤害 +2"""
        self.damage += 2

    def upgrade_hp(self):
        """升级生命：上限 +2，当前血量也 +2"""
        self.max_hp += PLAYER_HP_BONUS
        self.hp += PLAYER_HP_BONUS

    def upgrade_speed(self):
        """升级移速：移速 +10%（累计，向下取整到实际速度）"""
        self.speed_bonus += SPEED_BONUS_PCT

    def upgrade_attack_speed(self, amount):
        """升级攻击速度：传入具体值"""
        self.fire_rate_bonus += amount

    def upgrade_bullet_count(self, amount):
        """升级子弹数量：传入具体值"""
        self.bullet_count += amount

    def upgrade_pierce(self):
        """升级子弹穿透：+1"""
        self.pierce += PIERCE_BONUS

    def upgrade_bullet_size(self, amount):
        """升级子弹大小：传入具体加成百分比（如 0.30 = +30%）"""
        self.bullet_size_bonus += amount

    def upgrade_bounce(self):
        """升级子弹弹射：+1 次弹射"""
        self.bounce += BOUNCE_COUNT

    def upgrade_brainwash(self):
        """升级洗脑：首次获得 1%，每次 +1%"""
        if self.brainwash_chance == 0.0:
            self.brainwash_chance = 0.01
        else:
            self.brainwash_chance += 0.01

    def upgrade_regen(self):
        """升级生命回复：每秒 +1 血"""
        self.regen = True

    def upgrade_knockback(self):
        """升级击退：首次获得 1 格，后续 +1 格"""
        if not self.knockback_enabled:
            self.knockback_enabled = True
        else:
            self.knockback_dist += KNOCKBACK_BONUS

    def upgrade_explosion(self):
        """升级爆炸：首次开启，后续增加范围"""
        if not self.explosion_enabled:
            self.explosion_enabled = True
        else:
            self.explosion_radius += EXPLOSION_RADIUS_BONUS

    def upgrade_summon(self):
        """升级召唤：开启召唤（每10秒一只十二生肖）"""
        self.summon_enabled = True

    def upgrade_summon_atk_speed(self, amount):
        """升级召唤物攻击速度"""
        self.summon_atk_bonus += amount

    def upgrade_summon_move_speed(self, amount):
        """升级召唤物移速"""
        self.summon_speed_bonus += amount

    def upgrade_summon_duration(self, amount):
        """升级召唤物持续时间"""
        self.summon_duration_bonus += amount

    def upgrade_barrier_radius(self):
        """升级屏障范围：+1 格（首次开启屏障）"""
        self.barrier_enabled = True
        self.barrier_radius += BARRIER_RADIUS_BONUS

    def upgrade_barrier_freq(self):
        """升级屏障频率：翻倍（首次开启屏障）"""
        self.barrier_enabled = True
        self.barrier_freq += BARRIER_FREQ_BONUS

    def upgrade_lifesteal(self):
        """升级吸血：首次获得 10% 概率，后续叠加"""
        if self.lifesteal == 0.0:
            self.lifesteal = 0.10  # 首次 10%（每 10 发必触发 1 次）
        else:
            self.lifesteal = min(1.0, self.lifesteal + 0.10)  # 每次 +10%，最高 100%

    def try_lifesteal(self):
        """命中敌人时尝试触发吸血（假概率：概率越高，保底间隔越短）"""
        if self.lifesteal <= 0:
            return False
        self._lifesteal_counter += 1
        # 保底间隔 = 1/概率，即 10%→10发, 20%→5发, 100%→1发
        pity = max(1, int(1.0 / self.lifesteal))
        if self._lifesteal_counter >= pity:
            self._lifesteal_counter = 0
            self.heal(LIFESTEAL_HEAL)
            return True
        return False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, PLAYER_WIDTH, PLAYER_HEIGHT)


class CombatSystem:
    """战斗系统 - 管理敌人、子弹、玩家、自动攻击、无限生成"""

    def __init__(self, center_x, center_y):
        self.player = Player(center_x, center_y)
        self.enemies = []
        self.bullets = []
        self.damage_texts = []        # 伤害跳字
        self.explosions = []          # 爆炸特效
        self.big_texts = []           # 大文字特效（如飞身踢）
        self.allies = []              # 被洗脑的友军
        self.fire_cooldown = 0.0      # 射击间隔计时器
        self.spawn_cooldown = 0.0     # 敌人生成计时器
        self.game_time = 0.0          # 游戏总时间（秒），用于解锁敌人 tier
        self.on_kill_callback = None  # 击杀回调（由 GameScene 设置）
        self._barrier_pulse = 0.0      # 屏障脉冲动画计时
        self.auto_attack = True            # 自动攻击开关
        self._elite_timer = 0.0       # 精英怪生成计时器
        self.archers = []             # 弓箭手列表
        self.arrows = []              # 箭矢列表
        self._archer_spawn_timer = 0.0  # 弓箭手生成计时器
        self.enemy_color_overrides = {}  # 敌人颜色覆盖（背景对比）
        self.player_contrast_color = None  # 角色对比色覆盖
        self._special_enemy_timer = 0.0   # 特殊敌人生成计时器
        self._special_enemy_queue = list(SPECIAL_ENEMY_TYPES)  # 5种轮换队列
        random.shuffle(self._special_enemy_queue)
        self.summons = []                 # 召唤物列表
        self._summon_timer = 0.0          # 召唤计时器
        self._summon_first_done = False   # 首次召唤标记（选中召唤后立即召唤1只）
        self._summoned_history = set()    # 已召唤过的生肖（永久记录，不重复）
        self._taunt_timer = 0.0            # 嘲讽触发计时器
        self._taunt_pending = {}           # 待取嘲讽结果 {key: enemy_id}
        self._taunt_pool = []              # 预生成嘲讽语池
        self._local_taunt_pool = []        # 本地嘲讽语池（兜底，永不枯竭）

        # 预生成嘲讽池：用全局共享池（Game 启动时后台预填），不阻塞等待
        global _global_taunt_pool
        if _global_taunt_pool:
            self._taunt_pool = list(_global_taunt_pool)
            _global_taunt_pool.clear()

        # 初始生成一些敌人（只生成 tier 0）
        self._spawn_initial_enemies(center_x, center_y)

    def apply_enemy_colors(self, overrides):
        """应用敌人颜色覆盖（背景对比调整），并更新现有敌人颜色"""
        self.enemy_color_overrides = overrides
        for enemy in self.enemies:
            if enemy.elite:
                enemy.color = overrides.get("elite", enemy.color)
            elif isinstance(enemy, Archer):
                enemy.color = overrides.get("archer", enemy.color)
            else:
                enemy.color = overrides.get(f"tier{enemy.tier}", enemy.color)

    def _spawn_summon(self, px, py):
        """生成一只召唤物：不重复（永久记录历史），每 10 秒一只，各持续 10 秒"""
        # 从未召唤过的生肖中选
        remaining = [z for z in SUMMON_ZODIAC if z not in self._summoned_history]
        if not remaining:
            # 已集齐 12 种，重置历史重新循环
            self._summoned_history = set()
            remaining = list(SUMMON_ZODIAC)
        zodiac = random.choice(remaining)
        self._summoned_history.add(zodiac)
        s = Summon(
            px + random.uniform(-60, 60),
            py + random.uniform(-60, 60),
            zodiac,
            attack=SUMMON_ATTACK
        )
        # 应用召唤强化加成
        s.speed = s.speed * (1 + self.player.summon_speed_bonus)
        s.lifetime = SUMMON_DURATION * (1 + self.player.summon_duration_bonus)
        s.attack_interval = s.attack_interval * (1 / (1 + self.player.summon_atk_bonus))
        self.summons.append(s)
        return s

    def _shoot_summon_bullet(self, summon, target):
        """射击型召唤物发射子弹（套用玩家全部子弹效果：穿透/弹射/多发/爆炸/伤害/大小）"""
        dx = target.x - summon.x
        dy = target.y - summon.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist == 0:
            dir_x, dir_y = 1, 0
        else:
            dir_x, dir_y = dx / dist, dy / dist
        p = self.player
        size = int(BULLET_SIZE * (1 + p.bullet_size_bonus))
        # 多发子弹：套用玩家弹量
        count = p.bullet_count
        start_x = summon.x + summon.width / 2 - size / 2
        start_y = summon.y + summon.height / 2 - size / 2
        for i in range(count):
            if count > 1:
                # 扇形散开（同玩家）
                spread_deg = 15
                t = i / (count - 1)
                ang = (-spread_deg + 2 * spread_deg * t) * math.pi / 180
                cos_a, sin_a = math.cos(ang), math.sin(ang)
                bx = dir_x * cos_a - dir_y * sin_a
                by = dir_x * sin_a + dir_y * cos_a
            else:
                bx, by = dir_x, dir_y
            bullet = Bullet(start_x, start_y, bx, by,
                            pierce=p.pierce, size=size, bounce=p.bounce)
            bullet.speed = PLAYER_SPEED * BULLET_SPEED_FACTOR
            bullet.range_left = PLAYER_SPEED * BULLET_RANGE_FACTOR
            bullet.damage = p.damage
            bullet.color = summon.bullet_color  # 该生肖专属子弹颜色
            bullet.is_summon = True
            bullet.summon_owner = summon  # 记录发射者（爆炸时用其颜色）
            self.bullets.append(bullet)

    def _on_enemy_killed(self):
        """敌人被击杀时调用（含洗脑判定）"""
        if self.player.on_kill():
            # 达到升级条件，调用外部回调
            if self.on_kill_callback:
                self.on_kill_callback()
        # 洗脑判定：击杀时概率生出友军
        if random.random() < self.player.brainwash_chance:
            x, y = self.player.x, self.player.y
            # 在玩家附近生成友军
            import math
            angle = random.uniform(0, 2 * math.pi)
            dist = 60
            ax = x + math.cos(angle) * dist
            ay = y + math.sin(angle) * dist
            self.allies.append(Ally(ax, ay, attack_power=self.player.damage))

    def _apply_knockback(self, enemy, from_x, from_y, dist_grill):
        """平滑击退：从 (from_x,from_y) 方向推开敌人"""
        kx = enemy.x - from_x
        ky = enemy.y - from_y
        kdist = math.sqrt(kx * kx + ky * ky)
        if kdist > 0:
            knock_px = dist_grill * 80
            enemy.apply_knockback(kx / kdist, ky / kdist, knock_px)

    def _on_enemy_hit_for_brainwash(self, enemy):
        """命中敌人触发洗脑判定（爆炸/子弹/屏障/弹射通用）"""
        if random.random() < self.player.brainwash_chance:
            x = enemy.x + enemy.width / 2
            y = enemy.y + enemy.height / 2
            self.allies.append(Ally(x, y, attack_power=self.player.damage))

    def _show_big_text(self, text, x, y):
        """显示大文字特效（1 秒消失）"""
        self.big_texts.append(BigText(x, y, text))

    def _get_max_tier(self):
        """根据游戏时间获取当前允许的最大敌人 tier
        每 180 秒（3 分钟）解锁下一级
        """
        minutes = int(self.game_time / 60)
        phase = minutes // 3  # 每 3 分钟一阶段
        return min(phase, 5)  # 最多解锁到 tier 5

    def _spawn_initial_enemies(self, cx, cy):
        """从画面外随机位置生成初始敌人（全部为默认 tier 0）"""
        for i in range(10):
            self._spawn_enemy_around(cx, cy, max_tier=0)

    def _spawn_enemy_around(self, center_x, center_y, max_tier=None):
        """在远处随机位置生成一个敌人（随机 tier 0 ~ max_tier）"""
        if max_tier is None:
            max_tier = self._get_max_tier()
        angle = random.uniform(0, 2 * math.pi)
        distance = random.randint(ENEMY_SPAWN_DIST_MIN, ENEMY_SPAWN_DIST_MAX)
        x = center_x + math.cos(angle) * distance
        y = center_y + math.sin(angle) * distance
        # 在 0~max_tier 之间随机选择 tier，权重越高级越低
        if max_tier <= 0:
            tier = 0
        else:
            # 让高级敌人稀有：权重组 (max_tier+1, max_tier, ..., 1)
            weights = list(range(max_tier + 1, 0, -1))
            tier = random.choices(range(max_tier + 1), weights=weights)[0]
        e = Enemy(x, y, tier=tier)
        # 应用背景对比色覆盖
        if f"tier{tier}" in self.enemy_color_overrides:
            e.color = self.enemy_color_overrides[f"tier{tier}"]
        # 按游戏时间强化属性（每2分钟攻击/生命+10%）
        e.apply_growth(self.game_time)
        self.enemies.append(e)

    def find_nearest_enemy(self, player_x, player_y):
        """寻找离玩家最近的敌人"""
        nearest = None
        min_dist = float('inf')
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            dist = enemy.distance_to(player_x, player_y)
            if dist < min_dist:
                min_dist = dist
                nearest = enemy
        return nearest, min_dist

    def _find_nearest_alive_enemy(self, x, y, exclude=None):
        """寻找离 (x,y) 最近的存活敌人，排除指定敌人，且距离大于最小弹射范围"""
        nearest = None
        min_dist = float('inf')
        min_bounce_dist = 20  # 最小弹射距离，避免弹到自己
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy is exclude:
                continue
            dx = enemy.x - x
            dy = enemy.y - y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < min_dist:
                min_dist = dist
                nearest = enemy
        # 过滤掉距离过近（几乎重叠）的目标
        if nearest is not None and min_dist < min_bounce_dist:
            # 找第二近的
            second = None
            second_dist = float('inf')
            for enemy in self.enemies:
                if not enemy.alive or enemy is exclude or enemy is nearest:
                    continue
                dx = enemy.x - x
                dy = enemy.y - y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < second_dist:
                    second_dist = dist
                    second = enemy
            return second
        return nearest

    def _find_screen_enemy(self, x, y):
        """寻找画面内（玩家视野 700x420）最近的敌人，无则返回 None"""
        nearest = None
        min_d = float('inf')
        px, py = self.player.x, self.player.y
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            # 画面内判断：以玩家为中心 ±700 x ±420（屏幕 1280x720 的一半）
            if abs(enemy.x - px) > 700 or abs(enemy.y - py) > 420:
                continue
            d = enemy.distance_to(x, y)
            if d < min_d:
                min_d = d
                nearest = enemy
        return nearest

    def shoot_bullet(self, src_x, src_y, target_x, target_y):
        """发射子弹（支持多发、穿透）"""
        dx = target_x - src_x
        dy = target_y - src_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist == 0:
            dir_x, dir_y = 1, 0
        else:
            dir_x = dx / dist
            dir_y = dy / dist

        player = self.player
        count = player.bullet_count      # 多发子弹数量
        pierce = player.pierce           # 穿透次数
        size = int(BULLET_SIZE * (1 + player.bullet_size_bonus))  # 子弹大小
        bounce = player.bounce           # 弹射次数
        # 子弹起点（玩家中心）
        start_x = src_x + PLAYER_WIDTH / 2 - size / 2
        start_y = src_y + PLAYER_HEIGHT / 2 - size / 2

        if count <= 1:
            self.bullets.append(Bullet(start_x, start_y, dir_x, dir_y, pierce, size, bounce))
        else:
            # 多发子弹：以目标方向为中心，扇形散开
            spread_deg = 15  # 单侧角度
            for i in range(count):
                if count == 1:
                    ang = 0
                else:
                    # 均匀分布在 -spread_deg ~ +spread_deg
                    t = i / (count - 1)
                    ang = (-spread_deg + 2 * spread_deg * t) * math.pi / 180
                # 旋转方向向量
                cos_a, sin_a = math.cos(ang), math.sin(ang)
                bx = dir_x * cos_a - dir_y * sin_a
                by = dir_x * sin_a + dir_y * cos_a
                self.bullets.append(Bullet(start_x, start_y, bx, by, pierce, size, bounce))

    def update(self, dt, player_x, player_y):
        """
        更新战斗系统
        - 自动攻击最近的敌人（进入 AUTO_ATTACK_RANGE 范围）
        - 更新所有子弹
        - 更新所有敌人（朝玩家靠近）
        - 碰撞检测
        - 无限生成敌人
        """
        # --- 累计游戏时间（用于解锁敌人 tier）---
        self.game_time += dt
        # 本帧已生成跳字的敌人（避免多发子弹同帧跳字堆叠）
        self._frame_taunt_enemies = set()

        # --- 自动射击（攻击速度受加成）---
        if self.auto_attack:
            nearest, dist = self.find_nearest_enemy(player_x, player_y)
            if nearest is not None and dist <= AUTO_ATTACK_RANGE:
                self.fire_cooldown -= dt
                if self.fire_cooldown <= 0:
                    self.shoot_bullet(player_x, player_y, nearest.x, nearest.y)
                    # 攻击速度加成：间隔 = 1/(FIRE_RATE*(1+bonus))
                    rate = FIRE_RATE * (1 + self.player.fire_rate_bonus)
                    self.fire_cooldown = 1.0 / rate

        # --- 更新子弹 ---
        for bullet in self.bullets[:]:
            bullet.update(dt)
            if not bullet.alive:
                self.bullets.remove(bullet)

        # --- 更新伤害跳字（0.5秒后消失）---
        for text in self.damage_texts[:]:
            if not text.update(dt):
                self.damage_texts.remove(text)

        # --- 更新爆炸特效 ---
        for exp in self.explosions[:]:
            if not exp.update(dt):
                self.explosions.remove(exp)

        # --- 更新大文字特效 ---
        for bt in self.big_texts[:]:
            if not bt.update(dt):
                self.big_texts.remove(bt)

        # --- 子弹击中敌人检测（支持穿透、弹射、吸血）---
        # 用 while 遍历避免修改列表时索引错乱
        enemy_iter = 0
        while enemy_iter < len(self.enemies):
            enemy = self.enemies[enemy_iter]
            if not enemy.alive:
                enemy_iter += 1
                continue

            hit = False
            bullet_iter = 0
            while bullet_iter < len(self.bullets):
                bullet = self.bullets[bullet_iter]
                if enemy.get_rect().colliderect(bullet.get_rect()):
                    hit = True
                    # 暴击判定（召唤物子弹用固定伤害，不暴击）
                    if bullet.damage is not None:
                        dmg = bullet.damage
                        is_crit = False
                    else:
                        dmg, is_crit = self.player.get_damage_with_crit()
                    enemy.take_damage(dmg)
                    p = self.player
                    # 子弹命中：吸血 + 洗脑
                    self.player.try_lifesteal()
                    self._on_enemy_hit_for_brainwash(enemy)
                    # 子弹击退（平滑）——多发子弹每个都击退，弹射子弹也击退
                    if p.knockback_enabled and enemy.alive:
                        self._apply_knockback(enemy, player_x, player_y, p.knockback_dist)
                    # 爆炸（如果开启）
                    if p.explosion_enabled:
                        # 爆炸伤害 = 子弹伤害100% + 敌人生命10% 向下取整
                        b_dmg = dmg + (enemy.max_hp // 10)
                        radius_px = p.explosion_radius * 80
                        ex = enemy.x + enemy.width / 2
                        ey = enemy.y + enemy.height / 2
                        for en in self.enemies[:]:
                            if not en.alive:
                                continue
                            # 跳过当前正在处理的敌人（由外层统一处理击杀）
                            if en is enemy:
                                continue
                            en_ex = en.x + en.width / 2
                            en_ey = en.y + en.height / 2
                            dx = en_ex - ex
                            dy = en_ey - ey
                            dist = math.sqrt(dx * dx + dy * dy)
                            if dist <= radius_px:
                                en.take_damage(b_dmg)
                                en.stun(EXPLOSION_STUN)  # 爆炸停顿
                                # 爆炸也能吸血 + 洗脑
                                self.player.try_lifesteal()
                                self._on_enemy_hit_for_brainwash(en)
                                # 爆炸也能击退
                                if p.knockback_enabled and en.alive:
                                    self._apply_knockback(en, ex, ey, p.knockback_dist)
                                if not en.alive:
                                    self.enemies.remove(en)
                                    self._on_enemy_killed()
                        # 生成爆炸特效（召唤物子弹爆炸用召唤物颜色）
                        exp = Explosion(ex, ey, radius_px)
                        if getattr(bullet, 'is_summon', False):
                            exp.custom_color = bullet.color
                        self.explosions.append(exp)
                        # 爆炸触发击退时弹出"飞身踢"文字
                        if p.knockback_enabled:
                            self._show_big_text("飞身踢", ex, ey)
                    # 生成伤害跳字（同一敌人只保留一个，新跳字替换旧跳字，避免堆叠成块）
                    if id(enemy) not in self._frame_taunt_enemies:
                        self._frame_taunt_enemies.add(id(enemy))
                        # 查找该敌人已有的存活跳字，有则替换
                        replaced = False
                        for old_dt in self.damage_texts:
                            if getattr(old_dt, 'owner_id', None) == id(enemy):
                                old_dt.text = str(dmg)
                                old_dt.font_size = old_dt._calc_font_size(str(dmg), is_crit)
                                old_dt.is_crit = is_crit
                                old_dt.elapsed = 0.0
                                replaced = True
                                break
                        if not replaced:
                            dt_new = DamageText(
                                enemy.x + enemy.width / 2 + random.uniform(-6, 6),
                                enemy.y + random.uniform(-6, 6),
                                str(dmg),
                                is_crit
                            )
                            dt_new.owner_id = id(enemy)  # 标记归属敌人
                            self.damage_texts.append(dt_new)

                    if not enemy.alive:
                        # 敌人死亡：移除并触发击杀回调（保护索引，防止爆炸已移除）
                        if enemy_iter < len(self.enemies) and self.enemies[enemy_iter] is enemy:
                            self.enemies.pop(enemy_iter)
                        elif enemy in self.enemies:
                            self.enemies.remove(enemy)
                        self._on_enemy_killed()
                        # enemy_iter 不递增（列表缩短了），退出子弹循环
                        # 子弹处理：穿透或弹射
                        if bullet.pierce > 0:
                            bullet.pierce -= 1
                        elif bullet.bounce > 0:
                            # 弹射到另一个活敌
                            target = self._find_nearest_alive_enemy(bullet.x, bullet.y, exclude=None)
                            if target is not None:
                                dx = target.x - bullet.x
                                dy = target.y - bullet.y
                                dist = math.sqrt(dx * dx + dy * dy)
                                if dist > 0:
                                    bullet.dir_x = dx / dist
                                    bullet.dir_y = dy / dist
                                    bullet.bounce -= 1
                                    bullet.x = enemy.x + enemy.width / 2
                                    bullet.y = enemy.y + enemy.height / 2
                                else:
                                    self.bullets.pop(bullet_iter)
                            else:
                                self.bullets.pop(bullet_iter)
                        else:
                            self.bullets.pop(bullet_iter)
                        break  # 退出子弹循环，处理下一个敌人

                    # 敌人没死
                    if bullet.pierce > 0:
                        bullet.pierce -= 1
                    else:
                        self.bullets.pop(bullet_iter)
                        # 敌人没死且子弹不可穿透：子弹消失，继续下一个子弹
                        bullet_iter -= 1
                    bullet_iter += 1
                else:
                    bullet_iter += 1

            if not hit:
                enemy_iter += 1
            # 如果 hit 且敌人没死，enemy_iter 递增继续下一个敌人
            elif enemy.alive:
                enemy_iter += 1
            # 如果 hit 且敌人死了，enemy_iter 已经正确（列表缩短）

        # --- 更新敌人 ---
        for enemy in self.enemies[:]:
            if enemy.alive:
                enemy.update(dt, player_x, player_y)

        # --- 更新友军（洗脑）---
        for ally in self.allies[:]:
            ally.update(dt, player_x, player_y, self.enemies)
            if not ally.alive:
                self.allies.remove(ally)
                continue
            # 友军超出画面外自动传送回玩家身边
            dist_to_player = ally.distance_to(player_x, player_y)
            if dist_to_player > 2000:
                ally.x = player_x + random.uniform(-50, 50)
                ally.y = player_y + random.uniform(-50, 50)
            # 友军攻击最近的敌人（近战碰撞）
            if self.enemies:
                nearest_enemy = None
                min_d = float('inf')
                for en in self.enemies:
                    if not en.alive:
                        continue
                    d = ally.distance_to(en.x, en.y)
                    if d < min_d:
                        min_d = d
                        nearest_enemy = en
                if nearest_enemy is not None and min_d < ally.width:
                    # 友军攻击敌人
                    nearest_enemy.take_damage(ally.attack)
                    if not nearest_enemy.alive:
                        self.enemies.remove(nearest_enemy)
                        # 友军击杀也可触发洗脑
                        self._on_enemy_killed()

        # --- 能量屏障脉冲 ---
        self._barrier_pulse = (self._barrier_pulse + dt) % 2.0

        # --- 能量屏障伤害 ---
        p = self.player
        if p.barrier_enabled:
            radius_px = p.barrier_radius * 80  # 格转像素
            freq = p.barrier_freq
            if not hasattr(self, "_barrier_timer"):
                self._barrier_timer = 0.0
            self._barrier_timer += dt
            if self._barrier_timer >= 1.0 / freq:
                self._barrier_timer -= 1.0 / freq
                center_x = player_x + PLAYER_WIDTH / 2
                center_y = player_y + PLAYER_HEIGHT / 2
                for enemy in self.enemies[:]:
                    if not enemy.alive:
                        continue
                    ex = enemy.x + enemy.width / 2
                    ey = enemy.y + enemy.height / 2
                    dx = ex - center_x
                    dy = ey - center_y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= radius_px:
                        enemy.take_damage(p.barrier_damage)
                        # 屏障击中敌人也能触发吸血 + 洗脑
                        self.player.try_lifesteal()
                        self._on_enemy_hit_for_brainwash(enemy)
                        if not enemy.alive:
                            self.enemies.remove(enemy)
                            self._on_enemy_killed()

        # --- 生命回复 ---
        if p.regen and p.hp < p.max_hp:
            if not hasattr(self, "_regen_timer"):
                self._regen_timer = 0.0
            self._regen_timer += dt
            if self._regen_timer >= 1.0:
                self._regen_timer -= 1.0
                p.heal(REGEN_AMOUNT)

        # --- 画面内无敌人超过 1 秒则立即刷新 ---
        on_screen_enemy = False
        for en in self.enemies:
            if en.alive:
                dx = en.x - player_x
                dy = en.y - player_y
                if abs(dx) < 1280 and abs(dy) < 720:
                    on_screen_enemy = True
                    break
        if not on_screen_enemy:
            if not hasattr(self, "_empty_timer"):
                self._empty_timer = 0.0
            self._empty_timer += dt
            if self._empty_timer >= ENEMY_EMPTY_REFRESH:
                self._empty_timer = 0.0
                # 立即刷新一批敌人（画面外生成，会靠近）
                for _ in range(3):
                    self._spawn_enemy_around(player_x, player_y)
        else:
            self._empty_timer = 0.0

        # --- 无限生成敌人（每分钟 +10% 速率）---
        self.spawn_cooldown -= dt
        while self.spawn_cooldown <= 0:
            minutes = max(1, self.game_time // 60)
            dynamic_interval = ENEMY_SPAWN_INTERVAL / (1 + ENEMY_GROWTH_RATE * minutes)
            self.spawn_cooldown += dynamic_interval
            self._spawn_enemy_around(player_x, player_y)

        # --- 精英怪：间隔随分钟缩短 + 属性成长 ---
        self._elite_timer += dt
        elite_interval = ELITE_SPAWN_INTERVAL / (1 + ENEMY_GROWTH_RATE * max(1, self.game_time // 60))
        if self._elite_timer >= elite_interval:
            self._elite_timer -= elite_interval
            angle = random.uniform(0, 2 * math.pi)
            dist = random.randint(1200, 2500)
            ex = player_x + math.cos(angle) * dist
            ey = player_y + math.sin(angle) * dist
            el = Enemy(ex, ey, tier=random.randint(0, 5), elite=True)
            if "elite" in self.enemy_color_overrides:
                el.color = self.enemy_color_overrides["elite"]
            el.apply_growth(self.game_time)
            self.enemies.append(el)

        # --- 特殊敌人：间隔随分钟缩短 + 属性成长 ---
        self._special_enemy_timer += dt
        special_interval = SPECIAL_ENEMY_INTERVAL / (1 + ENEMY_GROWTH_RATE * max(1, self.game_time // 60))
        if self._special_enemy_timer >= special_interval:
            self._special_enemy_timer -= special_interval
            if not self._special_enemy_queue:
                self._special_enemy_queue = list(SPECIAL_ENEMY_TYPES)
                random.shuffle(self._special_enemy_queue)
            enemy_cls = self._special_enemy_queue.pop(0)
            angle = random.uniform(0, 2 * math.pi)
            dist = random.randint(800, 2000)
            sx = player_x + math.cos(angle) * dist
            sy = player_y + math.sin(angle) * dist
            sp_enemy = enemy_cls(sx, sy)
            sp_enemy.apply_growth(self.game_time)
            self.enemies.append(sp_enemy)

        # --- 弓箭手生成：间隔随分钟缩短 + 属性成长 ---
        self._archer_spawn_timer += dt
        archer_interval = 60 / (1 + ENEMY_GROWTH_RATE * max(1, self.game_time // 60))
        if self._archer_spawn_timer >= archer_interval:
            self._archer_spawn_timer -= archer_interval
            # 每 60 秒刷新 3 只弓箭手
            for _ in range(3):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.randint(ARCHER_ATTACK_RANGE + 200, ARCHER_ATTACK_RANGE + 600)
                ax = player_x + math.cos(angle) * dist
                ay = player_y + math.sin(angle) * dist
                ar = Archer(ax, ay)
                if "archer" in self.enemy_color_overrides:
                    ar.color = self.enemy_color_overrides["archer"]
                ar.apply_growth(self.game_time)
                self.enemies.append(ar)

        # --- 弓箭手射击逻辑（遍历 enemies 中的 Archer）---
        for archer in [e for e in self.enemies if isinstance(e, Archer) and e.alive]:
            dx = player_x - archer.x
            dy = player_y - archer.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist >= ARCHER_FLEE_RANGE and dist <= ARCHER_ATTACK_RANGE:
                archer.fire_cooldown -= dt
                if archer.fire_cooldown <= 0:
                    archer.fire_cooldown = ARCHER_FIRE_INTERVAL
                    dir_x, dir_y = archer.get_fire_direction(player_x, player_y)
                    self.arrows.append(Arrow(archer.x + archer.width / 2, archer.y + archer.height / 2, dir_x, dir_y))

        # --- 屏障敌人对玩家伤害 ---
        for be in [e for e in self.enemies if isinstance(e, BarrierEnemy) and e.alive]:
            px = player_x + PLAYER_WIDTH / 2
            py = player_y + PLAYER_HEIGHT / 2
            dist = math.sqrt((be.x - px) ** 2 + (be.y - py) ** 2)
            be._barrier_timer += dt
            if be._barrier_timer >= 1.0:
                be._barrier_timer -= 1.0
                if dist <= be.barrier_radius:
                    self.player.take_damage(be.barrier_damage)

        # --- 召唤物：每 10 秒召唤一只十二生肖（不重复，上限 12）---
        if self.player.summon_enabled:
            # 首次开启时立即召唤 1 只
            if not self._summon_first_done:
                self._summon_first_done = True
                self._spawn_summon(player_x, player_y)
            self._summon_timer += dt
            if self._summon_timer >= SUMMON_INTERVAL:
                self._summon_timer -= SUMMON_INTERVAL
                # 清理过期召唤物
                self.summons = [s for s in self.summons if s.alive]
                self._spawn_summon(player_x, player_y)
        # 更新召唤物
        for s in self.summons[:]:
            s.update(dt, self.enemies, player_x, player_y)
            if not s.alive:
                self.summons.remove(s)
                continue
            if s.is_shooter:
                # 射击型：只攻击画面内敌人（无画面内敌人则待命）
                nearest = self._find_screen_enemy(s.x, s.y)
                if nearest is not None:
                    s.fire_cooldown -= dt
                    if s.fire_cooldown <= 0:
                        s.fire_cooldown = 1.0 / (FIRE_RATE * (1 + self.player.summon_atk_bonus))
                        self._shoot_summon_bullet(s, nearest)
            else:
                # 近战型：碰撞敌人造成伤害（击退 + 爆炸 + 受击效果）
                for en in self.enemies[:]:
                    if en.alive and s.get_rect().colliderect(en.get_rect()):
                        if s.attack_cooldown <= 0:
                            s.attack_cooldown = s.attack_interval
                            en.take_damage(s.attack)  # 受击效果（flash_timer）
                            # 小幅度击退
                            if not en.elite:
                                kx = en.x - s.x
                                ky = en.y - s.y
                                kdist = math.sqrt(kx * kx + ky * ky)
                                if kdist > 0:
                                    en.apply_knockback(kx / kdist, ky / kdist, SUMMON_KNOCKBACK)
                            # 爆炸：对范围内敌人造成伤害 + 停顿 + 爆炸特效
                            b_radius = EXPLOSION_RADIUS * 80
                            ex = en.x + en.width / 2
                            ey = en.y + en.height / 2
                            b_dmg = s.attack + (en.max_hp // 10)
                            for en2 in self.enemies[:]:
                                if not en2.alive or en2 is en:
                                    continue
                                d2x = en2.x + en2.width / 2 - ex
                                d2y = en2.y + en2.height / 2 - ey
                                if math.sqrt(d2x * d2x + d2y * d2y) <= b_radius:
                                    en2.take_damage(b_dmg)
                                    en2.stun(EXPLOSION_STUN)
                                    if not en2.alive:
                                        self.enemies.remove(en2)
                                        self._on_enemy_killed()
                            # 爆炸特效（用召唤物自身颜色）
                            exp = Explosion(ex, ey, b_radius)
                            exp.custom_color = s.color
                            self.explosions.append(exp)
                            if not en.alive:
                                self.enemies.remove(en)
                                self._on_enemy_killed()
                        break

        # --- 更新箭矢（穿透敌人，直到击中玩家）---
        for arrow in self.arrows[:]:
            arrow.update(dt)
            # 箭矢不伤害敌人（穿透），只检测玩家碰撞
            player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
            if player_rect.colliderect(arrow.get_rect()):
                self.player.take_damage(arrow.damage)
                self.arrows.remove(arrow)
                continue
            # 超出太远消失（防止无限飞行）
            ax_d = arrow.x - player_x
            ay_d = arrow.y - player_y
            if math.sqrt(ax_d * ax_d + ay_d * ay_d) > 3000:
                self.arrows.remove(arrow)

        # --- 敌人嘲讽气泡（AI 生成，后台预取不卡帧）---
        self._update_taunts(dt)

    def _update_taunts(self, dt):
        """每个敌人都发嘲讽气泡（从预生成池取，不阻塞）"""
        if ai_assistant is None or not ai_assistant.AI_ENABLED:
            return
        # 嘲讽池不足时，从全局池补充（后台预填，不阻塞）
        global _global_taunt_pool
        if len(self._taunt_pool) < 10 and _global_taunt_pool:
            take = min(10 - len(self._taunt_pool), len(_global_taunt_pool))
            self._taunt_pool.extend(_global_taunt_pool[:take])
            del _global_taunt_pool[:take]
        # 给画面内的敌人发嘲讽（进入画面才发，存活期间每 5 秒发一次，内容不重复）
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            # 气泡显示中或冷却中，跳过
            if enemy.taunt_timer > 0 or enemy.taunt_cooldown > 0:
                continue
            # 进入画面才发（屏幕 1280x720 可见范围）
            dx = enemy.x - self.player.x
            dy = enemy.y - self.player.y
            if abs(dx) > 700 or abs(dy) > 420:
                continue  # 画面外不发
            # 从池取一条没被该敌人用过的嘲讽语
            text = self._get_fresh_taunt(enemy)
            enemy.taunt_text = text
            enemy.taunt_timer = 3.0
            enemy.taunt_cooldown = 5.0  # 每 5 秒发一次
        # 气泡计时（在 Enemy.update 里处理）
        self._taunt_timer += dt

    def _get_fresh_taunt(self, enemy):
        """从嘲讽池取一条该敌人没用过的嘲讽语"""
        # 尝试 AI 池
        for pool in (self._taunt_pool, self._local_taunt_pool):
            idx = 0
            while idx < len(pool):
                candidate = pool[idx]
                if candidate not in enemy.taunt_used:
                    pool.pop(idx)
                    enemy.taunt_used.add(candidate)
                    return candidate
                idx += 1
        # 池里都被用过了，重置本地池
        if not self._local_taunt_pool:
            self._local_taunt_pool = ai_assistant.get_local_taunts_pool()
        if self._local_taunt_pool:
            text = self._local_taunt_pool.pop(0)
            enemy.taunt_used.add(text)
            return text
        return "哼！"

    def _request_taunt_batch(self, used_texts=None):
        """同步补充嘲讽池（一次性生成 12 条，仅池空时触发）"""
        try:
            taunts = ai_assistant.get_taunts_batch(12, used_texts)
            self._taunt_pool.extend(taunts)
        except Exception:
            pass

    def _build_taunt_context(self):
        """构建嘲讽上下文（玩家状态）"""
        hp_ratio = self.player.hp / self.player.max_hp if self.player.max_hp else 0
        if hp_ratio < 0.2:
            return "玩家残血了，快嘲讽他"
        if self.player.kill_count > 20:
            return f"玩家已经杀了{self.player.kill_count}个敌人"
        if self.player.level > 3:
            return f"玩家等级{self.player.level}"
        return "常规嘲讽"

    def check_player_collision(self, player_x, player_y):
        """检查玩家是否与任何敌人碰撞（会扣血）"""
        player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
        for enemy in self.enemies:
            if enemy.alive and player_rect.colliderect(enemy.get_rect()):
                return True, enemy
        return False, None

    def draw(self, screen, camera_x, camera_y):
        """绘制所有敌人、子弹、友军、屏障、伤害跳字"""
        # 先绘制能量屏障（在敌人之下）
        p = self.player
        if p.barrier_enabled:
            radius_px = p.barrier_radius * 80
            cx = p.x + PLAYER_WIDTH / 2 - camera_x
            cy = p.y + PLAYER_HEIGHT / 2 - camera_y
            # 脉冲动画：alpha 和半径在 0.5s 周期内波动
            pulse = math.sin(self._barrier_pulse * math.pi * 2) * 0.3 + 0.7
            alpha_outer = int(100 * pulse)
            alpha_inner = int(30 * pulse)
            radius_var = int(radius_px * 0.05 * pulse)
            r = radius_px + radius_var
            barrier_surf = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(barrier_surf, (255, 255, 255, alpha_outer),
                               (r + 5, r + 5), r, width=3)
            pygame.draw.circle(barrier_surf, (255, 255, 255, alpha_inner),
                               (r + 5, r + 5), r - 3)
            screen.blit(barrier_surf, (cx - r - 5, cy - r - 5))
        # 先绘制敌人（含弓箭手）
        for enemy in self.enemies:
            if enemy.alive:
                enemy.draw(screen, camera_x, camera_y)
        # 绘制箭矢
        for arrow in self.arrows:
            arrow.draw(screen, camera_x, camera_y)
        # 再绘制友军（洗脑）
        for ally in self.allies:
            ally.draw(screen, camera_x, camera_y)
        # 绘制召唤物（十二生肖）
        for s in self.summons:
            s.draw(screen, camera_x, camera_y)
        # 再绘制子弹
        for bullet in self.bullets:
            bullet.draw(screen, camera_x, camera_y)
        # 绘制爆炸特效（在敌人之下）
        for exp in self.explosions:
            exp.draw(screen, camera_x, camera_y)
        # 最后绘制伤害跳字
        for dt_text in self.damage_texts:
            dt_text.draw(screen, camera_x, camera_y)
        # 大文字特效（最上层）
        for bt in self.big_texts:
            bt.draw(screen, camera_x, camera_y)
