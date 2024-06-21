import json
import logging
import os
import pickle
import socket

file_handler = logging.FileHandler('client.log', mode='w')
file_handler.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(filename)s : %(message)s', level=logging.DEBUG,
                    datefmt='%d/%m/%Y %I:%M:%S', handlers=[file_handler, console])


class User:
    def __init__(self):
        if 'data.json' in os.listdir():
            self.path = ""
        else:
            self.path = os.path.dirname(os.path.realpath(__file__)) + '\\'
        self.data = self.update_data(get=True)

        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((str(self.data['server'][0]), int(self.data['server'][1])))

        self.selected_user = None

    def update_data(self, get=False):
        if get:
            with open(f'{self.path}data.json', 'r') as file:
                self.data = json.load(file)
        else:
            with open(f'{self.path}data.json', 'w') as file:
                json.dump(self.data, file, indent=2)
        return self.data

    def commands(self):
        while 1:
            inp = input('>> ')
            if inp:
                if inp[0] == "!":
                    inp = inp.split(' ')
                    match inp[0][1:]:
                        case 'exit':
                            self.connection.send(b'server exit')
                            self.connection.close()
                            exit()
                        case 'chat':
                            if len(inp) == 1:
                                print("Please choice user")
                            else:
                                self.selected_user = inp[1]
                                if self.selected_user not in self.data['chats']:
                                    self.connection.send(f'server nuwchat {self.selected_user}'.encode())
                                    self.data['chats'][self.selected_user] = self.connection.recv(1024).decode()
                                    self.update_data()
                else:
                    if self.selected_user:
                        self.connection.send(f'chat {self.data['chats'][self.selected_user]} {inp}'.encode())
                    else:
                        logging.error('User Not Select')

    def run(self):
        try:
            while 1:
                ans = self.connection.recv(1024).decode()
                match ans:
                    case 'GiveData':
                        self.connection.send(pickle.dumps(self.data))

                    case 'SelectUserName':
                        id = self.connection.recv(1024).decode()
                        self.data['username'] = input(f'{ans}\n')
                        self.data['id'] = id
                        self.update_data()
                        self.connection.send(pickle.dumps(self.data))
                        logging.debug(self.connection.recv(1024))

                    case 'TypeMessage':
                        self.commands()
                        if self.connection.recv(1024).decode() != 'SuccessSend':
                            logging.error('ErrorSend')

                    case _:
                        logging.debug(ans)

        except Exception as e:
            self.connection.close()
            logging.error(e)


A = User()
A.run()
