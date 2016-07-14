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
import time
import sys
from envparse import env
from lisa_parser import ParseXML
from lisa_parser import parse_log_file
import parse_arguments
import sql_utils
import vm_utils


def create_tests_list(tests_dict):
    """
    Method creates a list of dicts with keys that
    match the column names from the SQL Server table,
    each dict corresponding to a table line
    """
    tests_list = list()
    for test_name, test_props in tests_dict['tests'].iteritems():
        for name, details in tests_dict['vms'].iteritems():
            test_dict = dict()
            test_dict['TestLocation'] = details['TestLocation']
            test_dict['HostName'] = details['hvServer']
            test_dict['HostVersion'] = details['hostOSVersion']
            test_dict['GuestOSType'] = details['os']
            try:
                test_dict['TestResult'] = test_props['results'][name]
            except KeyError:
                print('Test result not found for %s on vm %s' %
                      (test_name, name))
                continue
            test_dict['TestCaseName'] = test_name
            test_dict['TestArea'] = tests_dict['testSuite']
            test_dict['TestDate'] = format_date(tests_dict['timestamp'])
            test_dict['GuestOSDistro'] = details['OSName']
            test_dict['KernelVersion'] = details['OSBuildNumber']
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


def get_vm_info(vms_dict):
    """
    Method calls the get_vm_details function in order
    to find the Kernel version and Distro Name from the vm
    and saves them in the vm dictionary
    """
    for vm_name, vm_details in vms_dict.iteritems():
        vm_values = vm_utils.get_vm_details(vm_name, vm_details['hvServer'])
        if not vm_values:
            print('Unable to get vm details for %s' % vm_name)
            sys.exit(2)

        vm_info = {}

        # Stop VM
        vm_utils.manage_vm('stop', vm_name, vm_details['hvServer'])
        for value in vm_values.split('\r\n')[:-1]:
            result_tuple = ParseXML.parse_from_string(value)
            vm_info.update({
                result_tuple[0]: result_tuple[1]
            })

        vm_details['OSBuildNumber'] = vm_info['OSBuildNumber']
        vm_details['OSName'] = vm_info['OSName']

    return vms_dict


def create_tests_dict(xml_file, log_file):
    """
    The method creates the general tests dictionary
     in order for it to be processed for db insertion
    """
    # Parsing given xml and log files
    xml_parser = ParseXML(xml_file)
    tests_object = xml_parser()
    parse_log_file(log_file, tests_object)

    # Getting more VM details from KVP exchange
    is_booting = False
    for vm_name, vm_details in tests_object['vms'].iteritems():
        if not vm_utils.manage_vm('check', vm_name, vm_details['hvServer']):
            print('Starting %s' % vm_name)
            if vm_utils.manage_vm('start', vm_name, vm_details['hvServer']):
                is_booting = True
            else:
                print("Unable to start vm. Exiting")
                sys.exit(2)

    if is_booting:
        wait = 40
        print('Waiting %d seconds for VMs to boot' % wait)
        time.sleep(wait)

    tests_object['vms'] = get_vm_info(tests_object['vms'])

    return tests_object


def main(args):
    env.read_envfile('config/.env')
    # Parse arguments and check if they exist
    input_files = parse_arguments.parse_arguments(args)

    if not all(input_files):
        print('Invalid command line arguments')
        sys.exit(2)

    tests_object = create_tests_dict(
        input_files[0],
        input_files[1]
    )

    # Parse values to be inserted
    insert_values = create_tests_list(tests_object)

    # Connect to db and insert values in the table
    db_connection, db_cursor = sql_utils.init_connection()
    for table_line in insert_values:
        sql_utils.insert_values(db_cursor, 'TestResults', table_line)

    db_cursor.execute('select * from TestResults')

    rows = db_cursor.fetchall()
    for row in rows:
        print(row)

    db_connection.commit()

if __name__ == '__main__':
    main(sys.argv[1:])
