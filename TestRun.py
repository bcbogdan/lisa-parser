from __future__ import print_function
from file_parser import ParseXML
from file_parser import parse_ica_log
from VirtualMachine import VirtualMachine
import logging

logger = logging.getLogger(__name__)


class TestRun(object):
    def __init__(self):
        self.suite = ''
        self.timestamp = ''
        self.log_path = ''
        self.vms = dict()
        self.test_cases = dict()
        self.lis_version = ''

    def update_from_xml(self, xml_path):
        xml_object = ParseXML(xml_path)
        logger.debug('Parsed XML file')
        self.suite = xml_object.get_tests_suite()
        logger.debug('Saving Tests Suite name - %s', self.suite)

        for test_case_name, props in xml_object.get_tests().iteritems():
            logger.debug('Initializing TestCase object for %s', test_case_name)
            self.test_cases[test_case_name] = TestCase(
                name=test_case_name,
                properties=props
            )

        for vm_name, vm_details in xml_object.get_vms().iteritems():
            logger.debug('Initializing VirtualMachine object for %s', vm_name)
            self.vms[vm_name] = VirtualMachine(
                vm_name=vm_name,
                hv_server=vm_details['hvServer'],
                os=vm_details['os']
                )

    def update_from_ica(self, log_path):
        parsed_ica = parse_ica_log(log_path)
        logger.debug('Parsed ICA log file')

        self.timestamp = parsed_ica['timestamp']
        logger.debug('Saving timestamp - %s', self.timestamp)

        try:
            self.log_path = parsed_ica['logPath']
            logger.debug('Saving log folder path - %s', self.log_path)
        except KeyError:
            logger.warning('Log folder path not found in ICA log')

        try:
            self.lis_version = parsed_ica['lisVersion']
            logger.debug('Saving LIS version - %s', self.lis_version)
        except KeyError:
            logger.warning('LIS Version not found in ICA Log')

        for vm_name, props in parsed_ica['vms'].iteritems():
            logger.debug('Updating VM, %s, with details from ICA log',
                         vm_name)
            self.vms[vm_name].host_os = props['hostOS']
            self.vms[vm_name].hv_server = props['hvServer']
            self.vms[vm_name].location = props['TestLocation']

        for test_name, test_props in self.test_cases.iteritems():
            self.test_cases[test_name].update_results(parsed_ica['tests'][test_name])
            logger.debug(
                'Saving test result for %s - %s',
                test_name, parsed_ica['tests'][test_name][1]
            )

    def update_from_vm(self, kvp_fields):
        for vm_name, vm_object in self.vms.iteritems():
            vm_object.update_from_kvp(kvp_fields)

    def parse_for_db_insertion(self):
        insertion_list = list()
        for test_name, test_object in self.test_cases.iteritems():
            for vm_name, vm_object in self.vms.iteritems():
                test_dict = dict()
                try:
                    test_dict['TestResult'] = test_object.results[vm_name]
                except KeyError:
                    logger.error('Unable to find test result for %s on vm %s',
                                 test_name, vm_name)
                    logger.info('Skipping %s for database insertion', test_name)
                    continue

                test_dict['LogPath'] = self.log_path
                test_dict['TestID'] = test_object.covered_cases
                test_dict['TestLocation'] = vm_object.location
                test_dict['HostName'] = vm_object.hv_server
                test_dict['HostVersion'] = vm_object.host_os
                test_dict['GuestOSType'] = vm_object.os
                test_dict['LISVersion'] = self.lis_version
                test_dict['TestCaseName'] = test_name
                test_dict['TestArea'] = self.suite
                test_dict['TestDate'] = TestRun.format_date(
                    self.timestamp
                )

                if not vm_object.kvp_info:
                    test_dict['GuestOSDistro'] = ''
                    test_dict['KernelVersion'] = ''
                    logger.warning('No values found for VM Distro and '
                                   'VM Kernel Version')
                else:
                    try:
                        """For some distros OSMajorVersion field is empty"""
                        test_dict['GuestOSDistro'] = ' '.join([
                            vm_object.kvp_info['OSName'],
                            vm_object.kvp_info['OSMajorVersion']
                        ])
                    except KeyError:
                        test_dict['GuestOSDistro'] = vm_object.kvp_info['OSName']
                    test_dict['KernelVersion'] = vm_object.kvp_info['OSBuildNumber']

                insertion_list.append(test_dict)

        return insertion_list

    @staticmethod
    def format_date(test_date):
        """Formats the date taken from the log file

             in order to align with the sql date format - YMD
            """

        split_date = test_date.split()
        split_date[0] = split_date[0].split('/')
        return ''.join(
            [split_date[0][2], split_date[0][0], split_date[0][1]]
        )


class TestCase(object):
    def __init__(self, name, properties):
        self.name = name
        self.covered_cases = TestCase.get_covered_cases(properties)
        self.results = dict()

    def update_results(self, vm_result):
        self.results[vm_result[0]] = vm_result[1]

    @staticmethod
    def get_covered_cases(properties):
        for param_name, value in properties['testparams']:
            if param_name == 'TC_COVERED':
                return value

        return None
