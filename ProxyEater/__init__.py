# ProxyEater
# CodeWriter21

__version__ = "1.2.1"
__author__ = "CodeWriter21"
__email__ = "CodeWriter21@gmail.com"
__license__ = "Apache-2.0"
__copyright__ = "Copyright 2022 CodeWriter21"
__github__ = "https://github.com/MPCodeWriter21/ProxyEater"
__url__ = "https://github.com/MPCodeWriter21/ProxyEater"

from .Scraper import Scraper
from .Proxy import Proxy, ProxyType, ProxyList, ProxyStatus
from .__main__ import main

__all__ = ['Scraper', 'Proxy', 'ProxyType', 'ProxyList', 'ProxyStatus']
