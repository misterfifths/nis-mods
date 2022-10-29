import codecs
from typing import Optional, Union

"""
Implements a string encoding 'wide_shift_jis' that is shift_jis with lower
ASCII printables converted to their full-width equivalents and spaces
converted to U+3000 Ideographic Space before they are encoded. Decoding
converts full-width characters to their ASCII equivalents.

For example, encoding 'A! b' would generate the Shift-JIS bytes for 'Ａ！　ｂ'.
And decoding those bytes would return us to the plain ASCII 'A! b'.

This allows us to more easily deal with full-width English strings - they are
narrowed upon decoding, and widened again when converted to bytes.

Heavily following the example from
https://github.com/pyserial/pyserial/blob/master/serial/tools/hexlify_codec.py
"""


ASCII_TO_WIDE = {c: ord('！') + c - ord('!') for c in range(ord('!'), ord('~') + 1)}
ASCII_TO_WIDE[ord(' ')] = ord('　')  # ideographic space

WIDE_TO_ASCII = {ord('！') + c - ord('!'): c for c in range(ord('!'), ord('~') + 1)}
WIDE_TO_ASCII[ord('　')] = ord(' ')

_shift_jis_codecinfo = codecs.lookup('shift_jis')


def widen(s: str) -> str:
    return s.translate(ASCII_TO_WIDE)


def narrow(s: str) -> str:
    return s.translate(WIDE_TO_ASCII)


def encode(input: str, errors: str = 'strict') -> tuple[bytes, int]:
    return _shift_jis_codecinfo.encode(widen(input), errors)


def decode(input: bytes, errors: str = 'strict') -> tuple[str, int]:
    s, bytes_consumed = _shift_jis_codecinfo.decode(input, errors)
    return (narrow(s), bytes_consumed)


class Codec(codecs.Codec):
    def encode(self, input: str, errors: str = 'strict') -> tuple[bytes, int]:
        return encode(input, errors)

    def decode(self, input: bytes, errors: str = 'strict') -> tuple[str, int]:
        return decode(input, errors)


class IncrementalEncoder(codecs.IncrementalEncoder):
    def __init__(self, errors: str = 'strict') -> None:
        self.errors = errors
        self._wrapped_encoder = _shift_jis_codecinfo.incrementalencoder(errors)

    def reset(self) -> None:
        self._wrapped_encoder.reset()

    def getstate(self) -> Union[int, str]:
        return self._wrapped_encoder.getstate()

    def setstate(self, state: Union[int, str]) -> None:
        return self._wrapped_encoder.setstate(state)

    def encode(self, input: str, final: bool = False) -> bytes:
        return self._wrapped_encoder.encode(widen(input), final)


class IncrementalDecoder(codecs.IncrementalDecoder):
    def __init__(self, errors: str = 'strict') -> None:
        self.errors = errors
        self._wrapped_decoder = _shift_jis_codecinfo.incrementaldecoder(errors)

    def reset(self) -> None:
        self._wrapped_decoder.reset()

    def getstate(self) -> tuple[bytes, int]:
        return self._wrapped_decoder.getstate()

    def setstate(self, state: tuple[bytes, int]) -> None:
        return self._wrapped_decoder.setstate(state)

    def decode(self, input: bytes, final: bool = False) -> str:
        return narrow(self._wrapped_decoder.decode(input, final))


class StreamWriter(Codec, codecs.StreamWriter):
    pass


class StreamReader(Codec, codecs.StreamReader):
    pass


_codec_info = codecs.CodecInfo(name='wide_shift_jis',
                               encode=encode,
                               decode=decode,
                               incrementalencoder=IncrementalEncoder,
                               incrementaldecoder=IncrementalDecoder,
                               streamreader=StreamReader,
                               streamwriter=StreamWriter)


def _registry_search_fn(name: str) -> Optional[codecs.CodecInfo]:
    if name != _codec_info.name:
        return None

    return _codec_info


def register_codec() -> None:
    codecs.register(_registry_search_fn)
