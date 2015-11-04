# coding=utf-8
"""
Script will contain classes and methods for parsing pdf files and search
for mentioned in names file pair of strings.
"""
import os

from lxml import etree
import utils


class PaymentAnalyzer:
    """
    This class contains methods responsible for managing payments file
    for different persons/localizations. As required on init must be
    provided `lookup_files` that should be dictionary with keys
    *person* and *localizations* where this last should be presented
    as list of files that should be looked in `input_files` which
    should be also list but with special xml files.
    """

    def __init__(self, **kwargs):
        self.lookup_dirs = utils.LOOKUP_FILES
        self.input_files = utils.INPUT_FILES
        self.lookup_persons = []
        self.localizations = []

    @staticmethod
    def _get_operations_from_statements(statements):
        """
        Prepare list of all operations in all statements

        :param statements: list of statements Elements
        :return: list of operations Elements
        """
        operations = []
        for statement in statements:
            operations.extend(statement.findall(utils.OPERATION))
        return operations

    def search_payments(self, xml_file, localization):
        """
        Search payments according to the persons list in `xml_file`.

        :param xml_file: xml file
        :return: dictionary with data about payments
        """
        root = self.parse_xml(open(xml_file, 'rb'))
        statements = root.findall(utils.STATEMENT)
        operations = self._get_operations_from_statements(statements)
        certain_results, likely_results = self.analyze_operations(operations)
        payments_file = os.path.basename(xml_file).split('.')[0]
        file_name = os.path.basename(localization).split('.')[0]
        person = os.path.dirname(localization).split('/')[-1:][0]
        title = '{}_{}'.format(person, payments_file)
        return {
            'dir_name': person,
            'file_name': file_name,
            'title': title,
            'certain_results': certain_results,
            'likely_results': likely_results,
            'payments_file': payments_file,
        }

    def analyze_operations(self, operations):
        """
        Analyze `operations` according to the list of persons taken from
        class variable. If `first_name` and `last_name` were found in
        `pay_description` properly formatted record is appended
        `certain_results` list. In case when only part of last_name was
        matched and whole first_name such payment is going to
        `likely_results` list.

        :param operations: list of operation Elements
        :return: certain_results, likely_results
        """
        certain_results = []
        likely_results = []
        template = "%s; %s; %szl; %s; %s;"
        for operation in operations:
            description = self.find_in_tag(operation, utils.DESCRIPTION)
            operation_amount = self.find_in_tag(operation, utils.AMOUNT)
            if description == utils.EXTERNAL_TRANSFER:
                payer = self.find_in_tag(operation, utils.NAME)
                st_date = self.find_in_tag(operation, utils.STATEMENT_DATE)
                pay_description = self.find_in_tag(
                    operation, utils.OPERATION_CONTENT
                ).lower()
                for child in self.lookup_persons:
                    first_name = child[0] in pay_description
                    last_name = child[1] in pay_description
                    if last_name and first_name:
                        first_name = child[0]
                        last_name = child[1]
                        certain_results.append(
                            template % (
                                last_name, first_name, operation_amount,
                                st_date, pay_description
                            )
                        )
                    else:
                        last_name = child[1][:-2] in pay_description.lower()
                        if last_name:
                            likely_results.append(
                                template % (
                                    payer, child[1], operation_amount,
                                    st_date, pay_description
                                )
                            )
        return certain_results, likely_results

    @staticmethod
    def _is_string(text):
        return isinstance(text, (str, unicode))

    def find_in_tag(self, parent, tag):
        """
        Method lookup in `parent` specified `tag`.
        It returns string with concatenates texts of founded tags.

        :param parent: parent object where should be looking for
        :param tag: tag object to be found
        :return: all founded objects text joined to one string
        """
        look = "*[starts-with(local-name(), '{}')]".format(tag)
        tags = [e.text for e in parent.xpath(look) if self._is_string(e.text)]
        return ' '.join(tags)

    @staticmethod
    def prepare_output_file(payment_data):
        """
        Method get template file and prepare output in html format.
        Finally it writes output to new html file.

        :param payment_data: parameters
        """
        template = open("./templates/index.html", 'r').read()
        title = "<div id='title'><h1>%s</h1></div>" % payment_data.get('title')
        primary_table = "<h1>Płatności pewne</h1><table " \
                        "id='primary_result'><tr>" \
                        "<td class='header'>nazwisko dziecka</td>" \
                        "<td class='header'>imię dziecka</td>" \
                        "<td class='header'>kwota</td>" \
                        "<td class='header'>dnia</td>" \
                        "<td class='header'>tytul przelewu</td></tr>"
        secondary_table = "<h1 class='red'>Płatności podobne</h1><table " \
                          "id='secondary_result'><tr>" \
                          "<td class='header'>wpłacający</td>" \
                          "<td class='header'>nazwisko dziecka</td>" \
                          "<td class='header'>kwota</td>" \
                          "<td class='header'>dnia</td>" \
                          "<td class='header'>tytul przelewu</td></tr>"

        for certain_row in payment_data.get('certain_results'):
            primary_table = '%s<tr>' % primary_table
            for field in certain_row.split(';'):
                primary_table = '%s<td>%s</td>' % (
                    primary_table, field.encode('utf-8')
                )
            primary_table = '%s</tr>' % primary_table

        for likely_row in payment_data.get('likely_results'):
            secondary_table = '%s<tr>' % secondary_table
            for field in likely_row.split(';'):
                secondary_table = '%s<td>%s</td>' % (
                    secondary_table, field.encode('utf-8')
                )
            secondary_table = '%s</tr>' % secondary_table

        primary_table = '%s</tr></table>' % primary_table
        secondary_table = '%s</tr></table>' % secondary_table
        result = template.replace("<div id='title'></div>", title)
        result = result.replace(
            '<title></title>',
            '<title>%s</title>' % payment_data.get('title')
        )
        result = result.replace(
            "<table id='primary'></table>", primary_table
        )
        result = result.replace(
            "<table id='secondary'></table>", secondary_table
        )
        file_name = '{}_{}.html'.format(
            payment_data.get('payments_file'),
            payment_data.get('file_name')
        )
        path = os.path.join(
            utils.OUTPUT, payment_data.get('dir_name'), file_name
        )
        output = open(path, 'w')
        output.write(result)
        output.close()

        css_path = os.path.join(
            utils.OUTPUT, payment_data.get('dir_name'), utils.STYLE_FILE
        )
        output_css = open(css_path, 'w')
        output_css.write(open("./templates/style.css", 'r').read())
        output_css.close()

    @staticmethod
    def parse_xml(xml_input, root_tag=None):
        """
        Parse incoming xml file

        :param xml_input: input file in xml format
        :param root_tag: special root tag if needed to point
        :return: xml tree object
        """
        try:
            tree = etree.parse(xml_input)
            root = tree.getroot()
            return root.find(root_tag) if root_tag else root
        except etree.XMLSyntaxError:
            return 'XML syntax error'

    def read_lookup_file(self, localization):
        """
        Read string pairs and put them into class dictionary

        :return: sorted
        """
        for person in open(localization):
            self.lookup_persons.append(
                tuple(person.decode('utf8').lower().split())
            )
        return sorted(set(self.lookup_persons), key=lambda x: x[1])

    def _get_files_with_names(self):
        files = []
        for directory in self.lookup_dirs:
            path = os.path.join(utils.INPUT, directory)
            for root, dirs, file_names in os.walk(path):
                files = [
                    os.path.join(root, f)
                    for f in file_names if f.endswith('txt')
                ]
                files.extend(files)
        return files

    def search_for_payments(self):
        payments = []
        for _file in self._get_files_with_names():
            self.lookup_persons = self.read_lookup_file(_file)
            for input_file in self.input_files:
                input_file = os.path.join(utils.INPUT, input_file)
                payments.append(self.search_payments(input_file, _file))
        return payments


if __name__ == "__main__":
    parser = PaymentAnalyzer()
    payments_data = parser.search_for_payments()
    for data in payments_data:
        parser.prepare_output_file(data)
