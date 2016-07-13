import subprocess
from envparse import env


def manage_vm(action, vm_name, hv_server):
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
        return False
    else:
        return True


def get_vm_details(vm_name, hv_server):
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

    if ps_command.stdout:
        return ps_command.stdout.read()
    else:
        return False
