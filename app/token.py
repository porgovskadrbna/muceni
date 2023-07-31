import string
import random


def token() -> str:
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choice(characters) for _ in range(16))
    return random_string
