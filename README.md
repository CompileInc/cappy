# CAPPY [![PyPI](https://img.shields.io/pypi/v/cappy.svg?maxAge=2592000?style=plastic)](https://pypi.python.org/pypi/cappy/)

CAchingProxyinPython is a file based python proxy based on Sharebear's
[simple python caching proxy](http://sharebear.co.uk/blog/2009/09/17/very-simple-python-caching-proxy/).

## Install

```pip install cappy```

## Usage

```cappy run```

### Options

- ```--port``` - optional (default: 3030)
- ```--cache_dir``` - optional (default: Temporary platform specific folder)
- ```--cache_timeout``` - optional (default: 864000 seconds, use 0 for caching indefinitely)
- ```--cache_compress``` - optional (default: False) Compress and store the cache

## Building & Publishing

### Prerequisites

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Ensure PyPI credentials are configured in `~/.pypirc` per the [PyPI spec](https://packaging.python.org/en/latest/specifications/pypirc/).

### Workflow

Run the release helper to build wheels and source archives via Hatch:

```bash
./upload.sh
```

`upload.sh` shells out to `uvx hatch build` followed by `uvx hatch publish`, so Hatch runs in an ephemeral environment without a global install.
