import json
import logging
import os
import socket
import sys
import threading
import time
import uuid


class User:
    def __init__(self) -> None:
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if socket.gethostname() == 'DESKTOP-L2DEF1J':
            self.connection.connect((socket.gethostname(), 60000))
        else:
            self.connection.connect(('26.84.94.16', 60000))

        self.sessions = {}
        self.selected_user = None

        if 'venv' in os.listdir():
            self.path: str = os.path.dirname(os.path.realpath(__file__)) + '\\'
        else:
            self.path: str = ""

        if 'data.json' in self.__listdir():
            with open(fr'{self.path}data.json', 'r') as file:
                self.data = json.load(file)
        else:
            self.data = {'settings': {'header_len': 10}, 'un_fill_data': True}

        self.header_len = 10
        threading.Thread(target=self._recv_nonstop, daemon=True).start()

        # print(self.path,self.data)

        if not self.data.get('username'):
            inp = input('Select User Name\n')
            while not inp:
                inp = input()
            self.data['username'] = inp
        if not self.data.get('id'):
            session = uuid.uuid4().__str__()
            self.send('server', '1', session, {'action': 'user_id'})
            self.data['id'] = self._recv(session)['data']['id']
            self.send('session_end', '1', session)

        if self.data.get('un_fill_data'):
            uz = self.data['username']
            id = self.data['id']
            session = uuid.uuid4().__str__()
            self.send('server', '1', session, {'action': 'get_clear_userdata'})
            # print(dict(self._recv(session)['data']['data']))
            self.send('session_end', '1', session)

            self.data = dict(self._recv(session)['data']['data'])
            self.data['username'] = uz
            self.data['id'] = id
            self.update_data()

        self.data['settings']: dict = dict(self.data['settings'])
        self.header_len = int(self.data['settings']['header_len'])
        self.update_data()

    def send(self, type: str, version: str, session: str, data: None | dict = None) -> None:
        message = {'data': data, 'type': type, 'version': version, 'session': session, 'time': time.time().__str__(),
                   'author': self.data.get('id')}

        if session not in self.sessions:
            self.sessions[session] = []
        self.sessions[session].append(message)

        logging.debug(f'SEND {message}')
        data = json.dumps(message)

        header = f'{str(len(data)):>0{self.header_len}}'
        msg = header.encode('UTF-8') + data.encode()
        self.connection.sendall(msg)  # self.__save_sessions()

    def _recv(self, session=None, waiting: bool = True) -> dict:
        if session:
            return self.__recv_session(session, waiting)
        header = self.connection.recv(self.header_len)

        data_len = int(header.decode())
        data = self.connection.recv(data_len).decode()
        # print(time.time().__str__()[15:], header, data_len, data)
        logging.debug(f'RECV {data}')
        message = json.loads(data)
        message['time'] = time.time().__str__()
        return message

    def __recv_session(self, session: str, waiting: bool):
        def check_messages():
            for i, message in enumerate(self.sessions[session]):
                if message.get('nuw_message'):
                    message['nuw_message'] = False
                    self.sessions[session][i] = message
                    return message

        if waiting:
            while 1:
                otv = check_messages()
                if otv:
                    return otv
                time.sleep(0.2)
        else:
            return check_messages()

    def _recv_nonstop(self):
        while 1:
            message = self._recv()
            message['nuw_message'] = True
            session = message['session']
            if message['type'] == 'session_end':
                # del self.sessions[session]
                pass
            else:
                if session not in self.sessions:
                    self.sessions[session] = []
                if not message['data'].get('return'):
                    if message['type'] == 'server':
                        threading.Thread(target=self._message_server_handler, daemon=True, args=(message,)).start()
                    elif message['type'] == 'chat':
                        threading.Thread(target=self._message_chat_handler, daemon=True,
                                         args=(message,)).start()  # self._message_chat_handler(message)

            self.sessions[session].append(message)  # self.__save_sessions()

    def __save_sessions(self):
        with open(f'{self.path}sessions.json', 'w') as file:
            json.dump(self.sessions, file, indent=2)

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

    def _message_server_handler(self, message):
        session = message['session']
        match message['data']['action']:
            case 'give_data':
                while not 'data.json' in self.__listdir():
                    time.sleep(0.1)
                with open(fr'{self.path}data.json', 'r') as file:
                    self.send('server', '1', session, {'action': 'give_data', 'return': True, 'data': json.load(file)})

    def _message_chat_handler(self, message):
        session = message['session']
        match message['data']['action']:
            case 'nuw_message':
                friend_id = message['data']['friend_id']
                if self.data['chats'].get(friend_id):

                    self.data['chats'][friend_id].append(message['data']['data'])

                    self.update_data()
                    if self.selected_user == friend_id:
                        self.update_chat()

    def console_handler(self):
        while 1:
            inp: str = input('>> ')
            if not inp:
                continue
            session = uuid.uuid4().__str__()
            if inp[0] == "!":
                inp: list = inp.split(' ')
                match inp[0][1:]:
                    case 'chat':
                        if len(inp) == 1:
                            logging.error("Please choice user")
                            continue
                        self.selected_user = inp[1]

                        if self.selected_user not in self.data['username2id']:
                            self.send('chat', '1', session, {'action': 'nuw_chat', 'id': self.selected_user})
                            recv = self._recv(session)
                            friend_id = recv['data']['friend_id']
                            self.data['chats'][self.selected_user] = recv['data']['chat_id']
                            self.data['username2id'][self.selected_user] = friend_id
                            self.data['id2username'][friend_id] = self.selected_user
                        else:
                            friend_id = self.data['username2id'][self.selected_user]

                        self.selected_user = friend_id

                        self.send('chat', '1', session, {'action': 'get_history', 'id': friend_id})
                        self.data['chats'][self.selected_user] = list(self._recv(session)['data']['data'])

                        self.send('session_end', '1', session)
                        self.update_data()
                        self.update_chat()

                    case 'sys':
                        if inp[1] == 'refresh_data':
                            os.remove(fr'{self.path}data.json')
                            self.exit()
                        elif inp[1] == 'exit':
                            self.exit()
                        elif inp[1] == 'info':
                            for key in ['username', 'id', 'settings']:
                                data = self.data[key]
                                print(f'{key:>20}\t{data}')
            else:
                if self.selected_user:
                    self.send('chat', '1', session, {'action': 'nuw_message', 'id': self.selected_user, 'data': inp})

                    self.data['chats'][self.selected_user].append(
                        {"author": self.data['id'], "read": [self.data['id']], "date": time.time().__str__(),
                            "text": inp})

                    self.update_data()
                    self.update_chat()
                else:
                    logging.error('User Not Select')

    def exit(self, exit_code=0):
        self.send('server', '1', '-1', {'action': 'user_exit', 'exit_code': exit_code})
        self.connection.close()
        sys.exit(exit_code)

    def update_chat(self):
        chat = self.data['chats'][self.selected_user]
        chat_width: int = int(self.data['settings']['chat_width'])
        os.system('cls')
        logging.debug(f'chat with {self.data['id2username'][self.selected_user]}')

        print(f'{self.data['id2username'][self.selected_user]:<{chat_width // 2}}{'ME':>{chat_width // 2}}', end='\n\n')
        if chat:
            for message in chat:
                if message['author'] == self.data['id']:
                    print(f'{message['text']:>{chat_width}}')
                else:
                    print(f'{message['text']:<{chat_width}}')

    def __listdir(self):
        if self.path == '':
            listdir = os.listdir()
        else:
            listdir = os.listdir(self.path)
        return listdir


if __name__ == '__main__':
    file_handler = logging.FileHandler('client.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : [%(filename)s:%(lineno)d] : %(message)s',
                        level=logging.DEBUG, datefmt='%d/%m/%Y %I:%M:%S', handlers=[file_handler, console])

    user = User()
    user.console_handler()

    # pyinstaller -F -n Bushdo -i "C:\Users\serdy\PycharmProjects\Bushdo\Bushdo.ico" client/client.py
