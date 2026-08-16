"""
AI 助手 - 调用 OpenAI 兼容 API（本地部署）
功能：
1. 敌人嘲讽气泡（大模型生成嘲讽语）
2. 升级推荐（根据已选升级项推荐三选一）
使用后台线程避免卡游戏，带结果缓存。
"""
import json
import threading
import urllib.request
import urllib.error

# ===== 配置（可通过 config.xlsx 覆盖）=====
AI_API_URL = "http://192.168.5.16:20128/v1"
AI_API_KEY = "sk-b6f4d3879cc4a442-aroz1n-d4d3d242"
AI_MODEL = "ds/deepseek-v4-flash"
AI_ENABLED = True
AI_TIMEOUT = 20

# 缓存：避免重复请求
_taunt_cache = {}       # key -> 嘲讽语
_recommend_cache = {}   # key -> 推荐

# 后台线程队列
_request_queue = []
_queue_lock = threading.Lock()
_result_store = {}      # 请求 id -> 结果
_next_id = 0


def _call_api(messages, max_tokens=200):
    """调用 OpenAI 兼容 API，返回文本。失败返回 None"""
    import requests as _requests
    url = AI_API_URL.rstrip("/") + "/chat/completions"
    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.9,
    }
    try:
        resp = _requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {AI_API_KEY}"},
            timeout=AI_TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        raw = resp.content.decode("utf-8", errors="replace")
        # 健壮解析：提取第一个 { 到最后一个 } 之间的完整 JSON
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start:end + 1]
        import json as _json
        data = _json.loads(raw)
        content = data["choices"][0]["message"]["content"]
        return content.strip() if content else None
    except Exception as e:
        print(f"[AI] 请求失败: {e}")
        return None





def _worker():
    """后台线程：处理请求队列"""
    global _next_id
    while True:
        item = None
        with _queue_lock:
            if _request_queue:
                item = _request_queue.pop(0)
        if item is None:
            threading.Event().wait(0.1)
            continue
        req_id, kind, messages, max_tokens = item
        result = _call_api(messages, max_tokens)
        _result_store[req_id] = result


def _start_worker():
    """启动后台线程（懒启动）"""
    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def _enqueue(kind, messages, max_tokens=100):
    """入队异步请求，返回请求 id"""
    global _next_id
    if not AI_ENABLED:
        return None
    with _queue_lock:
        _next_id += 1
        req_id = _next_id
        _request_queue.append((req_id, kind, messages, max_tokens))
    return req_id


def _poll(req_id):
    """轮询结果，返回 None 表示未完成"""
    return _result_store.get(req_id)


# ========== 嘲讽气泡 ==========

def get_taunt_async(taunt_key, context=""):
    """
    异步获取敌人嘲讽语。
    返回请求 id（用于 poll），或返回缓存的文本。
    """
    if taunt_key in _taunt_cache:
        return _taunt_cache[taunt_key]
    if not AI_ENABLED:
        return "哼！"
    prompt = (
        "你是一个肉鸽游戏里的敌人，正在嘲讽玩家角色。"
        "根据情况用一句话嘲讽玩家，要求短小精悍（不超过15字），带点得意或挑衅。"
        f"当前情况：{context}。只输出嘲讽语本身，不要引号。"
    )
    req_id = _enqueue("taunt", [{"role": "user", "content": prompt}], 50)
    if req_id is None:
        return None
    # 同步等待（首次请求，简单处理）
    import time
    for _ in range(40):  # 最多等 4 秒
        result = _poll(req_id)
        if result is not None:
            _taunt_cache[taunt_key] = result
            return result
        time.sleep(0.1)
    return "哼！"


def get_taunt_sync(context=""):
    """同步获取嘲讽语（用于测试）"""
    if not AI_ENABLED:
        return "哼！"
    prompt = (
        "你是一个肉鸽游戏里的敌人，正在嘲讽玩家角色。"
        "根据情况用一句话嘲讽玩家，要求短小精悍（不超过15字），带点得意或挑衅。"
        f"当前情况：{context}。只输出嘲讽语本身，不要引号。"
    )
    return _call_api([{"role": "user", "content": prompt}], 50) or "哼！"


# ========== 升级推荐 ==========

def get_taunts_batch(count=12, used_texts=None):
    """同步获取一批嘲讽语（一次请求生成多条，用换行分隔）"""
    if not AI_ENABLED:
        return ["哼！"] * count
    used_hint = ""
    if used_texts:
        used_hint = f"之前用过：{','.join(list(used_texts)[-8:])}。不要重复这些。"
    prompt = (
        f"你是肉鸽游戏里的敌人，正在嘲讽玩家。请一次性生成{count}条不同的嘲讽语，"
        "每条**不超过10个字**，口语化、带挑衅语气。"
        f"{used_hint}"
        "用换行分隔每条，不要序号、不要引号、不要标点、不要解释。"
    )
    result = _call_api([{"role": "user", "content": prompt}], 400)
    if not result:
        return ["哼！"] * count
    lines = [l.strip() for l in result.split("\n") if l.strip()]
    # 去重 + 截断10字
    seen = set(used_texts or set())
    taunts = []
    for l in lines:
        l = l.replace("1.", "").replace("2.", "").replace("3.", "").strip()
        if len(l) > 10:
            l = l[:10]
        if l and l not in seen:
            taunts.append(l)
            seen.add(l)
        if len(taunts) >= count:
            break
    # 不足则补默认
    while len(taunts) < count:
        taunts.append("哼！")
    return taunts[:count]


