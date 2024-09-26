import json
import logging
import os
import socket
import threading


class User:
    def __init__(self) -> None:
        if 'data.json' in os.listdir():
            self.path: str = ""
        else:
            self.path: str = os.path.dirname(os.path.realpath(__file__)) + '\\'
        self.data = self.update_data(get_from_file=True)

        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if socket.gethostname() == 'DESKTOP-L2DEF1J':
            IP = '127.0.0.1'
        else:
            IP = str(self.data['server'][0])

        self.connection.connect((IP, int(self.data['server'][1])))

        self.selected_user = None
        threading.Thread(target=self.recv_nonstop)

    def send(self, data: str) -> None:
        logging.debug(f'SEND  {data}')
        msg = f'{str(len(data)):>0{self.data['settings']['header_len']}}'.encode('UTF-8') + data.encode()
        self.connection.sendall(msg)

    def recv(self) -> str:
        data_len: int = int(self.connection.recv(self.data['settings']['header_len']).decode())
        data: str = self.connection.recv(data_len).decode()
        logging.debug(f'RECV {data}')
        return data

    def recv_nonstop(self):
        inp: list[str] = self.recv().split()

        if inp[0] == 'nuw_message':
            self.data['chat_history'][inp[1]] = json.loads(''.join(inp[2:]))
            if self.selected_user == inp[1]:
                self.update_chat()

    def update_data(self, get_from_file: bool = False, get_from_memory: bool = False) -> dict:
        if get_from_file:
            with open(f'{self.path}data.json', 'r') as file:
                self.data = json.load(file)
            return self.data
        if get_from_memory:
            return self.data
        with open(f'{self.path}data.json', 'w') as file:
            json.dump(self.data, file, indent=2)
        return self.data

    def commands(self) -> None:
        inp: str = input('>> ')
        if inp:
            if inp[0] == "!":
                inp: list = inp.split(' ')
                match inp[0][1:]:
                    case 'exit':
                        self.send('server exit')
                        self.connection.close()
                        exit()

                    case 'chat':
                        if len(inp) == 1:
                            print("Please choice user")

                        else:
                            self.selected_user: str = inp[1]
                            if self.selected_user not in self.data['chats_id']:
                                self.send(f'server nuwchat {self.selected_user}')
                                self.data['chats_id'][self.selected_user] = self.recv()
                                self.update_data()

                            self.send(f'history {self.data['chats_id'][inp[1]]}')
                            chat: list = json.loads(self.recv())

                            self.data['chats_history'][self.selected_user] = chat
                            self.update_data()
                            self.update_chat()


            else:
                if self.selected_user:
                    self.send(f'chat {self.data['chats_id'][self.selected_user]} {inp}')
                    self.data['chats_history'][self.selected_user].append(json.loads(self.recv()))
                    self.update_data()
                    self.update_chat()
                else:
                    logging.error('User Not Select')
                    return self.commands()
        else:
            return self.commands()


    def update_chat(self):
        chat = self.data['chats_history'][self.selected_user]
        chat_width: int = int(self.data['settings']['chat_width'])
        os.system('cls')
        logging.debug(f'chat with {self.selected_user}')

        print(f'{self.selected_user:<{chat_width // 2}}{'ME':>{chat_width // 2}}', end='\n\n')
        if chat:
            for message in chat:
                if message['author'] == self.data['id']:
                    print(f'{message['text']:>{chat_width}}')
                else:
                    print(f'{message['text']:<{chat_width}}')

    def run(self) -> None:
        try:
            while 1:
                ans: str = self.recv()
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


if __name__ == '__main__':
    file_handler = logging.FileHandler('client.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : [%(filename)s:%(lineno)d] : %(message)s',
                        level=logging.DEBUG,
                        datefmt='%d/%m/%Y %I:%M:%S', handlers=[file_handler, console])

    A = User()
    A.run()
