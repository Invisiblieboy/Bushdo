import asyncio
import json
import time
import uuid

import rsa
from fastapi import APIRouter
from uuid_extensions import uuid7str

from server.utils1 import Server

router = APIRouter(prefix='/auth', tags=['auth'])
sessions = set()
server = Server()

@router.get('/login')
def login():
    pass


@router.get('/singup')
def login(name: str, pubkey: int) -> bytes:
    server_data = server.data

    if server_data['username2id'].get(name):
        return rsa.encrypt(json.dumps({'data':'sosi'}).encode('utf8'), rsa.PublicKey(pubkey, 65537))

    uid = uuid7str()
    data = {'session': uuid.uuid4().__str__(),
            'uid': uid}

    server_data['id2username'][uid] = name
    server_data['username2id'][name] = uid
    server.data = server_data
    server.update_data()

    sessions.add(data['session'])

    return rsa.encrypt(json.dumps(data).encode('utf8'), rsa.PublicKey(pubkey, 65537))


async def main():
    pubkey, privkey = rsa.newkeys(2 ** 10)
    print(pubkey)
    crypto_mess = login('spiwt22', pubkey.n)
    mess: dict = json.loads(rsa.decrypt(crypto_mess, privkey).decode('utf8'))
    print(mess)


if __name__ == '__main__':
    asyncio.run(main())
