# client.py 转播直播间信息到服务器
import socket
import json

def send(data,host = 'localhost', port = 9999):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    #序列化
    json_data = json.dumps(data)
    client.send(json_data.encode('utf-8'))

    #响应
    response = client.recv(1024)
    print("响应",response.decode('utf-8'))

    client.close()
