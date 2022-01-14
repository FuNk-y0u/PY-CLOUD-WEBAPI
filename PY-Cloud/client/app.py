import eel
from pyc import*


@eel.expose
def _login(username, password):
	pyc = PYC_WEB_API()
	result = int(pyc.loginUi("100", username,password))
	if result == -1:
		eel.alert_login("Your account doesnt exsists! Try Signing up!",)
	if result == 1:
		eel.alert_login("Account Logged in sucessfully! Now proceeding to home page!", "SUCESS")

@eel.expose
def _signup(username, password):
	pyc = PYC_WEB_API()
	print("Sending signup info....")
	result = int(pyc.signupUi("101", username, password))
	if result == -1:
		eel.alert_signup("Your account already exsists!")
	if result == 1:
		eel.alert_signup("your account is create sucessfully!")

@eel.expose
def _getUserName():
	error = "ERROR"
	files = "This is a file"
	try:
		with open("usrdata") as usrdata:
			usrdata = usrdata.read()
			if usrdata == "":
				eel.return_eel(error)
			else:
				try:
					usrdata = usrdata.split("<sep>")	
					username = usrdata[0]
					eel.return_eel(username)

					pyc = PYC_WEB_API()
					filenames = pyc.getFileNames()

					eel.get_fileN(filenames)
				except:
					eel.return_eel(error)
	except:
		eel.return_eel(error)

eel.init("ui")
eel.start("home.html",  mode = "default")




