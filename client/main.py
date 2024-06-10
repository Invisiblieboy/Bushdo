import json
import os
import socket

s = socket.socket()
port = 55555
s.connect(('127.0.0.1', port))
path = os.path.dirname(os.path.realpath(__file__)) + '\\'

ans = s.recv(1024).decode()
while ans != 'Successful login':
    if ans == 'give me your data':
        with open(f'{path}data.json', 'r') as file:
            data = json.load(file)
        s.send(str(data).encode())

    elif ans == 'select username':
        with open(f'{path}data.json', 'r') as file:
            data = json.load(file)
        data['username'] = input(f'{ans}\n')
        with open(f'{path}data.json', 'w') as file:
            json.dump(data, file)
        s.send(str(data).encode())
    ans = s.recv(1024).decode()

s.send(input('your_message\n').encode())
s.close()
