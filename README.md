# 微信输入法快捷短语工具 🎉

**已实现完整的读写功能！**

让 AI（Cursor/Claude）可以读取和修改你的微信输入法快捷短语。

## 🚀 快速使用

```bash
cd /Users/ruicheng.gu/Documents/SLS/slspersonaldocs/07_tools/wetype-hotwords

# 列出所有快捷短语
python3 wetype_raw.py list

# 搜索
python3 wetype_raw.py search "关键词"

# 添加新短语
python3 wetype_raw.py add "触发词" "展开的内容"

# 删除短语
python3 wetype_raw.py delete "触发词"

# 导出到 JSON
python3 wetype_raw.py export backup.json

# 输出 JSON（供 AI 读取）
python3 wetype_raw.py json
```

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `wetype_raw.py` | **主工具** - 支持读写的版本 |
| `wetype_tool.py` | 旧版只读工具（使用 strings 命令） |
| `MMKV/` | 腾讯 MMKV 源码及编译后的 Python 绑定 |

## 🔧 技术实现

1. **读取**：直接解析 MMKV 二进制文件，提取 `hotWordList` JSON 数据
2. **写入**：使用编译好的 MMKV Python 绑定写入数据

### 数据位置
```
~/Library/Application Support/WeType/mmkv/wetype.settings
```

### 依赖
- Python 3.9+
- 编译好的 MMKV Python 模块（已包含在 `MMKV/Python/build/` 目录）

## 🤖 AI 集成示例

让 AI 帮你管理快捷短语：

```
用户：帮我添加一个快捷短语，输入"thx"展开为"感谢您的反馈，我会尽快处理。"

AI 执行：
python3 wetype_raw.py add "thx" "感谢您的反馈，我会尽快处理。"
```

```
用户：搜索所有和"文档"相关的快捷短语

AI 执行：
python3 wetype_raw.py search "文档"
```

## ⚠️ 注意事项

1. **增删改操作会自动重启微信输入法**，无需手动操作 ✨
2. 建议定期备份：`python3 wetype_raw.py export backup_$(date +%Y%m%d).json`
3. 微信输入法的设备同步可能会覆盖本地修改
4. 如果自动重启失败，可以手动在系统偏好设置中切换一下输入法

## 🔨 重新编译 MMKV（如需要）

如果 MMKV 模块出问题，可以重新编译：

```bash
cd MMKV/Python
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j8
```

需要安装 CMake：`brew install cmake`






