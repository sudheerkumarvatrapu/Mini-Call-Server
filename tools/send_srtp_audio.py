#!/usr/bin/env python3
"""Send deterministic AES-CM/HMAC-SHA1 SRTP to a learned peer endpoint."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import socket
import struct
import subprocess
import time


DEFAULT_MASTER_KEY_SALT = "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwd"


def aes_ecb_encrypt(key: bytes, blocks: bytes) -> bytes:
    if len(key) != 16 or len(blocks) % 16:
        raise ValueError("AES-128 ECB requires a 16-byte key and complete blocks")
    result = subprocess.run(
        ["openssl", "enc", "-aes-128-ecb", "-K", key.hex(), "-nopad"],
        input=blocks,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def derive_session_material(master_key: bytes, master_salt: bytes, label: int, length: int) -> bytes:
    key_id = label << 64
    initial_counter = (int.from_bytes(master_salt, "big") << 16) ^ key_id
    blocks = bytearray()
    block_count = (length + 15) // 16
    for counter in range(block_count):
        blocks.extend((initial_counter + counter).to_bytes(16, "big"))
    return aes_ecb_encrypt(master_key, bytes(blocks))[:length]


def session_keys(master_key_salt: bytes) -> tuple[bytes, bytes, bytes]:
    if len(master_key_salt) != 30:
        raise ValueError("SDES AES_CM_128_HMAC_SHA1_80 requires 30 key+salt bytes")
    master_key = master_key_salt[:16]
    master_salt = master_key_salt[16:]
    return (
        derive_session_material(master_key, master_salt, 0x00, 16),
        derive_session_material(master_key, master_salt, 0x01, 20),
        derive_session_material(master_key, master_salt, 0x02, 14),
    )


def srtp_packet(
    payload: bytes,
    sequence: int,
    timestamp: int,
    ssrc: int,
    encryption_key: bytes,
    authentication_key: bytes,
    session_salt: bytes,
    roc: int = 0,
) -> bytes:
    header = struct.pack("!BBHII", 0x80, 0, sequence & 0xFFFF, timestamp & 0xFFFFFFFF, ssrc)
    packet_index = (roc << 16) | (sequence & 0xFFFF)
    initial_counter = (
        (int.from_bytes(session_salt, "big") << 16)
        ^ (ssrc << 64)
        ^ (packet_index << 16)
    )
    counter_blocks = bytearray()
    for counter in range((len(payload) + 15) // 16):
        counter_blocks.extend((initial_counter + counter).to_bytes(16, "big"))
    key_stream = aes_ecb_encrypt(encryption_key, bytes(counter_blocks))[: len(payload)]
    encrypted_payload = bytes(left ^ right for left, right in zip(payload, key_stream))
    authenticated = header + encrypted_payload
    auth_tag = hmac.new(authentication_key, authenticated + struct.pack("!I", roc), hashlib.sha1).digest()[:10]
    return authenticated + auth_tag


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind-ip", default="0.0.0.0")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--key", default=DEFAULT_MASTER_KEY_SALT)
    parser.add_argument("--duration", type=float, default=8.0)
    parser.add_argument("--wait-timeout", type=float, default=5.0)
    parser.add_argument("--packet-ms", type=float, default=20.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    master_key_salt = base64.b64decode(args.key, validate=True)
    encryption_key, authentication_key, salt = session_keys(master_key_salt)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.bind_ip, args.port))
    sock.settimeout(args.wait_timeout)
    try:
        _packet, peer = sock.recvfrom(4096)
    except TimeoutError:
        print(f"SRTP sender timed out waiting on {args.bind_ip}:{args.port}", flush=True)
        return 2

    packet_interval = args.packet_ms / 1000.0
    packet_count = max(int(args.duration / packet_interval), 1)
    sequence = 1000
    timestamp = 0
    ssrc = 0x53525450
    payload = bytes([0xFF]) * 160
    deadline = time.monotonic()
    for index in range(packet_count):
        packet = srtp_packet(
            payload,
            sequence + index,
            timestamp + (160 * index),
            ssrc,
            encryption_key,
            authentication_key,
            salt,
        )
        sock.sendto(packet, peer)
        deadline += packet_interval
        time.sleep(max(deadline - time.monotonic(), 0.0))
    print(f"SRTP sender sent {packet_count} packets from {args.bind_ip}:{args.port} to {peer[0]}:{peer[1]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
