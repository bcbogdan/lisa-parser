"""
Copyright (c) Cloudbase Solutions 2016
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import print_function
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree
import re
import logging


class ParseXML(object):
    """
    Class used to parse a specific xml test suite file
    """
    def __init__(self, file_path):
        self.tree = ElementTree.ElementTree(file=file_path)
        self.root = self.tree.getroot()

    def get_tests(self):
        """
        Iterates through the xml file looking for <test> sections
         and initializes a dict for every test case returning them in
         the end

         Dict structure:
            { 'testName' : { 'details' : {}, 'results' : {} }
        """
        logger = logging.getLogger(__name__)
        logger.debug('Initializing empty tests dict')
        tests_dict = dict()

        logger.debug('Iterating through suiteTest section')
        for test in self.root.iter('suiteTest'):
            tests_dict[test.text.lower()] = {
                'details': {},
                'results': {}
            }

            for test_case in self.root.iter('test'):
                # Check if testCase was not commented out
                if test_case.find('testName').text == test.text:
                    logger.debug('Getting test details for - %s', test.text)
                    tests_dict[test.text.lower()]['details'] = \
                        self.get_test_details(test_case)

        return tests_dict

    @staticmethod
    def get_test_details(test_root):
        """
        Gets and an XML object and iterates through it
         parsing the test details into a dictionary

         Dict structure:
            { 'testProperty' : [ value(s) ] }
        """

        test_dict = dict()
        for test_property in test_root.getchildren():
            if test_property.tag == 'testName':
                continue
            elif not test_property.getchildren():
                test_dict[test_property.tag] = \
                    test_property.text.strip().split()
            else:
                test_dict[test_property.tag] = list()
                for item in test_property.getchildren():
                    if test_property.tag == 'testparams':
                        parameter = item.text.split('=')
                        test_dict[test_property.tag].append(
                            (parameter[0], parameter[1])
                        )
                    else:
                        test_dict[test_property.tag].append(item.text)

        return test_dict

    def get_vms(self):
        """
        Method searches for the 'vm' sections in the XML file
        saving a dict for each vm found.
        Dict structure:
        {
            vm_name: { vm_details }
        }
        """
        logger = logging.getLogger(__name__)
        logger.debug('Getting VM details from XML files')
        vm_dict = dict()
        for machine in self.root.iter('vm'):
            vm_dict[machine.find('vmName').text] = {
                'hvServer': machine.find('hvServer').text,
                'sshKey': machine.find('sshKey').text,
                'os': machine.find('os').text
            }

        return vm_dict

    def __call__(self):
        parsed_xml = dict()
        parsed_xml['testSuite'] = self.root.find('testSuites').getchildren()[0]\
            .find('suiteName').text
        parsed_xml['tests'] = self.get_tests()
        parsed_xml['vms'] = self.get_vms()

        return parsed_xml

    # TODO: Narrow exception field
    @staticmethod
    def parse_from_string(xml_string):
        """
        Static method that parses xml content from a string
        The method is used to parse the output of the PS command
        that is sent to the vm in order to get more details

        It returns a dict with the following structure:
        {
            vm_property: value
        }
        """
        logger = logging.getLogger(__name__)
        try:
            logger.debug('Converting XML string from PS Command')
            root = ElementTree.fromstring(xml_string.strip())
            prop_name = ''
            prop_value = ''
            for child in root:
                if child.attrib['NAME'] == 'Name':
                    prop_name = child[0].text
                elif child.attrib['NAME'] == 'Data':
                    prop_value = child[0].text

            return prop_name, prop_value
        except Exception, ex:
            logger.error('Failed to parse XML string,', exc_info=True)
            return False


def parse_log_file(log_file, test_results):
    """
    Parses through the final log file, ica.log,
     looking for the test results and test timestamp
     and saving the in the previously created object from
     the xml file
    """
    # Go through log file until the final results part
    logger = logging.getLogger(__name__)
    logger.debug('Iterating through %s file until the test results part', log_file)
    with open(log_file, 'r') as log_file:
        for line in log_file:
            if line.strip() == 'Test Results Summary':
                break

        # Get timestamp
        logging.debug('Saving timestamp of test run')
        test_results['timestamp'] = re.search(
            '([0-9/]+) ([0-9:]+)',
            log_file.next()).group(0)
        vm_name = ""
        logging.debug('Timestamp - %s', test_results['timestamp'])

        for line in log_file:
            line = line.strip()
            if re.search("^VM:", line) and len(line.split()) == 2:
                vm_name = line.split()[1]
                logging.debug('Saving VM name - %s', vm_name)
                # Check if there are any details about the VM
                try:
                    test_results['vms'][vm_name]['TestLocation'] = 'Hyper-V'
                except KeyError:
                    test_results['vms'][vm_name] = dict()
                    test_results['vms'][vm_name]['TestLocation'] = 'Azure'

            # TODO: Find better regex pattern
            elif re.search('^Test', line) and \
                    re.search('(Success|Failed)', line):
                test = line.split()
                try:
                    test_results['tests'][test[1].lower()]['results'][vm_name] = \
                        test[3]
                    logging.debug('Saving test result for %s - %s',
                                  test[1].lower(), test[3])
                except KeyError:
                    logging.debug('Test %s was not listed in Test Suites section. '
                                  'It will be ignored from the final results', test)
            elif re.search('^OS', line):
                test_results['vms'][vm_name]['hostOSVersion'] = \
                    line.split(':')[1].strip()
                logging.debug('Saving Host OS Version - %s',
                              test_results['vms'][vm_name]['hostOSVersion'])
            elif re.search('^Server', line):
                test_results['vms'][vm_name]['hvServer'] = \
                    line.split(':')[1].strip()
                logging.debug('Saving server location - %s',
                              test_results['vms'][vm_name]['hvServer'])
            elif re.search('^Logs can be found at', line):
                test_results['logDir'] = line.split()[-1]
                logging.debug('Saving log folder path - %s', test_results['logDir'])

    return test_results
