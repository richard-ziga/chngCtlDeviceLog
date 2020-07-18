#!/usr/bin/env python

# THIS HELPS RUN THE SCRIPT ON PYTHON 2 OR 3
from __future__ import absolute_import, division, print_function

# IMPORT MODULES
import json
import mytools
import netmiko
import signal
import sys

# THIS PREVENTS TRACEBACK FOR THE ^C
signal.signal(signal.SIGINT, signal.SIG_DFL)  # KeyboardInterrupt: Ctrl-C

# THIS WILL LOOK FOR X INPUTS
if len(sys.argv) < 3:
    print('Usage: sendconfig.py commands.txt devices.json')
    exit()

# THIS WILL CHECK FOR CONNECTION PROBLEMS AND PUT THEM IN THE VARIABLE
netmiko_exceptions = (netmiko.ssh_exception.NetMikoTimeoutException,
                      netmiko.ssh_exception.NetMikoAuthenticationException)

# THIS GETS USERNAME PASSWORD AND CHANGE NUMBER
username, password = mytools.get_credentials()

change_number = mytools.get_input('Please enter and approved change number: ')

# THIS LOADS THE COMMAND LINE ARGUMENTS INTO VARIABLES
with open(sys.argv[1]) as cmd_file:
    commands = cmd_file.readlines()

with open(sys.argv[2]) as dev_file:
    devices = json.load(dev_file)

# THIS IS PREP FOR THE WRITE TO RESULTS-CHANGE.JSON FILE AT THE END
results = {'Successful': [], 'Failed': []}

# THIS IS THE CORE - IN THIS SCRIPT A CONFIG COMMAND  WRITES  AND OUTPUT IS
# WRITTEN TO A FILE FOR EACH DEVICE
for device in devices:
    device['username'] = username
    device['password'] = password
    try:
        print('~' * 79)
        print('Connecting to device:', device['ip'])
        print()
        connection = netmiko.ConnectHandler(**device)
        log_message = 'send log 6 "{} change {}"'
        connection.send_command(log_message.format('Starting', change_number))
        connection.send_config_set(commands)
        connection.send_command('wr')
        connection.send_command(log_message.format('Completed', change_number))
        filename = connection.base_prompt + '.txt'
        with open(filename, 'w') as out_file:
            for command in commands:
                out_file.write('## Output of ' + command + '\n\n')
        connection.disconnect()

# HERE THE RESULTS IS WRITTEN TO VARIABLES
        results['Successful'].append(device['ip'])
    except netmiko_exceptions as error:
        print('Failed to ', device['ip'], error)
        results['Failed'].append(': '.join((device['ip'], str(error))))

# HERE THE RESULTS ARE WRITTEN TO A RESULTS-CHANGE.JSON FILE
print(json.dumps(results, indent=2))
with open('results-' + change_number + '.json', 'w') as results_file:
    json.dump(results, results_file, indent=2)
