

def activity(activity_id=1, type_tag='Backup', parent=2, name='mock',
             deleted=False, source_id=3, source_name='mock',
             destination_id=4, destination_name='mock',
             state='Completed', time='/Date(1351118760000)/'):
    return {
        'ID': activity_id,
        'Type': type_tag,
        'ParentId': parent,
        'DisplayName': name,
        'IsBackupConfigurationDeleted': deleted,
        'SourceMachineAgentId': source_id,
        'SourceMachineName': source_name,
        'DestinationMachineAgentId': destination_id,
        'DestinationMachineName': destination_name,
        'CurrentState': state,
        'TimeOfActivity': time
    }
