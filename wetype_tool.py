#!/usr/bin/env python3
"""
微信输入法快捷短语（热词）读写工具

由于 MMKV 是二进制格式，这个工具通过以下方式工作：
1. 读取：使用 strings 命令提取 JSON 数据
2. 写入：通过中间 JSON 文件，配合微信输入法的导入功能

使用方法：
    python3 wetype_tool.py export              # 导出快捷短语到 JSON
    python3 wetype_tool.py export -o out.json  # 导出到指定文件
    python3 wetype_tool.py list                # 列出所有快捷短语
    python3 wetype_tool.py search <关键词>      # 搜索快捷短语
    python3 wetype_tool.py add <key> <text>    # 添加新短语（需要手动导入）
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 微信输入法数据路径
WETYPE_MMKV_PATH = os.path.expanduser("~/Library/Application Support/WeType/mmkv/wetype.settings")
DEFAULT_EXPORT_PATH = os.path.expanduser("~/Desktop/wetype_hotwords.json")

def read_hotwords_raw():
    """从 MMKV 文件读取原始热词数据"""
    if not os.path.exists(WETYPE_MMKV_PATH):
        print(f"❌ 找不到微信输入法数据文件: {WETYPE_MMKV_PATH}")
        return None
    
    # 使用 strings 命令提取文本
    result = subprocess.run(
        ["strings", WETYPE_MMKV_PATH],
        capture_output=True,
        text=True
    )
    
    content = result.stdout
    
    # 查找 hotWordList 后面的 JSON 数组
    # 尝试多种模式匹配
    patterns = [
        r'hotWordList\n(\[.*?\])\n',  # 标准格式
        r'hotWordList(\[.*?\])(?=\n|clipboardTempList)',  # 紧凑格式
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        for match in matches:
            try:
                # 尝试解析 JSON
                data = json.loads(match)
                if isinstance(data, list) and len(data) > 0:
                    return data
            except json.JSONDecodeError:
                continue
    
    # 如果上述方法失败，尝试更激进的方法
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line == 'hotWordList' and i + 1 < len(lines):
            next_line = lines[i + 1]
            if next_line.startswith('['):
                # 可能是多行 JSON，需要拼接
                json_str = next_line
                j = i + 2
                while j < len(lines) and not json_str.rstrip().endswith(']'):
                    json_str += lines[j]
                    j += 1
                try:
                    data = json.loads(json_str)
                    if isinstance(data, list):
                        return data
                except:
                    pass
    
    return None

def parse_hotwords(raw_data):
    """解析热词数据为更友好的格式"""
    if not raw_data:
        return []
    
    hotwords = []
    for item in raw_data:
        hw = {
            "id": item.get("hw_id", ""),
            "key": item.get("key", ""),
            "text": item.get("text", ""),
            "timestamp": item.get("timestamp", 0),
        }
        # 清理文本
        hw["key"] = hw["key"].strip() if hw["key"] else ""
        hw["text_preview"] = hw["text"][:100] + "..." if len(hw["text"]) > 100 else hw["text"]
        hotwords.append(hw)
    
    return hotwords

def export_hotwords(output_path=None):
    """导出快捷短语到 JSON 文件"""
    raw_data = read_hotwords_raw()
    if not raw_data:
        print("❌ 无法读取热词数据")
        return False
    
    hotwords = parse_hotwords(raw_data)
    output_path = output_path or DEFAULT_EXPORT_PATH
    
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "count": len(hotwords),
        "source": WETYPE_MMKV_PATH,
        "hotwords": hotwords
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已导出 {len(hotwords)} 条快捷短语到: {output_path}")
    return True

def list_hotwords():
    """列出所有快捷短语"""
    raw_data = read_hotwords_raw()
    if not raw_data:
        print("❌ 无法读取热词数据")
        return
    
    hotwords = parse_hotwords(raw_data)
    
    print(f"\n📝 微信输入法快捷短语 (共 {len(hotwords)} 条)")
    print("=" * 60)
    
    for i, hw in enumerate(hotwords, 1):
        key_display = hw['key'] if hw['key'] else "(无触发词)"
        text_preview = hw['text_preview'].replace('\n', '\\n')
        print(f"\n{i}. 触发词: {key_display}")
        print(f"   内容: {text_preview}")

def search_hotwords(keyword):
    """搜索快捷短语"""
    raw_data = read_hotwords_raw()
    if not raw_data:
        print("❌ 无法读取热词数据")
        return
    
    hotwords = parse_hotwords(raw_data)
    results = []
    
    for hw in hotwords:
        if keyword.lower() in hw['key'].lower() or keyword.lower() in hw['text'].lower():
            results.append(hw)
    
    if not results:
        print(f"❌ 未找到包含 '{keyword}' 的快捷短语")
        return
    
    print(f"\n🔍 搜索结果: '{keyword}' (共 {len(results)} 条)")
    print("=" * 60)
    
    for i, hw in enumerate(results, 1):
        key_display = hw['key'] if hw['key'] else "(无触发词)"
        text_preview = hw['text_preview'].replace('\n', '\\n')
        print(f"\n{i}. 触发词: {key_display}")
        print(f"   内容: {text_preview}")

def get_hotwords_json():
    """获取热词数据的 JSON 字符串（供 AI 读取）"""
    raw_data = read_hotwords_raw()
    if not raw_data:
        return json.dumps({"error": "无法读取热词数据"}, ensure_ascii=False)
    
    hotwords = parse_hotwords(raw_data)
    return json.dumps(hotwords, ensure_ascii=False, indent=2)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "export":
        output_path = None
        if len(sys.argv) >= 4 and sys.argv[2] == "-o":
            output_path = sys.argv[3]
        export_hotwords(output_path)
    
    elif command == "list":
        list_hotwords()
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("用法: python3 wetype_tool.py search <关键词>")
            return
        search_hotwords(sys.argv[2])
    
    elif command == "json":
        # 直接输出 JSON，供 AI 读取
        print(get_hotwords_json())
    
    elif command == "help":
        print(__doc__)
    
    else:
        print(f"❌ 未知命令: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()






