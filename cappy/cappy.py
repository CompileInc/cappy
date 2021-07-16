# -*- coding: utf-8 -*-

from __future__ import absolute_import
import six.moves.BaseHTTPServer
import datetime
import errno
import gzip
import os
import six.moves.socketserver
import sys
import tempfile

from cgi import parse_header, parse_multipart
from six.moves.urllib.parse import urlparse, ParseResult, parse_qs
from datetime import timedelta

import fire
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def log(*args):
    message = "".join(args)
    message = "[CAPPY] " + message
    sys.stdout.write(message + "\n")
    sys.stdout.flush()

CACHE_DIR = tempfile.gettempdir()
CACHE_DIR_NAMESPACE = "cappy"
CACHE_TIMEOUT = 60 * 60 * 24
CACHE_COMPRESS = False


def get_cache_dir(cache_dir):
    return os.path.join(cache_dir, CACHE_DIR_NAMESPACE)


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


def get_hashed_filepath(stub, method, parsed_url, params):
    hash_template = '{method}:{stub}{param_str}'
    param_str = ''
    if not stub:
        stub = 'index.html'
    if params:
        param_str = '&'.join(['{}={}'.format(k,v) for k,v in params.items()])
    elif method == 'GET' and parsed_url.query:
        param_str = parsed_url.query
    if param_str:
        param_str = '?'+param_str
    return hash_template.format(method=method, stub=stub, param_str=param_str)


class CacheHandler(six.moves.socketserver.ThreadingMixIn, six.moves.BaseHTTPServer.BaseHTTPRequestHandler):
    # Based on http://sharebear.co.uk/blog/2009/09/17/very-simple-python-caching-proxy/
    def get_cache(self, parsed_url, url, params={}):
        cachepath = '{}{}'.format(parsed_url.netloc, parsed_url.path)
        method = self.command
        dirpath, filepath_stub = split_path(cachepath)
        data = None
        filepath = get_hashed_filepath(stub=filepath_stub, method=method, parsed_url=parsed_url, params=params)

        cache_file = os.path.join(get_cache_dir(CACHE_DIR), dirpath, filepath)
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

        fopen = gzip.open if CACHE_COMPRESS else open

        if hit:
            log("Cache hit")
            file_obj = fopen(cache_file, 'rb')
            data = file_obj.readlines()
            file_obj.close()
        else:
            log("Cache miss")
            data = self.make_request(url=url, params=params, method=method)
            # make dirs before you write to file
            dirname, _filename = split_path(cache_file)
            make_dirs(dirname)
            file_obj = fopen(cache_file, 'wb+')
            file_obj.writelines(data)
            file_obj.close()
        return data

    def make_request(self, url, params={}, method='GET'):
        s = requests.Session()
        retries = Retry(total=3, backoff_factor=1)
        req = requests.Request(method, url, data=params)
        prepped = req.prepare()
        log("Requesting " + url)
        s.mount('http://', HTTPAdapter(max_retries=retries))
        return s.send(prepped)

    def _normalize_params(self, params):
        for k, v in params.items():
            if isinstance(v, list):
                v_str = ','.join(v)
                params[k] = v_str
        return params

    def get_post_params(self):
        ctype, pdict = parse_header(self.headers['content-type'])
        postvars = {}
        if ctype == 'multipart/form-data':
            postvars = parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers['content-length'])
            postvars = parse_qs(self.rfile.read(length), keep_blank_values=1)
        return self._normalize_params(postvars)

    def normalize_parsed_url(self, parsed_url):
        path = parsed_url.path
        result = ParseResult(scheme=parsed_url.scheme,
                             netloc=parsed_url.netloc,
                             path=path.rstrip('/'),
                             params='',
                             query=parsed_url.query,
                             fragment=parsed_url.fragment)
        return result

    def process_request(self, params={}):
        # cappy expects the urls to be well formed.
        # Relative urls must be handled by the application
        url = self.path.lstrip('/')
        parsed_url = self.normalize_parsed_url(urlparse(url))
        log("URL to serve: ", url)
        data = self.get_cache(parsed_url, url, params)
        # lstrip in case you want to test it on a browser
        self.send_response(200)
        self.end_headers()
        self.wfile.writelines(data)

    def do_GET(self):
        self.process_request()

    def do_POST(self):
        params = self.get_post_params()
        self.process_request(params)


class CacheProxy(object):
    def run(self, port=3030,
            cache_dir=CACHE_DIR,
            cache_timeout=CACHE_TIMEOUT,
            cache_compress=CACHE_COMPRESS):
        global CACHE_DIR
        global CACHE_TIMEOUT
        global CACHE_COMPRESS

        if cache_dir:
            CACHE_DIR = cache_dir

        CACHE_COMPRESS = cache_compress
        CACHE_TIMEOUT = cache_timeout

        if not os.path.isdir(CACHE_DIR):
            make_dirs(get_cache_dir(CACHE_DIR))

        server_address = ('', port)
        httpd = six.moves.BaseHTTPServer.HTTPServer(server_address, CacheHandler)

        log("Server started on port: {}".format(port))

        _compressed = "(compressed) " if CACHE_COMPRESS else ""
        log("Files cached {}at: {}".format(_compressed, get_cache_dir(CACHE_DIR)))

        _cache_timeout = CACHE_TIMEOUT if CACHE_TIMEOUT > 0 else '∞'
        log("Timeout set at: {} seconds".format(_cache_timeout))

        httpd.serve_forever()


def cli():
    fire.Fire(CacheProxy)

if __name__ == '__main__':
    cli()
