import pyodbc
import subprocess
import time
from string import Template
from envparse import env
from lisa_parser import ParseXML
from lisa_parser import parse_log_file
import pprint
import re


def create_tests_list(tests_dict):
    tests_list = list()
    for test_name, test_props in tests_dict['tests'].iteritems():
        for vm_name, vm_details in tests_dict['vms'].iteritems():
            test_dict = dict()
            test_dict['HostName'] = vm_details['hvServer']
            test_dict['HostVersion'] = vm_details['hostOSVersion']
            test_dict['GuestOSType'] = vm_details['os']
            test_dict['TestResult'] = tests_dict['tests'][test_name]['results'][vm_name][0]
            test_dict['TestCaseName'] = test_name
            test_dict['TestArea'] = tests_dict['testSuite']
            test_dict['TestDate'] = format_date(tests_dict['timestamp'])
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
    pp = pprint.PrettyPrinter(indent='4')
    xml_obj = ParseXML('demo_files/test.xml')
    tests_object = xml_obj()
    parse_log_file('demo_files/ica.log', tests_object)

    pp.pprint(tests_object)
    time.sleep(10)