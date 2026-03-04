import re
from datetime import date, timedelta


class AgentOrchestrator:
    """L1 mode: propose first, execute only after explicit apply."""

    def __init__(self, storage):
        self.storage = storage

    def propose_plan(self, goal_text, horizon_days=28, strategy="balanced", max_tasks_per_day=3):
        start = date.today()
        milestones = self._build_milestones(goal_text, start, horizon_days)
        task_templates = self._task_templates(goal_text)

        tasks = []
        day_cursor = 0
        for i, t in enumerate(task_templates):
            interval = 1 if strategy == "aggressive" else 2 if strategy == "balanced" else 3
            scheduled = start + timedelta(days=day_cursor)
            tasks.append(
                {
                    "temp_key": f"t{i+1}",
                    "title": t["title"],
                    "date": scheduled.isoformat(),
                    "estimate_min": t["estimate_min"],
                    "priority": t["priority"],
                    "depends_on": [f"t{i}"] if i > 0 else [],
                    "reason": t["reason"],
                }
            )
            if (i + 1) % max_tasks_per_day == 0:
                day_cursor += interval

        return {
            "goal": goal_text,
            "milestones": milestones,
            "tasks": tasks,
            "risks": [
                "计划可能过载：建议每天任务不超过 3 个。",
                "建议每周预留至少 1 天缓冲日处理突发情况。",
            ],
            "fallback_plan": [
                "若两天连续延期，自动把任务拆成 30 分钟颗粒度。",
                "状态不佳时，启动“3 分钟极速计划”只保留 1~3 个关键任务。",
            ],
        }

    def apply_plan(self, proposal):
        plan_id = self.storage.create_plan(
            goal_text=proposal["goal"],
            horizon_days=max(1, len(proposal.get("tasks", []))),
            strategy="approved",
        )
        inserted = []
        for task in proposal.get("tasks", []):
            task_id = self.storage.create_task(
                date=task["date"],
                title=task["title"],
                priority=task["priority"],
                estimate_min=task["estimate_min"],
                status="todo",
                tags="agent-generated",
            )
            self.storage.create_plan_item(plan_id, task_id, milestone="", confidence=0.75)
            inserted.append({"task_id": task_id, "title": task["title"]})

        return {"plan_id": plan_id, "inserted_tasks": inserted, "count": len(inserted)}

    def _build_milestones(self, goal_text, start, horizon_days):
        week_match = re.search(r"(\d+)\s*周", goal_text)
        weeks = int(week_match.group(1)) if week_match else max(1, horizon_days // 7)
        milestones = []
        for i in range(weeks):
            d = start + timedelta(days=(i + 1) * 7)
            milestones.append({"name": f"第{i+1}周里程碑", "date": d.isoformat()})
        return milestones

    def _task_templates(self, goal_text):
        if "答辩" in goal_text or "论文" in goal_text:
            return [
                {"title": "梳理论文核心贡献与答辩主线", "estimate_min": 90, "priority": "high", "reason": "先明确主线，避免后续返工"},
                {"title": "整理实验数据与图表", "estimate_min": 120, "priority": "high", "reason": "答辩证据材料准备"},
                {"title": "制作答辩PPT初稿", "estimate_min": 180, "priority": "high", "reason": "形成可演示版本"},
                {"title": "导师/同伴预审并收集反馈", "estimate_min": 60, "priority": "medium", "reason": "提前暴露问题"},
                {"title": "根据反馈迭代PPT和讲稿", "estimate_min": 120, "priority": "high", "reason": "提升论证完整性"},
                {"title": "全流程计时彩排", "estimate_min": 60, "priority": "medium", "reason": "控制节奏和时间"},
                {"title": "准备Q&A高频问题清单", "estimate_min": 90, "priority": "medium", "reason": "降低现场不确定性"},
                {"title": "最终检查材料与备份", "estimate_min": 45, "priority": "high", "reason": "避免临场故障"},
            ]
        return [
            {"title": "定义目标完成标准", "estimate_min": 45, "priority": "high", "reason": "明确可交付结果"},
            {"title": "拆分关键里程碑", "estimate_min": 60, "priority": "high", "reason": "建立执行路径"},
            {"title": "执行第一批关键任务", "estimate_min": 90, "priority": "high", "reason": "尽快启动"},
            {"title": "中期复盘并调整", "estimate_min": 45, "priority": "medium", "reason": "降低偏航风险"},
            {"title": "收尾与验收", "estimate_min": 60, "priority": "high", "reason": "确保闭环"},
        ]
