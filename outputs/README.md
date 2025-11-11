# OASIS 输出文件目录

本目录存储所有运行时生成的文件，包括日志、数据库和实验结果。

## 📂 目录结构

```
outputs/
├── logs/                   # 日志文件（按类型和日期归档）
│   ├── oasis/              # OASIS 系统日志
│   │   └── 2025-11/        # 按月归档
│   └── watermark/          # 水印日志
│       └── 2025-11/
│
├── databases/              # 数据库文件
│   ├── current/            # 当前实验数据库
│   └── archive/            # 历史数据库归档
│       └── 2025-11/
│
└── experiments/            # 实验结果归档
    └── 2025-11-11_exp1/    # 按日期和名称组织
```

## 📋 文件说明

### logs/ - 日志文件

#### OASIS 系统日志
- `oasis-*.log` - 主系统日志
- `social.agent-*.log` - Agent 行为日志
- `social.twitter-*.log` - Twitter 平台日志
- `table-*.log` - 数据库表操作日志

#### 水印日志
- `watermark-agent{N}-*.log` - 每个 Agent 的独立水印日志
- `watermark-*.log` - 共享水印管理器日志（旧模式）

### databases/ - 数据库文件

#### current/
- `simulation.db` - 当前运行的模拟数据库

#### archive/
- 按月份存储历史数据库
- 命名格式：`{实验名}_{日期}.db`

### experiments/ - 实验归档

每个实验目录包含：
- `metadata.json` - 实验元数据
- `simulation.db` - 数据库快照
- `config.json` - 使用的配置
- `results.md` - 结果报告

## 🔄 自动清理

### 清理旧日志（7天前）

```bash
python scripts/cleanup.py
```

### 手动清理

```powershell
# 清理所有日志
Remove-Item outputs/logs/**/*.log

# 清理归档数据库
Remove-Item outputs/databases/archive/**/*.db

# 保留最近的实验
Get-ChildItem outputs/experiments -Directory | 
    Where-Object {$_.CreationTime -lt (Get-Date).AddDays(-30)} | 
    Remove-Item -Recurse
```

## 📊 查看文件

### 查看最新日志

```bash
# OASIS 系统日志
ls -t outputs/logs/oasis/2025-11/*.log | head -1

# 水印日志
ls -t outputs/logs/watermark/2025-11/*.log | head -1
```

### 查看数据库

```python
import sqlite3
conn = sqlite3.connect('outputs/databases/current/simulation.db')
cursor = conn.cursor()

# 查看表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cursor.fetchall())
```

### 分析日志

```python
# 统计水印嵌入成功率
with open('outputs/logs/watermark/2025-11/watermark-agent0-*.log', 'r') as f:
    lines = f.readlines()
    success = sum(1 for line in lines if 'success' in line.lower())
    total = len(lines)
    print(f"成功率: {success/total*100:.2f}%")
```

## 📁 归档实验

### 自动归档

运行实验后自动归档：

```bash
python scripts/archive_experiment.py
```

### 手动归档

```bash
# 创建归档目录
mkdir outputs/experiments/2025-11-11_my_experiment

# 复制文件
cp outputs/databases/current/simulation.db outputs/experiments/2025-11-11_my_experiment/
cp config.json outputs/experiments/2025-11-11_my_experiment/

# 创建元数据
echo '{"date": "2025-11-11", "agents": 5, "rounds": 10}' > outputs/experiments/2025-11-11_my_experiment/metadata.json
```

## 🚫 .gitignore

本目录的所有输出文件都在 `.gitignore` 中：

```gitignore
outputs/logs/**/*.log
outputs/databases/**/*.db
outputs/experiments/**/
```

只有目录结构和 README 会被提交到 Git。

## 💡 最佳实践

### 1. 定期清理日志

```bash
# 每周运行一次
python scripts/cleanup.py --days 7
```

### 2. 重要实验及时归档

```bash
# 完成实验后立即归档
python scripts/archive_experiment.py --name "important_exp"
```

### 3. 数据库备份

```bash
# 备份当前数据库
cp outputs/databases/current/simulation.db \
   outputs/databases/archive/2025-11/backup_$(date +%Y%m%d).db
```

### 4. 日志分析

使用 `scripts/analyze_logs.py` 进行批量分析：

```bash
python scripts/analyze_logs.py --dir outputs/logs/watermark/2025-11
```

## 📈 磁盘空间管理

### 查看占用

```bash
du -sh outputs/*
```

### 预期大小

| 内容 | 单次运行 | 累计（1周） | 累计（1月） |
|------|----------|-------------|-------------|
| 日志 | ~5 MB | ~100 MB | ~400 MB |
| 数据库 | ~10 MB | ~200 MB | ~800 MB |
| 实验归档 | ~15 MB | ~300 MB | ~1.2 GB |
| **总计** | **~30 MB** | **~600 MB** | **~2.4 GB** |

### 清理建议

- 日志：保留最近 7 天
- 数据库：保留最近 30 天
- 实验归档：永久保留重要实验

## 🔗 相关脚本

- `scripts/cleanup.py` - 自动清理工具
- `scripts/archive_experiment.py` - 实验归档工具
- `scripts/analyze_logs.py` - 日志分析工具

## ❓ 常见问题

### Q: 日志文件太多怎么办？
**A**: 运行 `python scripts/cleanup.py --days 7` 清理 7 天前的日志。

### Q: 如何找到特定实验的日志？
**A**: 查看 `outputs/experiments/{实验名}/metadata.json` 中的日志路径。

### Q: 数据库文件损坏怎么办？
**A**: 从 `outputs/databases/archive/` 恢复最近的备份。

### Q: 如何压缩归档文件？
**A**: 
```bash
tar -czf outputs/experiments/archive_2025-11.tar.gz outputs/experiments/2025-11-*
```
