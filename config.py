import os

class Config(object):
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'a test key'
	#just makes sure that there are not security attacks