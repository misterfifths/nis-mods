#!/usr/bin/env python3

# pyright: reportPrivateUsage=none

from typing import Iterable, Optional
import ctypes as C
import textwrap
import inspect
from sys import stderr
from io import StringIO

"""
This script walks the ctypes module and generates two files:

ctypes_aliases.py is mainly categorized metatypes for the ctypes classes. For
instance, it collects all _SimpleCData subclasses into a Union, and builds up
a (very useful) AnyCType Union. It also provides a few ways to answer questions
about whether a given type is a ctype at runtime. With the exception of
AnyCType, this file is likely most useful internally.

ctypes_helpers.py is intended to be consumed by users of typed_struct. For
each built-in simple ctype, it exposes an alias for that type's Python
representation, annotated with our CField type. It also has similar classes
to allow easy annotation of C arrays of all the int and float ctypes.
"""


def pytype_for_typecode(typecode: str) -> type:
    TYPE_MAP: dict[str, type] = {
        # Basic types from the struct module
        'bBhHIlLqQnN': int,
        'efd': float,
        '?': bool,

        # Codes particular to ctypes
        'i': int,  # c_int, c_int32
        'g': float,  # c_longdouble

        # Pointers. Not differentiating these at the moment
        'P': C.pointer,  # type: ignore  # struct module's void *
        'O': C.pointer,  # type: ignore  # py_object
        'zZ': C.pointer,  # type: ignore  # c_char_p and c_wchar_p

        # Strings (which actually live as bytes, but this is just for
        # categorization purposes).
        'cs': str,  # struct module ones
        'u': str  # c_wchar
    }

    for codes, t in TYPE_MAP.items():
        if typecode in codes:
            return t

    raise ValueError(f'Unknown typecode "{typecode}"')


simple_type_names: list[str] = []
int_type_names: list[str] = []
float_type_names: list[str] = []
char_type_names: list[str] = []
pointer_type_names: list[str] = []
bool_type_name: str

# _SimpleCData classes to explicitly ignore.
# pylance doesn't know about c_voidp.
SIMPLE_CLASS_BLACKLIST = {'c_voidp'}

CTYPES_MODULE_NAME = 'C'

cls: type
for name, cls in inspect.getmembers(C, inspect.isclass):
    if cls is C._SimpleCData:  # type: ignore
        continue

    if not issubclass(cls, C._SimpleCData):
        continue

    if name in SIMPLE_CLASS_BLACKLIST:
        print(f'Skipping blacklisted class {name}', file=stderr)
        continue

    name = CTYPES_MODULE_NAME + '.' + name

    try:
        typecode = getattr(cls, '_type_')
    except AttributeError:
        print(f'Skipping {name}: no _type_ attribute', file=stderr)
        continue

    # special-case py_object: it's generic in the type system (but not in
    # reality, so quote it)
    if name == CTYPES_MODULE_NAME + '.py_object':
        name = f"'{name}[Any]'"

    simple_type_names.append(name)

    try:
        pytype = pytype_for_typecode(typecode)
    except ValueError:
        print(f'Skipping {name}: unknown _type_ "{typecode}"')
        continue

    if pytype is int:
        int_type_names.append(name)
    elif pytype is float:
        float_type_names.append(name)
    elif pytype is C.pointer:  # type: ignore
        pointer_type_names.append(name)
    elif pytype is str:
        char_type_names.append(name)
    elif pytype is bool:
        bool_type_name = name


def fixup_multiline_str(s: str) -> str:
    return textwrap.dedent(s.strip('\n'))


def wrap_code(s: str, width: int = 100, indent: int = 0) -> str:
    lines = textwrap.wrap(s, width=width, break_long_words=False, subsequent_indent=indent * ' ')
    return '\n'.join(lines)


def wrap_list_values(values: Iterable[str], indent: int = 0) -> str:
    return wrap_code(', '.join(values), indent=indent)


# like capitalize, but only changes the first letter
def upcase_first(s: str) -> str:
    if len(s) == 0:
        return s

    return s[0].upper() + s[1:]


