import asyncio
import json
import logging
import os
import pickle
import socket

from settings import *


class Server:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((socket.gethostname(), PORT))
        self.socket.listen(port_count)
        logging.debug('Socket is listening')

        self.path = os.path.dirname(os.path.realpath(__file__)) + '\\'
        self.data = self.update_data(get=True)

    def update_data(self, get=False):
        if get:
            with open(f'{self.path}data.json', 'r') as file:
                self.data = json.load(file)
        else:
            with open(f'{self.path}data.json', 'w') as file:
                json.dump(self.data, file, indent=2)
        return self.data

    async def commands(self, ans, data, connection):
        ans = ans.split(' ')
        match ans[0]:
            case 'chat':
                logging.info(ans)

            case 'server':
                match ans[1]:
                    case 'exit':
                        connection.close()
                        self.data['users_online'].remove(data['username'])
                        self.update_data()

    async def connect(self):
        while True:
            try:
                connection, addr = self.socket.accept()
                connection.send(b'GiveData')

                data = pickle.loads(connection.recv(1024))
                if data['username'] == "None":
                    connection.send(b'SelectUserName')
                    data = json.loads(connection.recv(1024).decode().replace('\'', '\"'))
                connection.send(b'SuccessLogin')

                logging.debug(f'Connect from {data['username']}')
                if data['username'] not in self.data['users_online']:
                    self.data['users_online'].append(data['username'])
                if data['username'] not in self.data['users_all']:
                    self.data['users_all'][data['username']] = {"unreaded_messages": []}

                self.update_data()
                while 1:
                    connection.send(b'TypeMessage')

                    ans = connection.recv(1024)
                    ans = ans.decode()
                    logging.debug(f'{data['username']} {ans}')
                    await self.commands(ans, data, connection)
                    connection.send(b'SuccessSend')
            except Exception as e:
                logging.info(f'{data['username']} leave')
                connection.close()
                self.data['users_online'].remove(data['username'])
                self.update_data()
                logging.error(e)

    async def run(self):
        await asyncio.gather(*(self.connect() for _ in range(port_count)))


if __name__ == '__main__':
    file_handler = logging.FileHandler('server/server.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(filename)s : %(message)s',
                        level=logging.DEBUG,
                        datefmt='%d/%m/%Y %I:%M:%S', handlers=[file_handler, console])

    serv = Server()
    asyncio.run(serv.run())
