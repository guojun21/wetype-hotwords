#!/usr/bin/env python3
"""
微信输入法快捷短语 读写工具 (使用 MMKV)

真正支持读写的版本！

使用方法：
    python3 wetype_rw.py list                      # 列出所有快捷短语
    python3 wetype_rw.py get <key>                 # 获取指定 key 的值
    python3 wetype_rw.py keys                      # 列出所有 keys
    python3 wetype_rw.py export <file.json>        # 导出热词到 JSON
    python3 wetype_rw.py import <file.json>        # 从 JSON 导入热词（会覆盖）
    python3 wetype_rw.py add <触发词> <内容>        # 添加一条快捷短语
    python3 wetype_rw.py delete <触发词>            # 删除一条快捷短语
"""

import sys
import os
import json
import time

# 添加 MMKV 模块路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MMKV_BUILD_DIR = os.path.join(SCRIPT_DIR, "MMKV", "Python", "build")
sys.path.insert(0, MMKV_BUILD_DIR)

import mmkv

# 微信输入法 MMKV 数据目录
WETYPE_MMKV_DIR = os.path.expanduser("~/Library/Application Support/WeType/mmkv")
WETYPE_MMKV_ID = "wetype.settings"

def get_wetype_kv():
    """获取微信输入法的 MMKV 实例"""
    # 初始化 MMKV，指定微信输入法的数据目录
    mmkv.MMKV.initializeMMKV(WETYPE_MMKV_DIR)
    kv = mmkv.MMKV(WETYPE_MMKV_ID)
    return kv

def list_all_keys():
    """列出所有 keys"""
    kv = get_wetype_kv()
    keys = kv.keys()
    print(f"\n📋 微信输入法 MMKV 所有 Keys ({len(keys)} 个):")
    print("=" * 60)
    for key in sorted(keys):
        print(f"  - {key}")
    return keys

def get_value(key):
    """获取指定 key 的值"""
    kv = get_wetype_kv()
    
    # 尝试不同类型
    val = kv.getString(key)
    if val:
        print(f"\n🔑 Key: {key}")
        print(f"📝 Value (string):\n{val}")
        return val
    
    val = kv.getBool(key)
    print(f"\n🔑 Key: {key}")
    print(f"📝 Value (bool): {val}")
    return val

def get_hotwords():
    """获取热词列表"""
    kv = get_wetype_kv()
    hotwords_json = kv.getString("hotWordList")
    if hotwords_json:
        try:
            return json.loads(hotwords_json)
        except json.JSONDecodeError:
            print("❌ 解析热词 JSON 失败")
            return []
    return []

def set_hotwords(hotwords):
    """设置热词列表"""
    kv = get_wetype_kv()
    hotwords_json = json.dumps(hotwords, ensure_ascii=False)
    kv.set(hotwords_json, "hotWordList")
    print("✅ 热词已保存！")
    print("⚠️  注意：可能需要重启微信输入法才能生效")

def list_hotwords():
    """列出所有热词"""
    hotwords = get_hotwords()
    print(f"\n📝 微信输入法快捷短语 (共 {len(hotwords)} 条)")
    print("=" * 60)
    
    for i, hw in enumerate(hotwords, 1):
        key = hw.get("key", "").strip() if hw.get("key") else "(无触发词)"
        text = hw.get("text", "")
        text_preview = text[:80].replace('\n', '\\n') + ("..." if len(text) > 80 else "")
        print(f"\n{i}. 触发词: {key}")
        print(f"   内容: {text_preview}")

def export_hotwords(output_file):
    """导出热词到 JSON 文件"""
    hotwords = get_hotwords()
    
    export_data = {
        "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(hotwords),
        "hotwords": hotwords
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已导出 {len(hotwords)} 条热词到: {output_file}")

def import_hotwords(input_file):
    """从 JSON 文件导入热词"""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if "hotwords" in data:
        hotwords = data["hotwords"]
    elif isinstance(data, list):
        hotwords = data
    else:
        print("❌ JSON 格式不正确")
        return
    
    set_hotwords(hotwords)
    print(f"✅ 已导入 {len(hotwords)} 条热词")

def add_hotword(key, text):
    """添加一条热词"""
    hotwords = get_hotwords()
    
    # 生成新的 hw_id
    new_id = str(int(time.time() * 1000))
    
    new_hotword = {
        "hw_id": new_id,
        "key": key,
        "text": text
    }
    
    # 添加到开头
    hotwords.insert(0, new_hotword)
    set_hotwords(hotwords)
    print(f"✅ 已添加热词: {key} -> {text[:50]}...")

def delete_hotword(key):
    """删除一条热词"""
    hotwords = get_hotwords()
    
    original_count = len(hotwords)
    hotwords = [hw for hw in hotwords if hw.get("key", "").strip() != key]
    
    if len(hotwords) == original_count:
        print(f"❌ 未找到触发词为 '{key}' 的热词")
        return
    
    deleted_count = original_count - len(hotwords)
    set_hotwords(hotwords)
    print(f"✅ 已删除 {deleted_count} 条热词")

def search_hotwords(keyword):
    """搜索热词"""
    hotwords = get_hotwords()
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

def print_help():
    print(__doc__)

def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_hotwords()
    
    elif command == "keys":
        list_all_keys()
    
    elif command == "get":
        if len(sys.argv) < 3:
            print("用法: python3 wetype_rw.py get <key>")
            return
        get_value(sys.argv[2])
    
    elif command == "export":
        if len(sys.argv) < 3:
            print("用法: python3 wetype_rw.py export <file.json>")
            return
        export_hotwords(sys.argv[2])
    
    elif command == "import":
        if len(sys.argv) < 3:
            print("用法: python3 wetype_rw.py import <file.json>")
            return
        import_hotwords(sys.argv[2])
    
    elif command == "add":
        if len(sys.argv) < 4:
            print("用法: python3 wetype_rw.py add <触发词> <内容>")
            return
        add_hotword(sys.argv[2], sys.argv[3])
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("用法: python3 wetype_rw.py delete <触发词>")
            return
        delete_hotword(sys.argv[2])
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("用法: python3 wetype_rw.py search <关键词>")
            return
        search_hotwords(sys.argv[2])
    
    elif command == "help":
        print_help()
    
    else:
        print(f"❌ 未知命令: {command}")
        print_help()

if __name__ == "__main__":
    main()






