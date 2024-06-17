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
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((socket.gethostname(), 60000))
        self.path = os.path.dirname(os.path.realpath(__file__)) + '\\'

        self.data = self.update_data(get=True)
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
            inp = input()
            if inp:
                inp = inp.split(' ')
                if inp[0][0] == "!":
                    match inp[0][1:]:
                        case 'exit':
                            self.connection.send(b'server exit')
                            self.connection.close()
                            exit()
                        case 'chat':
                            if len(inp) == 1:
                                print("Please choise user")
                            else:
                                self.selected_user = inp[1]
                else:
                    if self.selected_user:
                        self.connection.send(f'chat {self.selected_user} {inp[0]}'.encode())
                        break
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
                        self.data['username'] = input(f'{ans}\n')
                        self.update_data()
                        self.connection.send(pickle.dumps(self.data))
                        logging.info(self.connection.recv(1024))

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
