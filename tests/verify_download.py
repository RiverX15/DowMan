import os
import sys


ORIGINAL_FILE_PATH = 'test_file.bin'
DOWNLOADED_FILE_PATH = 'downloaded_file.bin'
CHUNK_SIZE_MB = 5
CHUNK_SIZE = CHUNK_SIZE_MB * 1024 * 1024

def compare_files_chunks(path1, path2, chunk_size=CHUNK_SIZE):
    if os.path.getsize(path1) != os.path.getsize(path2):
        print(
            f"Files differ in size: {path1} ({os.path.getsize(path1)} bytes) vs {path2} ({os.path.getsize(path2)} bytes)")
        return
    mismatches = []
    with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
        offset = 0
        while True:
            chunk1 = f1.read(chunk_size)
            chunk2 = f2.read(chunk_size)
            if not chunk1:
                break
            if chunk1 != chunk2:
                end_offset = offset + len(chunk1) - 1
                mismatches.append((offset, end_offset))
                print(f"Mismatch found in chunk: Start Index {offset}, End Index {end_offset}")
            offset += len(chunk1)
    if not mismatches:
        print('Downloaded file and source file MATCH.')
        return True
    else:
        print(f'Downloaded file and source file DO NOT MATCH. Found {len(mismatches)} mismatching chunks.')
        return False

if __name__ == '__main__':
    ok = compare_files_chunks(ORIGINAL_FILE_PATH, DOWNLOADED_FILE_PATH)
    sys.exit(0 if ok else 1)
