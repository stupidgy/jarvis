import json
import os
import tempfile
import unittest

from planner import AgentOrchestrator
from storage import AppStorage


class AppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.db = AppStorage(self.tmp.name)
        self.db.init_schema()
        self.db.seed_defaults()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_task_crud_and_list(self):
        tid = self.db.create_task("2026-03-10", "Test", "high", 30, "todo")
        self.assertTrue(tid > 0)
        tasks = self.db.list_tasks("2026-03-01", "2026-03-30")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["title"], "Test")

    def test_propose_and_apply_plan(self):
        orch = AgentOrchestrator(self.db)
        proposal = orch.propose_plan("我要在 4 周内完成毕业答辩准备", 28)
        self.assertIn("tasks", proposal)
        self.assertTrue(len(proposal["tasks"]) >= 5)

        result = orch.apply_plan(json.loads(json.dumps(proposal)))
        self.assertTrue(result["count"] > 0)


    def test_update_move_and_summary(self):
        tid1 = self.db.create_task("2026-03-10", "Task A", "high", 25, "todo")
        tid2 = self.db.create_task("2026-03-11", "Task B", "medium", 35, "todo")

        self.db.update_task_status(tid1, "done")
        self.db.move_task(tid2, "2026-03-10")

        tasks = self.db.list_tasks("2026-03-10", "2026-03-10")
        self.assertEqual(len(tasks), 2)
        statuses = {t["id"]: t["status"] for t in tasks}
        self.assertEqual(statuses[tid1], "done")
        self.assertEqual(statuses[tid2], "todo")

        summary = self.db.task_summary("2026-03-10", "2026-03-10")
        self.assertEqual(summary["todo"], 1)
        self.assertEqual(summary["done"], 1)
        self.assertEqual(summary["total_estimate_min"], 60)


if __name__ == "__main__":
    unittest.main()
