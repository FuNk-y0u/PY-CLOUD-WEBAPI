import socket
import time
import threading
import json
import os

# Protocols needed to be implemented:
# 1. login
# 2. signup
# 3. push
# 4. pull
# 5. share?	(To share files with other user)


# Protocols codes
ERROR	= -1
SUCESS	=  1

LOGIN	= 100
SIGNUP	= 101
PUSH	= 200
PULL	= 201
SHARE	= 202


class Server:
	def __init__(self):
		self.ip = "127.0.0.1"
		self.port = 5050

		self.buffer = 61440
		self.packet_size = 46080

		self.running = True

		self.seperator = "<sep>"

		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server.bind((self.ip, self.port))

	def __handle_client(self, conn):
		# Handle server protocols
		protocol = int(conn.recv(self.buffer).decode())
		
		if protocol == LOGIN:
			self.__login_data = conn.recv(self.buffer).decode()
			self.__login_data = self.__login_data.split(self.seperator)

			self.__username = self.__login_data[0]
			self.__password = self.__login_data[1]

			with open("userdata/userdata.json", "r") as data_file: 
				self.__file = json.load(data_file)

			if self.__username in self.__file:
				if self.__password == self.__file[self.__username]["password"]:
					conn.send(f"{SUCESS}".encode())
				else:
					conn.send(f"{ERROR}".encode())
			else:
				conn.send(f"{ERROR}".encode())
		elif protocol == SIGNUP:

			#re-receives the signup data
			self.__user_data = conn.recv(self.buffer).decode()
			self.__user_data = self.__user_data.split(self.seperator)

			self.__username = self.__user_data[0]
			self.__password = self.__user_data[1]

			#Checks and writes data in user data json file
			with open("userdata/userdata.json", "r") as data_file: 
				self.__file = json.load(data_file)

			if self.__username in self.__file:
				conn.send(f"{ERROR}".encode())
			else:
				self.__user_detail = {"password":self.__password}
				self.__file.update({self.__username:self.__user_detail})
				with open("userdata/userdata.json", "w") as data_file:
					json.dump(self.__file, data_file)

				os.mkdir(f"userfiles/{self.__username}")
				conn.send(f"{SUCESS}".encode())

		elif protocol == PUSH:
			# Getting the username
			user = conn.recv(self.buffer).decode()
			time.sleep(0.1)

			# Getting file info
			file_info = conn.recv(self.buffer).decode().split(self.seperator)
			
			# Extracting file data from the file info
			file_name = file_info[0]
			padding = int(file_info[1])
			packet_size = int(file_info[2])

			print("Push request!")
			print(f"file_name: {file_name}\nPadding: {padding}\nPacket amt: {packet_size}")
			
			# Getting the chunks and combining it to one
			file_data = b""
			while True:
				chunk = conn.recv(self.buffer)
				if chunk != str(SUCESS).encode():
					file_data += chunk
				else:
					break
			
			# Deleting the extra padding
			file_data = file_data.strip(b" "*padding)
			
			# Saving the file in the required place
			print("File saved!")
			with open(f"userfiles/{user}/{file_name}", "wb") as w:
				w.write(file_data)

		elif protocol == PULL:
			print("Pull request!")
			
			# Getting the username
			user = conn.recv(self.buffer).decode()
			time.sleep(0.1)

			# Getting the file name
			file_name = conn.recv(self.buffer).decode()
			file_path = f"userfiles/{user}/{file_name}"
			
			# Checking if the file exists or not
			print(user, file_name)
			if not os.path.exists(file_path):
				conn.send(str(ERROR).encode())
				conn.close()
				return
			
			# Sending the approval
			time.sleep(0.5)
			conn.send(str(SUCESS).encode())
			
			# Reading the file
			print("File exists!")
			with open(file_path, "rb") as file:
				file_data = file.read()
			
			# Calculating and adding the padding
			padding = self.packet_size - (len(file_data) % self.packet_size)
			file_data += b" " * padding
			packet_size = int(len(file_data) / self.packet_size)

			file_info = f"{file_name}{self.seperator}{padding}{self.seperator}{packet_size}"

			conn.send(file_info.encode())
			time.sleep(0.5)

			for i in range(0, len(file_data), self.packet_size):
				chunk = file_data[i:i+self.packet_size]
				conn.send(chunk)
				time.sleep(0.1)

			time.sleep(1)
			conn.send(str(SUCESS).encode())
			print("Sent sucessfully!")

		elif protocol == SHARE:
			print("Do share!")

		elif protocol == "300":
			self.__user_data = conn.recv(self.buffer).decode()
			files = os.listdir(self.__user_data)
			print(files)
		conn.close()

	def run(self):
		self.server.listen()
		print(f"Server listening in {self.ip}")
		
		while self.running:
			conn, addr = self.server.accept()
			
			new_thread = threading.Thread(target=self.__handle_client, args=(conn, ))
			new_thread.start()

	#Runs a scan for usernames in the usefiles folder
	def folder_check(self):
		if "userdata" not in os.listdir("."):
			os.mkdir("userdata")
			with open("userdata/userdata.json","+w") as data_file:
				data_file.write("{}")
				data_file.close()

		if "userfiles" not in os.listdir("."):
			os.mkdir("userfiles")

		with open("userdata/userdata.json", "r") as data_file: 
			self.__file = json.load(data_file)
		folders = os.listdir("./userfiles")
		usernames = list(self.__file.keys())
		
		for i in range(len(usernames)): #For loop action baby!
			if usernames[i] in folders:
				pass
			else:
				os.mkdir(f"userfiles/{usernames[i]}") #creates a folder 

		



if __name__ == "__main__":
	server = Server()
	server.folder_check()
	server.run()
