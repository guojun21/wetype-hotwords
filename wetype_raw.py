#!/usr/bin/env python3
"""
微信输入法快捷短语工具 - 直接解析 MMKV 原始数据

由于 MMKV 的 append-only 特性，同一个 key 可能有多个历史版本。
这个脚本直接解析原始二进制文件，找到 hotWordList 的所有版本。

使用方法：
    python3 wetype_raw.py list                 # 列出所有快捷短语
    python3 wetype_raw.py export <file.json>   # 导出到 JSON
    python3 wetype_raw.py search <关键词>       # 搜索
    python3 wetype_raw.py add <触发词> <内容>   # 添加（自动重启输入法）
    python3 wetype_raw.py delete <触发词>        # 删除（自动重启输入法）
"""

import sys
import os
import json
import re
import time
import subprocess

# 添加 MMKV 模块路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MMKV_BUILD_DIR = os.path.join(SCRIPT_DIR, "MMKV", "Python", "build")
sys.path.insert(0, MMKV_BUILD_DIR)

# 微信输入法路径
WETYPE_SETTINGS_FILE = os.path.expanduser("~/Library/Application Support/WeType/mmkv/wetype.settings")
WETYPE_MMKV_DIR = os.path.expanduser("~/Library/Application Support/WeType/mmkv")

def read_raw_hotwords():
    """直接从原始文件读取 hotWordList"""
    with open(WETYPE_SETTINGS_FILE, 'rb') as f:
        data = f.read()
    
    # 转换为字符串查找 JSON
    text = data.decode('utf-8', errors='ignore')
    
    # 查找所有 hotWordList 后面的 JSON 数组
    # 格式：hotWordList + 一些分隔符 + JSON 数组
    pattern = r'hotWordList.{0,10}(\[.*?\])\s*(?=\w|$)'
    
    all_hotwords = []
    
    # 找到所有 hotWordList 出现的位置
    hotword_positions = [m.start() for m in re.finditer(r'hotWordList', text)]
    
    for pos in hotword_positions:
        # 从这个位置开始，寻找 JSON 数组
        search_start = pos + len('hotWordList')
        remaining = text[search_start:search_start + 100000]  # 最多搜索 100KB
        
        # 找到第一个 [ 
        bracket_start = remaining.find('[')
        if bracket_start == -1:
            continue
        
        # 尝试找到匹配的 ]
        json_start = bracket_start
        bracket_count = 0
        json_end = -1
        
        for i, c in enumerate(remaining[json_start:]):
            if c == '[':
                bracket_count += 1
            elif c == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    json_end = json_start + i + 1
                    break
        
        if json_end == -1:
            continue
        
        json_str = remaining[json_start:json_end]
        
        try:
            hotwords = json.loads(json_str)
            if isinstance(hotwords, list) and len(hotwords) > 0:
                # 检查是否是有效的热词格式
                if isinstance(hotwords[0], dict) and ('hw_id' in hotwords[0] or 'key' in hotwords[0] or 'text' in hotwords[0]):
                    all_hotwords.append(hotwords)
        except json.JSONDecodeError:
            pass
    
    # 返回最长的那个（最完整的）
    if all_hotwords:
        return max(all_hotwords, key=len)
    return []

def get_mmkv_kv():
    """获取 MMKV 实例"""
    import mmkv
    mmkv.MMKV.initializeMMKV(WETYPE_MMKV_DIR)
    return mmkv.MMKV("wetype.settings")

