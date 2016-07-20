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
import os
import json
import logging.config
import datetime


def parse_arguments(arg_list):
    xml_file = ''
    log_file = ''
    env_file = ''
    log_level = 2

    try:
        opts, args = getopt.getopt(arg_list,
                                   "he:x:l:a:", ["xmlfile=", "logfile=", "dbg=", "env="])
    except getopt.GetoptError:
        print('Invalid command line arguments:')
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
        elif opt in ('-e', "--env"):
            env_file = arg
        elif opt in ('-a', "--dbg"):
            log_level = arg

    return xml_file, log_file, env_file, log_level


def setup_logging(
        default_path='config/log_config.json',
        default_level=logging.INFO,
        env_key='LOG_CFG'
):
    """
    Setup logging configuration
    """
    path = default_path
    level = default_level
    value = os.getenv(env_key, None)
    log_folder = 'logs'

    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as log_config:
            config = json.load(log_config)
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)

        info_log_file = \
            config['handlers']['info_file_handler']['filename'].split('.')

        error_log_file = \
            config['handlers']['error_file_handler']['filename'].split('.')

        config['handlers']['info_file_handler']['filename'] = \
            os.path.join(log_folder, info_log_file[0] + '-' +
                         datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") +
                         info_log_file[1])

        config['handlers']['error_file_handler']['filename'] = \
            os.path.join(log_folder, error_log_file[0] + '-' +
                         datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") +
                         error_log_file[1])

        config['root']['level'] = level

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=level)
