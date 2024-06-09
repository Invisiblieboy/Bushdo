import json
import os
import socket

s = socket.socket()
port = 55555
s.connect(('127.0.0.1', port))
message = s.recv(1024).decode()

if message == 'give me your data':
    if 'data.json' not in os.listdir():
        with open('data.json', 'w') as file:
            json.dump({"username": input('write your username')}, file)

    with open('data.json', 'r') as file:
        file = str(json.load(file))
        print(str(file), type(file))
        s.send(file.encode())

s.send(input('your_message\n').encode())
s.close()
