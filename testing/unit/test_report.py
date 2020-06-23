"""Unit tests for report"""

import unittest
import sys
import os
import time
from unittest.mock import MagicMock, mock_open, patch
from daq.report import MdTable 

class TestReport(unittest.TestCase):
    """Test class for Report"""

    def test_render(self):
        """Test md table render"""
        table = MdTable(['a', 'b', 'c'])
        table.add_row(['a ', 'a', ' '])
        table.add_row(['c', 'b', 'a '])
        expected = """|a|b|c|
|---|---|---|
|a|a||
|c|b|a|
"""
        self.assertEqual(expected, table.render())
          
if __name__ == '__main__':
    unittest.main()
