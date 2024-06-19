import json
import logging
import os
import pickle
import socket
import threading

from server.settings import *


class _Connection:
    def __init__(self, server, client, addr):
        self.server = server
        self.client = client
        self.addr = addr

        self.global_data = self.server.update_data(get_from_memory=True)
        self.data = None
        self.stop = False

    def auth(self):
        self.client.send(b'GiveData')

        self.data = pickle.loads(self.client.recv(1024))
        if not self.data['username']:
            self.client.send(b'SelectUserName')
            self.data = pickle.loads(self.client.recv(1024))
        self.client.send(b'SuccessLogin')

        logging.debug(f'Connect from {self.data['username']}')
        if self.data['username'] not in self.global_data['users_online']:
            self.global_data['users_online'].append(self.data['username'])
        if self.data['username'] not in self.global_data['users_all']:
            self.global_data['users_all'][self.data['username']] = {"unreaded_messages": []}

        self.server.update_data()

    def commands(self, ans):
        ans = ans.split(' ')
        match ans[0]:
            case 'chat':
                logging.info(ans)

            case 'server':
                match ans[1]:
                    case 'exit':
                        self.client.close()
                        self.global_data['users_online'].remove(self.data['username'])
                        self.server.update_data()
                        self.stop = True

    def run(self):
        self.auth()
        try:
            while 1:
                self.client.send(b'TypeMessage')
                ans = self.client.recv(1024).decode()
                logging.debug(f'{self.data['username']} {ans}')
                self.commands(ans)
                if self.stop:
                    break
                self.client.send(b'SuccessSend')
        except Exception as e:
            logging.info(f'{self.data['username']} leave')
            self.client.close()
            self.global_data['users_online'].remove(self.data['username'])
            self.server.update_data()
            logging.error(e)

    def __del__(self):
        pass


class Server:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((socket.gethostname(), PORT))
        self.socket.listen(port_count)
        logging.debug('Socket is listening')

        self.path = os.path.dirname(os.path.realpath(__file__)) + '\\'
        self.data = self.update_data(get_from_file=True)

        self.all_connections = []

    def update_data(self, get_from_file=False, get_from_memory=False):
        if get_from_file:
            with open(f'{self.path}data.json', 'r') as file:
                self.data = json.load(file)
            return self.data
        if get_from_memory:
            return self.data
        with open(f'{self.path}data.json', 'w') as file:
            json.dump(self.data, file, indent=2)
        return self.data

    def run(self):
        while True:
            client, addr = self.socket.accept()
            print('connect', client)
            connect = _Connection(self, client, addr)
            threading.Thread(target=connect.run).start()


if __name__ == '__main__':
    file_handler = logging.FileHandler('server/server.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(filename)s : %(message)s',
                        level=logging.DEBUG,
                        datefmt='%d/%m/%Y %I:%M:%S', handlers=[console])

    server = Server()
    server.run()
