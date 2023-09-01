import sys
import os
import argparse
import logging

logger = logging.getLogger('kepi')

def daemonise(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):

    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    os.chdir('/')
    os.umask(0)
    os.setsid()

    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    for f, mode, buffering in [
            (sys.stdin,  'r',  -1),
            (sys.stdout, 'a+', -1),
            (sys.stderr, 'a+',  0),
            ]:

        if mode!='r':
            f.flush()

        i = open(f, mode, buffering)
        os.dup2(i.fileno( ), f.fileno( ))

    logger.info("Daemon ready %s", os.getpid())

def parse():
    parser = argparse.ArgumentParser(
            description='send or receive ActivityPub messages')
    parser.add_argument(
            '--incoming', '-I', action='store_true',
            help='read an incoming message (rather than a message to send)')
    parser.add_argument(
            '--fifo', '-F', default='/var/run/kepi/kepi.fifo',
            help='filename for control pipe')
    parser.add_argument(
            '--pidfile', '-P', default='/var/run/kepi/kepi.pid',
            help='filename for process ID')
    parser.add_argument(
            '--spool', '-S', default='/var/spool/kepi',
            help='directory to store the messages')
    parser.add_argument(
            'input',
            help=(
                'the file to read ("-" for stdin)'
            ),
            )
    args = parser.parse_args()
    return args

def main():
    args = parse()
    print(args)
    if args.input=='-':
        f = sys.stdin
    else:
        f = open(args.input, 'r')

    message = json.load(f)

    print(message)

if __name__=='__main__':
    main()
