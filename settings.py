"""
肉鸽游戏 - 全局设置
"""

# 窗口
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
GAME_TITLE = "肉鸽游戏 Demo"

# 颜色
BG_COLOR = (18, 20, 28)          # 深色背景
MENU_BG = (24, 28, 40)           # 菜单背景
WHITE = (255, 255, 255)
GRAY = (120, 120, 130)
LIGHT_GRAY = (180, 180, 190)
HIGHLIGHT = (255, 200, 80)       # 选中高亮（金黄）
GREEN = (80, 220, 120)
RED = (220, 80, 80)
PLAYER_COLOR = (90, 180, 255)    # 玩家长方形颜色（浅蓝）
GRID_COLOR = (40, 44, 58)        # 网格线颜色

# 地图（程序化无限地图 - 草地风格）
GRASS_DARK = (52, 88, 44)        # 草地深色（备用）
GRASS_LIGHT = (66, 105, 52)      # 草地浅色（备用）
DIRT_COLOR = (96, 74, 52)        # 泥土色
TILE_SIZE = 80                   # 地块大小
MAP_SEED = 2025                  # 随机种子（保证地图稳定）
# 多种绿色瓦片颜色（随机分配）
GRASS_COLORS = [
    (30, 60, 30),   # 深绿
    (40, 75, 35),   # 墨绿
    (50, 85, 40),   # 中绿
    (58, 92, 45),   # 草绿
    (66, 102, 50),  # 浅绿
    (75, 110, 55),  # 亮绿
    (85, 120, 60),  # 嫩绿
    (95, 130, 65),  # 黄绿
]

# 彩蛋：同一瓦片停留时间奖励
EGG_STAY_TIME_DEFAULT = 60       # 默认 60 秒
EGG_STAY_TIME_MIN = 1            # 最小 1 秒
EGG_STAY_TIME_MAX = 60           # 最大 60 秒

# 玩家
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 60
PLAYER_SPEED = 300               # 每秒移动像素

# 战斗
ENEMY_COUNT = 10                 # 初始敌人数量
ENEMY_SIZE = 32                  # 基础敌人直径（px）
ENEMY_SPEED_FACTOR = 0.8         # 基础敌人移速 = 玩家移速的 0.8 倍
ENEMY_COLOR = (220, 70, 70)      # 敌人颜色（红色，作为备用）
# 敌人颜色和属性由 tier 决定（浅 → 深）
ENEMY_TIER_COLORS = [
    (180, 100, 100),   # tier 0 浅粉
    (200, 80, 80),     # tier 1
    (220, 60, 60),     # tier 2
    (235, 40, 40),     # tier 3
    (245, 20, 20),     # tier 4
    (255, 0, 0),       # tier 5 深红
]
# 每个 tier 的属性倍率 (攻击, 生命, 速度, 尺寸)
ENEMY_TIER_STATS = [
    (1.0, 1.0, 1.0, 1.0),     # tier 0: 基础
    (1.5, 2.0, 1.5, 1.2),     # tier 1: 稍强
    (2.0, 2.5, 2.0, 1.4),     # tier 2: 中级
    (2.5, 3.0, 2.5, 1.6),     # tier 3: 强
    (3.0, 3.5, 3.0, 1.8),     # tier 4: 很强
    (3.5, 4.0, 3.5, 2.0),     # tier 5: 超强
]
BULLET_SIZE = 8                  # 子弹直径（px）
BULLET_SPEED_FACTOR = 3          # 子弹速度 = 玩家移速的 3 倍
BULLET_RANGE_FACTOR = 10         # 射程 = 玩家移速的 10 倍
BULLET_COLOR = (255, 220, 90)    # 子弹颜色（黄色）
FIRE_RATE = 2                    # 每秒发射子弹数（2发/秒）
AUTO_ATTACK_RANGE = 600          # 自动攻击触发距离（px，敌人进入此范围自动开火）

