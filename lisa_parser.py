from __future__ import print_function
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree
import re


class ParseXML(object):
    # TODO: Add try catch handles for search inside XML
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
        tests_dict = dict()
        for test in self.root.iter('test'):
            test_name = test.find('testName').text
            tests_dict[test_name] = dict()
            tests_dict[test_name]['results'] = dict()
            tests_dict[test_name]['details'] = self.get_test_details(test)

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
                test_dict[test_property.tag] = test_property.text.strip().split()
            else:
                test_dict[test_property.tag] = list()
                for item in test_property.getchildren():
                    if test_property.tag == 'testparams':
                        parameter = item.text.split('=')
                        test_dict[test_property.tag].append((parameter[0], parameter[1]))
                    else:
                        test_dict[test_property.tag].append(item.text)

        return test_dict

    def get_vms(self):
        vm_list = list()
        for machine in self.root.iter('vm'):
            vm_list.append((
                machine.find('vmName').text,
                machine.find('hvServer').text,
                machine.find('sshKey').text
            ))

        return vm_list

    def __call__(self):
        parsed_xml = dict()
        parsed_xml['testSuite'] = self.root.find('testSuites').getchildren()[0].find('suiteName').text
        parsed_xml['tests'] = self.get_tests()
        parsed_xml['vms'] = self.get_vms()

        return parsed_xml


def parse_log_file(log_file, test_results):
    """
    Parses through the final log file, ica.log,
     looking for the test results and test timestamp
     and saving the in the previously created object from
     the xml file
    """
    # Go through log file until the final results part
    with open(log_file, 'r') as log_file:
        for line in log_file:
            if 'Test Results Summary' == line.strip():
                break

        # Get timestamp
        test_results['timestamp'] = re.search('([0-9/]+) ([0-9:]+)', log_file.next()).group(0)
        vm_name = ""
        for line in log_file:
            line = line.strip()
            if "VM:" in line:
                vm_name = line.split()[1]
            elif re.search('^Test', line):
                test = line.split()

                # Check if test failed and save error details
                if test[3] == "Failed":
                    log_file.next()
                    error_details = log_file.next().strip()
                else:
                    error_details = ""

                test_results[test[1]]['results'][vm_name] = (test[3], error_details)

    return test_results
