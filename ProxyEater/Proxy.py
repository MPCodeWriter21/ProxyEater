# ProxyEater.Proxy.py
# CodeWriter21

from __future__ import annotations

import os
import csv  # This module is used to write proxies to a csv file.
import json  # This module is used to parse the ProxyList to json.
import time  # This module is used to sleep the program.
import threading  # This module is used to create threads.
from enum import Enum
from typing import (Dict as _Dict, Union as _Union, Callable as _Callable,
                    Iterable as _Iterable, Optional as _Optional)

import requests  # This module is used for sending requests to the servers.
from requests.exceptions import InvalidProxyURL

__all__ = ['Proxy', 'ProxyType', 'ProxyList', 'ProxyStatus']


class ProxyStatus(Enum):
    """This class is used to define the status of a proxy."""
    UNKNOWN = 0
    ALIVE = 1
    DEAD = 2

    @staticmethod
    def from_name(name: str) -> ProxyStatus:
        """This method is used to for getting a ProxyStatus object from its
        name.

        :param name: The name of the ProxyStatus.
        :return: The ProxyStatus.
        """
        name = name.lower()
        if name == 'unknown':
            return ProxyStatus.UNKNOWN
        if name == 'alive':
            return ProxyStatus.ALIVE
        if name == 'dead':
            return ProxyStatus.DEAD
        raise ValueError(f'The proxy type({name}) is not valid.')


class ProxyType(Enum):
    """This class is used to define the type of proxy."""
    HTTP = 0
    HTTPS = 1
    SOCKS4 = 2
    SOCKS5 = 3

    @staticmethod
    def from_name(name: str) -> ProxyType:
        """This method is used to get the ProxyType from the name.

        :param name: The name of the ProxyType.
        :return: The ProxyType.
        """
        name = name.lower()
        if name == 'http':
            return ProxyType.HTTP
        if name == 'https':
            return ProxyType.HTTPS
        if name == 'socks4':
            return ProxyType.SOCKS4
        if name == 'socks5':
            return ProxyType.SOCKS5
        raise ValueError(f'The proxy type({name}) is not valid.')


