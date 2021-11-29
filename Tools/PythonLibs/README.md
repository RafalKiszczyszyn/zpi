## How to use
To build local library run command:
```
python build.py <source> <destination>
```
Source is a directory with `setup.py` and destination is a directory, where `wheel` is copied.

Then, include installed library in your project with command:
```
python -m pip install <library> --find-links <destination>
```

***Notice***:
This script installs automatically required dependencies: wheel and setuptools. Use virtual environment!