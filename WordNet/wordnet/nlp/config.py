import pathlib

BASE = pathlib.Path(__file__).resolve().parent
APP_DATA = BASE / 'AppData'

CONNECTION_STRING = str(APP_DATA / 'db.sqlite3')
