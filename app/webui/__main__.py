import argparse

from webui import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('--http-port', type=int)
    parser.add_argument('--controller-port', type=int)
    parser.add_argument('--log')
    args = parser.parse_args()
    main(args.config, args.controller_port, args.http_port, args.log)