# generates our class names from ctypes names, e.g. c_uint32 -> CUInt32
def camel_case_ctypename(name: str) -> str:
    PARTICLES_TO_CAPITALIZE = {'int', 'size', 'long', 'byte', 'short', 'double'}

    name = name.removeprefix(CTYPES_MODULE_NAME + '.')
    name = name.removeprefix('c_')

    name = upcase_first(name)

    for particle in PARTICLES_TO_CAPITALIZE:
        bits = name.split(particle)
        name = upcase_first(particle).join(bits)

    # e.g. Size_t -> SizeT
    bits = name.split('_')
    name = ''.join(upcase_first(bit) for bit in bits)

    return 'C' + name


# generates the name of the Array helper for the given ctype name
def camel_case_array_ctypename(name: str) -> str:
    return camel_case_ctypename(name) + 'Array'


def format_ctypes_union(union_name: str, ctypenames: Iterable[str], width: int = 100) -> str:
    typelist = ', '.join(ctypenames)

    prefix = f'{union_name} = Union['
    line = f'{prefix}{typelist}]'

    return wrap_code(line, width, indent=len(prefix))


def format_annotated_type(origin_typename: str, ctypename: str) -> str:
    name = camel_case_ctypename(ctypename)
    return f'{name} = Annotated[{origin_typename}, CField({ctypename})]'


def format_array_type(element_ctypename: str, element_pytypename: str) -> str:
    classname = camel_case_array_ctypename(element_ctypename)
    res = f'''
        class {classname}(CArray[{element_pytypename}, {element_ctypename}]):
            _type_: ClassVar[type[{element_ctypename}]] = {element_ctypename}

            def __class_getitem__(cls, params: Any) -> Any:
                return _shared_class_getitem(cls, params)
    '''

    return fixup_multiline_str(res)


def format_type_set(set_name: str,
                    typenames: Iterable[str],
                    type_ignore_first_line: bool = False,
                    extra_start_lines: Optional[Iterable[str]] = None) -> str:
    indent = 12  # for set elements in the multiline string below
    first_line_comment = '  # type: ignore' if type_ignore_first_line else ''

    start_lines_str = ''
    if extra_start_lines:
        for i, line in enumerate(extra_start_lines):
            if i > 0:
                start_lines_str += ' ' * indent
            start_lines_str += line + '\n'

        # make the next line line up correctly
        start_lines_str += ' ' * indent

    res = f'''
        {set_name}: Final[frozenset[type]] = frozenset(({first_line_comment}
            {start_lines_str}{wrap_list_values(typenames, indent=indent)}
        ))
    '''

    return fixup_multiline_str(res)


def generate_aliases_file() -> str:
    f = StringIO()

    def fprint(s: str = '') -> None:
        print(s, file=f)

    fprint(fixup_multiline_str(f'''
        # This file is generated by _gen_ctypes_info.py

        from typing import Any, Final, Union
        import ctypes as {CTYPES_MODULE_NAME}
    '''))

    fprint(format_ctypes_union('SimpleCType', simple_type_names))
    fprint()
    fprint(format_ctypes_union('IntCType', int_type_names))
    fprint()
    fprint(format_ctypes_union('FloatCType', float_type_names))
    fprint()
    fprint(format_ctypes_union('CharCType', char_type_names))
    fprint()
    fprint(format_ctypes_union('PointerCType', pointer_type_names))

    fprint()
    # TODO: Array[Any] isn't right, but the checker is upset with
    # Array['AnyCType']
    fprint(f"AnyCType = Union[SimpleCType, {CTYPES_MODULE_NAME}.Structure, "
           f"{CTYPES_MODULE_NAME}.Union, {CTYPES_MODULE_NAME}.Array[Any]]")

    fprint()
    # Need to remove py_object here, because we turned it into a string
    # earlier. Also it needs special casing in ALL_CTYPES.
    simple_type_names_without_pyobj = filter(lambda n: 'py_object' not in n, simple_type_names)
    extra_all_ctypes_lines = [f'{CTYPES_MODULE_NAME}.Structure,',
                              f'{CTYPES_MODULE_NAME}.Union,  # type: ignore',
                              f'{CTYPES_MODULE_NAME}.Array,  # type: ignore',
                              f'{CTYPES_MODULE_NAME}.py_object,  # type: ignore']
    fprint()
    fprint(format_type_set('ALL_CTYPES',
                           simple_type_names_without_pyobj,
                           type_ignore_first_line=True,
                           extra_start_lines=extra_all_ctypes_lines))

    fprint(format_type_set('INT_CTYPES', int_type_names))
    fprint(format_type_set('FLOAT_CTYPES', float_type_names))
    fprint(format_type_set('CHAR_CTYPES', char_type_names))

    fprint()
    fprint(fixup_multiline_str(f'''
        def is_builtin_ctype(t: type) -> bool:
            return t in ALL_CTYPES
    '''))

    fprint()
    fprint(fixup_multiline_str(f'''
        def is_int_ctype(t: type) -> bool:
            return t in INT_CTYPES
    '''))

    fprint()
    fprint(fixup_multiline_str(f'''
        def is_float_ctype(t: type) -> bool:
            return t in FLOAT_CTYPES
    '''))

    fprint()
    fprint(fixup_multiline_str(f'''
        def is_char_ctype(t: type) -> bool:
            return t in CHAR_CTYPES
    '''))

    fprint()
    fprint(fixup_multiline_str(f'''
        def is_ctype_subclass(t: type) -> bool:
            if is_builtin_ctype(t):
                return True

            try:
                mro = t.mro()
            except AttributeError:
                return False

            for supertype in mro:
                if is_builtin_ctype(supertype):
                    return True

            return False
    '''))

    return f.getvalue().rstrip('\n')


