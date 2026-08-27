"""Runner for all Orchestrator V1 Unit and Integration Tests."""

import unittest
import sys
from pathlib import Path

# Add repo root to sys.path
repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from demo.orchestrator.tests.test_coordinator import TestCoordinator
from demo.orchestrator.tests.test_adapters import TestAdapters
from demo.orchestrator.tests.test_engine import TestEngineWorkflows


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(TestCoordinator))
    s.addTest(unittest.makeSuite(TestAdapters))
    s.addTest(unittest.makeSuite(TestEngineWorkflows))
    return s


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite())
    sys.exit(0 if result.wasSuccessful() else 1)