class Proxy:
    geolocation_info: dict = {}
    status: ProxyStatus = ProxyStatus.UNKNOWN

    def __init__(self, ip: str, port: int, type_: ProxyType) -> None:
        self.ip: str = ip
        self.port: int = port
        if isinstance(type_, str):
            type_ = ProxyType.from_name(type_)
        self.type: ProxyType = type_

    def check_status(
        self,
        timeout: int = 10,
        url: str = 'http://icanhazip.com/',
        on_success_callback: _Optional[_Callable] = None,
        on_failure_callback: _Optional[_Callable] = None
    ) -> bool:
        """This method is used to check if the proxy is alive.

        :param timeout: The timeout of the request.
        :param url: The url to try to connect to through the proxy.
        :param on_success_callback: The callback to be called if the request succeeds.
        :param on_failure_callback: The callback to be called if the request fails.
        :return: True if the proxy is alive, False otherwise.
        """
        if on_success_callback is not None:
            if not callable(on_success_callback):
                raise TypeError('on_success_callback must be a callable.')
        else:
            on_success_callback = lambda proxy, status: None
        if on_failure_callback is not None:
            if not callable(on_failure_callback):
                raise TypeError('on_failure_callback must be a callable.')
        else:
            on_failure_callback = lambda proxy, error: None
        try:
            if requests.get(url, proxies={'http': str(self), 'https': str(self)},
                            timeout=timeout).status_code == 200:
                self.status = ProxyStatus.ALIVE
                on_success_callback(self, ProxyStatus.ALIVE)
                return True
            else:
                self.status = ProxyStatus.DEAD
                on_success_callback(self, ProxyStatus.DEAD)
                return False
        except Exception as ex:
            self.status = ProxyStatus.DEAD
            on_failure_callback(self, ex)
            return False

    @property
    def is_alive(self) -> bool:
        return self.status == ProxyStatus.ALIVE

    def check_geolocation(
        self,
        fields: str = 'status,message,continent,continentCode,country,countryCode,'
        'region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,'
        'query',
        on_error_callback: _Optional[_Callable] = None
    ) -> _Dict:
        """This method is used to check the geolocation of the proxy.

        :param fields: The fields to be returned.
        :param on_error_callback: The callback to be called if the request fails.
        """
        if on_error_callback is not None:
            if not callable(on_error_callback):
                raise TypeError('on_error_callback must be a callable.')
        else:
            on_error_callback = lambda proxy, error: None
        try:
            response = requests.get(
                url=f"http://ip-api.com/json/{self.ip}?fields={fields}"
            )
            self.geolocation_info = response.json()
            return self.geolocation_info
        except Exception as e:
            on_error_callback(self, e)
            return {}

    def get_geolocation_info(self) -> _Dict:
        if self.geolocation_info is None:
            return self.check_geolocation()
        return self.geolocation_info

    @staticmethod
    def from_text(text: str, default_type: _Optional[ProxyType] = None) -> 'Proxy':
        """This method is used to create a Proxy from a text.

        :param text: The text to create the Proxy from.
        :param default_type: The default type of the Proxy.
        :return: The Proxy.
        """
        if text.count(':') == 1:  # Proxies with no scheme; will use default_type
            ip, port = text.split(':')
            ip = ip.strip(' /')
            port = int(port)
            if default_type is None:
                raise ValueError(
                    f'`{text}`: Proxy without scheme: Default type is not specified.'
                )
            else:
                return Proxy(ip, port, default_type)
        elif text.count(':') == 2:  # Proxies having scheme
            scheme, ip, port = text.split(':')
            ip = ip.strip(' /')
            port = int(port)
            if scheme.lower() == 'http':
                return Proxy(ip, port, ProxyType.HTTP)
            if scheme.lower() == 'https':
                return Proxy(ip, port, ProxyType.HTTPS)
            if scheme.lower() == 'socks4':
                return Proxy(ip, port, ProxyType.SOCKS4)
            if scheme.lower() == 'socks5':
                return Proxy(ip, port, ProxyType.SOCKS5)
            raise ValueError(f'`{text}`: Proxy with unknown scheme: {scheme}')
        else:
            raise ValueError(f'`{text}`: Proxy with invalid format.')

    def __str__(self) -> str:
        return f'{self.type.name.lower()}://{self.ip}:{self.port}'

    def __repr__(self) -> str:
        return f"Proxy(ip='{self.ip}', port={self.port})"

    def __eq__(self, other: Proxy) -> bool:
        if not isinstance(other, Proxy):
            return False
        return self.ip == other.ip and self.port == other.port

    def __hash__(self) -> int:
        return hash(self.ip + str(self.port))

    def __dict__(self) -> dict:
        return {
            'ip': self.ip,
            'port': self.port,
            'type': self.type.name,
            'status': self.status.name,
            'scheme': self.type.name.lower(),
            'geolocation_info': self.geolocation_info
        }

    def __iter__(self):
        return iter(
            (
                ('ip', self.ip), ('port', self.port), ('type', self.type.name),
                ('status', self.status.name), ('scheme', self.type.name.lower()),
                ('geolocation_info', self.geolocation_info)
            )
        )


