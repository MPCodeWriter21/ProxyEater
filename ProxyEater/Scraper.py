# ProxyEater.Scraper.py
# CodeWriter21

from __future__ import annotations

from typing import Callable as _Callable, Optional as _Optional

import pandas  # This module is used to parse the html table.
import requests  # This module is used to send requests to the server.
from random_user_agent.user_agent import \
    UserAgent  # This module is used for generating random user agents.

from .Proxy import Proxy, ProxyList, ProxyType

useragent_generator = UserAgent()

__all__ = ['Scraper']


class Scraper:
    is_succeed: bool = False

    def __init__(
        self,
        url: str,
        parser: dict,
        method: str = 'GET',
        name: _Optional[str] = None,
        useragent: _Optional[str] = None,
        proxy: _Optional[Proxy] = None,
        request_timeout: int = 10
    ) -> None:
        self.session: requests.Session = requests.Session()
        if useragent:
            self.session.headers.update({'User-Agent': useragent})
        else:
            self.session.headers.update(
                {'User-Agent': useragent_generator.get_random_user_agent()}
            )
        self.url: str = url
        self.parser: dict = parser
        self.method: str = method
        self.name: str = name or ''
        self.parser_type: str = list(self.parser.keys())[0]
        self.parser_config: dict = list(self.parser.values())[0]
        self.default_type = ProxyType.from_name(
            self.parser_config.get('type', {}).get('default', 'HTTP')
        )
        self.is_https_header = self.parser_config.get('type',
                                                      {}).get('is_https_header', None)
        self.is_https_value = self.parser_config.get('type',
                                                     {}).get('is_https_value', 'yes')
        self.protocols = self.parser_config.get('type', {}).get('protocols', {})
        self.protocols_header = self.protocols.get('header', None)
        self.protocols_http = self.protocols.get('http', 'HTTP')
        self.protocols_https = self.protocols.get('https', 'HTTPS')
        self.protocols_socks4 = self.protocols.get('socks4', 'SOCKS4')
        self.protocols_socks5 = self.protocols.get('socks5', 'SOCKS5')
        self.pages_config = self.parser_config.get('pages', {})
        self.pages_start = self.pages_config.get('start', 1)
        self.pages_end = self.pages_config.get('end', "no-proxy")
        if (self.pages_end != "no-proxy") and (not isinstance(self.pages_end, int)):
            raise ValueError("The end page must be a number or 'no-proxy'.")
        if isinstance(self.pages_end, int):
            if self.pages_end < self.pages_start:
                raise ValueError("The end page must be greater than the start page.")
        self.pages_step = self.pages_config.get('step', 1)
        self.pages_url_format_name = self.pages_config.get('format name', 'page')
        self.proxy: _Optional[Proxy] = proxy
        self.request_timeout: int = request_timeout
        self.proxies: ProxyList = ProxyList()

    def request(self, url: str) -> requests.Response:
        return self.session.request(
            method=self.method,
            url=url,
            timeout=self.request_timeout,
            proxies=({
                'http': str(self.proxy),
                'https': str(self.proxy)
            }) if self.proxy else None
        )

    def get_proxies(
        self,
        on_progress_callback: _Optional[_Callable] = None,
        on_success_callback: _Optional[_Callable] = None,
        on_failure_callback: _Optional[_Callable] = None
    ) -> ProxyList:
        """This method is used to get proxies from the server.

        :param on_progress_callback: This is a callback function that is
                called when the scraper is in progress.
        :param on_success_callback: This is a callback function that is
                called when the scraper is successful.
        :param on_failure_callback: This is a callback function that is
                called when the scraper is failed.
        :return: A ProxyList object.
        """
        if on_progress_callback:
            if not isinstance(on_progress_callback, _Callable):
                raise TypeError('on_progress_callback must be a callable object.')
        else:
            on_progress_callback = lambda obj, progress, page: None
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

        def _get_proxies(page: int = 1) -> ProxyList:
            proxies_ = ProxyList()
            on_progress_callback(self, progress=0, page=page)
            response = self.request(self.url.format(page=page))
            on_progress_callback(self, progress=10, page=page)
            if self.parser_type == "pandas":
                dataframe = pandas.read_html(response.text
                                      )[self.parser_config.get('table_index', 0)]
                for i in range(0, len(dataframe)):
                    on_progress_callback(
                        self, progress=10 + (i / len(dataframe) * 90), page=page
                    )
                    try:
                        if not self.parser_config.get('combined', None):
                            ip = str(dataframe.loc[dataframe.index[i],
                                            self.parser_config.get('ip')]).strip()
                            port = int(
                                dataframe.loc[dataframe.index[i],
                                       self.parser_config.get('port')]
                            )
                            if self.is_https_header:
                                if str(dataframe.loc[dataframe.index[i], self.is_https_header]
                                       ).strip().lower() == self.is_https_value:
                                    proxies_.add(Proxy(ip, port, ProxyType.HTTPS))
                                else:
                                    proxies_.add(Proxy(ip, port, self.default_type))
                                continue
                            if self.protocols_header:
                                protocol = str(
                                    dataframe.loc[dataframe.index[i], self.protocols_header]
                                ).strip().lower()
                                if protocol == self.protocols_http:
                                    proxies_.add(Proxy(ip, port, ProxyType.HTTP))
                                elif protocol == self.protocols_https:
                                    proxies_.add(Proxy(ip, port, ProxyType.HTTPS))
                                elif protocol == self.protocols_socks4:
                                    proxies_.add(Proxy(ip, port, ProxyType.SOCKS4))
                                elif protocol == self.protocols_socks5:
                                    proxies_.add(Proxy(ip, port, ProxyType.SOCKS5))
                                else:
                                    proxies_.add(Proxy(ip, port, self.default_type))
                                continue
                            proxies_.add(Proxy(ip, port, self.default_type))
                        else:
                            combined: str = dataframe.loc[dataframe.index[i],
                                                   self.parser_config.get('combined')]
                            if len(combined.split(':')) == 2:
                                ip = combined.split(':')[0].strip()
                                port = int(combined.split(':')[1])
                                proxies_.add(Proxy(ip, port, ProxyType.HTTP))
                    except:
                        continue

            if self.parser_type == "json":
                data = response.json()[self.parser_config.get('data')]
                for index, i in enumerate(data):
                    on_progress_callback(
                        self, progress=10 + (index / len(data) * 90), page=page
                    )
                    proxies_.add(
                        Proxy(
                            str(i[self.parser_config.get('ip', '')]).strip(),
                            int(i[self.parser_config.get('port', '')]),
                            self.default_type
                        )
                    )

            if self.parser_type == "text":
                data = str(response.content, encoding='utf-8')
                for index, i in enumerate(data.split('\n')):
                    on_progress_callback(
                        self, progress=10 + (index / len(data) * 90), page=page
                    )
                    if len(i.split(':')) == 2:
                        proxies_.add(
                            Proxy(
                                i.split(':')[0].strip(), int(i.split(':')[1]),
                                self.default_type
                            )
                        )

            on_progress_callback(self, progress=100, page=page)

            return proxies_

        try:
            if self.pages_config:
                page_index = self.pages_start
                while True:
                    if self.pages_end == "no-proxy":
                        proxies = _get_proxies(page_index)
                        if proxies.count < 1:
                            break
                    elif page_index <= self.pages_end:
                        proxies = _get_proxies(page_index)
                    else:
                        raise ValueError(
                            'The pages_end value must be "no-proxy" or a number.'
                        )
                    page_index += self.pages_step
                    self.proxies.update(proxies)
            else:
                self.proxies.update(_get_proxies())

            self.is_succeed = True
            on_success_callback(self)
        except Exception as ex:
            self.is_succeed = False
            on_failure_callback(self, ex)

        return self.proxies
