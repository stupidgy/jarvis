#!/usr/bin/env python3
import argparse
import json
from datetime import date

from gui import run_gui
from planner import AgentOrchestrator
from storage import AppStorage


def cmd_init(args):
    db = AppStorage(args.db)
    db.init_schema()
    db.seed_defaults()
    print(f"Initialized database: {args.db}")


def cmd_add_task(args):
    db = AppStorage(args.db)
    task_id = db.create_task(
        date=args.date,
        title=args.title,
        priority=args.priority,
        estimate_min=args.estimate,
        status="todo",
        tags=args.tags,
    )
    print(f"Task created: {task_id}")


def cmd_list_tasks(args):
    db = AppStorage(args.db)
    tasks = db.list_tasks(args.start, args.end)
    print(json.dumps(tasks, ensure_ascii=False, indent=2))


def cmd_review(args):
    db = AppStorage(args.db)
    review_id = db.save_review(args.date, args.done, args.blockers, args.tomorrow)
    print(f"Review saved: {review_id}")


def cmd_propose_plan(args):
    db = AppStorage(args.db)
    orchestrator = AgentOrchestrator(db)
    proposal = orchestrator.propose_plan(
        goal_text=args.goal,
        horizon_days=args.horizon,
        strategy=args.strategy,
        max_tasks_per_day=args.max_tasks_per_day,
    )
    print(json.dumps(proposal, ensure_ascii=False, indent=2))


def cmd_apply_plan(args):
    db = AppStorage(args.db)
    orchestrator = AgentOrchestrator(db)
    with open(args.file, "r", encoding="utf-8") as f:
        proposal = json.load(f)
    result = orchestrator.apply_plan(proposal)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_gui(args):
    run_gui(args.db)


def build_parser():
    parser = argparse.ArgumentParser(description="Calendar pet app (GUI + CLI)")
    parser.add_argument("--db", default="pet_calendar.db", help="SQLite database path")

    sub = parser.add_subparsers(dest="command", required=False)

    p_gui = sub.add_parser("gui", help="Launch graphical desktop app")
    p_gui.set_defaults(func=cmd_gui)

    p_init = sub.add_parser("init-db", help="Initialize database schema")
    p_init.set_defaults(func=cmd_init)

    p_add = sub.add_parser("add-task", help="Add one task")
    p_add.add_argument("--date", required=True)
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--priority", choices=["high", "medium", "low"], default="medium")
    p_add.add_argument("--estimate", type=int, default=30)
    p_add.add_argument("--tags", default="")
    p_add.set_defaults(func=cmd_add_task)

    p_list = sub.add_parser("list-tasks", help="List tasks in date range")
    p_list.add_argument("--start", required=True)
    p_list.add_argument("--end", required=True)
    p_list.set_defaults(func=cmd_list_tasks)

    p_review = sub.add_parser("save-review", help="Save daily review")
    p_review.add_argument("--date", default=str(date.today()))
    p_review.add_argument("--done", required=True)
    p_review.add_argument("--blockers", required=True)
    p_review.add_argument("--tomorrow", required=True)
    p_review.set_defaults(func=cmd_review)

    p_prop = sub.add_parser("propose-plan", help="Generate plan proposal JSON")
    p_prop.add_argument("--goal", required=True)
    p_prop.add_argument("--horizon", type=int, default=28)
    p_prop.add_argument("--strategy", choices=["balanced", "aggressive", "conservative"], default="balanced")
    p_prop.add_argument("--max-tasks-per-day", type=int, default=3)
    p_prop.set_defaults(func=cmd_propose_plan)

    p_apply = sub.add_parser("apply-plan", help="Apply approved plan JSON file")
    p_apply.add_argument("--file", required=True)
    p_apply.set_defaults(func=cmd_apply_plan)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        run_gui(args.db)
