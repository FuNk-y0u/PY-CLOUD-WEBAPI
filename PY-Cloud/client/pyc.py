import socket
import json
import os
import sys
import getpass
import time
# Protocols codes
ERROR = -1
SUCESS=  1
protocols = {
	"login"	: "100",
	"signup": "101",
	"push"	: "200",
	"pull"	: "201",
	"share"	: "202",
	"files" : "300"
}	
	

class PYC:
	def __init__(self, argv):
		# Server info
		self.ip = "127.0.0.1"
		self.port = 5050
		
		#self.ip = "0.tcp.ngrok.io"
		#self.port = 16353
		self.buffer = 61440
		self.packet_size = 46080

		self.argv = argv
		self.seperator = "<sep>"

	def __connect(self):
		try:
			self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.client.connect((self.ip, self.port))
		except:
			print("Failed to connect to server! Check your internect connection or try later.")
			quit()

	def __send(self, data):
		self.client.send(data.encode())
		time.sleep(0.5)


	#------------------Account handling section--------------------#

	#For checking Usr Name
	def __check_username(self, username):
		length = len(username)
		if length <= 3:
			print("Error: Minimum number of character of a username is 3")
			quit()
		elif length >= 15:
			print("Error: Maximum number of chacter of a username is 15")
			quit()

	#For checking Usr Pswd
	def __check_password(self, password):
		if len(password) <= 3:
			print("Error: Minimum number of character of a password is 3")
			self.__send(str(ERROR))
			quit()
	
	def __signup(self, protocol_code):
		#Asking for user data
		self.username = input("Username: ")
		self.password = getpass.getpass()

		#Checking username and passwrd
		self.__check_username(self.username)
		self.__check_password(self.password)

		#User Data
		self.__user_data = f"{self.username}{self.seperator}{self.password}"

		#Sends Protocol Code
		self.__send(protocol_code)

		#Sends the userdata
		self.__send(self.__user_data)

		#Receives Responce
		self.__resp = int(self.client.recv(self.buffer).decode())

		#Shows status of the account creation
		if self.__resp == ERROR:
			#Faliure
			print("The account already exsists!")
			quit()
		elif self.__resp == SUCESS:
			#Creates file for auto sign up
			with open("usrdata","w") as self.__file:
				self.__file.write(f"{self.username}{self.seperator}{self.password}")
			#Sucess!
			print("The account has been registered!")

	def __login(self, protocol_code):

		#asking for user data
		self.username = input("Username: ")
		self.password = getpass.getpass()

		#user data
		self.__user_data = f"{self.username}{self.seperator}{self.password}"

		#Sends protocol code
		self.__send(protocol_code)

		#Sends the user data
		self.__send(self.__user_data)

		#Receives Responce
		self.__resp = int(self.client.recv(self.buffer).decode())

		#Shows status of the account login
		if self.__resp == ERROR:
			#Faliure
			print("Password or Username does not match!")
			quit()

		elif self.__resp == SUCESS:
			#Creates file for auto sign up
			with open("usrdata","w") as self.__file:
				self.__file.write(f"{self.username}{self.seperator}{self.password}")
			#Sucess!
			print("The account has been logged in!")


	#-----------Protocol defination----------------#
	def __push_protocol(self, protocol_code):
		# Checking for the userdata file
		if not os.path.isfile("usrdata"):
			print("Before pushing you need to create or login to your account!")
			self.__send(str(ERROR))
			quit()
		
		# Sending the protocol
		self.__send(protocol_code)

		# Reading the username and password
		with open("usrdata", "r") as r:
			user_data = r.read()
		username, password = user_data.split(self.seperator)
		self.__send(username)

		# Reading the file
		file = self.argv[2]
		print("Reading the file")
		with open(file, "rb") as r:
			file_data = r.read()
		
		# Calculating padding and packets size
		padding = self.packet_size - (len(file_data) % self.packet_size)
		file_data += b" " * padding
		packet_size = int(len(file_data) / self.packet_size)
		
		# Sending the file information to the server
		file_info = f"{file}{self.seperator}{padding}{self.seperator}{packet_size}"
		self.__send(file_info)
		time.sleep(0.5)

		# Sending actual packets by using chunking method		
		for i in range(0, len(file_data), self.packet_size):
			chunk = file_data[i:i+self.packet_size]
			print("Sending:", sys.getsizeof(chunk), "bytes..")

			self.client.send(chunk)
			time.sleep(0.1)
		
		# Telling the server that file tranfer is done
		time.sleep(1)
		self.__send(str(SUCESS))

		print("Total size:", sys.getsizeof(file_data), "bytes")
		print("Total packets:", packet_size)

	def __pull_protocol(self, protocol_code):
		# Checking for the userdata file
		if not os.path.isfile("usrdata"):
			print("Before pulling you need to create or login to your account!")
			quit()
		self.__send(protocol_code)
		
		# Reading the username and password
		with open("usrdata", "r") as r:
			user_data = r.read()
		username, password = user_data.split(self.seperator)
		self.__send(username)
		
		# Telling the server the file name
		file = self.argv[2].split("/")[-1]
		self.__send(file)
		
		# Getting the approval from the server
		approval = int(self.client.recv(self.buffer).decode())
		if approval == ERROR:
			print(f"{file} not found!")
			quit()
		
		# Getting the file info
		file_info = self.client.recv(self.buffer).decode().split(self.seperator)

		# Extracting the file data from the file info
		file_name = file_info[0]
		padding = int(file_info[1])
		packet_size = int(file_info[2])

		print("Receiving file!")
		print(f"file_name: {file_name}\npadding: {padding}\npacket_size: {packet_size}")
		
		# Receiving the packets and adding it together
		file_data = b""
		while True:
			chunk = self.client.recv(self.buffer)
			if chunk != str(SUCESS).encode():
				file_data += chunk
				print(f"Receiving: {sys.getsizeof(chunk)} bytes")
			else:
				break
		
		# Removing the padding
		file_data = file_data.strip(b" "*padding)
		print("Saving file...")
		with open(file_name.split("/")[-1], "wb") as w:
			w.write(file_data)
		
		print("Pull transaction completed!")

	def run(self):
		self.__connect()
		
		self.argv[1] = self.argv[1].lower()
		if self.argv[1] not in protocols:
			print("Unknown protocls!")
			self.client.send(str(ERROR).encode())
			quit()
		
		# Protocol handling
		protocol_code = protocols[self.argv[1]]
		if protocol_code == "100":
			self.__login(protocol_code)

		elif protocol_code == "101":
			self.__signup(protocol_code)

		elif protocol_code == "200":
			self.__push_protocol(protocol_code)

		elif protocol_code == "201":
			self.__pull_protocol(protocol_code)

		elif protocol_code == "202":
			self.client.send(protocol_code.encode())



