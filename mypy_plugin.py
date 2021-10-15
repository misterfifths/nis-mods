from typing import Any, Callable, Final, Optional

from mypy.errorcodes import TYPE_ARG, VALID_TYPE
from mypy.nodes import SymbolTableNode, Var
from mypy.plugin import AnalyzeTypeContext, ClassDefContext, Plugin
from mypy.types import Instance, RawExpressionType
from mypy.types import Type as MyPyType
from mypy.types import UnboundType

import astruct
from astruct.type_hints import CStr, CUInt8Array
from astruct.type_hints.carray import CArray


def _fullname(t: Any) -> str:
    return t.__module__ + '.' + t.__qualname__


SIZED_STRING_TYPE_FULLNAME: Final = _fullname(CStr)
SIZED_ARRAY_TYPE_FULLNAME_PREFIX: Final = _fullname(CUInt8Array).removesuffix('UInt8Array')
SIZED_ARRAY_TYPE_FULLNAME_SUFFIX: Final = 'Array'

CARRAY_PROTOCOL_FULLNAME: Final = _fullname(CArray)

TYPED_STRUCT_FULLNAME: Final = _fullname(astruct.typed_struct)

# The actual types of these have __module__ of _ctypes, which trips things up.
CTYPES_STRUCTURE_FULLNAME: Final = 'ctypes.Structure'
CTYPES_UNION_FULLNAME: Final = 'ctypes.Union'


class AStructCheckerPlugin(Plugin):
    def _has_valid_size_arg(self, analy_ctx: AnalyzeTypeContext) -> bool:
        tp, ctx, api = analy_ctx

        if len(tp.args) != 1:
            return False

        arg = tp.args[0]
        if isinstance(arg, RawExpressionType):
            # Literal ints
            if not isinstance(arg.literal_value, int) or arg.literal_value <= 0:
                return False
        elif isinstance(arg, UnboundType):
            # Anything else. At this point mypy seems to assume it will be a
            # type, so it's an UnboundType instance.
            # Try to look up what the argument is and hope we can tell that the
            # type of that thing is an int. This lets us support, e.g.,
            # CStr[SOME_CONSTANT], as long as we can determine that
            # SOME_CONSTANT is an int.

            # lookup_qualified isn't part of the API interface we get, but it
            # is there on the object. :-/
            node: SymbolTableNode = api.lookup_qualified(arg.name, ctx)  # type: ignore

            # node.type should be an Instance, which is to say it's a
            # particular instantiation of a type. If it is, then node.type.type
            # is a TypeInfo for the deduced type of the value, and that should
            # be a subtype of int.
            if not isinstance(node.type, Instance) or not node.type.type.has_base('builtins.int'):
                return False
        else:
            return False

        return True

    def _check_size_arg(self, analy_ctx: AnalyzeTypeContext) -> None:
        if not self._has_valid_size_arg(analy_ctx):
            tp, ctx, api = analy_ctx
            api.fail(f'{tp.name} requires a single positive integer parameter', ctx, code=TYPE_ARG)

    def _str_type_analyze_hook(self, analy_ctx: AnalyzeTypeContext) -> MyPyType:
        self._check_size_arg(analy_ctx)

        # Tell mypy that CStr[x] == str
        return analy_ctx.api.named_type('builtins.str', [])

    def _array_type_analyze_hook(self, analy_ctx: AnalyzeTypeContext) -> MyPyType:
        self._check_size_arg(analy_ctx)

        # Tell mypy that, e.g., CUInt8Array[8] is just CUInt8Array.
        # This does the trick for type checking purposes because those helper
        # types are specialized CArray subtypes.
        tp, _, api = analy_ctx
        # TODO: better way to get this type name?
        return api.named_type(f'astruct.type_hints.ctypes_helpers.{tp.name}', [])

    def get_type_analyze_hook(self,
                              fullname: str) -> Optional[Callable[[AnalyzeTypeContext], MyPyType]]:
        if fullname == SIZED_STRING_TYPE_FULLNAME:
            return self._str_type_analyze_hook

        if fullname.startswith(SIZED_ARRAY_TYPE_FULLNAME_PREFIX) and \
           fullname.endswith(SIZED_ARRAY_TYPE_FULLNAME_SUFFIX):
            return self._array_type_analyze_hook

        return None

    def _check_typed_struct_attr_type(self, node: Var) -> None:
        # At this point we will have gone through our type analysis hook, so
        # CStrs will have turned into strs, and CArray helpers into annotated
        # CArrays.

        # TODO: seemingly no way to inspect for Annotated metadata; it gets
        # erased by mypy early in the analysis process. So for now, nothing to
        # do here.
        pass

    def _decorator_hook(self, classdef_ctx: ClassDefContext) -> None:
        cls, _, api = classdef_ctx
        info = cls.info

        if not info.has_base(CTYPES_STRUCTURE_FULLNAME) and \
           not info.has_base(CTYPES_UNION_FULLNAME):
            api.fail('typed_struct can only be applied to subclasses of ctypes.Structure or '
                     'ctypes.Union', ctx=cls, serious=True, code=VALID_TYPE)

        if fields_sym := info.names.get('_fields_'):
            assert fields_sym.node  # for type checking purposes to remove the Optional
            api.fail('typed_struct cannot be applied to classes with a _fields_ attribute',
                     ctx=fields_sym.node, serious=True, code=VALID_TYPE)

        for sym_name, sym in info.names.items():
            node = sym.node
            if not isinstance(node, Var) or node.type is None:
                continue

            self._check_typed_struct_attr_type(node)

    def get_class_decorator_hook(self,
                                 fullname: str) -> Optional[Callable[[ClassDefContext], None]]:
        if fullname == TYPED_STRUCT_FULLNAME:
            return self._decorator_hook

        return None


def plugin(version: str) -> type[Plugin]:
    return AStructCheckerPlugin