# 敌人无限生成
ENEMY_SPAWN_INTERVAL = 1.0       # 每秒生成 1 个敌人
ENEMY_SPAWN_DIST_MIN = 1200      # 生成位置距玩家最小距离（画面外）
ENEMY_SPAWN_DIST_MAX = 2500      # 生成位置距玩家最大距离

# 冲刺技能
DASH_DISTANCE = 3                # 位移距离（单位：格，1格=80px）
DASH_DOUBLE_TAP_MS = 250         # 双击判定时间窗口（毫秒）
DASH_SPEED_FACTOR = 12           # 冲刺速度倍率（瞬间位移用）
DASH_COLOR = (255, 255, 255)     # 冲刺特效颜色

# 血量
PLAYER_HP = 10                   # 玩家血量
ENEMY_HP_MIN = 1                 # 敌人血量下限
ENEMY_HP_MAX = 5                 # 敌人血量上限
BULLET_DAMAGE = 1                # 子弹基础伤害

# 升级
KILLS_PER_LEVEL = 5              # 每击杀 N 个敌人升一级
PLAYER_HP_BONUS = 2              # 选生命时增加的HP上限
SPEED_BONUS_PCT = 0.10           # 选移速时增加的百分比
ATTACK_SPEED_MIN = 0.10          # 攻击速度加成下限 10%
ATTACK_SPEED_MAX = 1.00          # 攻击速度加成上限 100%
BULLET_COUNT_MIN = 1             # 子弹数量加成下限 +1
BULLET_COUNT_MAX = 5             # 子弹数量加成上限 +5
PIERCE_BONUS = 1                 # 子弹穿透每次 +1
BULLET_SIZE_BONUS_MIN = 0.50     # 子弹大小加成下限 50%
BULLET_SIZE_BONUS_MAX = 1.00     # 子弹大小加成上限 100%
BOUNCE_COUNT = 1                 # 子弹弹射次数每次 +1
LIFESTEAL_CHANCE = 0.10          # 吸血概率 10%
LIFESTEAL_PITY = 10              # 假概率：每 10 发必触发 1 次
LIFESTEAL_HEAL = 1               # 吸血回血量

# 暴击
CRIT_RATE_DEFAULT = 0.05         # 默认暴击率 5%
CRIT_DAMAGE_DEFAULT = 2.0        # 默认暴击伤害 200%（2倍）
CRIT_RATE_MIN = 0.05             # 暴击率升级下限 +5%
CRIT_RATE_MAX = 0.20             # 暴击率升级上限 +20%
CRIT_DMG_MIN = 0.05              # 暴击伤害升级下限 +5%
CRIT_DMG_MAX = 0.20              # 暴击伤害升级上限 +20%

# 伤害跳字
DAMAGE_TEXT_LIFETIME = 0.5       # 跳字显示 0.5 秒
DAMAGE_TEXT_COLOR = (255, 255, 255)   # 普通伤害白色
CRIT_TEXT_COLOR = (255, 60, 60)       # 暴击红色
CRIT_TEXT_SIZE = 24              # 暴击字体（略大于普通，不显方块）
DAMAGE_TEXT_SIZE = 20            # 普通字体

# 洗脑
BRAINWASH_CHANCE = 0.0           # 初始洗脑概率 0%（需升级获得）
BRAINWASH_DURATION = 30.0        # 友军持续 30 秒
BRAINWASH_COLOR = (100, 200, 255)  # 友军颜色（浅蓝）
BRAINWASH_SIZE = 1.2             # 友军大小倍率（比普通敌人略大）

# 能量屏障
BARRIER_RADIUS = 1               # 初始范围 1 格（1格=80px，比角色略大）
BARRIER_DAMAGE = 1               # 范围内敌人每秒伤害
BARRIER_COLOR = (255, 255, 255)  # 白色屏障
BARRIER_ALPHA = 60               # 屏障透明度
BARRIER_RADIUS_BONUS = 0.5       # 范围升级 +0.5 格（小幅提升）
BARRIER_FREQ_BONUS = 1.0         # 频率升级 +100%（翻倍）

