import random


def generateUserID() -> str:
    return "1" + str(random.randint(10 ** 9, 10 ** 10 - 1))


def generateChatID() -> str:
    return "2" + str(random.randint(10 ** 9, 10 ** 10 - 1))