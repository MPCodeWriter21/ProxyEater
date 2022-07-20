# ProxyEater.__main__.py
# CodeWriter21

import sys
import json
import pathlib

import log21
import importlib_resources

from .Proxy import Proxy, ProxyType, ProxyList
from .Scraper import Scraper

import ProxyEater

path = importlib_resources.files('ProxyEater')

logger = log21.get_logger("ProxyEater")


def scrape(args):
    if not args.source:
        source = path / 'sources.json'
    else:
        source = pathlib.Path(args.source)
    if not source.exists():
        logger.error(f'The source {source} does not exist.')
        return
    if source.is_dir():
        logger.error(f'The source {source} is a directory.')
        return
    # Parse the source
    with source.open() as f:
        source_data = json.load(f)

    # Parse the proxy
    if args.proxy:
        proxy = Proxy.from_text(args.proxy)
    else:
        proxy = None
    logger.info(f'Using proxy: {proxy}')

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
                logger.error(f'The proxy type({type_}) is not valid.')
                return
            proxy_types.append(proxy_type)
    # Convert proxy types to ProxyType objects
    proxy_types = [ProxyType.from_name(str(x)) for x in proxy_types]

    useragent = args.useragent

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

            def checking_callback(proxy_list: ProxyList, progress: float):
                logger.progress_bar(progress, 100)

        logger.info(f'Scraping {config.get("id")}...')
        scraper = Scraper(config.get('url'), config.get('parser'), method=config.get('method'),
                          name=config.get('id'), useragent=useragent, proxy=proxy, request_timeout=args.timeout)
        proxies_ = scraper.get_proxies(on_progress_callback=progress_callback, on_success_callback=finish_callback,
                                       on_failure_callback=error_callback)

        collected_proxies_count = proxies_.count
        # Filter the proxies
        logger.info('Filtering the proxies...')
        proxies_ = proxies_.filter(type_=proxy_types)
        if args.verbose:
            logger.info(f'{scraper.name}: Removed {collected_proxies_count - proxies_.count} proxies of wrong type.')
        collected_proxies_count = proxies_.count
        # Check the proxies
        logger.info('Checking if the proxies are alive...')
        proxies_.check_all(timeout=args.timeout, threads_no=args.threads, on_progress_callback=checking_callback,
                           url=args.url)
        if args.verbose:
            logger.info(f'{scraper.name}: Removed {collected_proxies_count - proxies_.count} dead proxies.')

        proxies.update(proxies_)
        logger.info(f'Scraped {len(proxies)} proxies.')

        if args.verbose:
            logger.info(f'Writing {proxies.count} proxies to {args.output}...')
        # Write to file
        if args.format == 'text':
            proxies.to_text_file(args.output, '\n')
        elif args.format == 'json':
            proxies.to_json_file(args.output, include_status=args.include_status,
                                 include_geolocation=args.include_geolocation)
        elif args.format == 'csv':
            proxies.to_csv_file(args.output, include_status=args.include_status,
                                include_geolocation=args.include_geolocation)
    logger.info(f'Wrote {proxies.count} proxies to {args.output}.')


def check(args):
    # Validate the source path
    if not args.source:
        logger.error('The source path is not specified.')
        return
    source = pathlib.Path(args.source)
    if not source.exists():
        logger.error(f'The source {source} does not exist.')
        return
    if source.is_dir():
        logger.error(f'The source {source} is a directory.')
        return

    # Parse the source file
    if args.source_format == 'text':
        proxies = ProxyList.from_text_file(source, '\n', args.default_type)
    elif args.source_format == 'json':
        proxies = ProxyList.from_json_file(source)
    elif args.source_format == 'csv':
        proxies = ProxyList.from_csv_file(source, args.default_type)
    else:
        logger.error(f'The source format {args.source_format} is not valid.')
        return

    logger.progress_bar = log21.ProgressBar(format_='{prefix}{bar}{suffix} {percentage}%', style='{')

    def checking_callback(proxy_list: ProxyList, progress: float):
        logger.progress_bar(progress, 100)

    # Check the proxies
    count = proxies.count
    if args.verbose:
        logger.info('Checking if the proxies are alive...')
        logger.info('Number of proxies:', proxies.count)
    proxies.check_all(timeout=args.timeout, threads_no=args.threads, on_progress_callback=checking_callback,
                      url=args.url)
    if args.verbose:
        logger.info(f'Removed {count - proxies.count} dead proxies.')
    logger.info(f'Alive proxies: {proxies.count}')

    # Write to file
    if args.format == 'text':
        proxies.to_text_file(args.output, '\n')
    elif args.format == 'json':
        proxies.to_json_file(args.output, include_status=args.include_status,
                             include_geolocation=args.include_geolocation)
    elif args.format == 'csv':
        proxies.to_csv_file(args.output, include_status=args.include_status,
                            include_geolocation=args.include_geolocation)
    logger.info(f'Wrote {proxies.count} proxies to {args.output}.')


