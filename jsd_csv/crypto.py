"""
Cryptographic helper for decrypting JioSaavn media URLs.
Uses DES ECB mode with standard JioSaavn key b'38346591'.
Includes PyCryptodome implementation with a pure Python fallback.
"""

import base64
import logging

logger = logging.getLogger(__name__)

SAAVN_DES_KEY = b"38346591"

# Try importing pycryptodome
_HAS_PYCRYPTODOME = False
try:
    from Crypto.Cipher import DES
    _HAS_PYCRYPTODOME = True
except ImportError:
    _HAS_PYCRYPTODOME = False


# Pure Python DES implementation as fallback if pycryptodome is missing
# Standard DES S-boxes, permutations, and key schedule
_PC1 = [
    57, 49, 41, 33, 25, 17, 9, 1, 58, 50, 42, 34, 26, 18,
    10, 2, 59, 51, 43, 35, 27, 19, 11, 3, 60, 52, 44, 36,
    63, 55, 47, 39, 31, 23, 15, 7, 62, 54, 46, 38, 30, 22,
    14, 6, 61, 53, 45, 37, 29, 21, 13, 5, 28, 20, 12, 4
]

_PC2 = [
    14, 17, 11, 24, 1, 5, 3, 28, 15, 6, 21, 10, 23, 19, 12, 4,
    26, 8, 16, 7, 27, 20, 13, 2, 41, 52, 31, 37, 47, 55, 30, 40,
    51, 45, 33, 48, 44, 49, 39, 56, 34, 53, 46, 42, 50, 36, 29, 32
]

_SHIFTS = [1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1]

_IP = [
    58, 50, 42, 34, 26, 18, 10, 2, 60, 52, 44, 36, 28, 20, 12, 4,
    62, 54, 46, 38, 30, 22, 14, 6, 64, 56, 48, 40, 32, 24, 16, 8,
    57, 49, 41, 33, 25, 17, 9, 1, 59, 51, 43, 35, 27, 19, 11, 3,
    61, 53, 45, 37, 29, 21, 13, 5, 63, 55, 47, 39, 31, 23, 15, 7
]

_FP = [
    40, 8, 48, 16, 56, 24, 64, 32, 39, 7, 47, 15, 55, 23, 63, 31,
    38, 6, 46, 14, 54, 22, 62, 30, 37, 5, 45, 13, 53, 21, 61, 29,
    36, 4, 44, 12, 52, 20, 60, 28, 35, 3, 43, 11, 51, 19, 59, 27,
    34, 2, 42, 10, 50, 18, 58, 26, 33, 1, 41, 9, 49, 17, 57, 25
]

_EXPANSION = [
    32, 1, 2, 3, 4, 5, 4, 5, 6, 7, 8, 9,
    8, 9, 10, 11, 12, 13, 12, 13, 14, 15, 16, 17,
    16, 17, 18, 19, 20, 21, 20, 21, 22, 23, 24, 25,
    24, 25, 26, 27, 28, 29, 28, 29, 30, 31, 32, 1
]

_SBOXES = [
    [
        14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0, 7,
        0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8,
        4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0,
        15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 3, 14, 10, 0, 6, 13
    ],
    [
        15, 1, 8, 14, 6, 11, 3, 4, 9, 7, 2, 13, 12, 0, 5, 10,
        3, 13, 4, 7, 15, 2, 8, 14, 12, 0, 1, 10, 6, 9, 11, 5,
        0, 14, 7, 11, 10, 4, 13, 1, 5, 8, 12, 6, 9, 3, 2, 15,
        13, 8, 10, 1, 3, 15, 4, 2, 11, 6, 7, 12, 0, 5, 14, 9
    ],
    [
        10, 0, 9, 14, 6, 3, 15, 5, 1, 13, 12, 7, 11, 4, 2, 8,
        13, 7, 0, 9, 3, 4, 6, 10, 2, 8, 5, 14, 12, 11, 15, 1,
        13, 6, 4, 9, 8, 15, 3, 0, 11, 1, 2, 12, 5, 10, 14, 7,
        1, 10, 13, 0, 6, 9, 8, 7, 4, 15, 14, 3, 11, 5, 2, 12
    ],
    [
        7, 13, 14, 3, 0, 6, 9, 10, 1, 2, 8, 5, 11, 12, 4, 15,
        13, 8, 11, 5, 6, 15, 0, 3, 4, 7, 2, 12, 1, 10, 14, 9,
        10, 6, 9, 0, 12, 11, 7, 13, 15, 1, 3, 14, 5, 2, 8, 4,
        3, 15, 0, 6, 10, 1, 13, 8, 9, 4, 5, 11, 12, 7, 2, 14
    ],
    [
        2, 12, 4, 1, 7, 10, 11, 6, 8, 5, 3, 15, 13, 0, 14, 9,
        14, 11, 2, 12, 4, 7, 13, 1, 5, 0, 15, 10, 3, 9, 8, 6,
        4, 2, 1, 11, 10, 13, 7, 8, 15, 9, 12, 5, 6, 3, 0, 14,
        11, 8, 12, 7, 1, 14, 2, 13, 6, 15, 0, 9, 10, 4, 5, 3
    ],
    [
        12, 1, 10, 15, 9, 2, 6, 8, 0, 13, 3, 4, 14, 7, 5, 11,
        10, 15, 4, 2, 7, 12, 9, 5, 6, 1, 13, 14, 0, 11, 3, 8,
        9, 14, 15, 5, 2, 8, 12, 3, 7, 0, 4, 10, 1, 13, 11, 6,
        4, 3, 2, 12, 9, 5, 15, 10, 11, 14, 1, 7, 6, 0, 8, 13
    ],
    [
        4, 11, 2, 14, 15, 0, 8, 13, 3, 12, 9, 7, 5, 10, 6, 1,
        13, 0, 11, 7, 4, 9, 1, 10, 14, 3, 5, 12, 2, 15, 8, 6,
        1, 4, 11, 13, 12, 3, 7, 14, 10, 15, 6, 8, 0, 5, 9, 2,
        6, 11, 13, 8, 1, 4, 10, 7, 9, 5, 0, 15, 14, 2, 3, 12
    ],
    [
        13, 2, 8, 4, 6, 15, 11, 1, 10, 9, 3, 14, 5, 0, 12, 7,
        1, 15, 13, 8, 10, 3, 7, 4, 12, 5, 6, 11, 0, 14, 9, 2,
        7, 11, 4, 1, 9, 12, 14, 2, 0, 6, 10, 13, 15, 3, 5, 8,
        2, 1, 14, 7, 4, 10, 8, 13, 15, 12, 9, 0, 3, 5, 6, 11
    ]
]

