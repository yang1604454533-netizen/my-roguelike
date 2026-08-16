"""
肉鸽游戏 - 素材加载模块
加载 PNG 素材（场景、角色、敌人），提供统一访问
"""
import os
import pygame

ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")

# 场景素材（瓦片集）
SCENE_TILES = {
    "草原": "grassland.png",
    "沙漠": "desert.png",
    "雪地": "snow.png",
    "地牢": "dungeon_32x32.png",
    "熔岩": "lava.png",
    "水域": "water_land_tiles.png",
    "墓地": "graveyard.png",
    "星空": "space.png",
}

# 角色/敌人素材
CHARACTER_SPRITE = "Hero.png"      # 玩家（4帧动画 32x32）
ENEMY_SPRITE = "Enemy.png"         # 敌人（4帧动画 32x32）

_cache = {}


def load_image(name, scale=None):
    """加载图片，带缓存。scale=(w,h) 缩放"""
    if name in _cache:
        return _cache[name]
    path = os.path.join(ASSET_DIR, name)
    if not os.path.exists(path):
        return None
    surf = pygame.image.load(path)
    # 有视频模式时优化格式，没有则用原格式
    try:
        if pygame.display.get_surface():
            surf = surf.convert_alpha()
    except Exception:
        pass
    if scale:
        surf = pygame.transform.scale(surf, scale)
    _cache[name] = surf
    return surf


# 每个场景的有效瓦片坐标（瓦片集里非空区域）: (x, y) 为 32x32 块的起始像素
SCENE_TILE_POS = {
    "草原": (0, 0),
    "沙漠": (0, 0),
    "雪地": (0, 32),     # 左上角透明，取第二行
    "地牢": (160, 160),  # 大图截图，取内容密集区
    "熔岩": (256, 256),  # 大图截图，内容在中央
    "水域": (32, 0),     # 左上部分透明
    "墓地": (0, 0),
    "星空": (0, 0),
}

# 这些素材是大图（截图），需要取较大的代表区域而不是 32x32 瓦片
SCENE_LARGE_TILE = {
    "地牢": (128, 128),
    "熔岩": (128, 128),
}


def load_scene_tile(scene_name, scale=(80, 80)):
    """
    加载场景瓦片。scene_name 为场景中文名。
    从瓦片集指定坐标取一个代表瓦片，缩放到目标大小。
    若指定区域全黑/透明，自动向右下方搜索第一个有内容的块。
    """
    tile_file = SCENE_TILES.get(scene_name)
    if not tile_file:
        return None
    tileset = load_image(tile_file)
    if tileset is None:
        return None
    w, h = tileset.get_size()
    tile_size = min(32, w, h)
    # 优先用指定坐标
    start_x, start_y = SCENE_TILE_POS.get(scene_name, (0, 0))
    # 大图素材：取较大代表区域
    large = SCENE_LARGE_TILE.get(scene_name)
    if large:
        lw, lh = large
        sx = min(start_x, max(0, w - lw))
        sy = min(start_y, max(0, h - lh))
        tile = tileset.subsurface((sx, sy, min(lw, w - sx), min(lh, h - sy))).copy()
    else:
        tile = _find_valid_tile(tileset, start_x, start_y, tile_size, w, h)
    if scale and tile is not None:
        tile = pygame.transform.scale(tile, scale)
    return tile


def _find_valid_tile(tileset, start_x, start_y, tile_size, w, h):
    """从起始位置搜索第一个有内容的 32x32 瓦片"""
    # 限制搜索范围（防止遍历整张大图）
    max_search = 12
    for gy in range(start_y, min(start_y + tile_size * 4, h), tile_size):
        for gx in range(start_x, min(start_x + tile_size * 4, w), tile_size):
            if gx + tile_size > w or gy + tile_size > h:
                continue
            tile = tileset.subsurface((gx, gy, tile_size, tile_size)).copy()
            # 检查是否有效（非全黑/非全透明）
            try:
                if tile.get_flags() & pygame.SRCALPHA:
                    mask = pygame.mask.from_surface(tile)
                    if mask.count() > tile_size * tile_size * 0.3:
                        return tile
                else:
                    arr = pygame.surfarray.array3d(tile)
                    if arr.mean() > 25:
                        return tile
            except Exception:
                pass
            max_search -= 1
            if max_search <= 0:
                break
    # 找不到有效瓦片，返回起始位置
    if start_x + tile_size <= w and start_y + tile_size <= h:
        return tileset.subsurface((start_x, start_y, tile_size, tile_size)).copy()
    return None


def load_character(scale=(40, 60)):
    """加载玩家角色（Hero.png 第一帧），缩放到角色大小"""
    sprite = load_image(CHARACTER_SPRITE)
    if sprite is None:
        return None
    frame = sprite.subsurface((0, 0, 32, 32)).copy()
    if scale:
        frame = pygame.transform.scale(frame, scale)
    return frame


def load_enemy_sprite(scale=(32, 32)):
    """加载敌人精灵（Enemy.png 第一帧），缩放到敌人大小"""
    sprite = load_image(ENEMY_SPRITE)
    if sprite is None:
        return None
    frame = sprite.subsurface((0, 0, 32, 32)).copy()
    if scale:
        frame = pygame.transform.scale(frame, scale)
    return frame
