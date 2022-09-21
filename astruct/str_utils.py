import codecs
from typing import ByteString


class NullTerminationError(ValueError):
    """An error with the null termination of a C-style string. A subclass of
    ValueError."""
    pass


def get_incremental_decoder(encoding: str, errors: str = 'strict') -> codecs.IncrementalDecoder:
    """Convenience function to create an incremental decoder for the given
    encoding and error handler."""
    return codecs.getincrementaldecoder(encoding)(errors)


def decode_null_terminated(bs: ByteString,
                           decoder: codecs.IncrementalDecoder,
                           offset: int = 0,
                           ignore_missing: bool = False) -> tuple[str, int]:
    """Decodes up to the first null character in the given bytes and
    returns the resulting string (without the null) and the offset where it
    ends (after its null if there was one). Does not attempt to decode any
    bytes after the first null character.

    If ignore_missing is False (the default), raises a NullTerminationError
    if no null character is decoded from the bytes.

    The decoder is reset before beginning to decode, and will be reset upon
    exit from this function, either by return or exception.
    """
    res = ''
    one_byte = bytearray(1)  # avoiding some churn

    decoder.reset()
    for i in range(offset, len(bs)):
        final = i == len(bs) - 1
        one_byte[0] = bs[i]

        # decode() returns '' if the input was ok but incomplete, a character
        # if it has decoded something, or raises an error if the byte moved us
        # to an invalid state.
        try:
            c = decoder.decode(one_byte, final)
        except UnicodeDecodeError as e:
            decoder.reset()
            raise e

        if c == '\0':
            # We're done!
            decoder.reset()  # probably unnecessary in this case
            return (res, i + 1)

        if c:
            res += c

    # We didn't hit a null.
    decoder.reset()
    if ignore_missing:
        return (res, len(bs))

    raise NullTerminationError('Missing null terminator in string')


def encode_null_terminated(s: str, encoding: str, errors: str = 'strict') -> bytes:
    """Encodes s using the given encoding, adding a zero character to the end
    if necessary.

    No attempt is made to detect a zero character before the end of the string,
    so if given a string like 'a\\0b', this will generate the string 'a\\0b\\0'
    and encode that.
    """
    if not s.endswith('\0'):
        s += '\0'

    return s.encode(encoding, errors)
