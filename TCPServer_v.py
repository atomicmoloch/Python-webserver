import threading
import time
import os
import mimetypes
from datetime import datetime

from socket import *

# Use this port number
serverPort = 12006
# Create a TCP socket
serverSocket = socket(AF_INET, SOCK_STREAM)
# Bind our port number to the socket we created
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('', serverPort))
serverSocket.settimeout(120)


#todo - add customization, probably via a config file
notFoundPage = ('404: File Not Found').encode()
errorPage = ('500 Server Error').encode()


def getMimeType(filename):
    mimeType, encoding = mimetypes.guess_type(filename)
    return mimeType

def getFile(fileName):
    status = 200
    if os.path.exists(fileName):
        try:
            if os.path.isdir(fileName):
                if os.path.exists(fileName + "/index.html"):
                    return getFile(fileName + "/index.html")
                elif os.path.exists(fileName + "/index.htm"):
                    return getFile(fileName + "/index.htm")
                else:
                    fileContent = "Directory browsing not yet implemented".encode()
                    mimeType = "text/html"
            else:
                reqFile = open(fileName, "rb")
                fileContent = reqFile.read()
                reqFile.close()
                mimeType = getMimeType(fileName)
        except Exception as e:
            status = 500
            fileContent = errorPage
            mimeType = "text/html"
    else:
        #todo: add custom error pages
        fileContent = notFoundPage
        status = 404
        mimeType = "text/html"
    return (fileContent, status, mimeType)

def getHeader(status, mimeType):
    header = "HTTP/1.0" #Honestly can't even claim this due to standard noncompliance
    if status == 200:
        header = header + " 200 OK\r\n"
    elif status == 404:
        header = header + " 404 NOT FOUND\r\n"
    elif status == 500:
        header = header + " 500 INTERNAL SERVER ERROR\r\n"

    header = header + "Date: " + (datetime.utcnow()).strftime("%b %d %Y %H:%M:%S") + "GMT \r\n"
    header = header + "Content-Type: " + mimeType + "\r\n"
    header = header + "\r\n"
    return header.encode()

def http09Get(splitRequest):
    fileName = "." + ((splitRequest[0])[4:])
    reqFile = getFile(fileName)
    return reqFile[0]

def http10Get(splitRequest):
    splitRequest[0]=(splitRequest[0])[:-9]
    fileName = "." + ((splitRequest[0])[4:])
    reqFile = getFile(fileName)
    header = getHeader(reqFile[1], reqFile[2])
    return header + reqFile[0]

def takeGetRequest(connexion, splitRequest):
    if (splitRequest[0])[-8:-4] == "HTTP": #Filters out http 0.9 requests
        toSend = http10Get(splitRequest)
    else:
        # handles http 0.9
        toSend = http09Get(splitRequest)
    connexion.send(toSend)

def takeHeadRequest(connexion, splitRequest):
    reqFile = getFile((splitrequest[0])[4:-9])
    connexion.send(getHeader(reqFile[1], reqFile[2]))

def takeRequest(connexion, address):
    # Receive and decode
    request = connexion.recv(1024).decode()
    print('Connexion Received: ' + request)
    splitRequest = request.splitlines()
    if len(splitRequest) > 0: #Occasionally get empty requests due to connexion errors
        if (splitRequest[0])[:3] == 'GET':
            takeGetRequest(connexion, splitRequest)
        elif (splitRequest[0])[:4] == 'HEAD':
            takeHeadRequest(connexion, splitRequest)
    connexion.close()
    print('Connexion Closed')

def runServer():
    # Start listening
    serverSocket.listen(1)
    print('Server is ready to receive')
    while True:
        try:
            connexionSocket, addr = serverSocket.accept()
            thread = threading.Thread(target=takeRequest, args=(connexionSocket, addr))
            thread.start()
        except TimeoutError as e:
            pass
            # had some problems with ports remaining occupied hoping that a timeout plus this will fix it
        print("Current Threads: " + str(threading.active_count()))

runServer()
