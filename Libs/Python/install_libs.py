import sys
import os
import pathlib
import subprocess
import shutil


def main():
    if len(sys.argv) != 2:
        print('[ERROR] Invalid arguments. Run install_libs.py <destination>')
        sys.exit(1)

    destination = sys.argv[1]
    if not os.path.exists(destination):
        print(f"[ERROR] Destination='{destination}' does not exist")
        sys.exit(1)

    print('[INFO] Installing required dependencies')
    result = subprocess.run(['python', '-m', 'pip', 'install', 'wheel', 'setuptools'])
    if result.returncode != 0:
        print('[ERROR] Failed to install required dependencies')
        sys.exit(1)

    cwd = os.getcwd()
    base = str(pathlib.Path(__file__).resolve().parent)
    for libRoot in filter(os.path.isdir, [os.path.join(base, path) for path in os.listdir(base)]):
        os.chdir(libRoot)
        
        if not os.path.exists("setup.py"):
            print(f"[WARNING] Skipping lib='{libRoot}', reason='setup.py does not exist'")
            continue
        
        print(f"[INFO] Building lib='{libRoot}'")
        result = subprocess.run(["python", "setup.py", "bdist_wheel"])
        if result.returncode != 0:
            print(f"[ERROR] Failed to install lib='{libRoot}'")
            sys.exit(1)

        os.chdir(cwd)
        dist = os.path.join(libRoot, 'dist')
        for path in filter(lambda file: file.endswith('.whl'), [path for path in os.listdir(dist)]):
            print(f"[INFO] Coping wheel file from lib='{libRoot}' to '{destination}'")
            
            shutil.copy(os.path.join(dist, path), os.path.join(destination, path))

    print('Done!')
    sys.exit(0)


if __name__ == '__main__':
    main()
