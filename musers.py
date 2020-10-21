import os, time, datetime, socket, json
sock = socket.socket()
try:
        sock.connect(('83.219.149.12', 4900))
        #sock.connect(('localhost', 4900))
        if not os.path.exists("C://logs"):
                os.mkdir("C://logs")
        file = open ("C://logs/log.txt", 'a+')
        file.write("Начало: " + time.ctime() + "\n")
        file.close()
        sock.send('{"type" : "request", "token" : "1", "payload" : {"login" : "ivanov", "password" : "202cb962ac59075b964b07152d234b70", "action" : "getUpdates", "date" : -1, "data" : {"id" : 0, "address" : "улица Пушкина, дом Кукушкина", "items" : [{"id" : 40, "count" : 1, "comment" : "ХЕЛП"}], "name" : "НОЛЬ ПОМОЩИ"}}}'.encode('utf-8'))
        #sock.send('{"type" : "request", "token" : "e10adc3949ba59abbe56e057f20f883e", "payload" : {"action" : "getData", "data" : {"id" : 0, "status" : 0, "date" : 1599766326, "items" : [{"id" : 0, "price" : 322, "count" : 1, "comment" : "ХЕЛП"}], "name" : "НОЛЬ ПОМОЩИ"}}}'.encode('utf-8'))
        data = sock.recv(131072)
        #file = open ("C://logs/file.txt", 'w')
        #file.write(data.decode('utf-8'))
        #file.close()
        print(data.decode('utf-8'))
        #file = open ("C://logs/log.txt", 'a+')
        #file.write("Конец: " + time.ctime() + "\n\n")
        #file.close()
        print("всё ок")
except Exception as exp:
        print("Ошибка: " + str(exp))
input("Press Enter")
sock.close()

