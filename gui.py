import json
from datetime import date, timedelta
import tkinter as tk
from tkinter import messagebox, ttk

from planner import AgentOrchestrator
from storage import AppStorage


class CalendarPetGUI:
    def __init__(self, root: tk.Tk, db_path: str):
        self.root = root
        self.root.title("日历清单桌宠 - MVP")
        self.root.geometry("980x680")

        self.db = AppStorage(db_path)
        self.db.init_schema()
        self.db.seed_defaults()
        self.orchestrator = AgentOrchestrator(self.db)
        self.current_proposal = None

        self._build_layout()
        self.refresh_tasks()

    def _build_layout(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.task_tab = ttk.Frame(notebook)
        self.review_tab = ttk.Frame(notebook)
        self.agent_tab = ttk.Frame(notebook)

        notebook.add(self.task_tab, text="任务日历清单")
        notebook.add(self.review_tab, text="晚间复盘")
        notebook.add(self.agent_tab, text="复杂目标拆分")

        self._build_task_tab()
        self._build_review_tab()
        self._build_agent_tab()

    def _build_task_tab(self):
        filters = ttk.LabelFrame(self.task_tab, text="查询区间")
        filters.pack(fill="x", padx=8, pady=8)

        ttk.Label(filters, text="开始日期(YYYY-MM-DD)").grid(row=0, column=0, padx=6, pady=6)
        self.start_date_var = tk.StringVar(value=str(date.today()))
        ttk.Entry(filters, textvariable=self.start_date_var, width=15).grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(filters, text="结束日期").grid(row=0, column=2, padx=6, pady=6)
        self.end_date_var = tk.StringVar(value=str(date.today() + timedelta(days=7)))
        ttk.Entry(filters, textvariable=self.end_date_var, width=15).grid(row=0, column=3, padx=6, pady=6)

        ttk.Button(filters, text="刷新任务", command=self.refresh_tasks).grid(row=0, column=4, padx=6, pady=6)

        add_box = ttk.LabelFrame(self.task_tab, text="新增任务")
        add_box.pack(fill="x", padx=8, pady=8)

        self.task_date_var = tk.StringVar(value=str(date.today()))
        self.task_title_var = tk.StringVar()
        self.task_priority_var = tk.StringVar(value="medium")
        self.task_estimate_var = tk.StringVar(value="30")
        self.task_tags_var = tk.StringVar()

        ttk.Label(add_box, text="日期").grid(row=0, column=0, padx=6, pady=6)
        ttk.Entry(add_box, textvariable=self.task_date_var, width=12).grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(add_box, text="标题").grid(row=0, column=2, padx=6, pady=6)
        ttk.Entry(add_box, textvariable=self.task_title_var, width=24).grid(row=0, column=3, padx=6, pady=6)

        ttk.Label(add_box, text="优先级").grid(row=0, column=4, padx=6, pady=6)
        ttk.Combobox(add_box, textvariable=self.task_priority_var, values=["high", "medium", "low"], width=10, state="readonly").grid(row=0, column=5, padx=6, pady=6)

        ttk.Label(add_box, text="预计分钟").grid(row=1, column=0, padx=6, pady=6)
        ttk.Entry(add_box, textvariable=self.task_estimate_var, width=12).grid(row=1, column=1, padx=6, pady=6)

        ttk.Label(add_box, text="标签").grid(row=1, column=2, padx=6, pady=6)
        ttk.Entry(add_box, textvariable=self.task_tags_var, width=24).grid(row=1, column=3, padx=6, pady=6)

        ttk.Button(add_box, text="添加任务", command=self.add_task).grid(row=1, column=5, padx=6, pady=6)

        table_box = ttk.LabelFrame(self.task_tab, text="任务列表")
        table_box.pack(fill="both", expand=True, padx=8, pady=8)

        columns = ("id", "date", "title", "priority", "estimate", "status", "tags")
        self.task_tree = ttk.Treeview(table_box, columns=columns, show="headings", height=16)
        for col, title, w in [
            ("id", "ID", 50),
            ("date", "日期", 110),
            ("title", "标题", 260),
            ("priority", "优先级", 80),
            ("estimate", "时长", 80),
            ("status", "状态", 90),
            ("tags", "标签", 180),
        ]:
            self.task_tree.heading(col, text=title)
            self.task_tree.column(col, width=w, anchor="center")
        self.task_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_box, orient="vertical", command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        action_bar = ttk.Frame(self.task_tab)
        action_bar.pack(fill="x", padx=8, pady=8)

        ttk.Button(action_bar, text="标记为完成", command=self.mark_done).pack(side="left", padx=6)

        ttk.Label(action_bar, text="改期到").pack(side="left", padx=6)
        self.move_date_var = tk.StringVar(value=str(date.today() + timedelta(days=1)))
        ttk.Entry(action_bar, textvariable=self.move_date_var, width=14).pack(side="left", padx=6)
        ttk.Button(action_bar, text="改期选中任务", command=self.move_selected_task).pack(side="left", padx=6)

    def _build_review_tab(self):
        frame = ttk.Frame(self.review_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.review_date_var = tk.StringVar(value=str(date.today()))
        ttk.Label(frame, text="复盘日期").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.review_date_var, width=15).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(frame, text="今天完成了什么？").grid(row=1, column=0, sticky="nw", padx=6, pady=6)
        self.done_text = tk.Text(frame, height=5, width=90)
        self.done_text.grid(row=1, column=1, padx=6, pady=6)

        ttk.Label(frame, text="未完成原因是什么？").grid(row=2, column=0, sticky="nw", padx=6, pady=6)
        self.blockers_text = tk.Text(frame, height=5, width=90)
        self.blockers_text.grid(row=2, column=1, padx=6, pady=6)

        ttk.Label(frame, text="明天最重要 1~3 件事").grid(row=3, column=0, sticky="nw", padx=6, pady=6)
        self.tomorrow_text = tk.Text(frame, height=5, width=90)
        self.tomorrow_text.grid(row=3, column=1, padx=6, pady=6)

        ttk.Button(frame, text="保存复盘", command=self.save_review).grid(row=4, column=1, sticky="e", padx=6, pady=8)

    def _build_agent_tab(self):
        frame = ttk.Frame(self.agent_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.goal_var = tk.StringVar(value="我要在 4 周内完成毕业答辩准备")
        self.horizon_var = tk.StringVar(value="28")
        self.strategy_var = tk.StringVar(value="balanced")
        self.max_tasks_var = tk.StringVar(value="3")

        ttk.Label(frame, text="复杂目标").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.goal_var, width=85).grid(row=0, column=1, columnspan=5, sticky="we", padx=6, pady=6)

        ttk.Label(frame, text="周期天数").grid(row=1, column=0, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.horizon_var, width=10).grid(row=1, column=1, padx=6, pady=6)

        ttk.Label(frame, text="策略").grid(row=1, column=2, padx=6, pady=6)
        ttk.Combobox(frame, textvariable=self.strategy_var, values=["balanced", "aggressive", "conservative"], width=14, state="readonly").grid(row=1, column=3, padx=6, pady=6)

        ttk.Label(frame, text="每日任务上限").grid(row=1, column=4, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.max_tasks_var, width=10).grid(row=1, column=5, padx=6, pady=6)

        ttk.Button(frame, text="生成拆分提案", command=self.generate_proposal).grid(row=2, column=5, sticky="e", padx=6, pady=6)

        ttk.Label(frame, text="提案 JSON（可手动编辑后再应用）").grid(row=3, column=0, columnspan=2, sticky="w", padx=6, pady=6)
        self.proposal_text = tk.Text(frame, height=18, width=110)
        self.proposal_text.grid(row=4, column=0, columnspan=6, padx=6, pady=6, sticky="nsew")

        frame.grid_rowconfigure(4, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        ttk.Button(frame, text="确认并写入任务", command=self.apply_proposal).grid(row=5, column=5, sticky="e", padx=6, pady=10)

    def refresh_tasks(self):
        try:
            tasks = self.db.list_tasks(self.start_date_var.get().strip(), self.end_date_var.get().strip())
        except Exception as exc:
            messagebox.showerror("查询失败", str(exc))
            return

        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        for t in tasks:
            self.task_tree.insert(
                "", "end",
                values=(t["id"], t["date"], t["title"], t["priority"], t["estimate_min"], t["status"], t.get("tags", "")),
            )

    def add_task(self):
        title = self.task_title_var.get().strip()
        if not title:
            messagebox.showwarning("提示", "任务标题不能为空")
            return
        try:
            estimate = int(self.task_estimate_var.get().strip())
            self.db.create_task(
                date=self.task_date_var.get().strip(),
                title=title,
                priority=self.task_priority_var.get().strip(),
                estimate_min=estimate,
                status="todo",
                tags=self.task_tags_var.get().strip(),
            )
            self.task_title_var.set("")
            self.task_tags_var.set("")
            self.refresh_tasks()
            messagebox.showinfo("成功", "任务已添加")
        except Exception as exc:
            messagebox.showerror("添加失败", str(exc))

    def _selected_task_id(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选中一个任务")
            return None
        vals = self.task_tree.item(selected[0], "values")
        return int(vals[0])

    def mark_done(self):
        task_id = self._selected_task_id()
        if task_id is None:
            return
        self.db.update_task_status(task_id, "done")
        self.refresh_tasks()

    def move_selected_task(self):
        task_id = self._selected_task_id()
        if task_id is None:
            return
        try:
            self.db.move_task(task_id, self.move_date_var.get().strip())
            self.refresh_tasks()
        except Exception as exc:
            messagebox.showerror("改期失败", str(exc))

    def save_review(self):
        try:
            rid = self.db.save_review(
                self.review_date_var.get().strip(),
                self.done_text.get("1.0", "end").strip(),
                self.blockers_text.get("1.0", "end").strip(),
                self.tomorrow_text.get("1.0", "end").strip(),
            )
            messagebox.showinfo("保存成功", f"复盘已保存（ID: {rid}）")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def generate_proposal(self):
        try:
            proposal = self.orchestrator.propose_plan(
                goal_text=self.goal_var.get().strip(),
                horizon_days=int(self.horizon_var.get().strip()),
                strategy=self.strategy_var.get().strip(),
                max_tasks_per_day=int(self.max_tasks_var.get().strip()),
            )
            self.current_proposal = proposal
            self.proposal_text.delete("1.0", "end")
            self.proposal_text.insert("1.0", json.dumps(proposal, ensure_ascii=False, indent=2))
        except Exception as exc:
            messagebox.showerror("生成失败", str(exc))

    def apply_proposal(self):
        text = self.proposal_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("提示", "请先生成或粘贴提案 JSON")
            return
        try:
            proposal = json.loads(text)
            result = self.orchestrator.apply_plan(proposal)
            self.refresh_tasks()
            messagebox.showinfo("写入成功", f"已创建计划 {result['plan_id']}，新增任务 {result['count']} 条")
        except Exception as exc:
            messagebox.showerror("写入失败", str(exc))


def run_gui(db_path: str = "pet_calendar.db"):
    root = tk.Tk()
    CalendarPetGUI(root, db_path)
    root.mainloop()
