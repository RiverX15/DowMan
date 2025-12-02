import os


ORIGINAL_FILE_PATH = 'test_file.bin'
DOWNLOADED_FILE_PATH = 'downloaded_file.bin'
CHUNK_SIZE = 65536

def compare_files(path1, path2, chunk_size = CHUNK_SIZE):
    if os.path.getsize(path1)!=os.path.getsize(path2):
        return False
    with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
        while True:
            chunk1 = f1.read(chunk_size)
            chunk2 = f2.read(chunk_size)
            if chunk1!=chunk2:
                return False
            if not chunk1:
                return True

if compare_files(ORIGINAL_FILE_PATH, DOWNLOADED_FILE_PATH):
    print('Downloaded file and source file match.')
else:
    print('Downloaded file and source file do not match.')
