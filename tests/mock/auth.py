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
                'id': MOCK_KEY
            },
            'serviceCatalog': backup_endpoint
        }
    }

    return reply
