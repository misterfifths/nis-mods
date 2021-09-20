from typing import Any, Optional
from dataclasses import dataclass
from ._type_hint_utils import first_annotated_md_of_type
from .type_hints.metadata import CField


@dataclass
class CFieldAttr:
    """Represents the configuration of a CField-annotated attribute on a
    typed_struct."""
    cfield: CField

    @classmethod
    def from_hint(cls, hint: Any, unannotated_hint: Any) -> Optional['CFieldAttr']:
        """Constructs an instance from the given type hint if possible.

        If the hint is not an Annotated instance with the CField metadata,
        returns None.
        """
        cfld = first_annotated_md_of_type(hint, CField)
        if cfld is None:
            return None

        return cls(cfld)
