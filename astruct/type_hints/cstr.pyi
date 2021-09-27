from typing import Any

# See notes in str_types.py about this. It's a hack.


class CStr:
    def __class_getitem__(cls, params: Any) -> Any: ...

    def __get__(self, obj: Any, type: type | None = ...) -> str: ...
    def __set__(self, obj: Any, value: str) -> None: ...
