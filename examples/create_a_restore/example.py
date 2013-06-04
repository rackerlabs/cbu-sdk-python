import sys

from rcbu.client.connection import Connection
from rcbu.client.client import Client


if len(sys.argv) != 3:
    print('usage: {0} username password'.format(sys.argv[0]))
    quit()

username = sys.argv[1]
password = sys.argv[2]

print('Connecting...')
conn = Connection(username, password=password)
client = Client(conn)
print('Connected!')

print("Grabbing the core maintainer's agent...")
ag = [agent for agent in client.agents if
      agent.name.startswith('agent-test-ubuntu')][0]
print('Minion, do my bidding!')

print('Grabbing the first backup configuration I find...')
conf = ag.backup_configurations[0]
print('This is how you will perform this backup...')
print('Inclusions:')
print('    ', conf.inclusions)
print('Exclusions:')
print('    ', conf.exclusions)

print('Starting a backup...')
backup = client.create_backup(conf)
backup.start()
print('Started! (id: {0})'.format(backup.id))

print('Waiting for it to finish...')
backup.wait_for_completion(poll_interval=0.5)
print('Done!')

print('Checking backup...')
backup_report = backup.report
backup_report.raise_if_not_ok()
print('All good!')

print('Now creating a restore from this successful backup...')
restore = client.create_restore(backup.id, source_agent=ag,
                                destination_path='/root',
                                destination_agent=ag,  # by default
                                overwrite=False)  # by default, too
print('Created restore: {0}'.format(restore.id))

print('Now restoring...')
restore.start()
restore.wait_for_completion(poll_interval=.5)
print('Restore complete!')

print('...and the result is...')
restore_report = restore.report
restore_report.raise_if_not_ok()
print('OK!')

print('The backup took: {0}'.format(backup_report._time['duration']))
print('The restore took: {0}'.format(restore_report._time['duration']))