# 生命回复
REGEN_AMOUNT = 1                 # 生命回复每秒 +1 血

# 敌人刷新
ENEMY_EMPTY_REFRESH = 1.0        # 画面内无敌人超过 1 秒则立即刷新

# 爆炸
EXPLOSION_RADIUS = 1             # 初始爆炸范围 1 格（80px）
EXPLOSION_RADIUS_BONUS = 0.3     # 爆炸范围升级 +0.3 格（小幅提升）
EXPLOSION_COLOR = (255, 140, 30) # 火焰橙
EXPLOSION_DURATION = 0.35        # 爆炸特效持续时间
EXPLOSION_STUN = 0.2             # 爆炸时敌人停顿时间

# 濒血
LOW_HP_THRESHOLD = 0.10          # 血量低于 10% 触发濒血警告

# 击退
KNOCKBACK_DISTANCE = 1           # 初始击退距离 1 格（80px）
KNOCKBACK_BONUS = 1              # 击退距离升级 +1 格

# 精英怪
ELITE_SPAWN_INTERVAL = 60        # 每 60 秒（1 分钟）出现 1 个精英怪
ELITE_SIZE_MULT = 2.0            # 体型 2 倍
ELITE_HP_MULT = 10               # 血量 10 倍
ELITE_ATK_MULT = 2               # 攻击力 2 倍
ELITE_SPD_MULT = 0.9             # 移速 = 角色初始移速 × 0.9
ELITE_COLOR = (255, 200, 60)     # 精英怪颜色（金色）

# 弓箭手
ARCHER_COLOR = (150, 200, 120)   # 弓箭手颜色（绿色）
ARCHER_SIZE = 30                 # 弓箭手尺寸
ARCHER_HP = 3                    # 弓箭手血量
ARCHER_SPEED = 150               # 移速 0.5（玩家300的一半）
ARCHER_ATTACK_RANGE = 500        # 攻击距离（保持距离）
ARCHER_FLEE_RANGE = 200          # 玩家靠近逃跑的距离
ARCHER_FIRE_INTERVAL = 2.0       # 射击间隔（秒）
ARCHER_ARROW_DAMAGE = 1          # 箭矢伤害
ARCHER_ARROW_SPEED = 400         # 箭矢速度
ARCHER_ARROW_COLOR = (200, 200, 150)  # 箭矢颜色

# 特殊敌人（每 30 秒一只，2.5 分钟内 5 种都出现）
SPECIAL_ENEMY_INTERVAL = 30      # 每 30 秒生成一只特殊敌人
SPECIAL_ENEMY_HP_MULT = 5        # 血厚敌人生命倍数
SPECIAL_ENEMY_SPD_MULT = 0.9     # 快速敌人移速 = 角色初始移速 × 0.9
SPECIAL_ENEMY_ATK_MULT = 5       # 高攻敌人攻击倍数
SPECIAL_ENEMY_CRIT_MULT = 5      # 高暴击敌人暴击率倍数（5×5%=25%）
SPECIAL_ENEMY_BARRIER_MULT = 2   # 屏障敌人屏障范围倍数（角色初始2倍）
SPECIAL_ENEMY_BARRIER_DAMAGE = 1 # 屏障敌人每秒伤害

