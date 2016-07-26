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
import logging
import time
import sys
from envparse import env
from lisa_parser import ParseXML
from lisa_parser import parse_log_file
import config
import sql_utils
import vm_utils

logger = logging.getLogger(__name__)


def create_tests_list(tests_dict):
    """
    Method creates a list of dicts with keys that
    match the column names from the SQL Server table,
    each dict corresponding to a table line
    """
    logger.debug('Creating a list with the lines to be inserted')
    tests_list = list()
    # TODO : Check not to save empty values
    for test_name, test_props in tests_dict['tests'].iteritems():
        for name, details in tests_dict['vms'].iteritems():
            test_dict = dict()

            # Getting test id from tests dict
            try:
                for param in test_props['details']['testparams']:
                    if param[0] == 'TC_COVERED':
                        test_dict['TestID'] = param[1]
            except KeyError:
                logger.warning('No params found for %s', test_name)

            test_dict['TestLocation'] = details['TestLocation']
            test_dict['HostName'] = details['hvServer']
            test_dict['HostVersion'] = details['hostOSVersion']
            test_dict['GuestOSType'] = details['os']

            try:
                test_dict['TestResult'] = test_props['results'][name]
                test_dict['LogPath'] = tests_dict['logDir']
            except KeyError, ex:
                logger.warning('Test result not found for %s on vm %s',
                               test_name, name)
                continue

            try:
                test_dict['LISVersion'] = test_props['lisVersion']
            except KeyError, ex:
                logger.warning('LIS Version not found in XML file')

            test_dict['TestCaseName'] = test_name
            test_dict['TestArea'] = tests_dict['testSuite']
            test_dict['TestDate'] = format_date(tests_dict['timestamp'])

            try:
                test_dict['GuestOSDistro'] = details['OSName']
                test_dict['KernelVersion'] = details['OSBuildNumber']
            except KeyError, ex:
                logger.warning('Not saving distro and kernel version for test %s', test_name)
            logger.debug(test_dict)
            tests_list.append(test_dict)

    return tests_list


def format_date(test_date):
    """
    Formats the date taken from the log file
     in order to align with the sql date format - YMD
    """
    split_date = test_date.split()
    split_date[0] = split_date[0].split('/')
    return ''.join(
        [split_date[0][2], split_date[0][0], split_date[0][1]]
    )


def parse_cmd_output(cmd_ouput):
    vm_info = {}
    for value in cmd_ouput.split('\r\n')[:-1]:
        result_tuple = ParseXML.parse_from_string(value)
        vm_info.update({
            result_tuple[0]: result_tuple[1]
        })
    return vm_info


def get_vm_info(vms_dict, wait_to_boot, timeout=180):
    """
    Method calls the get_vm_details function in order
    to find the Kernel version and Distro Name from the vm
    and saves them in the vm dictionary
    """

    for vm_name, vm_details in vms_dict.iteritems():
        logging.debug('Running PS command to get details for %s', vm_name)
        vm_values = vm_utils.run_cmd('vm-info', vm_name, vm_details['hvServer'])
        is_booting = True

        if wait_to_boot[vm_name]:
            start = time.time()

        while is_booting:
            vm_info = parse_cmd_output(vm_values)

            if 'OSName' in vm_info.keys():
                is_booting = False
                continue

            current_time = time.time()
            if int(current_time - start) > timeout:
                logger.error('Unable to get details for %s', vm_name)
                sys.exit(0)

            logging.debug('Running PS command to get details for %s', vm_name)
            vm_values = vm_utils.run_cmd(
                'vm-info', vm_name, vm_details['hvServer']
            )

        logger.debug('Parsing xml output of PS command')
        for value in vm_values.split('\r\n')[:-1]:
            result_tuple = ParseXML.parse_from_string(value)
            vm_info.update({
                result_tuple[0]: result_tuple[1]
            })

        vm_details['OSBuildNumber'] = vm_info['OSBuildNumber']
        vm_details['OSName'] = ' '.join([vm_info['OSName'], vm_info['OSMajorVersion']])
        logger.debug('Saving %s and %s from parsed command',
                     vm_info['OSBuildNumber'], vm_details['OSName'])

    return vms_dict


def create_tests_dict(xml_file, log_file, run_vm_commands=True):
    """
    The method creates the general tests dictionary
     in order for it to be processed for db insertion
    """
    # Parsing given xml and log files
    logger.info('Parsing XML file - %s', xml_file)
    xml_parser = ParseXML(xml_file)
    tests_object = xml_parser()
    parse_log_file(log_file, tests_object)

    if run_vm_commands:
        # Getting more VM details from KVP exchange
        # TODO : Section should be handled by separate method
        logger.info('Getting VM details using PS Script')
        wait_to_boot = {}
        for vm_name, vm_details in tests_object['vms'].iteritems():
            logging.debug('Checking %s status', vm_name)
            vm_state = vm_utils.run_cmd('check', vm_name, vm_details['hvServer'])

            if vm_state.split('-----')[1].strip() == 'Off':
                logging.info('Starting %s', vm_name)
                vm_utils.run_cmd('start', vm_name, vm_details['hvServer'])
                wait_to_boot[vm_name] = True
            else:
                wait_to_boot[vm_name] = False

        tests_object['vms'] = get_vm_info(tests_object['vms'], wait_to_boot)

        # Stop VM
        logger.info('Running stop vm command')
        [
            vm_utils.run_cmd('stop', vm_name, vm_details['hvServer'])
            for vm_name, vm_details in tests_object['vms'].iteritems()
        ]

    return tests_object


def main(args):
    """
    The main entry point of the application
    """
    # Parse arguments and check if they exist
    parsed_arguments = config.parse_arguments(args)

    if not config.validate_input(parsed_arguments):
        print('Invalid command line arguments')
        sys.exit(0)

    config.setup_logging(
        default_level=int(parsed_arguments['level'])
    )

    logger.debug('Parsing env variables')
    env.read_envfile(parsed_arguments['env'])

    logger.info('Creating tests dictionary')
    tests_object = create_tests_dict(
        parsed_arguments['xml'],
        parsed_arguments['log'],
        parsed_arguments['vmInfo']
    )

    # Parse values to be inserted
    logger.info('Parsing tests dictionary for database insertion')
    insert_values = create_tests_list(tests_object)

    # Connect to db and insert values in the table
    logger.info('Initializing database connection')
    db_connection, db_cursor = sql_utils.init_connection()

    logger.info('Executing insertion commands')
    for table_line in insert_values:
        sql_utils.insert_values(db_cursor, 'TestResults', table_line)

    logger.info('Committing changes to the database')
    db_connection.commit()

if __name__ == '__main__':
    main(sys.argv[1:])
