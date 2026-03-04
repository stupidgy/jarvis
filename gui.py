import json
from datetime import date, timedelta
import tkinter as tk
from tkinter import messagebox, ttk

from planner import AgentOrchestrator
from storage import AppStorage


class CalendarPetGUI:
    def __init__(self, root: tk.Tk, db_path: str):
        self.root = root
        self.root.title("卡通桌宠任务助手")
        self.root.geometry("1180x780")
        self.root.configure(bg="#f7f9ff")

        self.db = AppStorage(db_path)
        self.db.init_schema()
        self.db.seed_defaults()
        self.orchestrator = AgentOrchestrator(self.db)

        self._pet_offset = 0
        self._pet_direction = 1

        self._configure_style()
        self._build_layout()
        self.refresh_tasks()
        self._animate_pet()

    def _configure_style(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("Header.TLabel", font=("Arial", 14, "bold"), foreground="#26335a")
        style.configure("Hint.TLabel", font=("Arial", 10), foreground="#5e6b94")
        style.configure("PetBubble.TLabel", font=("Arial", 11), background="#fff6d8", foreground="#3a3a3a", padding=10)
        style.configure("Card.TLabelframe", padding=10, background="#ffffff")
        style.configure("Card.TLabelframe.Label", font=("Arial", 11, "bold"), foreground="#32456b")
        style.configure("Pet.TFrame", background="#eef3ff")

    def _build_layout(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.task_tab = ttk.Frame(notebook)
        self.review_tab = ttk.Frame(notebook)
        self.agent_tab = ttk.Frame(notebook)

        notebook.add(self.task_tab, text="桌宠任务舱")
        notebook.add(self.review_tab, text="晚间复盘")
        notebook.add(self.agent_tab, text="目标拆分")

        self._build_task_tab()
        self._build_review_tab()
        self._build_agent_tab()

    def _build_task_tab(self):
        self.task_tab.columnconfigure(1, weight=1)
        self.task_tab.rowconfigure(0, weight=1)

        pet_panel = ttk.Frame(self.task_tab, style="Pet.TFrame")
        pet_panel.grid(row=0, column=0, sticky="ns", padx=(8, 12), pady=8)

        ttk.Label(pet_panel, text="今日桌宠", style="Header.TLabel").pack(anchor="w", padx=10, pady=(10, 6))
        self.pet_canvas = tk.Canvas(
            pet_panel,
            width=260,
            height=240,
            bg="#eef3ff",
            highlightthickness=0,
        )
        self.pet_canvas.pack(padx=10)
        self._draw_pet()

        self.pet_message_var = tk.StringVar(value="嗨！把任务交给我吧，今天也会发光发热 ✨")
        ttk.Label(
            pet_panel,
            textvariable=self.pet_message_var,
            style="PetBubble.TLabel",
            wraplength=220,
            justify="left",
        ).pack(fill="x", padx=10, pady=10)

        quick = ttk.LabelFrame(pet_panel, text="桌宠快捷动作")
        quick.pack(fill="x", padx=10, pady=(4, 12))
        ttk.Button(quick, text="刷新任务", command=lambda: self._pet_action("refresh")).grid(row=0, column=0, padx=6, pady=6)
        ttk.Button(quick, text="标记完成", command=lambda: self._pet_action("done")).grid(row=0, column=1, padx=6, pady=6)
        ttk.Button(quick, text="任务改期", command=lambda: self._pet_action("move")).grid(row=1, column=0, padx=6, pady=6)
        ttk.Button(quick, text="添加任务", command=lambda: self._pet_action("add")).grid(row=1, column=1, padx=6, pady=6)

        right_panel = ttk.Frame(self.task_tab)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(3, weight=1)

        summary = ttk.LabelFrame(right_panel, text="任务能量槽", style="Card.TLabelframe")
        summary.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self.todo_count_var = tk.StringVar(value="0")
        self.done_count_var = tk.StringVar(value="0")
        self.total_est_var = tk.StringVar(value="0 分钟")

        ttk.Label(summary, text="待办", style="Header.TLabel").grid(row=0, column=0, padx=16)
        ttk.Label(summary, textvariable=self.todo_count_var, style="Header.TLabel").grid(row=1, column=0, padx=16)
        ttk.Label(summary, text="已完成", style="Header.TLabel").grid(row=0, column=1, padx=16)
        ttk.Label(summary, textvariable=self.done_count_var, style="Header.TLabel").grid(row=1, column=1, padx=16)
        ttk.Label(summary, text="总预计时长", style="Header.TLabel").grid(row=0, column=2, padx=16)
        ttk.Label(summary, textvariable=self.total_est_var, style="Header.TLabel").grid(row=1, column=2, padx=16)

        filters = ttk.LabelFrame(right_panel, text="筛选与查找")
        filters.grid(row=1, column=0, sticky="ew", pady=6)

        ttk.Label(filters, text="开始日期").grid(row=0, column=0, padx=6, pady=6)
        self.start_date_var = tk.StringVar(value=str(date.today()))
        ttk.Entry(filters, textvariable=self.start_date_var, width=14).grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(filters, text="结束日期").grid(row=0, column=2, padx=6, pady=6)
        self.end_date_var = tk.StringVar(value=str(date.today() + timedelta(days=7)))
        ttk.Entry(filters, textvariable=self.end_date_var, width=14).grid(row=0, column=3, padx=6, pady=6)

        ttk.Label(filters, text="状态").grid(row=0, column=4, padx=6, pady=6)
        self.status_filter_var = tk.StringVar(value="all")
        ttk.Combobox(filters, textvariable=self.status_filter_var, values=["all", "todo", "done"], width=9, state="readonly").grid(row=0, column=5, padx=6, pady=6)

        ttk.Label(filters, text="关键词").grid(row=0, column=6, padx=6, pady=6)
        self.keyword_var = tk.StringVar()
        ttk.Entry(filters, textvariable=self.keyword_var, width=16).grid(row=0, column=7, padx=6, pady=6)
        ttk.Button(filters, text="搜索", command=self.refresh_tasks).grid(row=0, column=8, padx=6, pady=6)

        add_box = ttk.LabelFrame(right_panel, text="通过桌宠新增任务")
        add_box.grid(row=2, column=0, sticky="ew", pady=6)

        self.task_date_var = tk.StringVar(value=str(date.today()))
        self.task_title_var = tk.StringVar()
        self.task_priority_var = tk.StringVar(value="medium")
        self.task_estimate_var = tk.StringVar(value="30")
        self.task_tags_var = tk.StringVar()

        ttk.Label(add_box, text="日期").grid(row=0, column=0, padx=6, pady=6)
        ttk.Entry(add_box, textvariable=self.task_date_var, width=12).grid(row=0, column=1, padx=6, pady=6)
        ttk.Label(add_box, text="标题").grid(row=0, column=2, padx=6, pady=6)
        ttk.Entry(add_box, textvariable=self.task_title_var, width=24).grid(row=0, column=3, padx=6, pady=6)

        ttk.Label(add_box, text="优先级").grid(row=1, column=0, padx=6, pady=6)
        ttk.Combobox(add_box, textvariable=self.task_priority_var, values=["high", "medium", "low"], width=10, state="readonly").grid(row=1, column=1, padx=6, pady=6)
        ttk.Label(add_box, text="预计分钟").grid(row=1, column=2, padx=6, pady=6)
        ttk.Entry(add_box, textvariable=self.task_estimate_var, width=10).grid(row=1, column=3, padx=6, pady=6, sticky="w")

        ttk.Label(add_box, text="标签").grid(row=2, column=0, padx=6, pady=6)
        ttk.Entry(add_box, textvariable=self.task_tags_var, width=24).grid(row=2, column=1, columnspan=2, padx=6, pady=6, sticky="w")
        ttk.Button(add_box, text="添加任务", command=self.add_task).grid(row=2, column=3, padx=6, pady=6, sticky="e")

        table_box = ttk.LabelFrame(right_panel, text="任务列表（选中后可标记完成 / 改期）")
        table_box.grid(row=3, column=0, sticky="nsew", pady=6)
        table_box.columnconfigure(0, weight=1)
        table_box.rowconfigure(0, weight=1)

        columns = ("id", "date", "title", "priority", "estimate", "status", "tags")
        self.task_tree = ttk.Treeview(table_box, columns=columns, show="headings", height=16)
        for col, title, w in [
            ("id", "ID", 52),
            ("date", "日期", 110),
            ("title", "标题", 300),
            ("priority", "优先级", 90),
            ("estimate", "预计", 70),
            ("status", "状态", 80),
            ("tags", "标签", 150),
        ]:
            self.task_tree.heading(col, text=title)
            self.task_tree.column(col, width=w, anchor="center")
        self.task_tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_box, orient="vertical", command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        actions = ttk.Frame(table_box)
        actions.grid(row=1, column=0, sticky="ew", pady=8)
        ttk.Button(actions, text="标记选中任务完成", command=self.mark_done).grid(row=0, column=0, padx=6)
        ttk.Label(actions, text="改期到", style="Hint.TLabel").grid(row=0, column=1, padx=6)
        self.move_date_var = tk.StringVar(value=str(date.today() + timedelta(days=1)))
        ttk.Entry(actions, textvariable=self.move_date_var, width=14).grid(row=0, column=2, padx=6)
        ttk.Button(actions, text="执行改期", command=self.move_selected_task).grid(row=0, column=3, padx=6)

    def _draw_pet(self):
        c = self.pet_canvas
        c.delete("all")
        y = self._pet_offset
        c.create_oval(70, 35 + y, 190, 165 + y, fill="#ffd7b5", outline="#e9b894", width=2)
        c.create_polygon(95, 55 + y, 80, 20 + y, 120, 45 + y, fill="#ffd7b5", outline="#e9b894", width=2)
        c.create_polygon(165, 55 + y, 180, 20 + y, 140, 45 + y, fill="#ffd7b5", outline="#e9b894", width=2)
        c.create_oval(103, 82 + y, 118, 97 + y, fill="#2f3d66", outline="")
        c.create_oval(142, 82 + y, 157, 97 + y, fill="#2f3d66", outline="")
        c.create_oval(127, 97 + y, 133, 103 + y, fill="#ff9f9f", outline="")
        c.create_arc(112, 105 + y, 148, 130 + y, start=200, extent=140, style="arc", width=3, outline="#2f3d66")
        c.create_oval(75, 130 + y, 95, 145 + y, fill="#ffb7b7", outline="")
        c.create_oval(165, 130 + y, 185, 145 + y, fill="#ffb7b7", outline="")
        c.create_text(130, 195 + y, text="任务精灵", fill="#516497", font=("Arial", 12, "bold"))

    def _animate_pet(self):
        self._pet_offset += self._pet_direction
        if self._pet_offset >= 6 or self._pet_offset <= -6:
            self._pet_direction *= -1
        self._draw_pet()
        self.root.after(140, self._animate_pet)

    def _pet_action(self, action: str):
        if action == "refresh":
            self.refresh_tasks()
            self.pet_message_var.set("我帮你刷新好啦，继续冲刺！")
        elif action == "done":
            self.mark_done()
        elif action == "move":
            self.move_selected_task()
        elif action == "add":
            self.add_task()

    def _build_review_tab(self):
        frame = ttk.LabelFrame(self.review_tab, text="晚间复盘")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.review_date_var = tk.StringVar(value=str(date.today()))
        ttk.Label(frame, text="日期").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Entry(frame, textvariable=self.review_date_var, width=15).grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(frame, text="今日完成").grid(row=1, column=0, padx=6, pady=6, sticky="nw")
        self.done_text = tk.Text(frame, height=6, width=90)
        self.done_text.grid(row=1, column=1, padx=6, pady=6, sticky="ew")

        ttk.Label(frame, text="阻碍").grid(row=2, column=0, padx=6, pady=6, sticky="nw")
        self.blockers_text = tk.Text(frame, height=6, width=90)
        self.blockers_text.grid(row=2, column=1, padx=6, pady=6, sticky="ew")

        ttk.Label(frame, text="明日重点").grid(row=3, column=0, padx=6, pady=6, sticky="nw")
        self.tomorrow_text = tk.Text(frame, height=6, width=90)
        self.tomorrow_text.grid(row=3, column=1, padx=6, pady=6, sticky="ew")

        ttk.Button(frame, text="保存复盘", command=self.save_review).grid(row=4, column=1, padx=6, pady=10, sticky="e")
        frame.grid_columnconfigure(1, weight=1)

    def _build_agent_tab(self):
        frame = ttk.LabelFrame(self.agent_tab, text="复杂目标拆分（L1：先提案，后确认写入）")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.goal_var = tk.StringVar(value="我要在 4 周内完成毕业答辩准备")
        self.horizon_var = tk.StringVar(value="28")
        self.strategy_var = tk.StringVar(value="balanced")
        self.max_tasks_var = tk.StringVar(value="3")

        ttk.Label(frame, text="目标").grid(row=0, column=0, padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.goal_var, width=90).grid(row=0, column=1, columnspan=5, padx=6, pady=6, sticky="ew")

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

        status_filter = self.status_filter_var.get().strip()
        keyword = self.keyword_var.get().strip()
        if status_filter != "all":
            tasks = [t for t in tasks if t["status"] == status_filter]
        if keyword:
            tasks = [
                t
                for t in tasks
                if keyword.lower() in t["title"].lower() or keyword.lower() in (t.get("tags") or "").lower()
            ]

        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        for t in tasks:
            self.task_tree.insert(
                "",
                "end",
                values=(t["id"], t["date"], t["title"], t["priority"], t["estimate_min"], t["status"], t.get("tags", "")),
            )

        summary = self.db.task_summary(self.start_date_var.get().strip(), self.end_date_var.get().strip())
        self.todo_count_var.set(str(summary["todo"]))
        self.done_count_var.set(str(summary["done"]))
        self.total_est_var.set(f"{summary['total_estimate_min']} 分钟")
        self.pet_message_var.set(f"当前待办 {summary['todo']} 个，已完成 {summary['done']} 个，我会陪你完成的！")

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
            self.pet_message_var.set("新任务登记成功！我已经帮你记在清单里啦。")
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
        self.pet_message_var.set("太棒了！我给这条任务打上完成勋章 ✅")

    def move_selected_task(self):
        task_id = self._selected_task_id()
        if task_id is None:
            return
        try:
            self.db.move_task(task_id, self.move_date_var.get().strip())
            self.refresh_tasks()
            self.pet_message_var.set("任务改期完成，节奏稳住就一定能完成！")
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
