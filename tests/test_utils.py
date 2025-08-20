import unittest
from pathlib import Path
from src.utils import normalize_variable_name, get_relative_path

class TestUtils(unittest.TestCase):
    def test_normalize_variable_name(self):
        self.assertEqual(normalize_variable_name('$test'), '$test')
        self.assertEqual(normalize_variable_name('test'), '$test')
        self.assertEqual(normalize_variable_name('$$test'), '$test')
        self.assertEqual(normalize_variable_name(''), '$')

    def test_get_relative_path(self):
        base_dir = Path('/base')
        file_path = Path('/base/subdir/file.php')
        self.assertEqual(get_relative_path(file_path, base_dir), 'subdir/file.php')

if __name__ == '__main__':
    unittest.main()