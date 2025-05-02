import requests

def send_message(message):
    # server host ip, change if necessary
    url = "http://localhost:8000"
    response = requests.post(url, json={"message": message})
    print(response.text)

if __name__ == '__main__':
    message = input("Enter your message: ")
    send_message(message)

import requests


