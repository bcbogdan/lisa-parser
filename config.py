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

import datetime
import argparse
import json
import logging.config
import os

def init_arg_parser():
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        "xml_file_path", help="path to the xml config file"
    )
    arg_parser.add_argument("log_file_path", help="path to the ica log file")
    arg_parser.add_argument(
        "-c", "--config",
        help="path to the config file",
        default='config/db.config'
    )
    arg_parser.add_argument(
        "-l", "--loglevel",
        help="logging level",
        default=2, type=int
    )
    arg_parser.add_argument(
        "-k", "--skipkvp",
        default=False,
        action='store_true',
        help="flag that indicates if commands to the VM are run"
    )
    arg_parser.add_argument(
        "-p", "--perf",
        default=False,
        help="flag that indicates if a performance test is being processed and the"
             "path to the report file"
    )

    return arg_parser


def validate_input(parsed_arguments):
    # TODO - Add help messages for each case
    if not os.path.exists(parsed_arguments.xml_file_path) or \
            not os.path.exists(parsed_arguments.log_file_path):
        return False

    if not os.path.exists(parsed_arguments.config):
        return False

    if parsed_arguments.perf:
        if not os.path.exists(parsed_arguments.perf):
            return False

    return True


def setup_logging(
        default_path='config/log_config.json',
        default_level=logging.INFO,
        env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    if default_level == 1:
        level = logging.WARNING
    elif default_level == 2:
        level = logging.INFO
    elif default_level == 3:
        level = logging.DEBUG
    else:
        level = logging.INFO

    path = default_path
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
            config['handlers']['debug_file_handler']['filename'].split('.')

        error_log_file = \
            config['handlers']['error_file_handler']['filename'].split('.')

        config['handlers']['debug_file_handler']['filename'] = \
            os.path.join(log_folder, info_log_file[0] + '-' +
                         datetime.datetime.now()
                         .strftime("%Y-%m-%d_%H-%M-%S") +
                         info_log_file[1])

        config['handlers']['error_file_handler']['filename'] = \
            os.path.join(log_folder, error_log_file[0] + '-' +
                         datetime.datetime.now()
                         .strftime("%Y-%m-%d_%H-%M-%S") +
                         error_log_file[1])

        config['root']['level'] = level

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=level)
