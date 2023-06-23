import os


def random_string():
    return os.urandom(8).hex()
