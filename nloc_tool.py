"""
NLOC Tool, by RoadrunnerWMC
Started 2016-10-29; heavily refactored 2022-01-06 and 2022-01-12
"""

import argparse
from pathlib import Path
import struct
from typing import List, Optional

import nloc


def autodetect_file_type(path: Path) -> Optional[str]:
    """
    Try to auto-detect the file type from its contents.
    Returns "nloc_le", "nloc_be", "nloct", or None.
    """

    with path.open('rb') as f:
        first_8 = f.read(8)

    if first_8.startswith(bytes.fromhex('58 24 F3 A9')):
        return 'dict_le'

    if first_8 == b'NLOC\1\0\0\0':
        return 'nloc_le'
    elif first_8 == b'NLOC\0\0\0\1':
        return 'nloc_be'

    # NLOCT is text (UTF-8), and thus should have no null bytes
    with path.open('rb') as f:
        first_1024 = f.read(1024)

    if b'\0' in first_1024:
        return None
    else:
        return 'nloct'


def read_nloc_or_nloct(path: Path) -> nloc.LocalizationFile:
    """
    Auto-detect a file's type (NLOC or NLOCT), and return a
    corresponding LocalizationFile
    """
    file_type = autodetect_file_type(path)

    if file_type == 'nloc_le':
        return nloc.LocalizationFile.from_nloc(path.read_bytes(), endian='<')
    elif file_type == 'nloc_be':
        return nloc.LocalizationFile.from_nloc(path.read_bytes(), endian='>')
    elif file_type == 'dict_le':
        return nloc.LocalizationFile.from_nloc(path.with_suffix('.data').read_bytes()[0x10:], endian='<')
    elif file_type == 'nloct':
        return nloc.LocalizationFile.from_nloct(path.read_text(encoding='utf-8'))
    else:
        raise ValueError(f"Couldn't determine the file type of {path.name}")


def inject_nloc_data_into_dict_data(nloc_data: bytes, dict_fp: Path, data_fp: Path) -> None:
    """
    Inject NLOC file data into a dict/data file pair.
    """

    # Do data first so we can know the final .data size
    with data_fp.open('wb') as f:
        f.write(struct.pack('<4I', 0x12027020, len(nloc_data), 0, 0))
        f.write(nloc_data)

        # Align to 8
        data_file_size = 0x10 + len(nloc_data)
        while data_file_size % 8:
            f.write(b'\0')
            data_file_size += 1

    # Open original .dict file...
    with dict_fp.open('rb') as f:
        dict_contents = bytearray(f.read())

    nloc_data_size_align_4 = len(nloc_data)
    while nloc_data_size_align_4 % 4:
        nloc_data_size_align_4 += 1

    # ...inject new file sizes into it...
    dict_contents[0x68:0x6C] = struct.pack('<I', nloc_data_size_align_4)
    dict_contents[0x74:0x78] = struct.pack('<I', data_file_size)
    dict_contents[0x84:0x88] = struct.pack('<I', data_file_size)

    # ...and write the data back.
    with dict_fp.open('wb') as f:
        f.write(dict_contents)


def main(argv:list=None) -> None:
    """
    Main function
    """
    parser = argparse.ArgumentParser(
        description='NLOC Tool: NLOC <-> NLOCT conversion and patch-application script')

    parser.add_argument('input_file', type=Path,
        help='input file to convert'
        ' (NLOC, NLOCT, or DICT/DATA pair containing NLOC)'
        ' (for DICT/DATA, specify the DICT file, and the corresponding DATA file will be opened from the same directory)')
    parser.add_argument('output_file', nargs='?', type=Path,
        help='output file'
        ' (should be the opposite of the input file type)'
        ' (format determined by file extension: ".loc", ".loct", or ".dict")'
        ' (if writing to .dict/.data, the files must already exist,'
        ' and the new data will be injected into them, replacing their original message data)')

    parser.add_argument('--patch', type=Path, action='append', metavar='FILE',
        help='additional NLOCT file to patch on top of the input file.'
        ' You can specify this argument multiple times.')
    parser.add_argument('--output-endian', choices=['little', 'big'], default='little',
        help='if creating an NLOC file as output, this lets you pick the file endianness.'
        ' Default is little.'
        " There are no big-endian NLOC files in Luigi's Mansion Dark Moon,"
        ' but they can be found in other games by Next Level Games.')
    parser.add_argument('--sort', action='store_true',
        help='sort messages by ID before saving output file (if this'
        " isn't specified, messages will be saved in the same order as"
        'in the input file(s)')

    p_args = parser.parse_args(argv)

    input_file = p_args.input_file

    output_file = p_args.output_file
    if output_file is None:
        if input_file.suffix.lower() == '.loct':
            output_file = input_file.with_suffix('.loc')
        else:
            output_file = input_file.with_suffix('.loct')

    print(f'Opening {input_file.name}')
    loc_file = read_nloc_or_nloct(input_file)

    if p_args.patch:
        for patch_file in p_args.patch:
            print(f'Opening {patch_file.name} and applying it as a patch')
            loc_file.update(read_nloc_or_nloct(patch_file))

    if p_args.sort:
        loc_file.sort_by_id()

    if output_file.suffix.lower() == '.loc':
        endian_char = {'big': '>', 'little': '<'}[p_args.output_endian]
        out_data = loc_file.to_nloc(endian=endian_char)

        print(f'Writing output to {output_file.name}')
        with output_file.open('wb') as f:
            f.write(out_data)

    elif output_file.suffix.lower() == '.loct':
        out_str = loc_file.to_nloct()

        print(f'Writing output to {output_file.name}')
        with output_file.open('w', encoding='utf-8') as f:
            f.write(out_str)

    elif output_file.suffix.lower() == '.dict':
        dict_fp = output_file
        data_fp = output_file.with_suffix('.data')

        if not dict_fp.is_file():
            raise ValueError('Output .dict file must already exist')
        if not data_fp.is_file():
            raise ValueError('Output .data file must already exist')

        endian_char = {'big': '>', 'little': '<'}[p_args.output_endian]
        nloc_data = loc_file.to_nloc(endian=endian_char)

        print(f'Injecting output into {dict_fp.name} and {data_fp.name}')

        inject_nloc_data_into_dict_data(nloc_data, dict_fp, data_fp)

    else:
        print(f'Unknown output file extension: {output_file.suffix}')


if __name__ == '__main__':
    main()
