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

import getopt


def parse_arguments(arg_list):
    xml_file = ''
    log_file = ''

    try:
        opts, args = getopt.getopt(arg_list,
                                   "hx:l:", ["xmlfile=", "logfile="])
    except getopt.GetoptError:
        print('persist.py -x <XmlFile> -l <LogFile>')
        return False

    for opt, arg in opts:
        if opt == '-h':
            print('persist.py -x <XmlFile> -l <LogFile>')
            return False
        elif opt in ("-x", "--xmlfile"):
            xml_file = arg
        elif opt in ("-l", "--logfile"):
            log_file = arg

    return xml_file, log_file