def restart_wetype():
    """重启微信输入法"""
    try:
        # 杀掉微信输入法进程，系统会自动重启
        result = subprocess.run(
            ["killall", "WeType"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("🔄 微信输入法已重启")
            time.sleep(1)  # 等待一下让进程完全重启
            return True
        else:
            # killall 返回非0可能是进程不存在，也算成功
            print("🔄 微信输入法进程已处理")
            return True
    except subprocess.TimeoutExpired:
        print("⚠️  重启超时，但应该已经完成")
        return True
    except Exception as e:
        print(f"⚠️  重启微信输入法时出错: {e}")
        print("   你可以手动在系统偏好设置中切换一下输入法")
        return False

def list_hotwords():
    """列出所有热词"""
    hotwords = read_raw_hotwords()
    
    if not hotwords:
        print("❌ 未找到热词数据")
        return
    
    print(f"\n📝 微信输入法快捷短语 (共 {len(hotwords)} 条)")
    print("=" * 60)
    
    for i, hw in enumerate(hotwords, 1):
        key = hw.get("key", "").strip() if hw.get("key") else "(无触发词)"
        text = hw.get("text", "")
        text_preview = text[:80].replace('\n', '\\n') + ("..." if len(text) > 80 else "")
        print(f"\n{i}. 触发词: {key}")
        print(f"   内容: {text_preview}")

def export_hotwords(output_file):
    """导出热词到 JSON"""
    hotwords = read_raw_hotwords()
    
    if not hotwords:
        print("❌ 未找到热词数据")
        return
    
    export_data = {
        "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(hotwords),
        "hotwords": hotwords
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已导出 {len(hotwords)} 条热词到: {output_file}")

def search_hotwords(keyword):
    """搜索热词"""
    hotwords = read_raw_hotwords()
    
    if not hotwords:
        print("❌ 未找到热词数据")
        return
    
    results = []
    for hw in hotwords:
        key = hw.get("key", "")
        text = hw.get("text", "")
        if keyword.lower() in key.lower() or keyword.lower() in text.lower():
            results.append(hw)
    
    if not results:
        print(f"❌ 未找到包含 '{keyword}' 的热词")
        return
    
    print(f"\n🔍 搜索结果: '{keyword}' (共 {len(results)} 条)")
    print("=" * 60)
    
    for i, hw in enumerate(results, 1):
        key = hw.get("key", "").strip() if hw.get("key") else "(无触发词)"
        text = hw.get("text", "")
        text_preview = text[:80].replace('\n', '\\n') + ("..." if len(text) > 80 else "")
        print(f"\n{i}. 触发词: {key}")
        print(f"   内容: {text_preview}")

def add_hotword(trigger_key, text):
    """添加热词 - 通过 MMKV API"""
    import mmkv
    
    # 读取当前热词
    hotwords = read_raw_hotwords()
    
    # 创建新热词
    new_id = str(int(time.time() * 1000))
    new_hotword = {
        "hw_id": new_id,
        "key": trigger_key,
        "text": text
    }
    
    # 添加到开头
    hotwords.insert(0, new_hotword)
    
    # 写入
    mmkv.MMKV.initializeMMKV(WETYPE_MMKV_DIR)
    kv = mmkv.MMKV("wetype.settings")
    
    hotwords_json = json.dumps(hotwords, ensure_ascii=False)
    kv.set(hotwords_json, "hotWordList")
    
    print(f"✅ 已添加热词: {trigger_key}")
    print(f"   内容: {text[:50]}...")
    
    # 自动重启微信输入法
    restart_wetype()

def delete_hotword(trigger_key):
    """删除热词"""
    import mmkv
    
    hotwords = read_raw_hotwords()
    original_count = len(hotwords)
    
    # 过滤掉要删除的
    hotwords = [hw for hw in hotwords if hw.get("key", "").strip() != trigger_key]
    
    if len(hotwords) == original_count:
        print(f"❌ 未找到触发词为 '{trigger_key}' 的热词")
        return
    
    # 写入
    mmkv.MMKV.initializeMMKV(WETYPE_MMKV_DIR)
    kv = mmkv.MMKV("wetype.settings")
    
    hotwords_json = json.dumps(hotwords, ensure_ascii=False)
    kv.set(hotwords_json, "hotWordList")
    
    deleted_count = original_count - len(hotwords)
    print(f"✅ 已删除 {deleted_count} 条热词")
    
    # 自动重启微信输入法
    restart_wetype()

def get_hotwords_json():
    """返回 JSON 格式的热词（供 AI 读取）"""
    hotwords = read_raw_hotwords()
    return json.dumps(hotwords, ensure_ascii=False, indent=2)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "list":
        list_hotwords()
    elif cmd == "export":
        if len(sys.argv) < 3:
            print("用法: python3 wetype_raw.py export <file.json>")
            return
        export_hotwords(sys.argv[2])
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("用法: python3 wetype_raw.py search <关键词>")
            return
        search_hotwords(sys.argv[2])
    elif cmd == "add":
        if len(sys.argv) < 4:
            print("用法: python3 wetype_raw.py add <触发词> <内容>")
            return
        add_hotword(sys.argv[2], sys.argv[3])
    elif cmd == "delete":
        if len(sys.argv) < 3:
            print("用法: python3 wetype_raw.py delete <触发词>")
            return
        delete_hotword(sys.argv[2])
    elif cmd == "json":
        print(get_hotwords_json())
    else:
        print(f"❌ 未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()






