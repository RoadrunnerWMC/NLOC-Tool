"""
A Python implementation of Next Level Games's favorite hash function
"""

def hash(data: bytes, *,
        seed:int=0xFFFFFFFF,
        max_length:int=None,
        case_insensitive:bool=True,
        stop_at_null:bool=True) -> int:
    """
    This Python function represents many separate in-game functions:

    def sub_5DB130(seed: int, data: bytes) -> int:
        return hash(data, seed=seed)
    def sub_5DB158(data: bytes) -> int:
        return hash(data)
    def sub_5DB188(seed: int, data: bytes) -> int:
        return hash(data, seed=seed, case_insensitive=True)
    def sub_5DB1BC(data: bytes) -> int:
        return hash(data, case_insensitive=True)
    def sub_5DB1F8(data: bytes, max_length: int) -> int:
        return hash(data, max_length=max_length)
    def sub_5DB22C(data: bytes, max_length: int) -> int:
        return hash(data, max_length=max_length, case_insensitive=True)

    The default keyword arguments correspond to the most commonly used
    of these functions, 5DB158.

    `data` must be a bytes object.

    `seed` lets you add more data to an existing hash value instead of
    creating a new one; that is,
        h = hash(a)
        h = hash(b, seed=h)
        h = hash(c, seed=h)
    is equivalent to
        h = hash(a + b + c)
    assuming that a and b contain no null bytes.

    `max_length` lets you specify a maximum length, which can be less
    than the length of the input data. Any data beyond that is ignored.
    If a null byte is encountered before the limit is reached, the hash
    ends there instead.

    `case_insensitive` causes case insensitivity by converting uppercase
    ASCII characters to lowercase.

    `stop_at_null` causes the hashing to stop when a null byte is
    encountered. (Note that all known in-game hash functions do this,
    including those that let you specify a maximum length.)

    This function is naturally insensitive to leading spaces when used
    on ASCII data, though this is probably unintentional.
    """

    h = seed

    for i, c in enumerate(data):
        if stop_at_null and not c:
            break

        if max_length is not None and i >= max_length:
            break

        if case_insensitive and 65 <= c <= 90:
            c |= 0x20

        h = (h * 33 + c) & 0xFFFFFFFF

    return h


def hash_str(s: str) -> int:
    """
    Convenience function to NLG-hash a string (assumes latin-1 encoding)
    """
    return hash(s.encode('latin-1'))
