# ProxyEater.__main__.py
# CodeWriter21

import json
import pathlib

import log21
import importlib_resources

from .Proxy import Proxy, ProxyType, ProxyList
from .Scraper import Scraper

import ProxyEater

path = importlib_resources.files('ProxyEater')


def main():
    try:
        parser = log21.ColorizingArgumentParser()
        parser.add_argument('--source', '-s', help=f'The source of the proxies(default:{path / "sources.json"}).',
                            default=path / "sources.json")
        parser.add_argument('--output', '-o', help=f'The output file.')
        parser.add_argument('--format', '-f', help=f'The format of the output file(default:text).', default='text',
                            choices=['text', 'json', 'csv'])
        parser.add_argument('--proxy', '-p', help=f'The proxy to use for scraping.')
        parser.add_argument('--threads', '-t', help=f'The number of threads to use for scraping(default:25).', type=int,
                            default=25)
        parser.add_argument('--proxy-type', '-type', help=f'The type of the proxies(default:all).', default='')
        parser.add_argument('--timeout', '-to', help=f'The timeout of the requests(default:15).', default=15, type=int)
        parser.add_argument('--useragent', '-ua', help=f'The useragent of the requests(default:random).')
        parser.add_argument('--include-status', '-is', help=f'Include the status of the proxies in the output file.',
                            action='store_true')
        parser.add_argument('--include-geolocation', '-ig',
                            help=f'Include the geolocation info of the proxies in the output file.',
                            action='store_true')
        parser.add_argument('--verbose', '-v', help=f'The verbose of the program(default:False).', action='store_true')
        parser.add_argument('--quiet', '-q', help=f'The quiet of the program(default:False).', action='store_true')
        parser.add_argument('--version', '-V', help=f'The version of the program.', action='version',
                            version='%(prog)s ' + ProxyEater.__version__)
        args = parser.parse_args()

        source = pathlib.Path(args.source)
        if not source.exists():
            parser.error(f'The source {source} does not exist.')
            return
        if source.is_dir():
            parser.error(f'The source {source} is a directory.')
            return
        # Parse the source
        with source.open() as f:
            source_data = json.load(f)

        # Output Path
        if args.output:
            output = pathlib.Path(args.output)
        else:
            if args.format == 'text':
                ext = 'txt'
            elif args.format == 'json':
                ext = 'json'
            elif args.format == 'csv':
                ext = 'csv'
            else:
                parser.error(f'The format {args.format} is not supported.')
                return
            output = pathlib.Path('.') / ('proxies.' + ext)
            i = 2
            while output.exists():
                output = pathlib.Path('.') / f'proxies-{i}.{ext}'
                i += 1

        # Output Format
        if args.format == 'text' and (args.include_status or args.include_geolocation):
            parser.error(f'The format {args.format} does not support the include-status or include-geolocation.')
            return

        # Parse the proxy
        if args.proxy:
            if args.proxy.count(':') != 2:
                parser.error(f'The proxy {args.proxy} is not valid.')
                return
            scheme = args.proxy.split(':')[0]
            ip = args.proxy.split(':')[1]
            port = args.proxy.split(':')[2]
            if scheme not in ['http', 'https', 'socks4', 'socks5']:
                parser.error(f'The proxy {args.proxy} is not valid.')
                return
            if scheme == 'http':
                proxy_type = ProxyType.HTTP
            elif scheme == 'https':
                proxy_type = ProxyType.HTTPS
            elif scheme == 'socks4':
                proxy_type = ProxyType.SOCKS4
            elif scheme == 'socks5':
                proxy_type = ProxyType.SOCKS5
            else:
                parser.error(f'The proxy scheme({scheme}) is not valid.')
                return
            proxy = Proxy(ip, port, proxy_type)
        else:
            proxy = None

        if args.threads < 1:
            parser.error(f'The number of threads({args.threads}) is not valid.')
            return

        proxy_types = ['http', 'https', 'socks4', 'socks5']
        # Parse the proxy type
        if args.proxy_type:
            proxy_types = []
            for type_ in [x.strip() for x in args.proxy_type.split(',')]:
                if type_ == 'http':
                    proxy_type = ProxyType.HTTP
                elif type_ == 'https':
                    proxy_type = ProxyType.HTTPS
                elif type_ == 'socks4':
                    proxy_type = ProxyType.SOCKS4
                elif type_ == 'socks5':
                    proxy_type = ProxyType.SOCKS5
                else:
                    parser.error(f'The proxy type({type_}) is not valid.')
                    return
                proxy_types.append(proxy_type)
        # Convert proxy types to ProxyType objects
        proxy_types = [ProxyType.from_name(x) for x in proxy_types]

        timeout = int(args.timeout)
        if timeout < 0.1:
            parser.error(f'The timeout({timeout}) is not valid.')
            return

        useragent = args.useragent

        if args.verbose and args.quiet:
            parser.error(f'The verbose and quiet are both set.')
            return

        logger = log21.get_logger("ProxyEater", level='ERROR' if args.quiet else 'INFO')

        proxies = ProxyList()
        # Scrape
        for config in source_data:
            progress_callback = finish_callback = error_callback = checking_callback = None
            if args.verbose:
                logger.progress_bar = log21.ProgressBar(format_='{prefix}{bar}{suffix} {percentage}%', style='{')

                def progress_callback(scraper_: Scraper, progress: float):
                    logger.info(f'{scraper_.name}: Collected: {scraper_.proxies.count}, {progress:.2f}%', end='\r')

                def finish_callback(scraper_: Scraper):
                    logger.info(f'{scraper_.name}: Collected: {scraper_.proxies.count}, 100.0%')
                    logger.info(f'{scraper_.name}: Done.')

                def error_callback(scraper_: Scraper, error: Exception):
                    logger.error(f'{scraper_.name}: {error.__class__.__name__}: {error}')

                def checking_callback(proxy_list: Scraper, progress: float):
                    logger.progress_bar(progress, 100)

            logger.info(f'Scraping {config.get("id")}...')
            scraper = Scraper(config.get('url'), config.get('parser'), method=config.get('method'),
                              name=config.get('id'),
                              useragent=useragent, proxy=proxy, request_timeout=timeout)
            proxies_ = scraper.get_proxies(on_progress_callback=progress_callback, on_success_callback=finish_callback,
                                           on_failure_callback=error_callback)

            collected_proxies_count = proxies_.count
            # Check the proxies
            logger.info('Checking if the proxies are alive...')
            proxies_.check_all(timeout=timeout, threads_no=args.threads, on_progress_callback=checking_callback)
            if args.verbose:
                logger.info(f'{scraper.name}: Removed {collected_proxies_count - proxies_.count} dead proxies.')
            collected_proxies_count = proxies_.count
            # Filter the proxies
            logger.info('Filtering the proxies...')
            proxies_ = proxies_.filter(type_=proxy_types)
            if args.verbose:
                logger.info(
                    f'{scraper.name}: Removed {collected_proxies_count - proxies_.count} proxies of wrong type.')

            proxies.update(proxies_)
            logger.info(f'Scraped {len(proxies)} proxies.')

            if args.verbose:
                logger.info(f'Writing {proxies.count} proxies to {output}...')
            # Write to file
            if args.format == 'text':
                proxies.to_text_file(output, '\n')
            elif args.format == 'json':
                proxies.to_json_file(output, include_status=args.include_status,
                                     include_geolocation=args.include_geolocation)
            elif args.format == 'csv':
                proxies.to_csv_file(output, include_status=args.include_status,
                                    include_geolocation=args.include_geolocation)
        logger.info(f'Wrote {proxies.count} proxies to {output}.')
    except KeyboardInterrupt:
        log21.error('KeyboardInterrupt: Exiting...')
        return


if __name__ == '__main__':
    main()
