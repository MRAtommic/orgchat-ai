# -*- coding: utf-8 -*-
"""
webai/dns_patch.py — Isolated DNS Workaround
Workaround for specific cloud container environments (e.g. Railway / Docker)
where default DNS lookups might time out. Can be bypassed via DISABLE_DNS_PATCH=1.
"""

import os
import socket
import struct
import logging

logger = logging.getLogger("OrgChatAI.DNS")
_orig_getaddrinfo = socket.getaddrinfo

def dns_query_udp(hostname, dns_servers=None, timeout=2.0):
    if dns_servers is None:
        dns_servers = ["8.8.8.8", "1.1.1.1"]

    header = struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0)
    question = b''
    for part in hostname.split('.'):
        if not part:
            continue
        question += struct.pack('B', len(part)) + part.encode('ascii')
    question += b'\x00'
    question += struct.pack('!HH', 1, 1)
    packet = header + question

    for dns_server in dns_servers:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        try:
            sock.sendto(packet, (dns_server, 53))
            data, _ = sock.recvfrom(512)
            id, flags, qdcount, ancount, nscount, arcount = struct.unpack('!HHHHHH', data[:12])

            offset = 12
            while True:
                length = data[offset]
                if length == 0:
                    offset += 1
                    break
                offset += 1 + length
            offset += 4  # Skip QTYPE and QCLASS

            ips = []
            for _ in range(ancount):
                if (data[offset] & 0xc0) == 0xc0:
                    offset += 2
                else:
                    while True:
                        length = data[offset]
                        if length == 0:
                            offset += 1
                            break
                        offset += 1 + length
                type_, class_, ttl, rdlength = struct.unpack('!HHIH', data[offset:offset+10])
                offset += 10
                rdata = data[offset:offset+rdlength]
                offset += rdlength

                if type_ == 1 and rdlength == 4:  # A record
                    ips.append(socket.inet_ntoa(rdata))
            if ips:
                return ips
        except Exception:
            continue
        finally:
            sock.close()
    return []

def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if not host or host in ('localhost', '127.0.0.1', '::1', '0.0.0.0'):
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    is_ip = True
    for c in host:
        if c not in '0123456789.:[]abcdefABCDEF':
            is_ip = False
            break

    if is_ip:
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    ips = dns_query_udp(host)
    if ips:
        results = []
        for ip in ips:
            try:
                res = _orig_getaddrinfo(ip, port, family, type, proto, flags)
                for item in res:
                    results.append(item)
            except Exception:
                pass
        if results:
            return results

    return _orig_getaddrinfo(host, port, family, type, proto, flags)

def apply_dns_patch_if_needed():
    """Applies UDP DNS monkeypatch on non-Windows cloud containers unless explicitly disabled."""
    if os.name != 'nt' and os.environ.get("DISABLE_DNS_PATCH") != '1':
        socket.getaddrinfo = patched_getaddrinfo
        logger.info("DNS Monkeypatch applied successfully.")
    else:
        logger.debug("DNS Monkeypatch bypassed (Local Windows or Disabled).")
