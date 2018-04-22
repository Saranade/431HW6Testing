import sys
import shutil
import socket
import socketserver

# This program, FTP1server.py, aims at parsing a given string and determining whether or not
# that string is a valid FTP command. Contextual messages will also be sent to the console
# to give the user indication of what errors, if any, are popping up, as well as what the server
# is doing.
class Parser:
    def __init__(self,csock):
        sys.stdout.write("220 COMP 431 FTP server ready.\r\n")
        csock.send("220 COMP 431 FTP server ready.\r\n".encode())
        self.hasUsername = False
        self.hasPass = False
        self.hasPort = False
        self.hasQuitted = False
        self.filenum = 1
        self.fileArray = []
        self.sock = None
        self.clientsock = csock

    # isAscii takes a string and returns true if all of the characters in the string are a 128 bit
    # character or less, and false otherwise.
    def isAscii(self,s):
        return all(ord(c) < 128 for c in s)

    # chompSpaces takes a string as input and returns the same string with all of the leading spaces
    # removed. If there are no leading spaces, it will return the given string, and if the string is all
    # spaces, it will return an empty string.
    def chompSpaces(self,s):
        result = s
        while (result[:1] == " "):
            result = result[1:]
        return result

    # getHostPort takes a string and returns the host and port in the desired format. If the given
    # string is not a valid host port, it will return the string "invalid".
    def getHostPort(self,s):
        hostPort = ""
        commaCounter = 0
        # numHolder is -1 when not holding a number so that we can check at the end
        # to make sure we have a valid num to add onto the port.
        numHolder = -1
        port = 0
        for c in s:
            # If our character is a comma, put the number together and tack it onto hostPort.
            if (ord(c) == 44):
                commaCounter = commaCounter + 1
                if (numHolder < 256):
                    if (commaCounter < 5):
                        hostPort = hostPort + str(numHolder) + "."
                    # If we are at the 5th comma, the number is part of a port and must be multiplied by 256.
                    elif (commaCounter == 5):
                        port = numHolder * 256
                    # Reset the number holder
                    numHolder = -1
                else:
                    hostPort = "invalid"
            elif (ord(c) > 47 and ord(c) < 58):
                # Set numHolder to 0 if it is -1 so we can do some math.
                if (numHolder == -1):
                    numHolder = 0
                numHolder = numHolder * 10
                numHolder = numHolder + int(c)
            else:
                hostPort = "invalid"
        # In order to complete our hostPort, the comma count must be 5 and we must have a valid number
        # in the holder.
        if (commaCounter == 5 and numHolder != -1):
            hostPort = hostPort[:-1] + "," + str(port + numHolder)
        # Otherwise our given string is not a host port.
        else:
            hostPort = "invalid"
        return hostPort

    def parseCommand(self,given):
        # If we have quitted, do nothing at all.
        if (not self.hasQuitted):
            sys.stdout.write(given)

            # If our given string is less than 4 characters, it cannot possibly be a valid command.
            if (len(given) < 4):
                sys.stdout.write("500 Syntax error, command unrecognized.\r\n")
                clientsocket.send("500 Syntax error, command unrecognized.\r\n".encode())
            else:
                # Because all commands are of length 4, we know that our command will be the first 4 characters
                # from the given string.
                command = given[:4]
                command = command.lower()

                # Commands "user", "pass", and "type" behave similarly where the grammar is concerned,
                # so we can factor some code out by combining these in an if statement.
                if (command == "user" or command == "pass" or command == "type" or command == "port" or command == "retr"):
                    # If the command is not immediately followed by a space, it is invalid.
                    if (given[4] != " "):
                        sys.stdout.write("500 Syntax error, command unrecognized.\r\n")
                        clientsocket.send("500 Syntax error, command unrecognized.\r\n".encode())
                    else:
                        # Here we fetch everything following the command and variable number of spaces.
                        noCommand = self.chompSpaces(given[4:])
                        # The parameter will be everything from noCommand that is not the last two characters,
                        # which should be "\r\n".
                        param = noCommand[:-2]
                        if (command == "user"):
                            # If the parameter has non-ascii characters or "\r" or "\n" or is empty it is invalid.
                            if (not self.isAscii(param) or "\r" in param or "\n" in param or param == ""):
                                sys.stdout.write("501 Syntax error in parameter.\r\n")
                                clientsocket.send("501 Syntax error in parameter.\r\n".encode())
                            # If the last two characters are not CRLF then the CRLF is invalid.
                            elif (given[-2:] != "\r\n"):
                                sys.stdout.write("501 Syntax error in parameter.\r\n")
                                clientsocket.send("501 Syntax error in parameter.\r\n".encode())
                            # If we passed all these checks, we're good.
                            else:
                                self.hasUsername = True
                                sys.stdout.write("331 Guest access OK, send password.\r\n")
                                clientsocket.send("331 Guest access OK, send password.\r\n".encode())
                        elif (command == "pass"):
                            # Can't start a password without giving a username first.
                            if (not self.hasUsername):
                                sys.stdout.write("530 Not logged in.\r\n")
                                clientsocket.send("530 Not logged in.\r\n".encode())
                            elif (not self.isAscii(param) or "\r" in param or "\n" in param or param == ""):
                                sys.stdout.write("501 Syntax error in parameter.\r\n")
                                clientsocket.send("501 Syntax error in parameter.\r\n".encode())
                            elif (given[-2:] != "\r\n"):
                                sys.stdout.write("501 Syntax error in parameter.\r\n")
                                clientsocket.send("501 Syntax error in parameter.\r\n".encode())
                            else:
                                self.hasPass = True
                                sys.stdout.write("230 Guest login OK.\r\n")
                                clientsocket.send("230 Guest login OK.\r\n".encode())
                        elif (command == "port"):
                            isHP = self.getHostPort(param)
                            # Can't do port command if not logged in.
                            if (not self.hasUsername or not self.hasPass):
                                sys.stdout.write("530 Not logged in.\r\n")
                                clientsocket.send("530 Not logged in.\r\n".encode())
                            # Extra check here to make sure the hostPort is not "invalid".
                            elif (not self.isAscii(param) or "\r" in param or "\n" in param or param == "" or (isHP == "invalid")):
                                sys.stdout.write("501 Syntax error in parameter.\r\n")
                                clientsocket.send("501 Syntax error in parameter.\r\n".encode())
                            elif (given[-2:] != "\r\n"):
                                sys.stdout.write("501 Syntax error in parameter.\r\n")
                                clientsocket.send("501 Syntax error in parameter.\r\n".encode())
                            else:
                                self.hasPort = True
                                ip = isHP.split(",")[0]
                                port = isHP.split(",")[1]
                                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                self.sock.connect((ip, int(port)))
                                sys.stdout.write("200 Port command successful (" + isHP + ").\r\n")
                                clientsocket.send(("200 Port command successful (" + isHP + ").\r\n").encode())
                        elif (command == "retr"):
                            if (not self.hasUsername or not self.hasPass):
                                sys.stdout.write("530 Not logged in.\r\n")
                                clientsocket.send("530 Not logged in.\r\n".encode())
                            # If we have not identified a hostPort yet, must throw an error.
                            elif (not self.hasPort):
                                sys.stdout.write("503 Bad sequence of commands.\r\n")
                                clientsocket.send("503 Bad sequence of commands.\r\n".encode())
                            elif (not self.isAscii(param) or "\r" in param or "\n" in param or param == ""):
                                sys.stdout.write("501 Syntax error in parameter.\r\n")
                                clientsocket.send("501 Syntax error in parameter.\r\n".encode())
                            elif (given[-2:] != "\r\n"):
                                sys.stdout.write("501 Syntax error in parameter.\r\n")
                                clientsocket.send("501 Syntax error in parameter.\r\n".encode())
                            else:
                                # Filse that start with "/" or "\\", trim it and continue.
                                if (param[0] == "/" or param[0] == "\\"):
                                    param = param[1:]
                                # If we've already copied the file before, throw an error.
                                if(param in self.fileArray):
                                    sys.stdout.write("503 Bad sequence of commands.\r\n")
                                    clientsocket.send("503 Bad sequence of commands.\r\n".encode())
                                else:
                                    try:
                                        file = open(param, 'r')
                                        line = file.read(1024)
                                        self.sock.send(line)
                                        file.close()
                                        # file = open(param,'r')
                                        # for line in file:
                                        #     self.sock.send(line.encode())
                                        # # shutil.copy(param,"retr_files/file"+str(self.filenum))
                                        self.filenum = self.filenum + 1
                                        sys.stdout.write("150 File status okay.\r\n")
                                        clientsocket.send("150 File status ok.\r\n".encode())
                                        sys.stdout.write("250 Requested file action completed.\r\n")
                                        clientsocket.send("250 Requested file action completed.\r\n".encode())
                                        self.fileArray.append(param)
                                    # If we have a file not found exception or something like that, throw an error.
                                    except:
                                        sys.stdout.write("550 File not found or access denied.\r\n")
                                        clientsocket.send("550 File not found or access denied.\r\n".encode())
                        else:
                            if (not self.hasUsername or not self.hasPass):
                                sys.stdout.write("530 Not logged in.\r\n")
                                clientsocket.send("530 Not logged in.\r\n".encode())
                            # Type-code requires the parameter to be either A or I, so check for that.
                            elif (not (param == "A" or param == "I")):
                                sys.stdout.write("501 Syntax error in parameter.\r\n")
                                clientsocket.send("501 Syntax error in parameter.\r\n".encode())
                            elif (given[-2:] != "\r\n"):
                                sys.stdout.write("501 Syntax error in parameter.\r\n")
                                clientsocket.send("501 Syntax error in parameter.\r\n".encode())
                            else:
                                sys.stdout.write("200 Type set to " + param + ".\r\n")
                                clientsocket.send(("200 Type set to " + param + ".\r\n").encode())
                # Syst, Noop, and Quit function similarly, so we filter these together.
                elif (command == "syst" or command == "noop" or command == "quit"):
                    if (command == "syst" or command == "noop"):
                        if (not self.hasUsername or not self.hasPass):
                            sys.stdout.write("530 Not logged in.\r\n")
                            clientsocket.send("530 Not logged in.\r\n".encode())
                        elif (given[4:] != "\r\n"):
                            sys.stdout.write("501 Syntax error in parameter.\r\n")
                            clientsocket.send("501 Syntax error in parameter.\r\n".encode())
                        else:
                            if(command == "syst"):
                                sys.stdout.write("215 UNIX Type: L8.\r\n")
                                clientsocket.send("215 UNIX Type: L8.\r\n".encode())
                            else:
                                sys.stdout.write("200 Command OK.\r\n")
                                clientsocket.send("200 Command OK.\r\n".encode())
                    elif (command == "quit"):
                        # If the command is not immediately followed by "\r\n", it is not valid, regardless
                        # of what command it is.
                        if (given[5:] != "\r\n"):
                            self.hasQuitted = True
                            sys.stdout.write("221 Goodbye.\r\n")
                            clientsocket.send("221 Goodbye.\r\n".encode())
                            clientsocket.close()
                        else:
                            sys.stdout.write("501 Syntax error in parameter.\r\n")
                            clientsocket.send("501 Syntax error in parameter.\r\n".encode())
                # If command was not caught in an if statement above, then it is an invalid command.
                else:
                    sys.stdout.write("500 Syntax error, command unrecognized.\r\n")
                    clientsocket.send("500 Syntax error, command unrecognized.\r\n".encode())

port = sys.argv[1];

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(("", int(port)))
serversocket.listen(1)
# print("Before true loop...")
while True:
    (clientsocket, address) = serversocket.accept()
    parser = Parser(clientsocket)
    isTrue = True
    # print("Accepted connection, reading...")
    while isTrue:
        try:
            data = clientsocket.recv(1024).decode()
            lines = data.split('\r\n')
            for line in lines:
                # print("Given line is... " + line)
                if (line != ''):
                    parser.parseCommand(line + '\r\n')
        except:
            # do nothing
            isTrue = False
