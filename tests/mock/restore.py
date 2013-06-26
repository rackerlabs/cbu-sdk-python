"""Mocking restore objects."""


def restore(restore_id=1, backup_id=1, overwrites=False,
            backup_config_id=1, backup_config_name='mock',
            src_id=1, src_name='mock', dest_id=1, dest_name='mock',
            dest_path='/mock', encrypted=False, password='mock'):
    return {
        'RestoreId': restore_id,
        'BackupId': backup_id,
        'OverwriteFiles': overwrites,
        'BackupConfigurationId': backup_config_id,
        'BackupConfigurationName': backup_config_name,
        'BackupMachineId': src_id,
        'BackupMachineName': src_name,
        'DestinationMachineId': dest_id,
        'DestinationMachineName': dest_name,
        'DestinationPath': dest_path,
        'IsEncrypted': encrypted,
        'EncryptedPassword': password,
        'PublicKey': {
            'ModulusHex': 1,
            'ExponentHex': 1
        }
    }
