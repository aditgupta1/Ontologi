from googlesearch import search

def get_query_links():

	# query = input("Enter Your Query: ")
	query = 'tensorflow'

	urls = []

	for url in search(query, stop = 30):
		urls.append(url)

	return urls