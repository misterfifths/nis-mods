from typing import Final, Optional, ByteString
import codecs
import unicodedata
from .byte_utils import hexlify
from .display_utils import safe_2_cell_str, NONPRINTABLE_REPLACEMENT_CHAR


BYTE_CONTINUATION_CHAR: Final = '⋯'


def decode_one(decoder: codecs.IncrementalDecoder,
               bs: ByteString,
               start_idx: int,
               end_idx: int) -> Optional[tuple[str, int]]:
    """Attempts to decode a single character from the given bytes using the
    given decoder. Returns a tuple of the character and the number of bytes
    consumed to generate it, or None if no character could be decoded."""
    # Max bytes to try to give to the decoder. I don't know of any that use
    # more than 4, but I'm no expert.
    MAX_BYTES_PER_CHAR = 4

    max_bytes_to_feed = min(MAX_BYTES_PER_CHAR, end_idx - start_idx + 1)
    c = ''

    # decode() really wants a bytes instance, and this seemed like less churn
    # than doing a 1-element slice each time.
    one_byte = bytearray(1)

    for byte_offset in range(0, max_bytes_to_feed):
        final = byte_offset == max_bytes_to_feed - 1
        one_byte[0] = bs[start_idx + byte_offset]

        try:
            c = decoder.decode(one_byte, final=final)
        except UnicodeDecodeError:
            # Adding more bytes isn't going to help this situation, and the
            # decoder is probably in a weird state, so best to bail.
            break

        # decode() will return the empty string if this is a valid step toward
        # a character, but we're just not there yet. If we're done with a char,
        # it will return it.
        if c:
            decoder.reset()  # probably unnecessary in this case
            return (c, byte_offset + 1)

    # No dice.
    decoder.reset()
    return None


def iffy_decode(bs: ByteString, /,
                offset: int = 0,
                count: Optional[int] = None,
                encoding: str = 'utf8',
                fallback_encoding: str = 'mac_roman',
                continuation_char: str = BYTE_CONTINUATION_CHAR,
                nonprintable_replacement_char: str = NONPRINTABLE_REPLACEMENT_CHAR,
                debug: bool = False) -> list[str]:
    """Returns a list where each element is a representation of the character
    at (or starting at) that byte in the input.

    For each byte, an attempt is made to decode a character starting there
    using encoding. If that fails, fallback_encoding is used on that single
    byte. If that fails, nonprintable_replacement_char is used.

    If a byte is part of a multibyte encoding of a character, the value in
    the return corresponding to the first byte will be the character itself.
    All subsequent bytes that are part of that encoding will have the value
    continuation_char.
    """
    if count is None:
        count = len(bs) - offset
    else:
        count = min(len(bs) - offset, count)

    end_idx = offset + count - 1

    decoder = codecs.getincrementaldecoder(encoding)(errors='strict')
    res: list[str] = []
    i = offset
    one_byte = bytearray(1)  # saving on some churn in the fallback case
    while i <= end_idx:
        if one_tup := decode_one(decoder, bs, i, end_idx):
            s, bytes_consumed = one_tup

            if debug:
                consumed_bytes = bs[i:i + bytes_consumed]
                name = unicodedata.name(s, '')
                print(f'{safe_2_cell_str(s)}\t<- {hexlify(consumed_bytes):<15}\t'
                      f'U+{ord(s):<8x} {name}')
        else:
            one_byte[0] = bs[i]
            bytes_consumed = 1
            try:
                s = one_byte.decode(fallback_encoding, errors='strict')
            except UnicodeDecodeError:
                s = nonprintable_replacement_char

            if debug:
                print(f'{safe_2_cell_str(s)}\t<~ {hexlify(one_byte):<15}')

        res.append(s)
        for _ in range(1, bytes_consumed):
            res.append(continuation_char)

        i += bytes_consumed

    return res
