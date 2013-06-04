MOCK_KEY = 'key'
MOCK_ENDPOINT = 'http://tacobackup.com/v1.0/912371'
MOCK_ENDPOINT_STRIPPED = 'http://tacobackup.com/v1.0'


def authenticate():
    backup_endpoint = [
        {
            'type': 'rax:backup',
            'endpoints': [
                {
                    'publicURL': MOCK_ENDPOINT
                }
            ]
        },
        {
            'type': 'something:else',
            'endpoints': [
                {
                    'publicURL': MOCK_ENDPOINT + '/not-right'
                }
            ]
        }
    ]

    reply = {
        'access': {
            'token': {
                'expires': '2013-06-05T05:20:28.306-05:00',
                'id': MOCK_KEY,
                'tenant': {
                    'id': 111111
                }
            },
            'serviceCatalog': backup_endpoint
        }
    }

    return reply
