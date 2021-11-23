import sys
import os
import pathlib
import subprocess
import shutil


def main():
    if len(sys.argv) != 3:
        print('[ERROR] Invalid arguments. Run install.py <source> <destination>')
        sys.exit(1)

    source = sys.argv[1]
    destination = sys.argv[2]
    
    if not os.path.exists(source):
        print(f"[ERROR] Source='{source}' does not exist")
        sys.exit(1)

    if not os.path.exists(destination):
        print(f"[ERROR] Destination='{destination}' does not exist")
        sys.exit(1)

    print('[INFO] Installing required dependencies')
    result = subprocess.run(['python', '-m', 'pip', 'install', 'wheel', 'setuptools'])
    if result.returncode != 0:
        print('[ERROR] Failed to install required dependencies')
        sys.exit(1)

    cwd = os.getcwd()
    
    print("[INFO] Building wheel from setup.py")
    os.chdir(source)
    result = subprocess.run(["python", "setup.py", "bdist_wheel"])
    if result.returncode != 0:
        print(f"[ERROR] Failed to install library from source='{source}'")
        sys.exit(1)

    dist = os.path.join(source, 'dist')
    for path in filter(lambda file: file.endswith('.whl'), [path for path in os.listdir(dist)]):
            print(f"[INFO] Coping wheel file from source='{dist}' to '{destination}'")
            shutil.copy(os.path.join(dist, path), os.path.join(destination, path))

    print('Done!')
    sys.exit(0)


if __name__ == '__main__':
    main()
