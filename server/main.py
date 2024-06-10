import asyncio
import json
import logging
import socket

from settings import *

async def connect(s):
    try:
        while True:
            connection, addr = s.accept()
            connection.send('give me your data'.encode())

            data = json.loads(connection.recv(1024).decode().replace('\'', '\"'))
            if data['username'] == "None":
                connection.send('select username'.encode())
                data = json.loads(connection.recv(1024).decode().replace('\'', '\"'))
            connection.send('Successful login'.encode())

            logging.debug(f'Connect from {data['username']} {addr}')
            logging.debug(f'{data['username']} {connection.recv(1024).decode()}')

            connection.close()
    except Exception as e:
        logging.error(e)


async def main():
    file_handler = logging.FileHandler('server/server.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(filename)s : %(message)s',
                        level=logging.DEBUG,
                        datefmt='%d/%m/%Y %I:%M:%S', handlers=[file_handler, console])

    s = socket.socket()
    s.bind((IP, PORT))
    s.listen(port_count)
    logging.debug('Socket is listening')

    await asyncio.gather(*(connect(s) for _ in range(port_count)))


if __name__ == '__main__':
    asyncio.run(main())
