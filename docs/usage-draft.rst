================================
Python RCBU API Bindings (draft)
================================

To be designed in the open. This is a preliminary draft for
Racklanta's eyes. What would you like to see the binding do? How can
it simplify working with your backups? Let me know!

The goal is to be simple and hide network communication from the
user. It should document that it does so, but working with it should
be natural.

Alejandro Cabrera <alejandro.cabrera@rackspace.com>

====================
Python Bindings v0.2
====================

Classes::

    Connection: authenticate and establish a connection with the API. Has account visibility.
    Agent: represents operations and information has access to. Controls an agent.
    BaseConfiguration: Functionality common to configurations.
    BackupConfiguration(Base): Handles information, updating, deleting, and more.
    RestoreConfiguration(Base): As above.
    Report: carries information common to all report classes.
    BackupReport(Report): ...
    RestoreReport(Report): ...
    Status: carries information about a running backup or restore
    BackupStatus(Status): ...
    RestoreStatus(Status): ...
    Backup: a handler for a backup to run. Allows one to start, stop,
            and investigate a backup.
    Restore: a handler for restores.
    

Usage:

.. code-block:: pycon

    >>> conn = rcbu.client.Connection(username, apikey)

    # Connection-wide functionality
    >>> conn.agents
    [(112233, 'awesome-backup'), ('445566', 'critical')]
    >>> conn.backup_configurations  # account-wide
    [(178291, 'daily-sql', (398643, 'dumb-logs')]
    >>> conn.restore_configurations
    [(98213649, 'daily-sql-snapshot1', (7851234, 'dumb-logs-snapshot3')]
    >>> conn.api_endpoint
    'https://backup.api.rackspacecloud.com/v1.0'
    >>> conn.api_version
    'v1.0'
    >>> conn.active_backups
    [(9823698, 'daily-sql-10'), ...]
    >>> conn.active_restores
    [(8923964, 'dumb-logs-snapshot3')]

    # Working with an Agent
    >>> agent = conn.get_agent(112233)
    >>> agent.name
    'awesome-backup'
    >>> agent.backup_configurations  # for this agent
    [...]
    >>> agent.restore_configurations
    [...]
    >>> agent.active_backups
    [...]
    >>> agent.active_restores
    [...]
    >>> agent.is_busy()
    True
    >>> agent.is_encrypted()
    False
    >>> agent.is_enabled()
    True
    >>> agent.delete()
    >>> agent.encrypt()

    # Working with a BackupConfiguration
    # Similarly for RestoreConfigurations
    >>> config = conn.get_backup_configuration(128936)
    >>> config.schedule
    >>> config.next_runtime()
    >>> config.is_enabled()
    False
    >>> config.notifies_on_failure()
    True
    >>> config.notifies_on_success()
    False
    >>> config.notification_email
    'another.lucky.admin@dunwanna.com'
    >>> config.update_from_file(path)
    >>> config.update_from_dict(conf)
    >>> config.disable()
    >>> config.enable()
    >>> config.delete()

    # Working with a BackupReport
    # Similarly for a RestoreReport
    >>> report = conn.get_backup_report(backup_id)
    >>> report.ok  # Did the backup succeed?
    True
    >>> report.error
    None
    >>> report.id
    892364
    >>> report.get_configuration()
    <object 'BackupConfiguration'>
    >>> report.is_restorable()
    True
    >>> report.duration
    <object 'datetime.datetime'>
    >>> report.files_searched()
    >>> report.bytes_searched()
    >>> report.bytes_backed_up()
    >>> report.errors
    [{"type": 123, "reason": "It broke.", "code": 123, "details": "Dang those cdlls and ssls."}, {...}]

    # Working with a Backup
    >>> backup = conn.create_backup(backup_configuration_id)
    >>> backup.running
    False
    >>> backup.inclusions
    [{...}]
    >>> backup.exclusions
    [{...}]
    >>> status = backup.start()
    >>> status.state
    "Searching"
    >>> backup.stop()
    >>> status.state
    "Cancelled"
    >>> backup.report()
    None
    >>> backup.start()
    <object 'BackupStatus'>
    >>> time.sleep(awhile)
    >>> backup.report()
    <object 'BackupReport'>
    >>> backup.report()
    <object 'BackupReport'>
