"""
Classes for messages and NLOC/NLOCT files
"""

import dataclasses
import struct
from typing import List, Union

import nlg_hash
import nlg_hash_plaintext


def hash_to_nloct_str(h: int) -> str:
    """
    Convert a hash value to a string that can be used to represent it in
    a NLOCT file.
    Returns a quoted plaintext value ('"KEY"') if possible, otherwise a
    1- to 8-char uppercase hex string.
    """
    plaintext = nlg_hash_plaintext.get_plaintext(h)

    if plaintext is None:
        return hex(h).upper()[2:]
    else:
        return '"%s"' % plaintext


def nloct_str_to_hash(s: str) -> int:
    """
    Convert a string key previously formed with hash_to_nloct_str() back
    to a hash value.
    """
    if s.startswith('"'):
        return nlg_hash.hash_str(k[1:-1])
    else:
        return int(k, 16)


@dataclasses.dataclass
class Message:
    """
    Represents a NLOC/NLOCT message
    """
    id: int
    text: str


@dataclasses.dataclass
class LocalizationFile:
    """
    Represents a NLOC or NLOCT file
    """
    lang_id: int = None

    # This is a list instead of a dict in order to preserve message
    # order. The game doesn't care about the order, but messages seem to
    # be encoded in probably the same order the developers wrote them
    # in, so preserving it is useful for understanding context and such.
    messages: List[Message] = dataclasses.field(default_factory=list)


    @classmethod
    def from_nloc(cls, data: bytes, *, endian:str='<') -> 'LocalizationFile':
        """
        Create a LocalizationFile from NLOC file data
        """
        self = cls()
        endian_name = 'le' if endian == '<' else 'be'

        lang_id, str_count = struct.unpack_from(endian + 'II', data, 8)

        full_str = data[0x14 + 8 * str_count:].decode('utf-16-' + endian_name)
        messages = []
        for i in range(str_count):
            s_id, s_start = struct.unpack_from(endian + 'II', data, 0x14 + 8 * i)
            s = full_str[s_start:full_str.index('\x00', s_start)]

            m = Message(s_id, s)
            messages.append((s_start, m))

        messages.sort(key=lambda e: e[0])

        return cls(lang_id, [m for k, m in messages])


    @classmethod
    def from_nloct(cls, file: str) -> 'LocalizationFile':
        """
        Create a LocalizationFile from NLOCT file data
        """

        def get_key_and_line(line: str) -> (int, str):
            """
            Given a line of NLOCT, isolate the int key and the string contents
            """
            if line.startswith('"'):
                # Hash a string
                str_end = line.index('"', 1)
                s = line[1:str_end]
                return nlg_hash.hash_str(s), line[str_end+1:].lstrip()

            else:
                return int(line.split(' ')[0], 16), line[line.index(' ')+1:].lstrip()

        self = cls()

        blockcomment = False
        for line in file.splitlines():
            # Allow ### to start/end block-comments a la CoffeeScript
            if line.startswith('###'):
                blockcomment = not blockcomment
                continue
            if blockcomment: continue

            if line.startswith('#') or not line: continue

            if line.lower().startswith('langid:'):
                # Language ID line; this is handled entirely differently
                lang_id_str = line[len('langid:'):].strip()
                if lang_id_str.startswith('"'):
                    self.lang_id = nlg_hash.hash_str(lang_id_str[1:-1])
                else:
                    self.lang_id = int(lang_id_str, 16)
                continue

            id_hash, msg = get_key_and_line(line)

            self.messages.append(Message(id_hash, msg))

        return self


    def to_nloc(self, *, endian:str='<') -> bytes:
        """
        Convert to NLOC file data
        """

        lang_id = self.lang_id
        if self.lang_id is None:
            print('WARNING: Language ID was not set. Defaulting to 0')
            lang_id = 0

        endian_name = 'le' if endian == '<' else 'be'

        header = bytearray()
        contents = bytearray()

        # TODO: is the value at 0x10 really an endian marker?
        header.extend(struct.pack(endian + '4s4I', b'NLOC', 1, lang_id, len(self.messages), (0 if endian == '<' else 1)))

        # Add message text in self.messages order
        msg_text_offsets = {}
        for msg in self.messages:
            msg_text_offsets[id(msg)] = len(contents) // 2
            contents.extend(msg.text.encode('utf-16-' + endian_name) + b'\0\0')

        # Then add to the header in message-ID order
        for msg in sorted(self.messages, key=lambda m: m.id):
            text_offset = msg_text_offsets[id(msg)]
            header.extend(struct.pack(endian + 'II', msg.id, text_offset))

        return bytes(header + contents)


    def to_nloct(self) -> str:
        """
        Convert to NLOCT file data
        """
        output = []

        if self.lang_id is not None:
            output.append('langid: ' + hash_to_nloct_str(self.lang_id))

        for msg in self.messages:
            output.append(hash_to_nloct_str(msg.id) + '    ' + msg.text)

        return '\n'.join(output)


    def update(self, other: 'LocalizationFile') -> None:
        """
        Patch another localization file on top of this one.
        Like dict.update(other).
        """
        if None not in [self.lang_id, other.lang_id] and self.lang_id != other.lang_id:
            raise ValueError(
                 "Can\'t combine messages from localization"
                f' files for different languages ("{self.lang_id}",'
                f' "{other.lang_id}"). For language-independent'
                 " patching, set the patch file's language ID to None"
                 ' first.')

        id_to_idx = {msg.id: i for i, msg in enumerate(self.messages)}

        for new_msg in other.messages:
            existing_idx = id_to_idx.get(new_msg.id)

            # Replace existing message if it's there; otherwise,
            # append it to the end
            if existing_idx is not None:
                self.messages[existing_idx] = new_msg
            else:
                self.messages.append(new_msg)


    def sort_by_id(self) -> None:
        """
        Sort all messages by ID
        """
        self.messages.sort(key=lambda m: m.id)


    def find_message(self, id: Union[int, str]) -> Message:
        """
        Find a Message instance by ID (int and str supported).
        Note that this is O(n).
        """
        if isinstance(key, str):
            key = nlg_hash.hash_str(key)

        for msg in self.messages:
            if msg.id == key:
                return msg


    def __getitem__(self, key: Union[int, str]) -> str:
        msg = self.find_message(key)
        if msg is None:
            raise KeyError
        else:
            return msg.text


    def __setitem__(self, key: Union[int, str], value: str) -> None:
        msg = self.find_message(key)
        if msg is None:
            raise KeyError
        else:
            msg.text = value
