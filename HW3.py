import sys
import shutil
import socket

# The Client class is aimed at processing high lever user commands for an FTP server.
# Three types of commmands are accepted: CONNECT, GET, and QUIT.
# If a given command is incorrect by FTP standards an error message will be printed to the console,
# otherwise the command will execute.
class Client:

    def __init__(self,cport):
        # set our "connected" variable to false so we cannot try to do "gets" before we have connected.
        self.hasConnected = False
        self.portCounter = 64
        self.port = int(cport)
        self.sock = None
        self.fileNum = 1
        self.replyParser = ReplyParser()


    # Simple helper program to determine if a string is made up of entire ascii characters.
    def isAscii(self,s):
        return all(ord(c) < 128 for c in s)

    # Chomps extra spaces in a string.
    def chompSpaces(self,s):
        result = s
        while (result[:1] == " "):
            result = result[1:]
        return result

    # Finds the next space in a string.
    def findNextSpace(self,s):
        result = -1
        canChange = True
        for i in range (0,len(s)):
            if (s[i] == ' ' and canChange):
                result = i
                canChange = False

    #   sys.stdout.write("Returning index " + str(result) + " as space.\n")
        return result

    # Returns true if the given string follows the proper format for a host.
    def isServerHost(self,s):
        if (len(s) < 2):
            return False
        else:
            if (not (s[0].isalnum())):
                # sys.stdout.write("Doesn't start with letter/num.\n")
                return False
            else:
                splits = s.split(".")
                for split in splits:
                    #sys.stdout.write("Split is: " + split + ".\n")
                    if (not (split.isalnum() and self.isAscii(split))):
                        # sys.stdout.write("Not alpha numeric after split.\n")
                        return False
        return True

    # Takes a string with substrings separated by periods (such as an IP address),
    # and replaces the periods with commas.
    def replaceWithCommas(self,s):
        splits = s.split(".")
        result = ""
        for split in splits:
            result = result + split + ","

        return result;

    # Parses the command given, and either prints an error message if the command is not valid,
    # Or executes (prints) the requested FTP commands if a valid command is given.
    def parseCommand(self,s):
        sys.stdout.write(s)
        # If our command doesn't start with an c, q, or q, then it cannot be valid.
        # Not sure if this is supposed to be case sensitive or not.
        if (len(s) < 1 or not(s[0].lower() == 'c' or s[0].lower() == 'g' or s[0].lower() == 'q')):
            print("ERROR -- request")
        else:
            if (s[0].lower() == 'c' and s[0:7].lower() == 'connect'):
                # sys.stdout.write("Found a connect command.\n")
                # Need a space immediately after the command or the parameter server host is incorrect.
                if (not(s[7] == ' ')):
                    print("ERROR -- server-host.")
                else:
                    param = self.chompSpaces(s[7:])
                    # sys.stdout.write("Param is: " + param +".\n")
                    nextSpace = self.findNextSpace(param)
                    serverHost = param[:nextSpace]
                    # sys.stdout.write("Server host  is " + serverHost + ".\n")
                    if (not self.isServerHost(serverHost)):
                        print("ERROR -- server-host.")
                    else:
                        serverPort = self.chompSpaces(param[nextSpace:])
                        # sys.stdout.write("Server port before chomp: " + serverPort + ".\n")
                        # Strip CRs and LFs to get message minus EOL characters. Do in this order to
                        # account for possibilities of "\r\n" and "\n\r" which is apparently an EOL for some systems...
                        serverPort = serverPort.rstrip("\r")
                        serverPort = serverPort.rstrip("\n")
                        serverPort = serverPort.rstrip("\r")
                        # sys.stdout.write("Server port after chomp: " + serverPort + ".\n")
                        if (not serverPort.isnumeric()):
                            print("ERROR -- server-port")
                        else:
                            port = int(serverPort)
                            if (serverPort[0] == '0'):
                                print("ERROR -- server-port")
                            elif(port > 65535 or port < 0):
                                print("ERROR -- server-port")
                            else:
                                print("CONNECT accepted for FTP server at host " + serverHost + " and port " + serverPort)
                                try:
                                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    self.sock.connect((serverHost, int(serverPort)))
                                    data = self.sock.recv(1024).decode()
                                    self.replyParser.parseReply(data + "\r\n")
                                    data = "USER anonymous\r\n"
                                    sys.stdout.write(data)
                                    self.sock.send(data.encode())
                                    data = self.sock.recv(1024).decode()
                                    self.replyParser.parseReply(data + "\r\n")
                                    data = "PASS guest@\r\n"
                                    sys.stdout.write(data)
                                    self.sock.send(data.encode())
                                    data = self.sock.recv(1024).decode()
                                    self.replyParser.parseReply(data + "\r\n")
                                    data = "SYST\r\n"
                                    sys.stdout.write(data)
                                    self.sock.send(data.encode())
                                    data = self.sock.recv(1024).decode()
                                    self.replyParser.parseReply(data + "\r\n")
                                    data = "TYPE I\r\n"
                                    sys.stdout.write(data)
                                    self.sock.send(data.encode())
                                    data = self.sock.recv(1024).decode()
                                    self.replyParser.parseReply(data + "\r\n")
                                    # sys.stdout.write("USER anonymous\r\n")
                                    # sys.stdout.write("PASS guest@\r\n")
                                    # sys.stdout.write("SYST\r\n")
                                    # sys.stdout.write("TYPE I\r\n")
                                    # print("Passed all data...")v
                                    self.hasConnected = True
                                    self.portCounter = 64
                                except:
                                    print("CONNECT failed")
            elif (s[0].lower() == 'g' and s[0:3].lower() == 'get'):
                # sys.stdout.write("Found a get command.\n")
                if (not self.hasConnected):
                    print("ERROR -- expecting CONNECT")
                else:
                    param = self.chompSpaces(s[3:]);
                    if (not self.isAscii(param)):
                        print("ERROR -- pathname")
                    else:
                        param = param.rstrip("\r")
                        param = param.rstrip("\n")
                        param = param.rstrip("\r")
                        print("GET accepted for " + param)
                        myIp = socket.gethostbyname(socket.gethostname())
                        portHost = self.replaceWithCommas(myIp)
                        portHost += "31," + str(self.portCounter)
                        #print("ip was: " + myIp)

                        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        serversocket.bind(("", int(self.port)))
                        serversocket.listen(1)

                        data = "PORT " + portHost + "\r\n"
                        self.sock.send(data.encode())
                        sys.stdout.write(data)
                        data = self.sock.recv(1024).decode()
                        self.replyParser.parseReply(data)
                        # print("Sending RETR Next")
                        data = "RETR " + param + "\r\n"
                        sys.stdout.write(data)
                        self.sock.send(data.encode())
                        data = self.sock.recv(1024).decode()
                        self.replyParser.parseReply(data)
                        # print("Sent RETR")
                        if (data != "550 File not found or access denied.\r\n"):
                            (clientsocket, address) = serversocket.accept()
                            line = clientsocket.recv(1024)
                            file = open("file" + str(self.fileNum), 'w')
                            file.write(line.decode())
                            file.close()
                            clientsocket.close()
                        # print("Done accepting...")
                        # chunk = clientsocket.recv(1024)
                        # # sys.stdout.write("PORT " + portHost + "\r\n")
                        # # sys.stdout.write("RETR " + param + "\r\n")
                        # # Increment port counter so that next time we get we attach to different port.
                        # file = open("file" + str(self.fileNum), 'w')
                        # file.write(chunk.decode())
                        # print("Wrote file...")
                        self.portCounter += 1
                        self.port += 1
            elif (s[0].lower() == 'q' and s[0:4].lower() == 'quit'):
                # sys.stdout.write("Found a quit command.\n")
                if (not self.hasConnected):
                    print("ERROR -- expecting CONNECT")
                else:
                    param = s
                    param = param.rstrip("\r")
                    param = param.rstrip("\n")
                    param = param.rstrip("\r")
                    if (param.lower() == 'quit'):
                        print("QUIT accepted, terminating FTP client")
                        self.sock.send("QUIT\r\n".encode())
                        sys.stdout.write("QUIT\r\n")
                        data = self.sock.recv(1024).decode()
                        self.replyParser.parseReply(data)
                        self.sock.close()
                    else:
                        print("ERROR -- request")
            else:
                print("ERROR -- request")

