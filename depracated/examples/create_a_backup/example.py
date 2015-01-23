import sys

from rcbu.client.connection import Connection
from rcbu.client.client import Client
import rcbu.client.backup_configuration as backup_config


if len(sys.argv) != 4:
    print('usage: {0} username region password'.format(sys.argv[0]))
    quit()

username = sys.argv[1]
region = sys.argv[2]
password = sys.argv[3]

print('Connecting...')
conn = Connection(username, region, password=password)
client = Client(conn)
print('Connected!')

print('Creating a new configuration...')
myconf = backup_config.from_file('backup_config.json')
myconf.connect(conn)
myconf.create()
print('Created!')

print('Starting a backup...')
backup = client.create_backup(myconf)
status = backup.start()
print('Started! (id: {0})'.format(backup.id))

print('Waiting for it to finish...')
backup.wait_for_completion(poll_interval=0.5)
print('Done!')

print('...and the result is...')
report = backup.report
report.raise_if_not_ok()
print('OK!')

print('The backup took: {0}'.format(report._time['duration']))
