"""
Utilities for looking up known plaintext strings for NLG hash values
"""

from pathlib import Path
from typing import Optional

import nlg_hash


PLAINTEXT_DATA_FILE = Path(__file__).parent / 'nlg_hash_plaintext_data.txt'



HashPlaintexts = None

def ensure_plaintexts_loaded() -> None:
    """
    Ensure that HashPlaintexts is loaded
    """
    global HashPlaintexts

    if HashPlaintexts is None:
        # Try to load it
        HashPlaintexts = {}

        if PLAINTEXT_DATA_FILE.is_file():
            with PLAINTEXT_DATA_FILE.open('r', encoding='utf-8') as f:
                for s in f.read().splitlines():
                    HashPlaintexts[nlg_hash.hash_str(s)] = s
        else:
            print("WARNING: Couldn't find hash-key repo file")


def get_plaintext(h: int) -> Optional[str]:
    """
    Use the plaintext hash keys file to try to find a key matching the
    provided hash value (int).
    """
    global HashPlaintexts

    ensure_plaintexts_loaded()

    return HashPlaintexts.get(h)