# The ReplyParser class takes a string with "parseReply" and prints whether or not there
# Is an error with the reply given.
class ReplyParser:
    # Simple helper program to determine if a string is made up of entire ascii characters.
    def isAscii(self, s):
        return all(ord(c) < 128 for c in s)

    def parseReply(self,s):
        # sys.stdout.write(s)
        if (len(s) < 4):
        # Not long enough
            print("ERROR -- reply-text")
        else:
            # Reply code set to 0 so it will fail tests.
            replyCode = 0;
            if (s[0:3].isnumeric()):
                # Only set to possibly correct integer value if the first three numbers are numeric.
                replyCode = int(s[0:3])
            if (not(s[3] == ' ') or s[0] == '0'):
                # No space after code
                print("ERROR -- reply-code")
            elif (not(s[-2:] == '\r\n')):
                # Reply code doesn't end in CRLF.
                print("ERROR -- <CRLF>")
            elif (replyCode < 100 or replyCode > 599):
                # Reply code isn't in the correct range.
                print("ERROR -- reply-code")
            elif (not (self.isAscii(s[3:]))):
                print("ERROR -- reply-text")
            else:
                # Reply code is ok.
                text = s[4:]
                text = text.rstrip("\r")
                text = text.rstrip("\n")
                text = text.rstrip("\r")
                text = text.rstrip("\r")
                text = text.rstrip("\n")
                text = text.rstrip("\r")
                print("FTP reply " + str(replyCode) + " accepted. Text is: " + text)

# client = Client();
# client.parseCommand("connect this.is.a.compute\u00ff 900\n\r")
# client.parseCommand("get apath\u00ff\n")
# client.parseCommand("quit\n\r")

# Here we create a list of commands from reading input lines.
# commandList = sys.stdin.read().splitlines(True)
# Loop through each line and parse it.
# for line in commandList:
#     client.parseCommand(line)

# print("here?")
port = sys.argv[1]
client = Client(port)
commandList = sys.stdin.read().splitlines(True)
# Loop through each line and parse it.
for line in commandList:
    # print("Parsing... " + line)
    client.parseCommand(line)
# client.parseCommand("connect compute.cs.unc.edu 9000\r\n")
# client.parseCommand("Get aFile.txt\r\n")
# client.parseCommand("Quit\r\n")
# commandList = sys.stdin.read().splitlines(True)
# Loop through each line and parse it.
# for line in commandList:
#     client.parseCommand(line)
# replyParser = ReplyParser()
# replyParser.parseReply("2bc COMP 431 FTP server ready.\r\n")