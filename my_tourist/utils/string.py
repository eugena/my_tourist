import random
import string


def get_random_string(length=8):
    """
    Generates a random string

    :param length: integer
    :return: str
    """
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join([random.choice(letters) for i in range(length)])
