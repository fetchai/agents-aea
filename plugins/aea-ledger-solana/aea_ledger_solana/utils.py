"""Utility functions for the Solana ledger."""
import logging
import zlib


default_logger = logging.getLogger(__name__)


def pako_inflate(data):
    # https://stackoverflow.com/questions/46351275/using-pako-deflate-with-python
    decompress = zlib.decompressobj(15)
    decompressed_data = decompress.decompress(data)
    decompressed_data += decompress.flush()
    return decompressed_data


# tests #
