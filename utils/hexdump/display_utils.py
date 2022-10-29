from wcwidth import wcswidth, wcwidth  # type: ignore[import]

COMBINER_ISOLATION_CHAR = '◌'
NONPRINTABLE_REPLACEMENT_CHAR = '.'


def control_char_symbol(c: str) -> str:
    """Returns one of the Unicode Control Picture characters (e.g. '␛') for
    the given single-character string with an ord() less than 32.

    Raises ValueError for invalid strings.
    """
    if len(c) != 1 or ord(c) >= 32:
        raise ValueError('Argument must be a single-character string with an ord() < 32')

    return chr(ord('␀') + ord(c))


def isolate_combiner(c: str, isolation_char: str = COMBINER_ISOLATION_CHAR) -> str:
    """Attempts to safely isolate a combining Unicode character c by appending
    isolation_char in the appropriate order.

    Raises ValueError for invalid strings.
    """
    if len(c) != 1 or wcwidth(c) != 0:
        raise ValueError('Argument must be a single-character string for with a width of 0')

    s = isolation_char + c
    if wcswidth(s) > 0:
        return s

    # try the other way
    s = c + isolation_char
    if wcswidth(s) > 0:
        return s

    # well... we did our best
    return isolation_char + c + ' '


def pad_to_2_cells(s: str) -> str:
    """Right-pads s with spaces so that it occupies at least 2 cells.

    Raises ValueError if s does not occupy at least 1 cell.
    """
    width: int = wcswidth(s)
    if width <= 0:
        raise ValueError('Argument must have a width >= 1')

    if wcswidth(s) >= 2:
        return s

    return s + ' '


def safe_2_cell_str(c: str,
                    nonprintable_replacement: str = NONPRINTABLE_REPLACEMENT_CHAR,
                    combiner_isolation_char: str = COMBINER_ISOLATION_CHAR) -> str:
    """Returns a printable, 2-cell wide version of the single-character string
    c, padded with spaces if necessary.

    If c is a combining character, it is isolated with combiner_isolation_char
    first. Non-printable lower ASCII characters are replaced with a symbol from
    the Control Pictures category, via control_char_symbol. Other non-printable
    characters are replaced with nonprintable_replacement.

    Raises a ValueError if any argument is not a single character or if
    either of the replacement characters does not have a width of 1.
    """
    if len(c) != 1 or len(nonprintable_replacement) != 1 or len(combiner_isolation_char) != 1:
        raise ValueError('Arguments must be single-character strings')

    if wcwidth(nonprintable_replacement) != 1:
        raise ValueError('nonprintable_replacement argument must have a width of 1 cell')

    if wcwidth(combiner_isolation_char) != 1:
        raise ValueError('combiner_isolation_char argument must have a width of 1 cell')

    if ord(c) < 32:
        return pad_to_2_cells(control_char_symbol(c))

    width: int = wcwidth(c)

    if width == -1:  # nonprintable
        return pad_to_2_cells(nonprintable_replacement)

    if width == 0:  # combiner
        return pad_to_2_cells(isolate_combiner(c, combiner_isolation_char))

    return pad_to_2_cells(c)
