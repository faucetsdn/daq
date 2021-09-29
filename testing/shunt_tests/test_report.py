"""Tests for shunt"""

import unittest
from shunt.shell_command_helper import ShellCommandHelper

class TestShunt(unittest.TestCase):
    """Test class for Report"""

    def test_script(self):
        """Test bash script test"""
        shellcmd = ShellCommandHelper()
        (retcode, _, _) = shellcmd.run_cmd("/bin/bash", ["testing/test_shunt.sh"])
        self.assertEqual(retcode, 0)


if __name__ == '__main__':
    unittest.main()