# 召唤（十二生肖召唤物）
SUMMON_INTERVAL = 10             # 每 10 秒召唤一只
SUMMON_DURATION = 20             # 召唤物持续 20 秒
SUMMON_SPEED = 240               # 召唤物移速
SUMMON_SIZE = 36                 # 召唤物尺寸（比默认敌人 32 大一点）
SUMMON_ATTACK = 1                # 召唤物攻击力（碰撞伤害）
SUMMON_KNOCKBACK = 30            # 召唤物击中敌人击退距离（像素，小幅度）
SUMMON_ATTACK_SPD_MIN = 0.10     # 召唤物攻速升级下限 +10%
SUMMON_ATTACK_SPD_MAX = 0.50     # 召唤物攻速升级上限 +50%
SUMMON_MOVE_SPD_MIN = 0.10       # 召唤物移速升级下限 +10%
SUMMON_MOVE_SPD_MAX = 0.20       # 召唤物移速升级上限 +20%
SUMMON_DURATION_MIN = 0.10       # 召唤物持续时间升级下限 +10%
SUMMON_DURATION_MAX = 0.20       # 召唤物持续时间升级上限 +20%
# 十二生肖名称（用于随机召唤，12 种不重复）
SUMMON_ZODIAC = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
# 射击型召唤物（前 6 种：发射子弹、跟随角色身边）
SUMMON_SHOOTERS = ["鼠", "牛", "虎", "兔", "龙", "蛇"]
# 每种射击召唤物的子弹颜色（与玩家子弹区分，且各不相同）
SUMMON_BULLET_COLORS = {
    "鼠": (200, 200, 220),   # 银白
    "牛": (180, 140, 100),   # 棕色
    "虎": (255, 170, 40),    # 橙黄
    "兔": (255, 200, 230),   # 粉
    "龙": (80, 220, 140),    # 青绿
    "蛇": (120, 200, 80),    # 草绿
}

# 敌人成长（随时间变强）
ENEMY_GROWTH_RATE = 0.10         # 每分钟敌人数量 +10%
ENEMY_STAT_GROWTH = 0.10         # 每 2 分钟敌人攻击/生命 +10%
ENEMY_STAT_GROWTH_INTERVAL = 120 # 属性成长间隔（秒，每2分钟）

# 存档文件
SAVE_FILE = "save.json"

# ===== Excel 配置覆盖 =====
# 从 config.xlsx 加载配置，覆盖上方默认值
# 用户可手动编辑 config.xlsx 后保存，重启游戏即生效
from config_loader import get_config

_cfg = get_config()

def _apply_overrides(module_namespace, cfg):
    """将 cfg 中存在的键覆盖到模块命名空间"""
    for key, value in cfg.items():
        if key in module_namespace:
            module_namespace[key] = value

_apply_overrides(globals(), _cfg)

# ===== 从 Excel 组装复杂数据结构 =====
# 射击召唤物子弹颜色（Excel 中每个生肖一个颜色键）
_bullet_color_keys = {
    "鼠": "SUMMON_BULLET_COLOR_MOUSE",
    "牛": "SUMMON_BULLET_COLOR_OX",
    "虎": "SUMMON_BULLET_COLOR_TIGER",
    "兔": "SUMMON_BULLET_COLOR_RABBIT",
    "龙": "SUMMON_BULLET_COLOR_DRAGON",
    "蛇": "SUMMON_BULLET_COLOR_SNAKE",
}
for _z, _key in _bullet_color_keys.items():
    if _key in _cfg:
        SUMMON_BULLET_COLORS[_z] = _cfg[_key]

# ===== AI 配置注入 =====
# 从 Excel 读取 AI 设置并应用到 ai_assistant
AI_API_URL = _cfg.get("AI_API_URL", "http://192.168.5.16:20128/v1")
AI_API_KEY = _cfg.get("AI_API_KEY", "sk-b6f4d3879cc4a442-aroz1n-d4d3d242")
AI_MODEL = _cfg.get("AI_MODEL", "ds/deepseek-v4-flash")
AI_ENABLED = _cfg.get("AI_ENABLED", True)
AI_TIMEOUT = _cfg.get("AI_TIMEOUT", 20)
try:
    import ai_assistant
    ai_assistant.configure(
        url=AI_API_URL, key=AI_API_KEY, model=AI_MODEL, enabled=AI_ENABLED)
    ai_assistant.AI_TIMEOUT = AI_TIMEOUT
except ImportError:
    pass
