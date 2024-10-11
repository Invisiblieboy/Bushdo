import json
import logging
import socket
import sys
import threading
import time
import uuid

from data.settings import *
from server.utils.clienthandler import _ClientHandler


class Server:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((IP, PORT))
        self.socket.listen(port_count)
        logging.info('Socket is listening')

        self.path_data = rf'server/data/data.json'
        self.data = self.update_data(get_from_file=True)

        self.authorized_connection: dict[str, _ClientHandler] = {}
        self.unknown_connections = {}

    def start(self):
        threading.Thread(target=self.console_handler, daemon=True).start()
        threading.Thread(target=self.unknown_connection_handler, daemon=True).start()

        while True:
            client, addr = self.socket.accept()
            connect = _ClientHandler(self, client, addr)
            self.unknown_connections[uuid.uuid4().__str__()] = connect
            threading.Thread(target=connect.start, daemon=True).start()

    def unknown_connection_handler(self):
        while 1:
            unknown_connections_nuw = {}
            for id, connection in self.unknown_connections.items():
                name = connection.get_name()
                if name:
                    self.authorized_connection[name] = connection
                else:
                    unknown_connections_nuw[id] = connection
            self.unknown_connections = unknown_connections_nuw
            time.sleep(0.2)

    def update_data(self, get_from_file=False, get_from_memory=False):
        if get_from_file:
            with open(self.path_data, 'r') as file:
                self.data = json.load(file)
        elif get_from_memory:
            pass
        else:
            with open(self.path_data, 'w') as file:
                json.dump(self.data, file, indent=2)
        return self.data

    def console_handler(self):
        while 1:
            text = input().split(' ')
            if text[0] == '!exit':
                for connect in self.unknown_connections.values():
                    connect.exit()
                for connect in self.authorized_connection.values():
                    connect.exit()
                sys.exit()
            elif text[0] == '!del':
                self.del_user(text[1])
            elif text[0] == '!clear_data':
                for connect in self.unknown_connections.values():
                    connect.exit()
                for connect in self.authorized_connection.values():
                    connect.exit()

                data_nuw = {}
                for key, item in self.data.items():
                    if type(item) == dict:
                        data_nuw[key] = {}
                    elif type(item) == list:
                        data_nuw[key] = []
                self.data = data_nuw
                self.update_data()
                print('+')



            else:
                print('Error input')

            time.sleep(0.1)

    def del_user(self, user):
        data = self.update_data()
        if data['username2id'].get(user):
            username = user
            id = data['username2id'].get(user)
        elif data['id2username'].get(user):
            id = user
            username = data['id2username'].get(user)
        else:
            print(f'Unknown user {user}')
            return 1

        del data['username2id'][username]
        del data['id2username'][id]

        for chat in data['users_all'][id].items():
            print(chat)
            try:
                if chat[0] != 'unread_messages':
                    del data['users_all'][chat[0]][id]
                if chat[1]:
                    del data['chats'][chat[1]]
            except Exception as e:
                print(f'Error {e}')

        del data['users_all'][id]

        with open(self.path_data, 'w') as file:
            json.dump(data, file, indent=2)
        print(f'Success delete {username}')


if __name__ == '__main__':
    file_handler = logging.FileHandler('server.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : [%(filename)s:%(lineno)d] : %(message)s',
                        level=logging.DEBUG, datefmt='%d/%m/%Y %I:%M:%S', handlers=[console])

    server = Server()
    server.start()
