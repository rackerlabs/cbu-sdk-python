"""A generator for mock job objects. Useful for testing activities
functionality."""


def job(job_type, state):
    return {
        'Type': job_type,
        'CurrentState': state
    }
