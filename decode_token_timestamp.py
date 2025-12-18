import base64
import struct
import time

tokens = [
    # Failing users
    "gAAAAABoxdcQ8NypGnat1kN-Ep_9eYpfklP0EzTSx8YwPgky2X", # User 324
    "gAAAAABoxdcQnTGUxq6e9XBvWuPhIeYT1peOhyBCplyNuVOThb", # User 325
    "gAAAAABoxdcQ6vuBcuUB2bpQ6DadvFN_VRKAx-iOJNxNdUF2c5", # User 326
    "gAAAAABoxdcQP7jeD4c1gjBSJR_fpPL3w5nVaAI_TzXG4xO3U7", # User 327
    "gAAAAABoxdcQasl5tSZk_300m41oTDZDXI1M0vyFKCsnJdG__T", # User 770
    # Working users
    "gAAAAABpG9Q1dJYx0US3hjgJ0hzhFQ-7gasCgKpeEJ-Op-reDY", # User 1
    "gAAAAABpG89StlK2KZjyYLgYVmNimstvI-x35Hfc4xAe0ziWS9", # User 9
    "gAAAAABpEUm6rEydDQg_Od-2FUA2I4o1IN1AWH_LHoj2MAIYlG", # User 186
]

def get_timestamp(token):
    try:
        # Fernet token is base64url encoded
        # The first byte is version (0x80), next 8 bytes are timestamp (int64 big endian)
        # We need to pad it to be valid base64
        padding = len(token) % 4
        if padding:
            token += "=" * (4 - padding)
            
        decoded = base64.urlsafe_b64decode(token)
        version = decoded[0]
        timestamp = struct.unpack(">Q", decoded[1:9])[0]
        return timestamp
    except Exception as e:
        print(f"Error decoding {token[:10]}...: {e}")
        return None

print(f"{'Token Prefix':<15} | {'Timestamp':<10} | {'Date'}")
print("-" * 60)

for token in tokens:
    ts = get_timestamp(token)
    if ts:
        print(f"{token[:12]:<15} | {ts:<10} | {time.ctime(ts)}")
