ProxyEater\[1.5.0\]
===================

![version](https://img.shields.io/pypi/v/ProxyEater)
![stars](https://img.shields.io/github/stars/MPCodeWriter21/ProxyEater)
[![CodeFactor](https://www.codefactor.io/repository/github/mpcodewriter21/proxyeater/badge)](https://www.codefactor.io/repository/github/mpcodewriter21/proxyeater)

A Python Proxy Scraper for gathering fresh proxies.

![issues](https://img.shields.io/github/issues/MPCodeWriter21/log21)
![contributors](https://img.shields.io/github/contributors/MPCodeWriter21/log21)

Install ProxyEater
------------------

To install **ProxyEater**, you can simply use the `pip install ProxyEater` command:

```commandline
python -m pip install ProxyEater
```

Or you can clone [the repository](https://github.com/MPCodeWriter21/ProxyEater) and run:

```commandline
git clone https://github.com/MPCodeWriter21/ProxyEater
cd ProxyEater
```

```commandline
python setup.py install
```

Usage
-----

```
usage: ProxyEater [-h] [--source SOURCE] [--output OUTPUT] [--file-format { text, json, csv }]
                  [--format FORMAT] [--include-status] [--threads THREADS] [--timeout TIMEOUT]
                  [--url URL] [--verbose] [--quiet] [--version] [--proxy PROXY] [--proxy-type
                  PROXY_TYPE] [--useragent USERAGENT] [--include-geolocation] [--no-check]
                  [--source-format { text, json, csv }] [--default-type { http, https, socks4,
                  socks5 }]
                  mode

positional arguments:
  mode              Modes: Scrape, Check

options:
  -h, --help
                        show this help message and exit
  --source SOURCE, -s SOURCE
                        The source of the proxies(default:C:\Users\Morteza\AppData\Local\Programs\
                        Python\Python310\lib\site-packages\ProxyEater\sources.json).
  --output OUTPUT, -o OUTPUT
                        The output file.
  --file-format { text, json, csv }, -ff { text, json, csv }
                        The format of the output file(default:text).
  --format FORMAT, -f FORMAT
                        The format for saving the proxies in text
                        file(default:"{scheme}://{ip}:{port}").
  --include-status, -is
                        Include the status of the proxies in the output file.
  --threads THREADS, -t THREADS
                        The number of threads to use for scraping(default:25).
  --timeout TIMEOUT, -to TIMEOUT
                        The timeout of the requests(default:15).
  --url URL, -u URL
                        The url to use for checking the proxies(default:http://icanhazip.com).
  --verbose, -v
                        The verbose of the program(default:False).
  --quiet, -q
                        The quiet of the program(default:False).
  --version, -V
                        The version of the program.

Scrape:
  Scrape mode arguments

  --proxy PROXY, -p PROXY
                        The proxy to use for scraping.
  --proxy-type PROXY_TYPE, -type PROXY_TYPE
                        The type of the proxies(default:all).
  --useragent USERAGENT, -ua USERAGENT
                        The useragent of the requests(default:random).
  --include-geolocation, -ig
                        Include the geolocation info of the proxies in the output file.
  --no-check, -nc
                        Use this option to skip the checking of the proxies after

Check:
  Check mode arguments

  --source-format { text, json, csv }, -sf { text, json, csv }
                        The format of the source file(default:text).
  --default-type { http, https, socks4, socks5 }, -dt { http, https, socks4, socks5 }
                        The default type of the proxies - Use this if you are providing proxies
                        without scheme(default:http).

```

About
-----
Author: CodeWriter21 (Mehrad Pooryoussof)

GitHub: [MPCodeWriter21](https://github.com/MPCodeWriter21)

Telegram Channel: [@CodeWriter21](https://t.me/CodeWriter21)

Aparat Channel: [CodeWriter21](https://www.aparat.com/CodeWriter21)

### License

![License](https://img.shields.io/github/license/MPCodeWriter21/ProxyEater)

[apache-2.0](http://www.apache.org/licenses/LICENSE-2.0)

### Donate

In order to support this project you can donate some crypto of your choice 8D

[Donate Addresses](https://github.com/MPCodeWriter21/ProxyEater/blob/master/DONATE.md)

Or if you can't, give [this project](https://github.com/MPCodeWriter21/ProxyEater) a star on GitHub :)


