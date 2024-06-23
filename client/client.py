import json
import logging
import os
import socket

file_handler = logging.FileHandler('client.log', mode='w')
file_handler.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logging.basicConfig(format='%(asctime)s : %(levelname)s : [%(filename)s:%(lineno)d] : %(message)s', level=logging.DEBUG,
                    datefmt='%d/%m/%Y %I:%M:%S', handlers=[file_handler, console])


class User:
    def __init__(self):
        if 'data.json' in os.listdir():
            self.path = ""
        else:
            self.path = os.path.dirname(os.path.realpath(__file__)) + '\\'
        self.data = self.update_data(get_from_file=True)

        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((str(self.data['server'][0]), int(self.data['server'][1])))

        self.selected_user = None

    def send(self, data: str):
        logging.debug(f'SEND  {data}')
        data = data.encode()
        msg = f'{str(len(data)):>0{self.data['settings']['header_len']}}'.encode('UTF-8') + data

        self.connection.sendall(msg)

    def recv(self) -> str:
        data_len = int(self.connection.recv(self.data['settings']['header_len']).decode())
        data = self.connection.recv(data_len).decode()
        logging.debug(f'RECV {data}')
        return data

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

    def commands(self):
        inp = input('>> ')
        if inp:
            if inp[0] == "!":
                inp = inp.split(' ')
                match inp[0][1:]:
                    case 'exit':
                        self.send('server exit')
                        self.connection.close()
                        exit()

                    case 'chat':
                        if len(inp) == 1:
                            print("Please choice user")
                        else:
                            self.selected_user = inp[1]
                            if self.selected_user not in self.data['chats']:
                                self.send(f'server nuwchat {self.selected_user}')
                                self.data['chats'][self.selected_user] = self.recv()
                                self.update_data()

                        self.send(f'history {self.data['chats'][inp[1]]}')
                        chat = json.loads(self.recv())

                        chat_width = int(self.data['settings']['chat_width'])
                        os.system('cls')
                        logging.debug(f'chat with {inp[1]}')
                        print(f'{inp[1]:<{chat_width // 2}}{'ME':>{chat_width // 2}}', end='\n\n')
                        if chat:
                            for message in chat:
                                if message['author'] == self.data['id']:
                                    print(f'{message['text']:>{chat_width}}')
                                else:
                                    print(f'{message['text']:<{chat_width}}')

            else:
                if self.selected_user:
                    self.send(f'chat {self.data['chats'][self.selected_user]} {inp}')
                else:
                    logging.error('User Not Select')

    def run(self):
        try:
            while 1:
                ans = self.recv()
                match ans:
                    case 'GiveData':
                        self.send(json.dumps(self.data))

                    case 'SelectUserName':
                        id = self.recv()
                        self.data['username'] = input(f'{ans}\n')
                        self.data['id'] = id
                        self.update_data()
                        self.send(json.dumps(self.data))
                        logging.debug(self.recv())

                    case 'TypeMessage':
                        self.commands()

                    case _:
                        if ans == 'SuccessLogin':
                            print('SuccessLogin')
                        else:
                            logging.debug(f'NOT DISTRIBUTED {ans}')

        except Exception as e:
            self.connection.close()
            logging.error(e)


A = User()
A.run()
