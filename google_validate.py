try:
    from googlesearch import search
except ImportError:
    print("No module named 'google' found")

# to search
query = "GeeksforGeeks"

for j in search(query):
    print(j)