"""Unit tests for combine_reports_from_date_range"""

import unittest
import sys
import re
import json
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import daq
import combine_reports_from_date_range
from combine_reports_from_date_range import _render_results, main, os
from daq.report import MdTable


class TestCombineReportsFromDateRange(unittest.TestCase):
    """Test class for Report"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        mock_path = os.path.join(self.script_path, 'mock', 'test_combine_reports_from_date_range')
        self.mocks = {'empty': ''}
        for filename in os.listdir(mock_path):
            with open(os.path.join(mock_path, filename)) as f:
                self.mocks[filename] = f.read()

    def _dict_compare(self, dict1, dict2):
        return json.dumps(dict1, sort_keys=True) == json.dumps(dict2, sort_keys=True)

    def test_render_results_with_no_results(self):
        """Test _render_results func"""
        aggregate = {'tests': {}, 'categories': {}, 'missing': {}, 'reports': {}}
        test_table = MdTable(['test'])
        test_table.add_row(['No results'])
        category_table = MdTable(['categories'])
        category_table.add_row(['No results'])
        missing_table = MdTable(['missing tests', 'count'])
        missing_table.add_row(['None'])
        report_table = MdTable(['reports'])
        all_tables = [test_table, category_table, missing_table, report_table]
        expected = '\n'.join(map(lambda x: x.render(), all_tables))
        self.assertEqual(expected, _render_results(aggregate))

    def test_render_results(self):
        """Test _render_results func"""
        aggregate = {
            'tests': {
                'test1': {'a': 1, 'b': 2, 'c': 1},
                'test2': {'a': 1, 'd': 1}
            }, 'categories': {
                'label1': {'a': 1, 'b': 2},
                'label2': {'a': 100, 'b': 1, 'c': 100}
            }, 'missing': {
                'z': 10,
                'aaa': 100
            }, 'reports': {
                '1234567890': True
            }}
        test_table = MdTable(['test', 'a', 'b', 'c', 'd'])
        test_table.add_row(['test1', '1', '2', '1', '0'])
        test_table.add_row(['test2', '1', '0', '0', '1'])
        category_table = MdTable(['categories', 'a', 'b', 'c'])
        category_table.add_row(['label1', '1', '2', '0'])
        category_table.add_row(['label2', '100', '1', '100'])
        missing_table = MdTable(['missing tests', 'count'])
        missing_table.add_row(['aaa', '100'])
        missing_table.add_row(['z', '10'])
        report_table = MdTable(['reports'])
        report_table.add_row(['1234567890'])
        all_tables = [test_table, category_table, missing_table, report_table]
        expected = '\n'.join(map(lambda x: x.render(), all_tables))
        self.assertEqual(expected, _render_results(aggregate))

    def test_main_with_local(self):

        device = 'device1'
        files_list = [
            'report_someotherdevice_2020-05-29T002333.json',
            'report_' + device + '_2019-05-29T002333.json',
            # only the following 2 should be processed
            'report_' + device + '_2020-05-29T002333.json',
            'report_' + device + '_2020-05-29T092333.json'
        ]
        os.listdir = MagicMock(return_value=files_list)
        def custom_open(report, mode=None):
            if report.endswith('report_' + device + '_2020-05-29T002333.json'):
                mock_name = "report_1.json"
            elif report.endswith('report_' + device + '_2020-05-29T092333.json'):
                mock_name = "report_2.json"
            elif re.search('combo.*\.md$', report):
                mock_name = 'empty'
            else:
                raise Exception(report + ' is not expected')
            return mock_open(read_data=self.mocks[mock_name]).return_value

        combine_reports_from_date_range._render_results = MagicMock(return_value="fake results")
        with patch("builtins.open", new=custom_open):
            main('device1', start=datetime.fromisoformat('2020-05-29'))
        expected_results = {
            'tests': {
                'base.startup.dhcp': {'pass': 2},
                'base.switch.ping': {'pass': 1, 'fail': 1},
                'base.target.ping': {'fail': 2}
            }, 'categories': {
                'Other1': {'pass': 1},
                'Other': {'pass': 2, 'fail': 3}
            }, 'missing': {
                'missing.test.1': 1
            }, 'reports': {
                'report_1_timestamp': True,
                'report_2_timestamp': True
            }}
        combine_reports_from_date_range._render_results.assert_called()
        call_args = combine_reports_from_date_range._render_results.call_args[0][0]
        assert self._dict_compare(call_args, expected_results)


if __name__ == '__main__':
    unittest.main()
