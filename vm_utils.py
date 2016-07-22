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

import subprocess
from envparse import env
import logging
import sys

logger = logging.getLogger(__name__)


def execute_command(command_arguments):
    ps_command = subprocess.Popen(
        command_arguments,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout_data, stderr_data = ps_command.communicate()

    logger.debug('Command output %s', stdout_data)

    if ps_command.returncode != 0:
        raise RuntimeError(
            "Command failed, status code %s stdout %r stderr %r" % (
                ps_command.returncode, stdout_data, stderr_data
            )
        )
    else:
        return stdout_data


def run_cmd(cmd_type, vm_name, hv_server):
    cmd_args = [
        env.str('PSPath'), 'cmd', '-Name', vm_name, '-ComputerName',
        hv_server
    ]

    if cmd_type == 'start':
        cmd_args[1] = 'start-vm'
    elif cmd_type == 'stop':
        cmd_args[1] = 'stop-vm'
    elif cmd_type == 'check':
        cmd_args[1] = 'get-vm'
        cmd_args.extend([
            '|', 'Select', 'State'
        ])
    elif cmd_type == 'vm-info':
        query_strings = [
            '"' + "Select * From Msvm_ComputerSystem where ElementName='" +
            vm_name + "'" + '";',
            '"' + "Associators of {$vm} Where AssocClass=Msvm_SystemDevice "
            "ResultClass=Msvm_KvpExchangeComponent" + '"'
        ]

        cmd_args = [
            env.str('PSPath'), '$vm', '=', 'Get-WmiObject', '-ComputerName',
            hv_server, '-Namespace', "root\\virtualization\\v2", '-Query',
            query_strings[0], '(', 'Get-WmiObject', '-ComputerName', hv_server,
            '-Namespace', 'root\\virtualization\\v2', '-Query',
            query_strings[1], ').GuestIntrinsicExchangeItems'
        ]

    try:
        return execute_command(cmd_args)
    except RuntimeError, e:
        logger.error('Error on running command', exc_info=True)
        logger.info('Terminating execution')
        sys.exit(0)
