from dataclasses import dataclass
from typing import Any, Optional

from ._type_hint_utils import first_annotated_md_of_type
from .type_hints.metadata import CField


@dataclass
class CFieldAttr:
    """Represents the configuration of a CField-annotated attribute on a
    typed_struct."""
    cfield: CField

    @classmethod
    def from_type_hint(cls,
                       attr_name: str,
                       hint: Any,
                       unannotated_hint: Any) -> Optional['CFieldAttr']:
        """Constructs an instance from the given type hint if possible.

        If the hint is not an Annotated instance with the CField metadata,
        returns None.
        """
        if cfld := first_annotated_md_of_type(hint, CField):
            return cls(cfld)

        return None
