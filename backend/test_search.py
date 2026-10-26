
from search import search_podcast

results = search_podcast("advice about friendship problems")

for result in results:
    print()
    print(result["episode"])
    print(result["timestamp"])
    print(result["similarity"])
    print(result["url"])
    print(result["preview"][:200])
    print("-" * 50)
