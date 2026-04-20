import asyncio
import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

MODULES_TO_RELOAD = [
    "config",
    "database",
    "models",
    "services.storage",
    "workers.pipeline",
    "routes.upload",
    "routes.jobs",
    "main",
]


def load_storage_with_database(database_url: str):
    os.environ["DATABASE_URL"] = database_url
    os.environ["STORAGE_TYPE"] = "db"

    for module_name in MODULES_TO_RELOAD:
        sys.modules.pop(module_name, None)

    database = importlib.import_module("database")
    importlib.import_module("models")
    database.init_db()

    return importlib.import_module("services.storage")


class DatabaseStorageTests(unittest.TestCase):
    def test_database_storage_round_trips_files_between_processes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "storage.sqlite"
            storage_module = load_storage_with_database(f"sqlite:///{db_path}")
            storage = storage_module.storage

            self.assertEqual(storage_module.settings.storage_type, "db")

            asyncio.run(storage.save("uploads/job.mp4", b"original-bytes"))
            self.assertEqual(storage.public_url("uploads/job.mp4"), "/storage/uploads/job.mp4")

            downloaded = Path(temp_dir) / "downloaded.mp4"
            storage.download_to_tmp("uploads/job.mp4", str(downloaded))
            self.assertEqual(downloaded.read_bytes(), b"original-bytes")

            replacement = Path(temp_dir) / "replacement.mp4"
            replacement.write_bytes(b"replacement-bytes")
            storage.upload_file("uploads/job.mp4", str(replacement))

            downloaded_after_replace = Path(temp_dir) / "downloaded-after-replace.mp4"
            storage.download_to_tmp("uploads/job.mp4", str(downloaded_after_replace))
            self.assertEqual(downloaded_after_replace.read_bytes(), b"replacement-bytes")

            storage.delete("uploads/job.mp4")
            with self.assertRaises(FileNotFoundError):
                storage.download_to_tmp("uploads/job.mp4", str(downloaded))

    def test_database_storage_route_serves_saved_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "storage.sqlite"
            storage_module = load_storage_with_database(f"sqlite:///{db_path}")
            storage_module.storage.save_sync("shorts/job/clip.mp4", b"fake-mp4")

            main = importlib.import_module("main")
            route = next(
                route
                for route in main.app.routes
                if getattr(route, "path", None) == "/storage/{key:path}"
            )

            response = route.endpoint("shorts/job/clip.mp4")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.body, b"fake-mp4")
            self.assertEqual(response.media_type, "video/mp4")


if __name__ == "__main__":
    unittest.main()
