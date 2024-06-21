import datetime
import json
import logging
import os
import random
import socket
import sys
import threading
import time

from server.settings import *


class _Connection:
    def __init__(self, server, client, addr):
        self.server = server
        self.client = client
        self.addr = addr

        self.global_data = self.server.update_data(get_from_memory=True)
        self.data = None

    def send(self, data: str):
        try:
            logging.debug(f'SEND to {self.data['username']} {data}')
        except TypeError:
            logging.debug(f'SEND {data}')
        data = data.encode()
        msg = f'{str(len(data)):>0{self.global_data['settings']['header_len']}}'.encode('UTF-8') + data

        self.client.sendall(msg)

    def recv(self) -> str:
        data_len = int(self.client.recv(self.global_data['settings']['header_len']).decode())
        data = self.client.recv(data_len).decode()
        logging.debug(f'RECV {data}')
        return data

    def auth(self):
        self.send('GiveData')
        try:
            self.data = json.loads(self.recv())
        except Exception as e:
            logging.error(f'Not successful load data file {e}')
            self.exit()
        else:
            if not self.data['username']:
                self.send('SelectUserName')
                id = generateUserID()
                self.send(id)
                self.data = json.loads(self.recv())

            if self.data['id'] not in self.global_data['users_all']:
                self.global_data['users_all'][self.data['id']] = {"unread_messages": []}
            if self.data['id'] not in self.global_data['id2username']:
                self.global_data['id2username'][self.data['id']] = self.data['username']
            if self.data['username'] not in self.global_data['username2id']:
                self.global_data['username2id'][self.data['username']] = self.data['id']

            if self.data['id'] not in self.global_data['users_online']:
                self.global_data['users_online'].append(self.data['id'])
            self.send('SuccessLogin')
            logging.info(f'Connect from {self.data['username']}')

            self.server.update_data()

    def commands(self, ans):
        ans = ans.split(' ')
        match ans[0]:
            case 'history':
                self.send(json.dumps(self.global_data['chats'][ans[1]]))
            case 'chat':
                text = ''
                for elem in ans[2:]:
                    text += elem + ' '
                message = {"author": self.data['id'],
                           "read": [self.data['id']],
                           "date": str(datetime.datetime.now()),
                           "text": text[:-1]}
                logging.info(message)
                self.global_data['chats'][ans[1]].append(message)

            case 'server':
                match ans[1]:
                    case 'exit':
                        self.exit()
                    case 'nuwchat':
                        user_id = self.global_data['username2id'][ans[2]]
                        if user_id in self.global_data['users_all'][self.data['id']]:
                            self.send(self.global_data['users_all'][self.data['id']][user_id])
                        else:
                            id = generateChatID()
                            self.global_data['chats'][id] = []

                            self.global_data['users_all'][self.data['id']][user_id] = id
                            self.global_data['users_all'][user_id][self.data['id']] = id

                            self.send(id)
        self.server.update_data()

    def exit(self, error=None):
        if error:
            logging.error(error)
        try:
            self.client.close()
        except:
            pass
        try:
            self.server.all_connections.remove(self)
            logging.info(f'{self.data['username']} leave')
        except:
            pass
        try:
            self.global_data['users_online'].remove(self.data['id'])
        except:
            pass
        self.server.update_data()
        exit()

    def run(self):
        self.auth()
        try:
            while 1:
                self.send('TypeMessage')
                ans = self.recv()
                self.commands(ans)
                self.send('SuccessSend')
        except Exception as e:
            self.exit(e)


def generateUserID() -> str:
    return "1" + str(random.randint(10 ** 9, 10 ** 10 - 1))


def generateChatID() -> str:
    return "2" + str(random.randint(10 ** 9, 10 ** 10 - 1))


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
            connect = _Connection(self, client, addr)
            self.all_connections.append(connect)
            threading.Thread(target=connect.run, daemon=True).start()

    def ConsoleHandler(self):
        while 1:
            text = input()
            if text == '!exit':
                for connect in self.all_connections:
                    logging.info(f'Terminate {connect}')
                    connect.exit()
                sys.exit()
            else:
                print(text)

            time.sleep(0.1)


if __name__ == '__main__':
    file_handler = logging.FileHandler('server/server.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(filename)s : %(message)s',
                        level=logging.DEBUG,
                        datefmt='%d/%m/%Y %I:%M:%S', handlers=[console])

    server = Server()
    threading.Thread(target=server.run, daemon=True).start()
    server.ConsoleHandler()
