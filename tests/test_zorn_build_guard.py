import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "shim" / "build.sh"

class BuildGuardTests(unittest.TestCase):
    def run_board(self, board):
        env = os.environ.copy()
        env["BOARD"] = board
        return subprocess.run(["bash", str(BUILD)], cwd=ROOT, env=env,
                              text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=5)

    def test_zorn_is_blocked(self):
        result = self.run_board("zorn")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("zorn build blocked", result.stdout)

    def test_unknown_board_is_blocked(self):
        result = self.run_board("not-a-board")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("unsupported BOARD", result.stdout)

if __name__ == "__main__":
    unittest.main()
