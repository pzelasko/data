# Copyright (c) Facebook, Inc. and its affiliates.
import lzma
import warnings
from io import BufferedIOBase
from typing import Iterable, Iterator, Tuple

from torchdata.datapipes.utils.common import validate_pathname_binary_tuple
from torchdata.datapipes.iter.util._archivereader import _ArchiveReaderIterDataPipe
from torch.utils.data import functional_datapipe


@functional_datapipe("read_from_xz")
class XzFileReaderIterDataPipe(_ArchiveReaderIterDataPipe):
    r"""
    Iterable DataPipe to uncompress xz (lzma) binary streams from an input iterable which contains tuples of
    path name and xy binary streams. This yields a tuple of path name and extracted binary stream.

    Args:
        datapipe: Iterable DataPipe that provides tuples of path name and xy binary stream
        length: Nominal length of the DataPipe

    Note:
        The opened file handles will be closed automatically if the default DecoderDataPipe
        is attached. Otherwise, user should be responsible to close file handles explicitly
        or let Python's GC close them periodically.
    """

    def __init__(self, datapipe: Iterable[Tuple[str, BufferedIOBase]], length: int = -1):
        super().__init__()
        self.datapipe: Iterable[Tuple[str, BufferedIOBase]] = datapipe
        self.length: int = length

    def __iter__(self) -> Iterator[Tuple[str, BufferedIOBase]]:
        for data in self.datapipe:
            validate_pathname_binary_tuple(data)
            pathname, data_stream = data
            self._open_source_streams[pathname].append(data_stream)
            try:
                extracted_fobj = lzma.open(data_stream, mode="rb")  # type: ignore[call-overload]
                new_pathname = pathname.rstrip(".xz")
                yield new_pathname, extracted_fobj  # type: ignore[misc]
            except Exception as e:
                warnings.warn(f"Unable to extract files from corrupted xz/lzma stream {pathname} due to: {e}, abort!")
                raise e

    def __len__(self):
        if self.length == -1:
            raise TypeError("{} instance doesn't have valid length".format(type(self).__name__))
        return self.length
