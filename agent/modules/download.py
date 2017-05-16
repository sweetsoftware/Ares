import requests


def run(url, destination=''):
    if not destination:
        destination= url.split('/')[-1]
    req = requests.get(url, stream=True)
    with open(destination, 'wb') as f:
        for chunk in req.iter_content(chunk_size=8000):
            if chunk:
                f.write(chunk)
    return 'Download complete', None