def get_recommend_async(upgrades, descs, player_stats):
    """
    异步获取升级推荐。
    返回请求 id 或缓存的推荐索引。
    """
    key = tuple(upgrades)
    if key in _recommend_cache:
        return _recommend_cache[key]
    if not AI_ENABLED:
        return 0
    options = "\n".join(
        f"{i+1}. {upgrades[i]} - {descs[i]}" for i in range(len(upgrades))
    )
    stats = "，".join(f"{k}={v}" for k, v in player_stats.items())
    prompt = (
        "你是肉鸽游戏的升级顾问。玩家当前属性：" + stats + "。"
        "升级面板有三个选项：\n" + options + "\n"
        "请分析玩家现状，推荐最适合的一个。只输出数字 1/2/3，不要其他内容。"
    )
    req_id = _enqueue("recommend", [{"role": "user", "content": prompt}], 10)
    if req_id is None:
        return None
    import time
    for _ in range(40):
        result = _poll(req_id)
        if result is not None:
            try:
                idx = int(result.strip()) - 1
                if 0 <= idx < len(upgrades):
                    _recommend_cache[key] = idx
                    return idx
            except ValueError:
                pass
            _recommend_cache[key] = 0
            return 0
        time.sleep(0.1)
    return 0


def get_recommend_sync(upgrades, descs, player_stats):
    """同步获取升级推荐（测试用）"""
    if not AI_ENABLED:
        return 0
    options = "\n".join(
        f"{i+1}. {upgrades[i]} - {descs[i]}" for i in range(len(upgrades))
    )
    stats = "，".join(f"{k}={v}" for k, v in player_stats.items())
    prompt = (
        "你是肉鸽游戏的升级顾问。玩家当前属性：" + stats + "。"
        "升级面板有三个选项：\n" + options + "\n"
        "请分析玩家现状，推荐最适合的一个。只输出数字 1/2/3，不要其他内容。"
    )
    result = _call_api([{"role": "user", "content": prompt}], 10)
    try:
        idx = int(result.strip()) - 1
        if 0 <= idx < len(upgrades):
            return idx
    except (ValueError, AttributeError):
        pass
    return 0


def configure(url=None, key=None, model=None, enabled=None):
    """运行时配置（供 config.xlsx 覆盖）"""
    global AI_API_URL, AI_API_KEY, AI_MODEL, AI_ENABLED
    if url:
        AI_API_URL = url
    if key:
        AI_API_KEY = key
    if model:
        AI_MODEL = model
    if enabled is not None:
        AI_ENABLED = enabled


# ========== 后台预取机制（供游戏内非阻塞调用） ==========
_prefetch_queue = []
_prefetch_lock = threading.Lock()
_prefetch_results = {}      # key -> 文本


def _prefetch_worker():
    """后台线程：处理预取队列，结果存入 dict"""
    while True:
        item = None
        with _prefetch_lock:
            if _prefetch_queue:
                item = _prefetch_queue.pop(0)
        if item is None:
            threading.Event().wait(0.1)
            continue
        key, messages, max_tokens = item
        result = _call_api(messages, max_tokens)
        _prefetch_results[key] = result or "哼！"


def start_prefetch_worker():
    """启动后台预取线程（幂等）"""
    if not hasattr(start_prefetch_worker, "_started"):
        start_prefetch_worker._started = True
        t = threading.Thread(target=_prefetch_worker, daemon=True)
        t.start()


def request_taunt_prefetch(key, context="", used_texts=None):
    """请求后台生成嘲讽语（非阻塞），用 key 标识结果"""
    if not AI_ENABLED:
        _prefetch_results[key] = "哼！"
        return
    start_prefetch_worker()  # 确保 worker 存在（兼容旧代码）
    # 限制队列长度，避免堆积导致后台卡死
    with _prefetch_lock:
        if len(_prefetch_queue) >= 5:
            return  # 队列已满，跳过本次
    used_hint = ""
    if used_texts:
        used_hint = f"之前用过：{','.join(list(used_texts)[-8:])}。不要重复这些。"
    prompt = (
        "你是肉鸽游戏里的敌人，正在嘲讽玩家。"
        "直接输出一句嘲讽语，**必须不超过10个字**，带得意或挑衅语气，口语化。"
        f"当前情况：{context}。{used_hint}"
        "只输出那一句话，不要解释、不要引号、不要标点符号、不要列多个选项。"
    )
    # 异步起一个临时线程，避免阻塞主线程、避免队列堆积
    import threading
    def _worker(key, messages, max_tokens):
        try:
            result = _call_api(messages, max_tokens)
            _prefetch_results[key] = result or "哼！"
        except Exception:
            _prefetch_results[key] = "哼！"
    t = threading.Thread(target=_worker, args=(key, [{"role": "user", "content": prompt}], 200), daemon=True)
    t.start()



def get_prefetch_result(key):
    """获取预取结果，未完成返回 None"""
    return _prefetch_results.get(key)


# ========== 本地嘲讽语库（AI 池耗尽时兜底，永不枯竭） ==========
LOCAL_TAUNTS = [
    "你跑不掉的", "菜鸟别挣扎", "这都打不中我", "弱得可怜啊", "来啊别怂",
    "就这点本事", "我站着给你打", "怕了就投降", "你手抖什么", "废物别浪费",
    "残血还敢浪", "躲什么躲", "打不到我吧", "就这水平", "快回家吧",
    "你太慢了", "别浪费时间", "我还没出力", "就这伤害", "菜就多练",
    "过来送死", "你不行啊", "小菜一碟", "轻松拿捏", "别跑了认输",
    "就这操作", "手速太慢", "毫无压力", "你打不赢", "放弃吧少年",
    "再练练吧", "就这走位", "我无敌了", "你还差得远", "别挣扎了",
]

def get_local_taunts_pool():
    """返回本地嘲讽语库（打乱顺序）"""
    import random as _r
    pool = list(LOCAL_TAUNTS)
    _r.shuffle(pool)
    return pool