def generate_helpers_file() -> str:
    f = StringIO()

    def fprint(s: str = '') -> None:
        print(s, file=f)

    ALL_PLACEHOLDER = '<ALL_PLACEHOLDER>'

    fprint(fixup_multiline_str(f'''
        # This file is generated by _gen_ctypes_info.py

        from typing import Annotated, Any, ClassVar
        import ctypes as {CTYPES_MODULE_NAME}
        from .carray import CArray
        from .metadata import CField, Length

        {ALL_PLACEHOLDER}
    '''))

    all: list[str] = []

    fprint('# Annotated bool type')
    all.append(camel_case_ctypename(bool_type_name))
    fprint(format_annotated_type('bool', bool_type_name))

    fprint('\n')
    fprint('# Annotated int types')
    for typename in int_type_names:
        all.append(camel_case_ctypename(typename))
        fprint(format_annotated_type('int', typename))

    fprint('\n')
    fprint('# Annotated float types')
    for typename in float_type_names:
        all.append(camel_case_ctypename(typename))
        fprint(format_annotated_type('float', typename))

    fprint('\n')
    fprint('# Array helpers')
    fprint(fixup_multiline_str('''
    def _shared_class_getitem(cls: type[CArray[Any, Any]], params: Any) -> Any:
        if not isinstance(params, int) or params <= 0:
            raise TypeError(f'{cls.__name__} requires a single, positive integer length argument')

        return Annotated[CArray[cls._py_type_, cls._type_], Length(params)]  # type: ignore
    '''))

    fprint()
    fprint('# bool array')
    all.append(camel_case_array_ctypename(bool_type_name))
    fprint(format_array_type(bool_type_name, 'bool'))

    fprint()
    fprint('# int arrays')
    for typename in int_type_names:
        all.append(camel_case_array_ctypename(typename))
        fprint(format_array_type(typename, 'int'))
        fprint()

    fprint('# float arrays')
    for typename in float_type_names:
        all.append(camel_case_array_ctypename(typename))
        fprint(format_array_type(typename, 'float'))
        fprint()

    all_str = '__all__ = ['
    all_str += ', '.join(f"'{name}'" for name in all)
    all_str += ']'
    all_str = wrap_code(all_str, indent=11)

    res = f.getvalue().rstrip('\n')
    return res.replace(ALL_PLACEHOLDER, all_str)


if __name__ == '__main__':
    ALIASES_FILE = 'ctypes_aliases.py'
    HELPERS_FILE = 'ctypes_helpers.py'

    print(f'Generating {ALIASES_FILE}... ', end='')
    with open(ALIASES_FILE, 'w') as f:
        print(generate_aliases_file(), file=f)
    print('done')

    print(f'Generating {HELPERS_FILE}... ', end='')
    with open(HELPERS_FILE, 'w') as f:
        print(generate_helpers_file(), file=f)
    print('done')
