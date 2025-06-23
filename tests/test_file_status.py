import unittest
from src.table_modifier.file_status import FileStatus, FileStage, FileFlag

class TestFileStatus(unittest.TestCase):
    def test_default_status(self):
        status = FileStatus()
        self.assertEqual(status.stage, FileStage.NEW)
        self.assertEqual(status.flags, FileFlag.UNKNOWN)

    def test_flag_combination(self):
        status = FileStatus(flags=FileFlag.VALID | FileFlag.EXPORTED)
        self.assertTrue(FileFlag.VALID in status.flags)
        self.assertTrue(FileFlag.EXPORTED in status.flags)

if __name__ == "__main__":
    unittest.main()