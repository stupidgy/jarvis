# 日历清单型桌宠（可执行 GUI 版本）

这是一个可直接使用的桌面程序（**Tkinter 图形界面 + SQLite 本地存储**），覆盖需求中的 MVP 核心流程：

- 日历清单：按日期新增任务、查看任务、标记完成、改期。
- 晚间复盘：填写并保存“完成/阻塞/明日重点”。
- 复杂目标拆分（L1）：先生成 Agent 提案 JSON，确认后再写入任务。

## 1. 启动方式

直接启动图形界面（推荐）：

```bash
python3 main.py
```

或显式启动：

```bash
python3 main.py gui
```

## 2. 图形界面功能

### 任务日历清单
- 输入日期、标题、优先级、预计时长、标签，一键新增任务。
- 按日期区间查询任务。
- 选中任务后可：
  - 标记为完成。
  - 改期到指定日期（状态自动标记为 `delayed`）。

### 晚间复盘
- 模板包含三项：
  1. 今天完成了什么
  2. 未完成原因
  3. 明天最重要 1~3 件事
- 一键保存到本地数据库。

### 复杂目标拆分（L1）
- 输入复杂目标（例如“4周毕业答辩准备”）生成结构化提案。
- 可在文本框中手动调整 JSON。
- 点击“确认并写入任务”后才真正入库。

## 3. CLI 仍可用（便于脚本化）

```bash
python3 main.py init-db
python3 main.py add-task --date 2026-03-05 --title "完成实验图表" --priority high --estimate 120 --tags "论文,答辩"
python3 main.py list-tasks --start 2026-03-01 --end 2026-03-10
python3 main.py save-review --date 2026-03-04 --done "完成PPT初稿" --blockers "排版慢" --tomorrow "完成讲稿+彩排"
python3 main.py propose-plan --goal "我要在 4 周内完成毕业答辩准备" --horizon 28 --strategy balanced > plan.json
python3 main.py apply-plan --file plan.json
```

## 4. 数据模型

- `Task(id, title, date, priority, estimate_min, status, parent_task_id)`
- `Plan(id, goal_text, horizon_days, strategy, created_at)`
- `PlanItem(id, plan_id, task_id, milestone, confidence)`
- `Review(id, date, done_summary, blockers, tomorrow_focus)`
- `ReminderRule(id, type, time, enabled, quiet_hours)`

