# ProxyEater.Scraper.py
# CodeWriter21

from typing import Callable as _Callable

import requests  # This module is used to send requests to the server.
import pandas  # This module is used to parse the html table.

from random_user_agent.user_agent import UserAgent  # This module is used to generate random user agents.

from .Proxy import ProxyList, Proxy, ProxyType

useragent_generator = UserAgent()

__all__ = ['Scraper']


class Scraper:
    is_succeed: bool = False

    def __init__(self, url: str, parser: dict, method: str = 'GET', name: str = None, useragent: str = None,
                 proxy: Proxy = None, request_timeout: int = 10) -> None:
        self.session: requests.Session = requests.Session()
        if useragent:
            self.session.headers.update({'User-Agent': useragent})
        else:
            self.session.headers.update({'User-Agent': useragent_generator.get_random_user_agent()})
        self.url: str = url
        self.parser: dict = parser
        self.method: str = method
        self.name: str = name
        self.parser_type: str = list(self.parser.keys())[0]
        self.parser_config: dict = list(self.parser.values())[0]
        self.default_type = ProxyType.from_name(self.parser_config.get('type', {}).get('default', 'HTTP'))
        self.is_https_header = self.parser_config.get('type', {}).get('is_https_header', None)
        self.is_https_value = self.parser_config.get('type', {}).get('is_https_value', 'yes')
        self.protocols = self.parser_config.get('type', {}).get('protocols', {})
        self.protocols_header = self.protocols.get('header', None)
        self.protocols_http = self.protocols.get('http', 'HTTP')
        self.protocols_https = self.protocols.get('https', 'HTTPS')
        self.protocols_socks4 = self.protocols.get('socks4', 'SOCKS4')
        self.protocols_socks5 = self.protocols.get('socks5', 'SOCKS5')
        self.proxy: Proxy = proxy
        self.request_timeout: int = request_timeout
        self.proxies: ProxyList = ProxyList()

    def request(self) -> requests.Response:
        return self.session.request(
            method=self.method,
            url=self.url,
            timeout=self.request_timeout,
            proxies=({'http': str(self.proxy), 'https': str(self.proxy)}) if self.proxy else None
        )

    def get_proxies(self, on_progress_callback: _Callable = None, on_success_callback: _Callable = None,
                    on_failure_callback: _Callable = None) -> ProxyList:
        """
        This method is used to get proxies from the server.

        :param on_progress_callback: This is a callback function that is called when the scraper is in progress.
        :param on_success_callback: This is a callback function that is called when the scraper is successful.
        :param on_failure_callback: This is a callback function that is called when the scraper is failed.
        :return: A ProxyList object.
        """
        if on_progress_callback:
            if not isinstance(on_progress_callback, _Callable):
                raise TypeError('on_progress_callback must be a callable object.')
        else:
            on_progress_callback = lambda obj, progress: None
        if on_success_callback:
            if not isinstance(on_success_callback, _Callable):
                raise TypeError('on_success_callback must be a callable object.')
        else:
            on_success_callback = lambda obj: None
        if on_failure_callback:
            if not isinstance(on_failure_callback, _Callable):
                raise TypeError('on_failure_callback must be a callable object.')
        else:
            on_failure_callback = lambda obj, exception: None
        try:
            on_progress_callback(self, progress=0)
            response = self.request()
            on_progress_callback(self, progress=10)
            if self.parser_type == "pandas":
                df = pandas.read_html(response.text)[self.parser_config.get('table_index', 0)]
                for x in range(0, len(df)):
                    on_progress_callback(self, progress=10 + (x / len(df) * 90))
                    if not self.parser_config.get('combined', None):
                        ip = str(df.loc[df.index[x], self.parser_config.get('ip')]).strip()
                        port = int(df.loc[df.index[x], self.parser_config.get('port')])
                        if self.is_https_header:
                            if str(df.loc[df.index[x], self.is_https_header]).strip().lower() == self.is_https_value:
                                self.proxies.add(Proxy(ip, port, ProxyType.HTTPS))
                            else:
                                self.proxies.add(Proxy(ip, port, self.default_type))
                            continue
                        if self.protocols_header:
                            protocol = str(df.loc[df.index[x], self.protocols_header]).strip().lower()
                            if protocol == self.protocols_http:
                                self.proxies.add(Proxy(ip, port, ProxyType.HTTP))
                            elif protocol == self.protocols_https:
                                self.proxies.add(Proxy(ip, port, ProxyType.HTTPS))
                            elif protocol == self.protocols_socks4:
                                self.proxies.add(Proxy(ip, port, ProxyType.SOCKS4))
                            elif protocol == self.protocols_socks5:
                                self.proxies.add(Proxy(ip, port, ProxyType.SOCKS5))
                            else:
                                self.proxies.add(Proxy(ip, port, self.default_type))
                            continue
                        self.proxies.add(Proxy(ip, port, self.default_type))
                    else:
                        combined: str = df.loc[df.index[x], self.parser_config.get('combined')]
                        if len(combined.split(':')) == 2:
                            ip = combined.split(':')[0].strip()
                            port = int(combined.split(':')[1])
                            self.proxies.add(Proxy(ip, port, ProxyType.HTTP))

            if self.parser_type == "json":
                data = response.json()[self.parser_config.get('data')]
                for i, x in enumerate(data):
                    on_progress_callback(self, progress=10 + (i / len(data) * 90))
                    self.proxies.add(Proxy(
                        str(x[self.parser_config.get('ip', '')]).strip(),
                        int(x[self.parser_config.get('port', '')]),
                        self.default_type
                    ))

            if self.parser_type == "text":
                data = str(response.content, encoding='utf-8')
                for i, x in enumerate(data.split('\n')):
                    on_progress_callback(self, progress=10 + (i / len(data.split('\n')) * 90))
                    if len(x.split(':')) == 2:
                        self.proxies.add(Proxy(
                            x.split(':')[0].strip(),
                            int(x.split(':')[1]),
                            self.default_type
                        ))

            self.is_succeed = True
            on_success_callback(self)
        except Exception as e:
            self.is_succeed = False
            on_failure_callback(self, e)

        return self.proxies
