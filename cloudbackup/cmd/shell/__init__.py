#!/usr/bin/python
import argparse
import logging
import logging.config
import sys

import cloudbackup.cmd.shell.config

def main():
    return_value = 0

    argument_parser = argparse.ArgumentParser(description='Cloud Backup Api Shell')
    argument_parser.add_argument('--user-config', default=None, type=argparse.FileType('r'), required=True, help='JSON file containing username and API Key')
    argument_parser.add_argument('-dc', '--datacenter', default='ord', type=str, required=True, help='Datacenter the system is in', choices=['lon', 'syd', 'hkg', 'ord', 'iad', 'dfw'])
    argument_parser.add_argument('-lg', '--log-config', default=None, type=str, dest='logconfig', help='log configuration file')
    argument_parser.add_argument('--use-snet', default=False, action='store_true', help='Use Service Net instead of Public Net')
    argument_parser.add_argument('--api-host', default=None, type=str, required=False, help="Cloud Backup API Host to use. Default is to use the value in the service catalog")
    argument_parser.add_argument('--api-version', default=1, type=int, required=False, help="Cloud Backup API Version.")

    arguments = argument_parser.parse_args()

    # If the caller provides a log configuration then use it
    # Otherwise we'll add our own little configuration as a default
    # That captures stdout and outputs to .agent_unique_constraint_fix-py.log
    if arguments.logconfig is not None:
        logging.config.fileConfig(arguments.logconfig)
    else:
        lf = logging.FileHandler('.rackspace-cloud-backup-api-shell.log')
        lf.setLevel(logging.DEBUG)

        log = logging.getLogger()
        log.addHandler(lf)
        log.setLevel(logging.DEBUG)

    log = logging.getLogger()

    commandLineData = {
        'user': {
            'type': None,
            'id': None,
        },
        'auth': {
            'method': None,
            'value': None
        },
        'options': {
            'apihost': arguments.api_host,
            'apiversion': arguments.api_version,
            'datacenter': arguments.datacenter,
            'useServiceNet': arguments.use_snet
        }
    }

    config_obj = cloudbackup.cmd.shell.config.CloudBackupFileConfig(
        arguments.user_config,
        log,
        commandLineData=commandLineData
    )

    from cloudbackup.cmd.shell.interface import CloudBackupApiShell
    shell = CloudBackupApiShell(
        log,
        config_obj = config_obj
    )

    return_value = shell.doShell()

    return return_value


if __name__ == "__main__":
    sys.exit(main())
