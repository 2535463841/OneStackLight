import os
import sys

if os.getcwd() not in sys.path:  # noqa
    sys.path.append(os.getcwd())  # noqa

from common import manager


def main():
    m = manager.Manager()
    m.sync()


if __name__ == '__main__':
    main()
