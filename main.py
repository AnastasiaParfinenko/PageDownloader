import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote, urljoin
from collections import namedtuple
from pathlib import Path


class Url:
    def __init__(self, address):
        self.address = unquote(self.cut_address(address))

        parsed_url = urlparse(self.address)
        self.scheme = parsed_url.scheme
        self.domain = parsed_url.netloc

        path = self.domain + parsed_url.path
        if not path.endswith('html'):
            path += 'index.html'
        self.path = path

    def __repr__(self):
        return f'{self.address}'

    @staticmethod
    def cut_address(address):
        hash_index = address.find('#')
        if hash_index >= 0:
            address = address[:hash_index]

        question_index = address.find('?')
        if question_index >= 0:
            address = address[:question_index]

        if not (address.endswith('html') or address.endswith('/')):
            address += '/'

        return address


Response = namedtuple('Response', ['url', 'text'])


class RealInternet:
    @staticmethod
    def get(url):
        try:
            r = requests.get(url.address)
        except requests.exceptions.ConnectionError:
            return None

        if url.domain != Url(r.url).domain:
            return None

        return Response(Url(r.url), r.text)


class RealFS:
    @staticmethod
    def save(file_path, content):
        os.chdir('/tmp')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)


class App:
    def __init__(self, internet, fs, depth, visited_address):
        self.internet = internet
        self.fs = fs
        self.max_depth = depth
        self.visited_address = visited_address

    def download(self, cur_depth, address):
        url = Url(address)
        if not self.try_download(cur_depth, url):
            print('Invalid URL')

    def try_download(self, cur_depth, url):
        if url.address in self.visited_address:
            return True
        if cur_depth > self.max_depth:
            return False

        response = self.internet.get(url)
        if response:
            self.visited_address.add(response.url.address)
            text = self.process_links(cur_depth + 1, response)
            self.fs.save(response.url.path, text)
            return True

        return False

    def process_links(self, cur_depth, response):
        url = response.url
        patched_text = response.text
        links = get_links(response)
        for link in links:
            if not is_absolute(link):
                new_address = urljoin(url.address, link)
            elif Url(link).domain == url.domain:
                new_address = link
            else:
                continue

            new_url = Url(new_address)
            downloaded = self.try_download(cur_depth, new_url)

            new_link = internal_link(new_url, url) if downloaded else new_address

            patched_text = patched_text.replace(f'href="{link}"', f'href="{new_link}"', 1)

        return patched_text


def try_exit(text):
    if text == 'exit':
        sys.exit()


def is_absolute(address):
    parsed_url = urlparse(address)
    return True if parsed_url.scheme else False


def get_links(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    elements = soup.find_all(['a'])
    all_links_list = [el.get('href') for el in elements]
    links_list = [link for link in all_links_list if link and not link.startswith('#')]
    return links_list


def internal_link(ref_url, cur_url):
    ref_path = Path(ref_url.path)
    cur_path = Path(cur_url.path)
    new_link = os.path.relpath(ref_path, cur_path.parent)

    return new_link


def main():
    app = App(RealInternet(), RealFS(), 1, set())

    while True:
        address = input()
        try_exit(address)

        if not is_absolute(address):
            address = 'http://' + address

        app.download(0, address)


if __name__ == '__main__':
    main()
