# coding=utf-8
"""
File contains UT for scripts related with `payment_analyzer` project
"""
import os
from unittest import TestCase

from lxml import etree

from payment_analyzer import PaymentAnalyzer
from utils import STATEMENT, OPERATION
import utils

PERSON = "OSOBA"
PERSONS = "OSOBY"


class TestPaymentAnalyzer(TestCase):
    """Test class for `PaymentAnalyzer` class."""

    _OUTPUT = 'tests/test_dir/output'
    _OUTPUT_DIR = _OUTPUT + '/dir_1/'

    def setUp(self):
        utils.INPUT = 'tests'
        self.xml_file = 'tests/fixtures.xml'
        self.wrong_file = 'tests/wrong.xml'
        self.persons_file = 'tests/test_dir/persons'
        self.client_class = PaymentAnalyzer
        self.client = self.client_class()
        self.client.person = ''

    def tearDown(self):
        for f in os.listdir(self._OUTPUT_DIR):
            os.remove(os.path.join(self._OUTPUT_DIR, f))

    @staticmethod
    def open_xml_file(xml_file):
        return open(xml_file, 'rb')

    def test_parse_xml_syntax_error(self):
        f = self.open_xml_file(self.wrong_file)
        self.assertEqual('XML syntax error', self.client.parse_xml(f))

    def test_parse_xml(self):
        f = self.open_xml_file(self.xml_file)
        root = self.client.parse_xml(f)
        statements = root.findall(STATEMENT)
        self.assertEqual(len(statements), 1)
        operations = statements[0].findall(OPERATION)
        self.assertEqual(len(operations), 10)

    def test_find_in_xml_tag_multiple_children(self):
        root = etree.Element("root")
        children = etree.Element('children')
        for i in xrange(1, 5):
            name = "child{}".format(i)
            child = etree.Element(name.upper())
            child.text = '{}'.format(name)
            children.append(child)
        root.append(children)
        result = self.client.find_in_tag(children, 'CHILD')
        self.assertEqual(result, 'child1 child2 child3 child4')

    def test_find_in_tag_single_child(self):
        root = etree.Element("root")
        child_name = 'child'
        child = etree.Element(child_name.upper())
        child.text = '{}'.format(child_name)
        root.append(child)
        result = self.client.find_in_tag(root, 'CHILD')
        self.assertEqual(result, 'child')

    def test_read_lookup_file(self):
        response = self.client.read_lookup_file('tests/test_dir/persons')
        expected = [
            ('imie', 'nazwisko'),
            (u'imię', 'nazwisko'),
            ('stefan', u'brzęczyszczykiewicz'),
            ('stefan', u'brzęczyszczyk'),
            ('marian', 'kowalski'),
            ('witold', u'wójcik'),
            ('witek', u'wójcik'),
            ('witek', u'wojcik'),
        ]
        expected = sorted(expected, key=lambda x: x[1])
        self.assertListEqual(response, expected)

    def test_read_lookup_file_multiple_persons(self):
        response = self.client.read_lookup_file('tests/test_dir/persons')
        expected = [
            ('imie', 'nazwisko'),
            (u'imię', 'nazwisko'),
            ('stefan', u'brzęczyszczykiewicz'),
            ('stefan', u'brzęczyszczyk'),
            ('marian', 'kowalski'),
            ('witold', u'wójcik'),
            ('witek', u'wójcik'),
            ('witek', u'wojcik'),
        ]
        expected = sorted(expected, key=lambda x: x[1])
        self.assertListEqual(response, expected)

        response = self.client.read_lookup_file('tests/test_dir/dir_1/file_1.txt')
        expected = [
            ('pierwsz', 'osoba'),
        ]
        self.assertListEqual(response, expected)

    def test_get_files_with_names(self):
        utils.INPUT = 'tests/test_dir'
        self.client.lookup_dirs = ['dir_1', 'dir_2']
        response = self.client._get_files_with_names()
        expected = [
            'tests/test_dir/dir_1/file_1.txt',
            'tests/test_dir/dir_1/file_2.txt',
            'tests/test_dir/dir_2/some_file_1.txt',
            'tests/test_dir/dir_2/some_file_2.txt',
        ]
        self.assertListEqual(response, expected)

    def test_get_operations_from_statements(self):
        statement1 = etree.Element(utils.STATEMENT)
        operation1 = etree.Element(utils.OPERATION)
        operation2 = etree.Element(utils.OPERATION)
        statement1.append(operation1)
        statement1.append(operation2)
        statements = [statement1]
        response = self.client._get_operations_from_statements(statements)
        expected = [operation1, operation2]
        self.assertListEqual(response, expected)

    def test_analyze_operations(self):
        f = self.open_xml_file(self.xml_file)
        root = self.client.parse_xml(f)
        statements = root.findall(STATEMENT)
        operations = statements[0].findall(OPERATION)
        persons = self.client.read_lookup_file(self.persons_file)
        self.client.lookup_persons = persons
        response = self.client.analyze_operations(operations)
        self.assertEqual(len(response[0]), 7)
        self.assertEqual(len(response[1]), 9)

    def test_search_for_payments(self):
        utils.INPUT = 'tests'
        utils.LOOKUP_FILES = ['dir_1']
        self.client.lookup_dirs = ['test_dir']
        self.client.input_files = ['fixtures.xml']
        response = self.client.search_for_payments()
        expected = [
            {
                'dir_name': 'dir_1',
                'file_name': 'file_1',
                'certain_results': [],
                'likely_results': [],
                'title': 'dir_1_fixtures',
                'payments_file': 'fixtures',
            },
            {
                'dir_name': 'dir_2',
                'file_name': 'some_file_1',
                'certain_results': [],
                'likely_results': [],
                'title': 'dir_2_fixtures',
                'payments_file': 'fixtures',
            },
            {
                'dir_name': 'dir_1',
                'file_name': 'file_2',
                'certain_results': [],
                'likely_results': [],
                'title': 'dir_1_fixtures',
                'payments_file': 'fixtures',
            },
            {
                'dir_name': 'dir_2',
                'file_name': 'some_file_2',
                'certain_results': [],
                'likely_results': [],
                'title': 'dir_2_fixtures',
                'payments_file': 'fixtures',
            }
        ]
        self.assertListEqual(sorted(response), sorted(expected))

    def test_prepare_output_file(self):
        utils.OUTPUT = self._OUTPUT
        certain = u'certain_text'
        likely = u'likely_text'
        data = [
            {
                'dir_name': 'dir_1',
                'file_name': 'file_1',
                'certain_results': [
                    certain,
                ],
                'likely_results': [
                    likely,
                ],
                'title': 'dir_1_fixtures',
                'payments_file': 'fixtures',
            },
        ]
        self.client.prepare_output_file(data[0])
        output_files = os.listdir(self._OUTPUT_DIR)
        self.assertEqual(len(output_files), 2)
        path = os.path.join(self._OUTPUT_DIR, output_files[0])
        html_file = open(path).read()
        self.assertIn(certain, html_file.decode('utf8'))
        self.assertIn(likely, html_file.decode('utf8'))
