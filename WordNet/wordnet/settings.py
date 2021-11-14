import pathlib

BASE = pathlib.Path(__file__).resolve().parent
APP_DATA = BASE / 'AppData'

SENTIMENTS_DICTIONARY = APP_DATA / 'sentiments.csv'
