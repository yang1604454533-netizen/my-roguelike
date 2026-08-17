# 🎮 肉鸽游戏 (My Roguelike)

一款使用 **Python + Pygame** 开发的 2D 俯视角肉鸽生存射击游戏。无限地图、自动攻击、十二生肖召唤、AI 敌人嘲讽——在无尽的敌人浪潮中不断变强，挑战你的极限。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

---

## ✨ 核心玩法

- 🗺️ **无限地图** — 永不遇到边界，8 种随机场景（草原/沙漠/雪地/地牢/熔岩/水域/墓地/星空）
- 🔫 **自动攻击** — 角色自动锁定最近敌人射击，支持穿透、弹射、爆炸、击退、吸血
- 📈 **肉鸽成长** — 击杀敌人升级，从 16+ 种属性中三选一，构筑独特 Build
- 🐉 **十二生肖召唤** — 召唤 12 生肖助战，射击型与近战型各 6 种
- 💬 **AI 敌人嘲讽** — 敌人会实时嘲讽你（本地大模型生成，中文气泡）
- 👹 **多样敌人** — 普通/精英/特殊（5种）/弓箭手，随时间变强
- ⚡ **冲刺与暴击** — 双击方向键冲刺，暴击伤害随数值自适应放大

## 🎮 操作说明

| 按键 | 功能 |
|------|------|
| `W A S D` | 移动 |
| 双击方向键 | 冲刺 |
| `F1` | 打开 GM 面板 |
| `F2` | 切换自动攻击 |
| `F5` | 快速存档 |
| `G` | 切换游戏速度（1-10倍） |
| `ESC` | 返回菜单 |

## 🚀 快速开始

### 从源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/yang1604454533-netizen/my-roguelike.git
cd my-roguelike

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

## 📁 项目结构

```
my-roguelike/
├── main.py              # 游戏入口
├── game.py              # 游戏主控制（状态机）
├── game_scene.py        # 游戏场景（无限地图/相机/升级）
├── combat_system.py     # 战斗系统（敌人/子弹/召唤）
├── menu.py              # 主菜单
├── settings_scene.py    # 设置界面
├── settings.py          # 全局配置
├── config_loader.py     # Excel 配置加载
├── assets_manager.py    # 素材加载
├── ai_assistant.py      # AI 接口（嘲讽/推荐）
├── fonts.py             # 中文字体
├── zodiac_pixels.py     # 十二生肖像素图
├── assets/              # 游戏素材
├── config.xlsx          # 可调配置（本地，不入库）
├── requirements.txt     # 依赖清单
└── pyproject.toml       # 项目配置
```

## ⚙️ 配置说明

游戏数值可通过 **config.xlsx** 调整（本地文件，已加入 .gitignore）：
- 角色表 / 敌人表 / 召唤表 / 升级项表 / 战斗表 / AI设置表 / 通用表

修改保存后重启游戏即可生效。

## 🎯 已实现系统

- [x] 无限地图 + 8 种素材场景
- [x] 自动攻击 + 16 种升级属性
- [x] 十二生肖召唤（射击/近战）
- [x] 敌人 AI（嘲讽/躲避子弹）
- [x] 精英怪/特殊敌人/弓箭手
- [x] 游戏速度 1-10 倍
- [x] Excel 配置系统
- [x] 存档/读档
- [x] 伤害跳字（暴击自适应字号）

## 📊 开发统计

- **开发时长**：约 471 分钟（≈ 7.9 小时，AI 驱动持续迭代）
- **Token 消耗**：累计 1,016,598,758 token（约 10.2 亿，含对话输入 + 代码生成输出）
- **代码量**：13 个 Python 模块，约 5000+ 行
- **AI 辅助**：对话式 AI 驱动开发，从零到完整可玩

## 📝 许可证

本项目采用 [MIT License](LICENSE)。游戏素材来自 [Kenney](https://kenney.nl) 和 [OpenGameArt](https://opengameart.org)（CC0 免费可商用）。

## 🙏 致谢

- [Pygame](https://www.pygame.org) — 游戏引擎
- [Kenney](https://kenney.nl) — CC0 游戏素材
- [OpenGameArt](https://opengameart.org) — CC0 游戏素材

---

⭐ 如果喜欢这个项目，欢迎给个 Star！
