__author__ = 'dsidi'

import unittest


class MyTestCase(unittest.TestCase):
    def test_data_ingest(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
