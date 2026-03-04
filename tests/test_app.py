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

    def test_update_status_and_move(self):
        tid = self.db.create_task("2026-03-10", "Move Me", "medium", 20, "todo")
        self.db.update_task_status(tid, "done")
        self.db.move_task(tid, "2026-03-12")
        tasks = self.db.list_tasks("2026-03-01", "2026-03-30")
        self.assertEqual(tasks[0]["status"], "delayed")
        self.assertEqual(tasks[0]["date"], "2026-03-12")

    def test_propose_and_apply_plan(self):
        orch = AgentOrchestrator(self.db)
        proposal = orch.propose_plan("我要在 4 周内完成毕业答辩准备", 28)
        self.assertIn("tasks", proposal)
        self.assertTrue(len(proposal["tasks"]) >= 5)

        result = orch.apply_plan(json.loads(json.dumps(proposal)))
        self.assertTrue(result["count"] > 0)


if __name__ == "__main__":
    unittest.main()
