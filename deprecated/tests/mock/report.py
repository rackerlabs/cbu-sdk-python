"""A module that constructs mock report dictionaries."""


def report(config_id=1, name='mock', state='Completed',
           start='/Date(1351118760000)/',
           end='/Date(1351118760001)/',
           duration='00:00:00', errors=None,
           outcome='OK', diagnostics='OK'):
    """Base mock report."""
    return {
        'BackupConfigurationId': config_id,
        'BackupConfigurationName': name,
        'State': state,
        'StartTime': start,
        'CompletedTime': end,
        'Duration': duration,
        'NumErrors': len(errors) if errors else 0,
        'ErrorList': errors,
        'Reason': outcome,
        'Diagnostics': diagnostics
    }


def backup_report(agent_id=1, machine_name='mock', restorable=True,
                  files_searched=0, bytes_searched='2 GB',
                  files_stored=0, bytes_stored='2 GB',
                  **kwargs):
    """Returns a mock backup report."""
    base = report(**kwargs)
    base.update({
        'MachineAgentId': agent_id,
        'ComputerName': machine_name,
        'CanRestore': restorable,
        'FilesSearched': files_searched,
        'BytesSearched': bytes_searched,
        'FilesBackedUp': files_stored,
        'BytesBackedUp': bytes_stored
    })
    return base


def restore_report(backup_id=1, files_restored=0, bytes_restored='2 GB',
                   destination=1, path='/mock', **kwargs):
    """Returns a mock restore report."""
    base = report(**kwargs)
    base.update({
        'BackupConfigurationId': backup_id,
        'NumFilesRestored': files_restored,
        'NumBytesRestored': bytes_restored,
        'RestoreDestinationMachineId': destination,
        'RestoreDestination': path
    })
    return base
