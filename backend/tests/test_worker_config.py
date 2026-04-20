import importlib
import os
import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


class WorkerConfigTests(unittest.TestCase):
    def test_worker_defaults_to_single_process_concurrency(self):
        os.environ.pop("CELERY_CONCURRENCY", None)

        for module_name in ["config", "workers.pipeline"]:
            sys.modules.pop(module_name, None)

        pipeline = importlib.import_module("workers.pipeline")

        self.assertEqual(pipeline.celery_app.conf.worker_concurrency, 1)


if __name__ == "__main__":
    unittest.main()
