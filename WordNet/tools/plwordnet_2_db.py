import sqlite3


POS_TAGS = {
    'przyslowek': 'ADV',
    'rzeczownik': 'NOUN',
    'przymiotnik': 'ADJ',
    'czasownik': 'VERB',
    '': 'X'
}

ANNOTATIONS = {
    '- s ': -1,
    '- s': -1,
    '- m': -2,
    '+ s': 1,
    '+ m': 2
}


def get_all_pos_tags():
    import pandas as pd
    import pathlib

    csv = pd.read_csv(pathlib.Path(__file__).resolve().parent.parent / 'wordnet' / 'AppData' / 'sentiments.csv')
    tags = set()
    for index, row in csv.iterrows():
        tags.add(row['czesc_mowy'])

    return tags


def get_all_annotations():
    import pandas as pd
    import pathlib

    csv = pd.read_csv(pathlib.Path(__file__).resolve().parent.parent / 'wordnet' / 'AppData' / 'sentiments.csv')
    annotations = set()
    for index, row in csv.iterrows():
        annotations.add(row['stopien_nacechowania'])

    return annotations


def create_database():
    import pandas as pd
    import pathlib

    csv = pd.read_csv(pathlib.Path(__file__).resolve().parent.parent / 'wordnet' / 'AppData' / 'sentiments.csv')
    conn = sqlite3.Connection('db.sqlite3')
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS Annotations(
            id INTEGER PRIMARY KEY,
            lemma TEXT NOT NULL,
            pos TEXT NOT NULL,
            annotation INTEGER NOT NULL
        )
        ''')
    print('Created Annotations.')

    rows = []
    for index, csv_row in csv.iterrows():
        if str(csv_row['stopien_nacechowania']) in ['nan', 'amb']:
            continue
        row = (
            index,
            csv_row['lemat'],
            POS_TAGS[csv_row['czesc_mowy']],
            ANNOTATIONS[csv_row['stopien_nacechowania']])
        rows.append(row)

    conn.executemany(
        'INSERT INTO Annotations(id, lemma, pos, annotation) VALUES(?, ?, ?, ?)', rows)
    print(f'Inserted {len(rows)} rows.')

    conn.commit()
    conn.close()


if __name__ == '__main__':
    create_database()
