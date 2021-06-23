import requests

receive = requests.get('https://imgs.xkcd.com/comics/making_progress.png')
with open(r'image_2.jpeg','wb') as f:
    f.write(receive.content)
