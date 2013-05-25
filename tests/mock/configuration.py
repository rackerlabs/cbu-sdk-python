def backup_configuration(agent_id=1, is_active=True,
                         is_deleted=False, is_encrypted=False):
    return {
        'MachineAgentId': agent_id,
        'BackupConfigurationName': 'mock',
        'IsActive': is_active,
        'IsDeleted': is_deleted,
        'IsEncrypted': is_encrypted,
        'VersionRetention': 0,
        'MissedBackupActionId': 1,
        'Frequency': 'Manually',
        'StartTimeHour': None,
        'StartTimeMinute': None,
        'StartTimeAmPm': None,
        'DayOfWeekId': None,
        'HourInterval': None,
        'TimeZoneId': 'Eastern Standard Time',
        'NotifyRecipients': 'mock@mock.com',
        'NotifySuccess': False,
        'NotifyFailure': True,
        'Inclusions': [],
        'Exclusions': []
    }