class PYC_WEB_API:
	def __init__(self):

		# Server info
		self.ip = "127.0.0.1"
		self.port = 5050
		
		#self.ip = "0.tcp.ngrok.io"
		#self.port = 16353
		self.buffer = 61440
		self.packet_size = 46080

		self.seperator = "<sep>"

	def __connect(self):
		try:
			self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.client.connect((self.ip, self.port))
		except:
			print("Failed to connect to server! Check your internect connection or try later.")
			quit()

	def __send(self, data):
		self.client.send(data.encode())
		time.sleep(0.5)

		#------------------Account handling section--------------------#

	#For checking Usr Name
	def __check_username(self, username):
		length = len(username)
		if length <= 3:
			print("Error: Minimum number of character of a username is 3")
			quit()
		elif length >= 15:
			print("Error: Maximum number of chacter of a username is 15")
			quit()

	#For checking Usr Pswd
	def __check_password(self, password):
		if len(password) <= 3:
			print("Error: Minimum number of character of a password is 3")
			self.__send(str(ERROR))
			quit()
	
	def signupUi(self, protocol_code, username, password):
		self.password = password
		self.username = username
		self.protocol_code = protocol_code

		self.__connect()

		#Checking username and passwrd
		self.__check_username(self.username)
		self.__check_password(self.password)

		#User Data
		self.__user_data = f"{self.username}{self.seperator}{self.password}"

		#Sends Protocol Code
		self.__send(self.protocol_code)

		#Sends the userdata
		self.__send(self.__user_data)

		#Receives Responce
		self.__resp = int(self.client.recv(self.buffer).decode())

		#Shows status of the account creation
		if self.__resp == ERROR:
			#Faliure
			return ERROR
		elif self.__resp == SUCESS:
			#Creates file for auto sign up
			with open("usrdata","w") as self.__file:
				self.__file.write(f"{self.username}{self.seperator}{self.password}")
			#Sucess!
			return SUCESS

	def loginUi(self, protocol_code, username, password):

		self.username = username
		self.password = password
		self.protocol_code = protocol_code

		self.__connect()

		#user data
		self.__user_data = f"{self.username}{self.seperator}{self.password}"

		#Sends protocol code
		self.__send(self.protocol_code)

		#Sends the user data
		self.__send(self.__user_data)

		#Receives Responce
		self.__resp = int(self.client.recv(self.buffer).decode())

		#Shows status of the account login
		if self.__resp == ERROR:
			#Faliure
			return ERROR;

		if self.__resp == SUCESS:
			#Creates file for auto sign up
			with open("usrdata","w") as self.__file:
				self.__file.write(f"{self.username}{self.seperator}{self.password}")
			#Sucess!
			return SUCESS;

	def getFileNames(self):
		self.__connect()
		with open("usrdata") as self.__file:
			self.__file = self.__file.read()

		self.__file	= self.__file.split("<sep>")
		self.__send("300")
		self.__send(self.__file[0])
		self.__resp = self.client.recv(self.buffer).decode()

		return self.__resp




if __name__ == "__main__":
	if len(sys.argv) <= 1:
		print("Usage: pyc [protocol]")
		quit()

	pyc = PYC(sys.argv)
	pyc.run()
