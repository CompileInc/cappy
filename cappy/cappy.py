# -*- coding: utf-8 -*-

import BaseHTTPServer
import datetime
import errno
import os
import sys
import tempfile
import time

from urlparse import urlparse, ParseResult
from datetime import timedelta

import fire
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry



def log(*args):
    message = "".join(args)
    message = "[CAPPY] " + message
    sys.stdout.write(message+"\n")
    sys.stdout.flush()

CACHE_DIR = tempfile.gettempdir()
CACHE_TIMEOUT = 60 * 60 * 24


def make_dirs(path):
    # Helper to make dirs recursively
    # http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def split_path(path):
    split_path = path.split('/')
    dirname = None
    filename = None
    if len(split_path) > 1:
        last_fragment = split_path[-1]
        if '.' not in last_fragment:
            filename = ''
            dirname = path
        else:
            filename = last_fragment
            dirname = '/'.join(split_path[:-1])
    else:
        filename = ''
        dirname = path
    return (dirname, filename)


class CacheHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    # Based on http://sharebear.co.uk/blog/2009/09/17/very-simple-python-caching-proxy/
    def get_cache(self, parsed_url, url):
        cachepath = '{}{}'.format(parsed_url.netloc, parsed_url.path)
        dirpath, filepath = split_path(cachepath)
        data = None

        if not filepath:
            filepath = 'index.html'

        cache_file = os.path.join(CACHE_DIR, dirpath, filepath)

        hit = False
        if os.path.exists(cache_file):
            if CACHE_TIMEOUT == 0:
                hit = True
            else:
                last_modified = datetime.datetime.utcfromtimestamp(os.path.getmtime(cache_file))
                valid_till = last_modified + timedelta(seconds=CACHE_TIMEOUT)
                now = datetime.datetime.utcnow()

                if valid_till > now:
                    hit = True

        if hit:
            log("Cache hit")
            file_obj = open(cache_file, 'rb')
            data = file_obj.readlines()
            file_obj.close()
        else:
            log("Cache miss")
            data = self.make_request(url=url)
            # make dirs before you write to file
            dirname, _filename = split_path(cache_file)
            make_dirs(dirname)
            file_obj = open(cache_file, 'wb+')
            file_obj.writelines(data)
            file_obj.close()
        return data

    def make_request(self, url):
        s = requests.Session()
        retries = Retry(total=3, backoff_factor=1)
        log("Requesting "+url)
        s.mount('http://', HTTPAdapter(max_retries=retries))
        return s.get(url)

    def normalize_parsed_url(self, parsed_url):
        path = parsed_url.path
        result = ParseResult(scheme=parsed_url.scheme,
                             netloc=parsed_url.netloc,
                             path=path.rstrip('/'),
                             params='',
                             query=parsed_url.query,
                             fragment=parsed_url.fragment)
        return result

    def do_GET(self):
        # cappy expects the urls to be well formed.
        # Relative urls must be handled by the application
        url = self.path.lstrip('/')
        parsed_url = self.normalize_parsed_url(urlparse(url))
        log("URL to serve: ", url)
        data = self.get_cache(parsed_url, url)
        # lstrip in case you want to test it on a browser
        self.send_response(200)
        self.end_headers()
        self.wfile.writelines(data)


class CacheProxy(object):
    def run(self, port=3030,
            cache_dir=CACHE_DIR,
            cache_timeout=CACHE_TIMEOUT):
        global CACHE_DIR
        global CACHE_TIMEOUT

        if cache_dir:
            CACHE_DIR = cache_dir

        CACHE_TIMEOUT = cache_timeout

        if not os.path.isdir(CACHE_DIR):
            make_dirs(CACHE_DIR)

        server_address = ('', port)
        httpd = BaseHTTPServer.HTTPServer(server_address, CacheHandler)

        log("Server started on port: {}".format(port))
        log("Files cached at: {}".format(CACHE_DIR))
        _cache_timeout = CACHE_TIMEOUT if CACHE_TIMEOUT > 0 else '∞'
        log("Timeout set at: {} seconds".format(_cache_timeout))

        httpd.serve_forever()


def cli():
    fire.Fire(CacheProxy)

if __name__ == '__main__':
    cli()

