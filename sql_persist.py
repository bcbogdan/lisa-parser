from __future__ import print_function
import time
import sys
from envparse import env
from lisa_parser import ParseXML
from lisa_parser import parse_log_file
import parse_arguments
import sql_utils
import vm_utils

"""
Copyright (c) Cloudbase Solutions
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


# TODO - Check for Test location
def create_tests_list(tests_dict):
    tests_list = list()
    for test_name, test_props in tests_dict['tests'].iteritems():
        for name, details in tests_dict['vms'].iteritems():
            test_dict = dict()
            test_dict['TestLocation'] = details['TestLocation']
            test_dict['HostName'] = details['hvServer']
            test_dict['HostVersion'] = details['hostOSVersion']
            test_dict['GuestOSType'] = details['os']
            test_dict['TestResult'] = test_props['results'][name][0]
            test_dict['TestCaseName'] = test_name
            test_dict['TestArea'] = tests_dict['testSuite']
            test_dict['TestDate'] = format_date(tests_dict['timestamp'])
            test_dict['GuestOSDistro'] = details['OSName']
            test_dict['KernelVersion'] = details['OSBuildNumber']
            tests_list.append(test_dict)

    return tests_list


def format_date(test_date):
    split_date = test_date.split()
    split_date[0] = split_date[0].split('/')
    return ''.join(
        [split_date[0][2], split_date[0][0], split_date[0][1]]
    )


if __name__ == '__main__':
    env.read_envfile('config/.env')

    # Parse arguments and check if they exist
    input_files = parse_arguments.parse_arguments(sys.argv[1:])

    if not all(input_files):
        print('Invalid command line arguments')
        sys.exit(2)

    # Parsing given xml and log files
    xml_parser = ParseXML(input_files[0])
    tests_object = xml_parser()
    parse_log_file(input_files[1], tests_object)

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

    for vm_name, vm_details in tests_object['vms'].iteritems():
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

    #db_connection.commit()
