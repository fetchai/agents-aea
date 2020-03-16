import requests

response = requests.get(url="http://127.0.0.1:8020/status")
print(type(response))

# data = response.json()
#
# print(response.status_code==200)
