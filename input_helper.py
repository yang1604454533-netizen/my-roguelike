"""
肉鸽游戏 - 输入辅助
解决中文输入法(IME)下 WASD 无反应的问题：
1. 用 GetAsyncKeyState 直接读取物理按键状态（IME 无法拦截硬件状态）
2. 游戏窗口激活时自动关闭 IME
"""
import ctypes
import pygame

# 部分 pygame 按键常量 → Windows 虚拟键码(VK) 映射
_VK_MAP = {
    pygame.K_UP: 0x26, pygame.K_DOWN: 0x28, pygame.K_LEFT: 0x25, pygame.K_RIGHT: 0x27,
    pygame.K_SPACE: 0x20, pygame.K_ESCAPE: 0x1B, pygame.K_RETURN: 0x0D, pygame.K_TAB: 0x09,
    pygame.K_LSHIFT: 0xA0, pygame.K_RSHIFT: 0xA1, pygame.K_LCTRL: 0xA2, pygame.K_RCTRL: 0xA3,
    pygame.K_LALT: 0xA4, pygame.K_RALT: 0xA5, pygame.K_BACKSPACE: 0x08, pygame.K_DELETE: 0x2E,
    pygame.K_F1: 0x70, pygame.K_F2: 0x71, pygame.K_F3: 0x72, pygame.K_F4: 0x73,
    pygame.K_F5: 0x74, pygame.K_F6: 0x75, pygame.K_F7: 0x76, pygame.K_F8: 0x77,
    pygame.K_F9: 0x78, pygame.K_F10: 0x79, pygame.K_F11: 0x7A, pygame.K_F12: 0x7B,
}


def pygame_key_to_vk(key):
    """
    将 pygame 按键常量转为 Windows 虚拟键码(VK)
    - 字母键：pygame 用小写 ASCII(97-122)，Windows VK 用大写 ASCII(65-90)
    - 数字键：两者一致
    - 其他键查映射表
    返回 None 表示无法映射
    """
    # 字母键 a-z
    if pygame.K_a <= key <= pygame.K_z:
        return key - 32  # 小写 ASCII → 大写 ASCII(VK)
    # 大写字母 A-Z（用户可能绑定大写）
    if 65 <= key <= 90:
        return key
    # 数字键 0-9（主键盘）
    if pygame.K_0 <= key <= pygame.K_9:
        return key
    # 其他按键查表
    return _VK_MAP.get(key, None)


def is_physical_key_down(key):
    """
    用 GetAsyncKeyState 检查物理按键是否被按下
    不受中文输入法拦截影响
    """
    vk = pygame_key_to_vk(key)
    if vk is None:
        return False
    try:
        # 最高位为 1 表示当前按下
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
    except Exception:
        return False


def disable_ime():
    """关闭当前游戏窗口的中文输入法(IME)"""
    try:
        hwnd = pygame.display.get_wm_info().get("window")
        if not hwnd:
            return
        user32 = ctypes.windll.user32
        imm32 = ctypes.windll.imm32
        h_imc = imm32.ImmGetContext(hwnd)
        if h_imc:
            imm32.ImmSetOpenStatus(h_imc, False)  # 关闭 IME 输入
            imm32.ImmReleaseContext(hwnd, h_imc)
    except Exception:
        pass  # IME 关闭失败不影响游戏
