

def backup_configuration(agent_id=1, name='mock',
                         is_active=True, is_deleted=False, is_encrypted=False,
                         retention=0, missed_backup_action=1,
                         frequency='Manually', hour=None, minute=None,
                         am_pm=None, weekday=None, interval=None,
                         timezone='Eastern Standard Time',
                         email='mock@mock.com', on_success=False,
                         on_failure=True, inclusions=[], exclusions=[]):
    return {
        'MachineAgentId': agent_id,
        'BackupConfigurationName': name,
        'IsActive': is_active,
        'IsDeleted': is_deleted,
        'IsEncrypted': is_encrypted,
        'VersionRetention': retention,
        'MissedBackupActionId': missed_backup_action,
        'Frequency': frequency,
        'StartTimeHour': hour,
        'StartTimeMinute': minute,
        'StartTimeAmPm': am_pm,
        'DayOfWeekId': weekday,
        'HourInterval': interval,
        'TimeZoneId': timezone,
        'NotifyRecipients': email,
        'NotifySuccess': on_success,
        'NotifyFailure': on_failure,
        'Inclusions': inclusions,
        'Exclusions': exclusions
    }