_P = [
    16, 7, 20, 21, 29, 12, 28, 17, 1, 15, 23, 26, 5, 18, 31, 10,
    2, 8, 24, 14, 32, 27, 3, 9, 19, 13, 30, 6, 22, 11, 4, 25
]


def _permute(block: int, table: list[int], in_len: int) -> int:
    res = 0
    for idx, pos in enumerate(table):
        if (block >> (in_len - pos)) & 1:
            res |= 1 << (len(table) - 1 - idx)
    return res


def _generate_keys(key_bytes: bytes) -> list[int]:
    key_int = int.from_bytes(key_bytes, "big")
    c_d = _permute(key_int, _PC1, 64)
    c = (c_d >> 28) & 0x0FFFFFFF
    d = c_d & 0x0FFFFFFF
    subkeys = []
    for shift in _SHIFTS:
        c = ((c << shift) & 0x0FFFFFFF) | (c >> (28 - shift))
        d = ((d << shift) & 0x0FFFFFFF) | (d >> (28 - shift))
        cd = (c << 28) | d
        subkeys.append(_permute(cd, _PC2, 56))
    return subkeys


def _des_decrypt_block(block_int: int, subkeys: list[int]) -> int:
    block = _permute(block_int, _IP, 64)
    left = (block >> 32) & 0xFFFFFFFF
    right = block & 0xFFFFFFFF
    for subkey in reversed(subkeys):
        exp = _permute(right, _EXPANSION, 32)
        xor_res = exp ^ subkey
        s_out = 0
        for i in range(8):
            chunk = (xor_res >> (42 - 6 * i)) & 0x3F
            row = ((chunk & 0x20) >> 4) | (chunk & 0x01)
            col = (chunk >> 1) & 0x0F
            val = _SBOXES[i][(row << 4) | col]
            s_out = (s_out << 4) | val
        f_res = _permute(s_out, _P, 32)
        left, right = right, left ^ f_res
    combined = (right << 32) | left
    return _permute(combined, _FP, 64)


def _pure_des_decrypt(cipher_bytes: bytes, key: bytes) -> bytes:
    subkeys = _generate_keys(key)
    out = bytearray()
    for i in range(0, len(cipher_bytes), 8):
        block = int.from_bytes(cipher_bytes[i : i + 8], "big")
        dec = _des_decrypt_block(block, subkeys)
        out.extend(dec.to_bytes(8, "big"))
    return bytes(out)


def unpad_pkcs5(data: bytes) -> bytes:
    """Remove standard PKCS5 / PKCS7 padding."""
    if not data:
        return data
    pad_len = data[-1]
    if 1 <= pad_len <= 8 and len(data) >= pad_len:
        # Check all padding bytes
        if data[-pad_len:] == bytes([pad_len] * pad_len):
            return data[:-pad_len]
    # Fallback: strip trailing zero bytes or non-printable bytes
    return data.rstrip(b"\x00")


def decrypt_saavn_url(encrypted_url: str) -> str:
    """
    Decrypts JioSaavn encrypted_media_url into direct CDN stream URL.
    
    Args:
        encrypted_url: Base64-encoded encrypted string from JioSaavn API.
        
    Returns:
        Decrypted direct URL string (e.g. https://aac.saavncdn.com/...)
    """
    if not encrypted_url:
        return ""
        
    encrypted_url = encrypted_url.strip()
    try:
        raw_cipher = base64.b64decode(encrypted_url)
    except Exception as e:
        logger.warning(f"Failed to base64 decode encrypted URL: {e}")
        return ""

    decrypted_bytes: bytes
    if _HAS_PYCRYPTODOME:
        try:
            cipher = DES.new(SAAVN_DES_KEY, DES.MODE_ECB)
            decrypted_bytes = cipher.decrypt(raw_cipher)
        except Exception as e:
            logger.debug(f"PyCryptodome failed, falling back to pure Python: {e}")
            decrypted_bytes = _pure_des_decrypt(raw_cipher, SAAVN_DES_KEY)
    else:
        decrypted_bytes = _pure_des_decrypt(raw_cipher, SAAVN_DES_KEY)

    unpadded = unpad_pkcs5(decrypted_bytes)
    return unpadded.decode("utf-8", errors="ignore").strip()
