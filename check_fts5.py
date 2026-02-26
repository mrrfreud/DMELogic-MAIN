import sqlite3
print('SQLite version:', sqlite3.sqlite_version)
print('Module version:', sqlite3.version)
conn = sqlite3.connect(':memory:')
try:
    conn.execute('CREATE VIRTUAL TABLE test USING fts5(content)')
    print('FTS5: YES')
except Exception as e:
    print(f'FTS5: NO ({e})')
conn.close()

# Check where sqlite3 DLL is
import os, sys
for p in sys.path:
    dll = os.path.join(p, 'sqlite3.dll')
    if os.path.exists(dll):
        print(f'Found sqlite3.dll at: {dll}')
    dll2 = os.path.join(p, '_sqlite3.pyd')
    if os.path.exists(dll2):
        print(f'Found _sqlite3.pyd at: {dll2}')

# Check DLLs directory
dlls_dir = os.path.join(os.path.dirname(sys.executable), 'DLLs')
if os.path.exists(dlls_dir):
    for f in os.listdir(dlls_dir):
        if 'sqlite' in f.lower():
            print(f'DLLs/{f}: {os.path.getsize(os.path.join(dlls_dir, f))} bytes')