class ProxyList(set):

    def __init__(self, proxies: _Optional[_Iterable[Proxy]] = None):
        super().__init__()
        if proxies is not None:
            self.update(proxies)

    def update(self, proxies: _Iterable[Proxy]):
        temp = set()
        for proxy in set(proxies):
            if isinstance(proxy, Proxy):
                temp.add(proxy)
            else:
                raise TypeError(
                    "ProxyList.update() argument must be a sequence of Proxy objects."
                )

        super().update(temp)

    def add(self, proxy: Proxy):
        if isinstance(proxy, Proxy):
            super().add(proxy)
        else:
            raise TypeError("ProxyList.add() argument must be a Proxy object.")

    def union(self, proxies: _Iterable[Proxy]):
        temp = set()
        for proxy in set(proxies):
            if isinstance(proxy, Proxy):
                temp.add(proxy)
            else:
                raise TypeError(
                    "ProxyList.union() argument must be a sequence of Proxy objects."
                )

        return super().union(temp)

    def check_all(
        self,
        timeout: int = 10,
        threads_no: int = 21,
        url: str = 'http://icanhazip.com/',
        remove_dead: bool = True,
        on_progress_callback: _Optional[_Callable] = None
    ) -> None:
        """This method is used to check the status of all proxies in the list.

        :param timeout: The timeout of the requests.
        :param threads_no: The number of threads to use.
        :param url: The url to try to connect to through the proxy.
        :param remove_dead: If True, dead proxies will be removed from the list.
        :param on_progress_callback: A callback function to be called on each progress.
        """
        if on_progress_callback is not None:
            if not callable(on_progress_callback):
                raise TypeError(
                    "ProxyList.check_all() argument on_progress_callback must be "
                    "a callable."
                )
        else:
            on_progress_callback = lambda proxy_list, progress: None

        length = len(self)
        finished: int = 0  # The number of proxies that have been checked.

        def check_proxy(proxy_: Proxy):
            """This function is used for checking the status of a proxy.

            :param proxy_: The proxy to check.
            :return:
            """
            nonlocal finished
            proxy_.check_status(timeout, url)
            if (not proxy_.is_alive) and remove_dead:
                self.remove(proxy_)
            finished += 1
            on_progress_callback(self, finished / length * 99.99)

        threads = []
        for proxy in self.copy():
            thread = threading.Thread(target=check_proxy, args=(proxy, ))
            threads.append(thread)
            thread.start()
            while len(threads) >= threads_no:
                for thread in threads.copy():
                    if not thread.is_alive():
                        threads.remove(thread)
                        break
                time.sleep(0.1)

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        on_progress_callback(self, 100)

    def to_text(
        self, separator: str = "\n", format_: str = '{scheme}://{ip}:{port}'
    ) -> str:
        """This method is used to convert the list to a text string.

        :param separator: The separator between proxies.
        :param format_: The format of each proxy.
        :return: The text string.
        """
        return separator.join(format_.format(**dict(proxy)) for proxy in self)

    def batch_collect_geolocations(
        self,
        fields: str = 'status,message,continent,continentCode,country,countryCode,'
        'region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,'
        'query',
        on_progress_callback: _Optional[_Callable] = None,
        on_error_callback: _Optional[_Callable] = None
    ) -> None:
        """This method is used to collect the geolocation of all proxies in the
        list.

        :param fields: The fields to be returned.
        :param on_progress_callback: A callback function to be called on each progress.
        :param on_error_callback: A callback function to be called on each error.
        """
        if on_progress_callback is not None:
            if not callable(on_progress_callback):
                raise TypeError(
                    "ProxyList.batch_collect_geolocations() argument on_progress_callback must be a"
                    " callable."
                )
        else:
            on_progress_callback = lambda proxy_list, progress: None
        if on_error_callback is not None:
            if not callable(on_error_callback):
                raise TypeError(
                    "ProxyList.batch_collect_geolocations() argument on_error_callback "
                    "must be a callable."
                )
        else:
            on_error_callback = lambda proxy_list, error: None
        all_proxies = list(self)
        for start_index in range(0, len(self), 100):
            end_index = start_index + 100 if start_index + 100 < len(self
                                                                     ) else len(self)
            proxies = all_proxies[start_index:end_index]
            try:
                response = requests.post(
                    url=f"http://ip-api.com/batch?fields={fields}",
                    json=[proxy.ip for proxy in proxies]
                ).json()
                for index, proxy in enumerate(proxies):
                    proxy.geolocation_info = response[index]
                on_progress_callback(self, end_index / len(self) * 100)
            except Exception as ex:
                on_error_callback(
                    self, Exception("Failed to collect geolocation information.", ex)
                )

    def to_json(
        self,
        indent: int = 4,
        include_status: bool = True,
        include_geolocation: bool = True
    ) -> str:
        """This method is used to convert the list to a json string.

        :param indent: The indentation of the json string.
        :param include_status: If True, the status of the proxy will be
                included in the json string.
        :param include_geolocation: If True, the geolocation of the
                proxy will be included in the json string.
        """
        if include_geolocation:
            self.batch_collect_geolocations()
        proxies = []
        for proxy in self:
            proxies.append(
                {
                    'ip': proxy.ip,
                    'port': proxy.port,
                    'type': proxy.type.name
                }
            )
            if include_status:
                proxies[-1]['status'] = proxy.status.name
            if include_geolocation:
                proxies[-1]['geolocation_info'] = proxy.get_geolocation_info()

        return json.dumps(proxies, indent=indent)

    def to_text_file(
        self,
        filename: _Union[str, os.PathLike],
        separator: str = "\n",
        format_: str = '{scheme}://{ip}:{port}'
    ) -> None:
        """This method is used to write the list to a text file.

        :param filename: The name of the text file.
        :param separator: The separator of the text file.
        :param format_: The format of each proxy.
        """
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(self.to_text(separator, format_))

    def to_json_file(
        self,
        filename: _Union[str, os.PathLike],
        indent: int = 4,
        include_status: bool = True,
        include_geolocation: bool = True
    ) -> None:
        """This method is used to write the list to a json file.

        :param filename: The name of the json file.
        :param indent: The indentation of the json string.
        :param include_status: If True, the status of the proxy will be
                included in the json string.
        :param include_geolocation: If True, the geolocation of the
                proxy will be included in the json string.
        """
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(self.to_json(indent, include_status, include_geolocation))

    def to_csv_file(
        self,
        filename: _Union[str, os.PathLike],
        include_status: bool = True,
        include_geolocation: bool = True
    ) -> None:
        """This method is used to convert the list to a csv file.

        :param filename: The name of the csv file.
        :param include_status: If True, the status of the proxy will be
                included in the csv file.
        :param include_geolocation: If True, the geolocation of the
                proxy will be included in the csv file.
        """
        if include_geolocation:
            self.batch_collect_geolocations()
        with open(filename, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            if include_status and include_geolocation:
                writer.writerow(['ip', 'port', 'type', 'status', 'geolocation_info'])
                for proxy in self:
                    writer.writerow(
                        [
                            proxy.ip, proxy.port, proxy.type.name, proxy.status.name,
                            proxy.get_geolocation_info()
                        ]
                    )
            elif include_status:
                writer.writerow(['ip', 'port', 'type', 'status'])
                for proxy in self:
                    writer.writerow(
                        [proxy.ip, proxy.port, proxy.type.name, proxy.status.name]
                    )
            elif include_geolocation:
                writer.writerow(['ip', 'port', 'type', 'geolocation_info'])
                for proxy in self:
                    writer.writerow(
                        [
                            proxy.ip, proxy.port, proxy.type.name,
                            proxy.get_geolocation_info()
                        ]
                    )
            else:
                writer.writerow(['ip', 'port', 'type'])
                for proxy in self:
                    writer.writerow([proxy.ip, proxy.port, proxy.type.name])

    @staticmethod
    def from_text(
        text: str,
        separator: str = "\n",
        default_type: _Optional[ProxyType] = None
    ) -> 'ProxyList':
        """This method is used to convert a text string to a ProxyList.

        :param text: The text string.
        :param separator: The separator of the text string.
        :param default_type: The default type of the proxy.
        """
        proxies = ProxyList()
        for proxy in text.split(separator):
            proxies.add(Proxy.from_text(proxy, default_type))
        return proxies

    @staticmethod
    def from_json(json_string: str) -> 'ProxyList':
        """This method is used to convert the json string to a ProxyList.

        :param json_string: The json string.
        """
        proxies = json.loads(json_string)
        proxy_list = ProxyList()
        for proxy in proxies:
            if 'ip' in proxy and 'port' in proxy and 'type' in proxy:
                proxy_ = Proxy(
                    ip=proxy['ip'],
                    port=proxy['port'],
                    type_=ProxyType.from_name(proxy['type'])
                )
            else:
                raise Exception(f"Invalid proxy format: {proxy}")
            if 'status' in proxy:
                proxy_.status = ProxyStatus.from_name(proxy['status'])
            if 'geolocation_info' in proxy:
                proxy_.geolocation_info = proxy['geolocation_info']
            proxy_list.add(proxy_)

        return proxy_list

    @staticmethod
    def from_text_file(
        filename: _Union[str, os.PathLike],
        separator: str = "\n",
        default_type: _Optional[ProxyType] = None
    ) -> 'ProxyList':
        """This method is used to convert a text file to a ProxyList.

        :param filename: The name of the text file.
        :param separator: The separator of the text file.
        :param default_type: The default type of the proxy.
        """
        with open(filename, 'r', encoding='utf-8') as file:
            return ProxyList.from_text(file.read(), separator, default_type)

    @staticmethod
    def from_json_file(filename: _Union[str, os.PathLike]) -> 'ProxyList':
        """This method is used to convert a json file to a ProxyList.

        :param filename: The name of the json file.
        """
        with open(filename, 'r', encoding='utf-8') as file:
            return ProxyList.from_json(file.read())

    @staticmethod
    def from_csv_file(
        filename: _Union[str, os.PathLike],
        default_type: _Optional[ProxyType] = None
    ) -> 'ProxyList':
        """This method is used to convert the csv file to a ProxyList.

        :param filename: The name of the csv file.
        :param default_type: The default type of the proxy.
        """
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            proxies = []
            for row in reader:
                proxies.append(row)
        proxy_list = ProxyList()
        for proxy in proxies:
            if len(proxy) == [3, 4, 5]:
                proxy_list.add(
                    Proxy(
                        ip=proxy[0],
                        port=int(proxy[1]),
                        type_=ProxyType.from_name(proxy[2])
                    )
                )
            elif len(proxy) == 2:
                if default_type is None:
                    raise InvalidProxyURL(
                        f"Invalid proxy format: {proxy}. "
                        "You should specify the default type."
                    )
                proxy_list.add(
                    Proxy(ip=proxy[0], port=int(proxy[1]), type_=default_type)
                )
            else:
                raise InvalidProxyURL(f"Invalid proxy format: {proxy}")
        return proxy_list

    def filter(
        self,
        status: _Optional[ProxyStatus] = None,
        type_: _Optional[_Union[ProxyType, _Iterable[ProxyType]]] = None,
        continent: _Optional[str] = None,
        country: _Optional[str] = None,
        region: _Optional[str] = None,
        city: _Optional[str] = None,
        isp: _Optional[str] = None,
        org: _Optional[str] = None,
        asname: _Optional[str] = None
    ) -> 'ProxyList':
        """This method is used to filter the list of proxies.

        :param status: The status of the proxy.
        :param type_: The type of the proxy.
        :param continent: The continent of the proxy.
        :param country: The country of the proxy.
        :param region: The region of the proxy.
        :param city: The city of the proxy.
        :param isp: The isp of the proxy.
        :param org: The org of the proxy.
        :param asname: The asname of the proxy.
        :return: The filtered list of proxies.
        """
        filtered_proxies = ProxyList()
        for proxy in self:
            if status is not None and proxy.status != status:
                continue
            if type_ is not None:
                if isinstance(type_, ProxyType):
                    if proxy.type != type_:
                        continue
                else:
                    if proxy.type not in type_:
                        continue
            if continent is not None and proxy.get_geolocation_info(
            )['continent'] != continent:
                continue
            if country is not None and proxy.get_geolocation_info(
            )['country'] != country:
                continue
            if region is not None and proxy.get_geolocation_info()['region'] != region:
                continue
            if city is not None and proxy.get_geolocation_info()['city'] != city:
                continue
            if isp is not None and proxy.get_geolocation_info()['isp'] != isp:
                continue
            if org is not None and proxy.get_geolocation_info()['org'] != org:
                continue
            if asname is not None and proxy.get_geolocation_info()['asname'] != asname:
                continue
            filtered_proxies.add(proxy)

        return filtered_proxies

    @property
    def count(self) -> int:
        return len(self)

    def __repr__(self):
        return f'ProxyList(count={len(self)})'
