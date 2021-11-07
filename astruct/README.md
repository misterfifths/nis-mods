An experiment to automatically generate ctypes.Structure/Union `_fields_` attributes from type hints, in the vein of `dataclass`.

The syntax worked out pretty nicely, I think, though it required some hacks to satisfy both mypy and pyright/pylance in VS Code.

The real added value is in automatically generating nice properties for C-style strings in your structs, with configurable handling of null-termination, encoding, and error resolution.

The code is decently commented, and there are lot of examples in the phantom_brave directory. Here's a taste from phantom_brave/skills.py:

```python
@typed_struct
class Skill(C.Structure):
    _pack_ = 1

    mana_cost: CUInt32
    id: CUInt16
    sp_cost: CUInt16
    name: CStr[22]

    # This field has some bizarre non-standard byte sequences, so we use
    # surrogateescape to make sure they round-trip correctly.
    description: Annotated[CStr[70], Encoding(errors='surrogateescape')]

    ...
```
