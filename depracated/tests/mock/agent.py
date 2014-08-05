

def agent(id_='1', version='1.065959', vault_size='2 GB',
          data_center='ORD', ip_address='0.0.0.0',
          name='mock', os='linux', os_version='13.04',
          encrypted=False, disabled=False, status='Unknown'):
    return {
        'MachineAgentId': id_,
        'AgentVersion': version,
        'BackupVaultSize': vault_size,
        'CleanupAllowed': True,
        'Datacenter': data_center,
        'IPAddress': ip_address,
        'MachineName': name,
        'OperatingSystem': os,
        'OperatingSystemVersion': os_version,
        'IsEncrypted': encrypted,
        'IsDisabled': disabled,
        'Status': status
    }
