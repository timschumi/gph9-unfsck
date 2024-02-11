#!/usr/bin/python3

import os
import struct
import sys

def pread(file, size, offset):
    file.seek(offset, os.SEEK_SET)
    return file.read(size)

filename = sys.argv[1]
file = open(filename, "rb")

maybe_mbr_magic = pread(file, 2, 0x1FE)
if maybe_mbr_magic != b"\x55\xAA":
    print("error: Wasn't able to find valid MBR magic", file=sys.stderr)
    sys.exit(1)

print(f"[*] Found a valid MBR magic")

if pread(file, 11, 0x0) == b"\xEB\x76\x90EXFAT   ":
    print(f"[*] Image is a raw exFAT image")
    start_of_exfat = 0x0
elif pread(file, 11, (start_of_exfat := struct.unpack("<I", pread(file, 4, 0x1C6))[0] * 512)) == b"\xEB\x76\x90EXFAT   ":
    print(f"[*] Image is a full disk image, with the first partition starting at {hex(start_of_exfat)}")
else:
    print("error: Wasn't able to find the exFAT partition", file=sys.stderr)
    sys.exit(1)

fat_offset = struct.unpack("<I", pread(file, 4, start_of_exfat + 80))[0]
fat_offset_real = start_of_exfat + fat_offset * 512
fat_length = struct.unpack("<I", pread(file, 4, start_of_exfat + 84))[0]
fat_length_real = fat_length * 512
cluster_offset = struct.unpack("<I", pread(file, 4, start_of_exfat + 88))[0]
cluster_offset_real = start_of_exfat + cluster_offset * 512
cluster_count = struct.unpack("<I", pread(file, 4, start_of_exfat + 92))[0]
bps_shift = struct.unpack("<B", pread(file, 1, start_of_exfat + 108))[0]
bps = 2 ** bps_shift
spc_shift = struct.unpack("<B", pread(file, 1, start_of_exfat + 109))[0]
spc = 2 ** spc_shift
bpc = bps * spc

print(f"[*] FatOffset is {hex(fat_offset)} ({hex(fat_offset_real)})")
print(f"[*] FatLength is {hex(fat_length)} ({fat_length_real})")
print(f"[*] ClusterHeapOffset is {hex(cluster_offset)} ({hex(cluster_offset_real)})")
print(f"[*] ClusterCount is {hex(cluster_count)}")
print(f"[*] BytesPerSector is {bps}")
print(f"[*] SectorsPerCluster is {spc}")
print(f"[*] BytesPerCluster is {bpc}")

processed_entries = set()
for i in range(cluster_count):
    if i + 2 in processed_entries:
        continue

    maybe_magic = pread(file, 16, cluster_offset_real + i * bpc)
    if maybe_magic[0:4] == b"RIFF":
        print(f"[+] Found WAV file starting at sector {i}")
        dump_name = f"{i}.wav"
    elif maybe_magic[4:11] == b"ftypmp4":
        print(f"[+] Found MP4 file starting at sector {i}")
        dump_name = f"{i}.mp4"
    else:
        continue

    dump_file = open(dump_name, "wb")

    next_entry = i + 2
    while next_entry >= 2 and next_entry <= cluster_count + 1 and next_entry not in processed_entries:
        data = pread(file, bpc, cluster_offset_real + (next_entry - 2) * bpc)
        dump_file.write(data)
        processed_entries.add(next_entry)
        next_entry = struct.unpack("<I", pread(file, 4, fat_offset_real + next_entry * 4))[0]

    if next_entry in processed_entries:
        print(f"[!] File terminated with a loop at entry {next_entry}")
    elif next_entry == 0xFFFFFFF7:
        print(f"[!] File terminated with a bad sector")
    elif next_entry != 0xFFFFFFFF:
        print(f"[!] File terminated with out of bounds entry number {next_entry}")

    dump_file.close()
