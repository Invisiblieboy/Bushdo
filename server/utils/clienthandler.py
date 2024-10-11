import json
import logging
import sys
import threading
import time
import uuid

from server.data.settings import *
from server.utils.generation import generateUserID, generateChatID


class _ClientHandler:
    def __init__(self, server, client, addr) -> None:
        self.server = server
        self.client = client
        self.addr = addr

        self.global_data = self.server.update_data(get_from_memory=True)
        self.data = None
        self.sessions = {}

        with open(fr'server/user/data.json', 'r') as file:
            self.user_data_file = json.load(file)

    def send(self, type: str, version: str|float|int, session: str, data: None | dict = None) -> None:
        message = {'data': data, 'type': type, 'version': str(version), 'session': session,
                   'time': time.time().__str__(),
                   'author': 'server'}

        if session not in self.sessions:
            self.sessions[session] = []
        self.sessions[session].append(message)

        try:
            logging.debug(f'SEND to {self.data['username']} {message}')
        except TypeError:
            logging.debug(f'SEND {message}')

        data = json.dumps(message)

        if not self.data:
            header = f'{str(len(data)):>0{10}}'
        else:
            header = f'{str(len(data)):>0{self.data['settings']['header_len']}}'
        msg = header.encode() + data.encode()
        self.client.sendall(msg)
        # self.__save_sessions()


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

    def _recv(self,session=None,waiting: bool =True) -> dict:
        if session:
            return self.__recv_session(session,waiting)
        try:
            data_len = int(self.client.recv(header_len).decode())
        except ConnectionResetError:
            logging.error('Connection lost')
            self.exit()

        data = self.client.recv(data_len).decode()
        logging.debug(f'RECV {data}')
        message = json.loads(data)
        message['time'] = time.time().__str__()
        return message

    def _recv_nonstop(self):
        while 1:
            message = self._recv()
            message['nuw_message'] = True
            session = message['session']

            if message['type'] == 'session_end':
                del self.sessions[session]
                pass
            else:
                if session not in self.sessions:
                    self.sessions[session] = []

                if message['type'] == 'server':
                    self._message_server_handler(message)
                elif message['type'] == 'chat':
                    self._message_chat_handler(message)

                self.sessions[session].append(message)
            # self.__save_sessions()

    def __save_sessions(self):
        with open('sessions.json', 'w') as file:
            json.dump(self.sessions, file, indent=2)


    def _message_server_handler(self, message):
        session = message['session']
        match message['data']['action']:
            case 'get_clear_userdata':
                self.send('server', '1', session, {'action': 'get_clear_userdata', 'data': self.user_data_file,
                                                   'return':True})
            case 'user_exit':
                # self.send('session_end', '1', session)
                self.exit()
            case 'user_id':
                user_id=generateUserID()
                self.send('server', '1', session, {'action': 'user_id', 'id': user_id,
                                           'return': True})
            case _:
                logging.error(f'Unknown action {message}')

    def _message_chat_handler(self, message):
        session = message['session']
        match message['data']['action']:
            case 'nuw_chat':
                friend_id = self.global_data['username2id'][message['data']['id']]
                if friend_id in self.global_data['users_all'][self.data['id']]:
                    chat_id = self.global_data['users_all'][self.data['id']][friend_id]
                else:
                    chat_id = generateChatID()
                    self.global_data['chats'][chat_id] = []
                    self.global_data['users_all'][self.data['id']][friend_id] = chat_id
                    self.global_data['users_all'][friend_id][self.data['id']] = chat_id

                self.send('chat', '1', session,{'action':'nuw_chat',
                                                'return':True,
                                                'chat_id': chat_id,
                                                'friend_id':friend_id})
                self.server.update_data()

            case 'get_history':
                chat_id = self.global_data['users_all'][self.data['id']][message['data']['id']]
                chat_history = self.global_data['chats'][chat_id]
                self.send('chat', '1', session, {'action': 'get_history', 'data': chat_history,'return':True})

            case 'nuw_message':
                chat_id = self.global_data['users_all'][self.data['id']][message['data']['id']]
                connection:_ClientHandler = self.server.authorized_connection.get(message['data']['id'])

                message_nuw = {"author": self.data['id'], "read": [self.data['id']], "date": time.time().__str__(),
                           "text": message['data']['data']}
                self.global_data['chats'][chat_id].append(message_nuw)

                connection.send('chat',1,session,{'action':'nuw_message',
                                            'chat_id':chat_id,
                                            'friend_id':self.data['id'],
                                            'data':message_nuw})

                time.sleep(0.1)
                self.send('session_end', '1', session)
                self.server.update_data()
            case _:
                logging.error(f'Unknown action {message}')

    def auth(self):
        session = uuid.uuid4().__str__()
        self.send('server', '1', session, {'action': 'give_data'})
        message = self._recv(session)
        self.data: dict = message['data']['data']
        session = message['session']
        if 1:
            if not self.data['username']:
                self.send('SelectUserName')
                self.send(generateUserID())
                self.data = self._recv()['data']

            if self.data['id'] not in self.global_data['users_all']:
                self.global_data['users_all'][self.data['id']] = {"unread_messages": []}
            if self.data['id'] not in self.global_data['id2username']:
                self.global_data['id2username'][self.data['id']] = self.data['username']
            if self.data['username'] not in self.global_data['username2id']:
                self.global_data['username2id'][self.data['username']] = self.data['id']

            if self.data['id'] not in self.global_data['users_online']:
                self.global_data['users_online'].append(self.data['id'])
            self.send('session_end', '1', session)
            logging.info(f'Connect from {self.data['username']}')

            self.server.update_data()

    def exit(self, error=None):
        if error:
            logging.error(error)
        try:
            self.client.close()
        except:
            pass
        try:
            self.server.all_connections.remove(self.data['id'])
            logging.info(f'{self.data['username']} leave')
        except:
            pass
        try:
            self.global_data['users_online'].remove(self.data['id'])
        except:
            pass
        self.server.update_data()
        sys.exit()

    def start(self):
        threading.Thread(target=self._recv_nonstop,daemon=True).start()
        self.auth()
        time.sleep(10**4)

    def get_name(self):
        try:
            return self.data['id']
        except:
            return None
