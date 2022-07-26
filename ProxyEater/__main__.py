# ProxyEater.__main__.py
# CodeWriter21
import sys
import json
import shutil
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
        logger.info(f'Using proxy: {proxy}')
    else:
        proxy = None

    proxy_types = []
    # Parse the proxy type
    if args.proxy_type:
        proxy_types = [x.strip() for x in args.proxy_type.split(',')]
    if not proxy_types:
        proxy_types = ['http', 'https', 'socks4', 'socks5']
    try:
        proxy_types = [ProxyType.from_name(x) for x in proxy_types]
    except ValueError as e:
        logger.error(e)
        return
    logger.info(f'Using proxy types: {[proxy_type.name for proxy_type in proxy_types]}')

    useragent = args.useragent

    proxies = ProxyList()
    # Scrape
    for config in source_data:
        progress_callback = finish_callback = error_callback = checking_callback = None
        if args.verbose:
            logger.progress_bar = log21.ProgressBar(format_='Proxies: {count} {prefix}{bar}{suffix} {percentage}%',
                                                    style='{', additional_variables={'count': 0})

            def progress_callback(scraper_: Scraper, progress: float, page: int):
                logger.info(f'{scraper_.name}: Collected: {scraper_.proxies.count}; Page: {page}, {progress:.2f}%',
                            end='\r')

            def finish_callback(scraper_: Scraper):
                logger.info(f'{scraper_.name}: Collected: {scraper_.proxies.count}, 100.0%')
                logger.info(f'{scraper_.name}: Done.')

            def error_callback(scraper_: Scraper, error: Exception):
                logger.error(f'{scraper_.name}: {error.__class__.__name__}: {error}')

            def checking_callback(proxy_list: ProxyList, progress: float):
                logger.progress_bar(progress, 100, count=proxy_list.count)

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
        if collected_proxies_count > 0 and not args.no_check:
            logger.info('Checking if the proxies are alive...')
            proxies_.check_all(timeout=args.timeout, threads_no=args.threads, on_progress_callback=checking_callback,
                               url=args.url)
            if args.verbose:
                logger.info(f'{scraper.name}: Removed {collected_proxies_count - proxies_.count} dead proxies.')

        proxies.update(proxies_)
        logger.info(f'Scraped {len(proxies)} proxies.')

        if proxies.count > 0:
            if args.include_geolocation:
                on_progress_callback = on_error_callback = None
                if args.verbose:
                    logger.progress_bar = log21.ProgressBar()

                    def on_progress_callback(proxy_list: ProxyList, progress: float):
                        logger.progress_bar(progress, 100)

                    def on_error_callback(proxy_list: ProxyList, error: Exception):
                        logger.error(f'{error.__class__.__name__}: {error}')
                logger.info('Getting the geolocation info of the proxies...')
                proxies.batch_collect_geolocations(on_progress_callback=on_progress_callback,
                                                   on_error_callback=on_error_callback)
            if args.verbose:
                logger.info(f'Writing {proxies.count} proxies to {args.output}...')
            # Write to file
            if args.file_format == 'text':
                proxies.to_text_file(args.output, '\n', format_=args.format)
            elif args.file_format == 'json':
                proxies.to_json_file(args.output, include_status=args.include_status,
                                     include_geolocation=args.include_geolocation)
            elif args.file_format == 'csv':
                proxies.to_csv_file(args.output, include_status=args.include_status,
                                    include_geolocation=args.include_geolocation)
    if proxies.count > 0:
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

    logger.progress_bar = log21.ProgressBar(format_='Proxies: {count} {prefix}{bar}{suffix} {percentage}%', style='{',
                                            additional_variables={'count': 0})

    def checking_callback(proxy_list: ProxyList, progress: float):
        logger.progress_bar(progress, 100, count=proxy_list.count)

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

    if proxies.count > 0:
        if args.include_geolocation:
            on_progress_callback = on_error_callback = None
            if args.verbose:
                logger.progress_bar = log21.ProgressBar()

                def on_progress_callback(proxy_list: ProxyList, progress: float):
                    logger.progress_bar(progress, 100)

                def on_error_callback(proxy_list: ProxyList, error: Exception):
                    logger.error(f'{error.__class__.__name__}: {error}')
            logger.info('Getting the geolocation info of the proxies...')
            proxies.batch_collect_geolocations(on_progress_callback=on_progress_callback,
                                               on_error_callback=on_error_callback)
        # Write to file
        if args.file_format == 'text':
            proxies.to_text_file(args.output, '\n', format_=args.format)
        elif args.file_format == 'json':
            proxies.to_json_file(args.output, include_status=args.include_status,
                                 include_geolocation=args.include_geolocation)
        elif args.file_format == 'csv':
            proxies.to_csv_file(args.output, include_status=args.include_status,
                                include_geolocation=args.include_geolocation)
        logger.info(f'Wrote {proxies.count} proxies to {args.output}.')


def main():
    try:
        parser = log21.ColorizingArgumentParser()
        parser.add_argument('mode', help='Modes: Scrape, Check')
        parser.add_argument('--source', '-s', help=f'The source of the proxies(default:{path / "sources.json"}).')
        parser.add_argument('--output', '-o', help=f'The output file.')
        parser.add_argument('--file-format', '-ff', help=f'The format of the output file(default:text).',
                            default='text',
                            choices=['text', 'json', 'csv'])
        parser.add_argument('--format', '-f', help='The format for saving the proxies in text file(default:'
                                                   '"{scheme}://{ip}:{port}").',
                            default='{scheme}://{ip}:{port}')
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
        scrap_arguments.add_argument('--no-check', '-nc',
                                     help=f'Use this option to skip the checking of the proxies after ',
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
            if args.file_format == 'text':
                ext = 'txt'
            elif args.file_format == 'json':
                ext = 'json'
            elif args.file_format == 'csv':
                ext = 'csv'
            else:
                parser.error(f'The format {args.file_format} is not supported.')
                return
            args.output = pathlib.Path('.') / ('proxies.' + ext)
            i = 2
            while args.output.exists():
                args.output = pathlib.Path('.') / f'proxies-{i}.{ext}'
                i += 1

        args.mode = args.mode.lower()
        if args.mode == 'scrape':
            scrape(args)
        elif args.mode == 'check':
            check(args)
    except KeyboardInterrupt:
        try:
            terminal_size = shutil.get_terminal_size().columns
        except OSError:
            terminal_size = 50
        if not terminal_size:
            terminal_size = 50
        logger.clear_line(terminal_size)
        logger.error('KeyboardInterrupt: Exiting...')
        sys.exit()


if __name__ == '__main__':
    main()
