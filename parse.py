import requests

URL = "https://machinelearningmastery.com/tensorflow-tutorial-deep-learning-with-tf-keras/"

url = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
htmltext = url.text
print(htmltext)
