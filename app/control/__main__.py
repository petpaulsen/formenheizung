import argparse

from control import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('-p', '--port', type=int)
    parser.add_argument('--log')
    args = parser.parse_args()
    main(args.config, args.port, args.log)
