#!/usr/bin/python
import argparse
import logging
import logging.config
import sys

def main():
    return_value = 0

    argument_parser = argparse.ArgumentParser(description='Cloud Backup Api Shell')
    argument_parser.add_argument('--user-config', default=None, type=argparse.FileType('r'), required=True, help='JSON file containing username and API Key')
    argument_parser.add_argument('-dc', '--datacenter', default='ord', type=str, required=True, help='Datacenter the system is in', choices=['lon', 'syd', 'hkg', 'ord', 'iad', 'dfw'])
    argument_parser.add_argument('-lg', '--log-config', default=None, type=str, dest='logconfig', help='log configuration file')
    argument_parser.add_argument('--use-snet', default=False, action='store_true', help='Use Service Net instead of Public Net')

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

    from cloudbackup.cmd.shell.interface import CloudBackupApiShell
    shell = CloudBackupApiShell(
        log,
        arguments.user_config,
        arguments.datacenter,
        use_servicenet=arguments.use_snet
    )

    return_value = shell.doShell()

    return return_value


if __name__ == "__main__":
    sys.exit(main())
