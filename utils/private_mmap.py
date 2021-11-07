import mmap
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union


@contextmanager
def private_mmap(path: Union[Path, str]) -> Iterator[mmap.mmap]:
    """Creates a private mmap of the given path. Changes to the mmap will not
    be reflected in the original file.

    To be used as a context manager with the 'with' statement.
    """
    fd = None
    mm = None
    try:
        fd = os.open(str(path), os.O_RDONLY)
        mm = mmap.mmap(fd, 0, mmap.MAP_PRIVATE)
        yield mm
    finally:
        if mm is not None:
            try:
                mm.close()
            except BufferError:
                # We frequently get a "cannot close exported pointers exist"
                # BufferError due to dangling ctypes references into the mmap.
                # There's no clear solution; even deleting objects and doing
                # a gc.collect() doesn't reliably fix the error.
                # I'm choosing to ignore it under the assumption that if we're
                # closing the mmap, the app is going down, and hopefully no one
                # will try to reference ctypes objects that point to it.
                pass

        if fd is not None:
            os.close(fd)
