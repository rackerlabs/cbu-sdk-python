"""A collection of function to take responses from the RCBU API
and convert them into binded objects."""
from rcbu.client.agent import Agent
from rcbu.client.backup_configuration import BackupConfiguration


def agent_from_response(body, connection):
    args = {
        'version': body['AgentVersion'],
        'datacenter': body['Datacenter'],
        'vault_size': body['BackupVaultSize'],
        'host': body['IPAddress'],
        'enabled': not body['IsDisabled'],
        'encrypted': body['IsEncrypted'],
        'agent_id': body['MachineAgentId'],
        'machine_name': body['MachineName'],
        'os': '{} {}'.format(body['OperatingSystem'],
                             body['OperatingSystemVersion']),
        'connection': connection
    }
    return Agent(**args)


def backup_config_from_response(body, connection):
    args = {
        'config_id': body['BackupConfigurationScheduleId'],
        'agent_id': body['MachineAgentId'],
        'config_name': body['BackupConfigurationName'],
        'active': body['IsActive'],
        'frequency': body['Frequency'],
        'data_retention_days': body['VersionRetention'],
        'inclusions': body['Inclusions'],
        'exclusions': body['Exclusions'],
        'email': body['NotifyRecipients'],
        'enabled': body['IsActive'],
        'notify_on_success': body['NotifySuccess'],
        'notify_on_fail': body['NotifyFailure'],
        'connection': connection,
        'next_runtime': body['NextScheduledRunTime'],
        'last_runtime': body['LastRunTime'],
        'last_backup_id': body['LastRunBackupReportId']
    }
    return BackupConfiguration(**args)


def backup_from_response(body):
    raise NotImplementedError()


def restore_from_response(body):
    raise NotImplementedError()
