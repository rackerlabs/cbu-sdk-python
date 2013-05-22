import sys
import time

from rcbu.client.client import Connection
import rcbu.client.backup_configuration as backup_config


if len(sys.argv) != 3:
    print('usage: {} username password'.format(sys.argv[0]))
    quit()

username = sys.argv[1]
password = sys.argv[2]

print('Connecting...')
conn = Connection(username, password=password)
print('Connected!')

print('Creating a new configuration...')
myconf = backup_config.from_file('backup_config.json')
myconf.connect(conn)
myconf.create()
print('Created!')

print('Starting a backup...')
backup = conn.create_backup(myconf)
status = backup.start()
print('Started!')

print('Waiting for it to finish...')
time.sleep(15)
backup.wait_for_completion(poll_interval_seconds=5)
print('Done!')

print('...and the result is...')
report = backup.report
report.raise_if_not_ok()
print('OK!')
