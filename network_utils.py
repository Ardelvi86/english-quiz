from functools import lru_cache
import ssl

import certifi


@lru_cache(maxsize=1)
def create_ssl_context():
    return ssl.create_default_context(cafile=certifi.where())
