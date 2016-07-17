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


def manage_vm(action, vm_name, hv_server):
    """
    Method starts, stops or checks a vm depending on
    the action that it has received

    It returns true if the command has been run successfully
    or false if any errors occurred
    """
    command = ''
    if action == 'start':
        command = 'start-vm'
    elif action == 'stop':
        command = 'stop-vm'
    elif action == 'check':
        ps_command = subprocess.Popen([
            env.str('PSPath'), 'get-vm', '-Name',
            vm_name, '-ComputerName', hv_server, '|', 'Select', 'State'
        ], stdout=subprocess.PIPE)

        if ps_command.stdout.read().strip().split('\n')[2].strip() == 'Off':
            print(ps_command.stdout.read())
            return False
        else:
            return True
    else:
        return False

    ps_command = subprocess.Popen([
        env.str('PSPath'), command, '-Name', vm_name,
        '-ComputerName ', hv_server
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if ps_command.stderr.read():
        print(ps_command.stdout.read())
        return False
    else:
        return True


def get_vm_details(vm_name, hv_server):
    """
    Method used to execute a series of PS commands
     in order to retrieve info on the selected vm

     The method returns a string containing XML formatted
     content
    """
    query_strings = [
        '"' + "Select * From Msvm_ComputerSystem where ElementName='" +
        vm_name + "'" + '";',
        '"' + "Associators of {$vm} Where AssocClass=Msvm_SystemDevice "
              "ResultClass=Msvm_KvpExchangeComponent" + '"'
    ]
    ps_command = subprocess.Popen([
        env.str('PSPath'), '$vm', '=',
        'Get-WmiObject', '-ComputerName', "'" + hv_server + "'",
        '-Namespace', "root\\virtualization\\v2", '-Query', query_strings[0],
        '(', 'Get-WmiObject', '-ComputerName', "'" + hv_server + "'",
        '-Namespace', 'root\\virtualization\\v2', '-Query',
        query_strings[1], ').GuestIntrinsicExchangeItems'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if ps_command.stderr().read():
        print(ps_command.stdout.read())
        return False
    else:
        return ps_command.stdout.read()