def main():
    try:
        parser = log21.ColorizingArgumentParser()
        parser.add_argument('mode', help='Modes: Scrape, Check')
        parser.add_argument('--source', '-s', help=f'The source of the proxies(default:{path / "sources.json"}).')
        parser.add_argument('--output', '-o', help=f'The output file.')
        parser.add_argument('--format', '-f', help=f'The format of the output file(default:text).', default='text',
                            choices=['text', 'json', 'csv'])
        parser.add_argument('--include-status', '-is', help=f'Include the status of the proxies in the output file.',
                            action='store_true')
        parser.add_argument('--threads', '-t', help=f'The number of threads to use for scraping(default:25).', type=int,
                            default=25)
        parser.add_argument('--timeout', '-to', help=f'The timeout of the requests(default:15).', default=15, type=int)
        parser.add_argument('--url', '-u', help='The url to use for checking the proxies'
                                                '(default:http://icanhazip.com).', default='http://icanhazip.com')
        parser.add_argument('--verbose', '-v', help=f'The verbose of the program(default:False).', action='store_true')
        parser.add_argument('--quiet', '-q', help=f'The quiet of the program(default:False).', action='store_true')
        parser.add_argument('--version', '-V', help=f'The version of the program.', action='version',
                            version='%(prog)s ' + ProxyEater.__version__)
        scrap_arguments = parser.add_argument_group('Scrape', 'Scrape mode arguments')
        scrap_arguments.add_argument('--proxy', '-p', help=f'The proxy to use for scraping.')
        scrap_arguments.add_argument('--proxy-type', '-type', help=f'The type of the proxies(default:all).', default='')
        scrap_arguments.add_argument('--useragent', '-ua', help=f'The useragent of the requests(default:random).')
        scrap_arguments.add_argument('--include-geolocation', '-ig',
                                     help=f'Include the geolocation info of the proxies in the output file.',
                                     action='store_true')
        check_arguments = parser.add_argument_group('Check', 'Check mode arguments')
        check_arguments.add_argument('--source-format', '-sf', help=f'The format of the source file(default:text).',
                                     default='text', choices=['text', 'json', 'csv'])
        check_arguments.add_argument('--default-type', '-dt', help=f'The default type of the proxies - '
                                                                   f'Use this if you are providing proxies without '
                                                                   f'scheme(default:http).',
                                     default='http', choices=['http', 'https', 'socks4', 'socks5'])
        args = parser.parse_args()

        if args.verbose and args.quiet:
            parser.error(f'The verbose and quiet are both set.')
            return

        logger.setLevel(log21.ERROR if args.quiet else log21.INFO)

        args.timeout = int(args.timeout)
        if args.timeout < 0.1:
            parser.error(f'The timeout({args.timeout}) is not valid.')
            return

        if args.threads < 1:
            parser.error(f'The number of threads({args.threads}) is not valid.')
            return

        # Output Path
        if args.output:
            args.output = pathlib.Path(args.output)
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
            args.output = pathlib.Path('.') / ('proxies.' + ext)
            i = 2
            while args.output.exists():
                args.output = pathlib.Path('.') / f'proxies-{i}.{ext}'
                i += 1

        # Output Format
        if args.format == 'text' and (args.include_status or args.include_geolocation):
            parser.error(f'The format {args.format} does not support the include-status or include-geolocation.')
            return

        args.mode = args.mode.lower()
        if args.mode == 'scrape':
            scrape(args)
        elif args.mode == 'check':
            check(args)
    except KeyboardInterrupt:
        logger.error('KeyboardInterrupt: Exiting...')
        sys.exit()
        return


if __name__ == '__main__':
    main()
