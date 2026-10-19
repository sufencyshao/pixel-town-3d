"""Isolated checks for restore integrity, repeat runs and preservation of edits."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


class RestoreChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'tools').mkdir()
        (self.root / 'catalog').mkdir()
        shutil.copy2(Path(__file__).with_name('restore-assets.py'), self.root / 'tools/restore-assets.py')
        self.data = b'original-test-asset\x00\x01'
        self.archive = self.root / 'source.zip'
        with zipfile.ZipFile(self.archive, 'w') as z:
            z.writestr('source/assets/test.bin', self.data)
        self.spec = {'archive': self.archive.name, 'tag': 'test', 'prefix': 'source/',
                     'sha256': hashlib.sha256(self.archive.read_bytes()).hexdigest(),
                     'files': [{'file': 'assets/test.bin', 'bytes': len(self.data),
                                'sha256': hashlib.sha256(self.data).hexdigest()}]}

    def tearDown(self):
        self.temp.cleanup()

    def run_restore(self):
        (self.root / 'catalog/restore-assets.json').write_text(json.dumps(self.spec))
        return subprocess.run([sys.executable, str(self.root / 'tools/restore-assets.py'),
                               '--archive', str(self.archive)], capture_output=True, text=True)

    def test_restore_and_repeat(self):
        self.assertEqual(self.run_restore().returncode, 0)
        self.assertEqual((self.root / 'assets/test.bin').read_bytes(), self.data)
        result = self.run_restore()
        self.assertEqual(result.returncode, 0)
        self.assertIn('Restored and verified 0 files; 1 already correct.', result.stdout)

    def test_preserve_modified_file(self):
        (self.root / 'assets').mkdir()
        (self.root / 'assets/test.bin').write_bytes(b'my local edits')
        self.assertNotEqual(self.run_restore().returncode, 0)
        self.assertEqual((self.root / 'assets/test.bin').read_bytes(), b'my local edits')

    def test_reject_wrong_archive(self):
        self.spec['sha256'] = '0' * 64
        self.assertNotEqual(self.run_restore().returncode, 0)
        self.assertFalse((self.root / 'assets').exists())

    def test_reject_path_traversal(self):
        self.spec['files'][0]['file'] = '../escape.bin'
        self.assertNotEqual(self.run_restore().returncode, 0)
        self.assertFalse((self.root.parent / 'escape.bin').exists())

    def test_reject_bad_member_hash(self):
        self.spec['files'][0]['sha256'] = '0' * 64
        self.assertNotEqual(self.run_restore().returncode, 0)
        self.assertFalse((self.root / 'assets/test.bin').exists())
        self.assertEqual(list((self.root / 'assets').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
