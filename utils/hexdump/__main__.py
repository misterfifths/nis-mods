import codecs
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from utils import private_mmap

from . import hexdump


def pos_nonzero_int(s: str) -> int:
    i = int(s)
    if i <= 0:
        raise ValueError('argument must be an integer > 0')

    return i


def pos_dec_int(s: str) -> int:
    i = int(s)
    if i < 0:
        raise ValueError('argument must be a positive integer')

    return i


def pos_hex_or_dec_int(s: str) -> int:
    if s.startswith('0x') or s.startswith('0X'):
        i = int(s[2:], base=16)
    else:
        i = int(s)

    if i < 0:
        raise ValueError('argument must be a positive integer')

    return i


def valid_encoding_name(s: str) -> str:
    try:
        codecs.lookup(s)
    except LookupError:
        raise ValueError('argument must be a valid Python encoding name')

    return s


def parse_args() -> Namespace:
    parser = ArgumentParser('hexdump')

    parser.add_argument(
        'file',
        help='The file to dump.',
        nargs=1)

    parser.add_argument(
        '-n',
        dest='count',
        metavar='LENGTH',
        help='Dump only length many bytes of the input. The argument is '
             'interpreted as a decimal number by default; prefix it with 0x '
             'or 0X to specify a hexadecimal number.',
        type=pos_hex_or_dec_int,
        default=None)

    parser.add_argument(
        '-s',
        dest='offset',
        help='Skip offset bytes from the start of the input. The argument is '
             'interpreted as a decimal number by default; prefix it with 0x '
             'or 0X to specify a hexadecimal number.',
        type=pos_hex_or_dec_int,
        default=0)

    parser.add_argument(
        '--encoding', '-e',
        help='The encoding to use to generate the string interpretation on the '
             'right side of the output. Multibyte encodings are supported. '
             'Default: utf8.',
        type=valid_encoding_name,
        default='utf8')

    parser.add_argument(
        '--fallback-encoding', '-f',
        metavar='ENCODING',
        help='The encoding to use in the case the initial encoding fails to '
             'recognize a character. Should be non-multibyte. Default: mac_roman.',
        type=valid_encoding_name,
        default='mac_roman')

    parser.add_argument(
        '--decimal', '-d',
        help='Print byte values in decimal rather than hexadecimal.',
        action='store_true',
        default=False)

    parser.add_argument(
        '--bytes-per-line', '-w',
        help='Specify how many bytes to print per line of output. Default: 16.',
        type=pos_nonzero_int,
        default=16)

    parser.add_argument(
        '--no-chars', '-N',
        help='Disable the character display in the output.',
        action='store_true',
        default=False)

    parser.add_argument(
        '--verbose', '-v',
        help='Enable verbose decoding debug output.',
        action='store_true',
        default=False)

    return parser.parse_args()


def die(s: str) -> int:
    print(s, file=sys.stderr)
    return 1


def main() -> int:
    args = parse_args()

    src = Path(args.file[0])
    if not src.is_file():
        return die(f'{src} is not a file')

    try:
        with private_mmap(src) as mm:
            hexdump(mm,  # type: ignore
                    offset=args.offset, count=args.count,
                    encoding=args.encoding, fallback_encoding=args.fallback_encoding,
                    decimal=args.decimal,
                    bytes_per_line=args.bytes_per_line, show_chars=not args.no_chars,
                    debug=args.verbose)
    except OSError as exc:
        if isinstance(exc, BrokenPipeError):
            return 0

        return die(f'Error opening {src}: {exc.strerror}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
