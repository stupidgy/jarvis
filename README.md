# 日历清单型桌宠（MVP 可执行程序）

这是一个基于 **Python + SQLite** 的可执行 MVP，覆盖你需求中的核心流程：

- 日历任务录入与查询。
- 每日晚间复盘记录。
- 复杂目标的 Agent 拆分提案（L1：先提案，确认后写入）。

> 说明：当前已提供 Tkinter 图形界面（GUI）+ CLI，便于快速体验完整流程。

## 1. 快速开始

```bash
python3 main.py init-db
```

## 2. 常用命令

### 启动图形界面
```bash
python3 main.py gui
```

> 任务列表支持双击任务直接切换完成/待办状态，减少按钮操作。


### 添加任务
```bash
python3 main.py add-task --date 2026-03-05 --title "完成实验图表" --priority high --estimate 120 --tags "论文,答辩"
```

### 查询日期范围任务
```bash
python3 main.py list-tasks --start 2026-03-01 --end 2026-03-10
```

### 保存晚间复盘
```bash
python3 main.py save-review --date 2026-03-04 \
  --done "完成了答辩PPT初稿" \
  --blockers "数据图排版耗时超预期" \
  --tomorrow "完成讲稿并进行一次彩排"
```

### 生成复杂目标拆分提案（L1）
```bash
python3 main.py propose-plan --goal "我要在 4 周内完成毕业答辩准备" --horizon 28 --strategy balanced > plan.json
```

### 审阅 plan.json 后再执行写入
```bash
python3 main.py apply-plan --file plan.json
```

## 3. 数据模型

- `Task(id, title, date, priority, estimate_min, status, parent_task_id)`
- `Plan(id, goal_text, horizon_days, strategy, created_at)`
- `PlanItem(id, plan_id, task_id, milestone, confidence)`
- `Review(id, date, done_summary, blockers, tomorrow_focus)`
- `ReminderRule(id, type, time, enabled, quiet_hours)`

## 4. MVP 能力边界

- 默认运行在 **L1 建议层**：`propose-plan` 只输出 JSON，不会直接修改任务。
- 用户显式执行 `apply-plan` 后，才会落库。
