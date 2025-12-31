import requests

url = ""

data = {"content":""}

headers = {'Content-Type': 'application/json'}

def ContentAdd(string):
    string += "\n"
    data["content"] += string

def Post():
    response = requests.post(url, json=data, headers=headers)
    data["content"] = ""

if __name__ == "__main__":
    print("請執行main.py!")