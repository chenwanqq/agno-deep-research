try:
    from googlesearch import search
except ImportError:
    print("No module named 'google' found")

# to search
query = "202年9月6日北京天气"

for result in search(query, num_results=10,advanced=True):
    print("url:",result.url)
    print("title:",result.title)
    print("description:",result.description,len(result.description))
    print("---")

