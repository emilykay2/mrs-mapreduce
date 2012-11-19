from mrs.fileformats import BinReader, BinWriter

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO


def test_roundtrip():
    kv_pairs = [(b'key 1', b'value 1'),
            (b'hello', b'world'),
            (b'the', b'end')]

    f = BytesIO()
    writer = BinWriter(f)
    for pair in kv_pairs:
        writer.writepair(pair)
    writer.finish()

    f.seek(0)

    reader = BinReader(f)
    new_pairs = list(reader)

    assert new_pairs == kv_pairs

# vim: et sw=4 sts=4
