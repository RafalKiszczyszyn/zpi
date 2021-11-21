ANNOTATIONS = {
    '- s ': 0,
    '- s': 0,
    '- m': 0,
    '+ s': 1,
    '+ m': 1
}


def createDataSet():
    import pandas as pd

    csv = pd.read_csv('sentiments.csv')
    dataSet = pd.DataFrame(columns=['Example', 'Target'])

    for index, csv_row in csv.iterrows():
        if str(csv_row['stopien_nacechowania']) in ['nan', 'amb']:
            continue

        target = ANNOTATIONS[str(csv_row['stopien_nacechowania'])]
        example1 = str(csv_row['przyklad1'])
        example2 = str(csv_row['przyklad2'])

        if example1 != 'nan':
            row = {'Example': example1, 'Target': target}
            dataSet = dataSet.append(row, ignore_index=True)
        if example2 != 'nan':
            row = {'Example': example1, 'Target': target}
            dataSet = dataSet.append(row, ignore_index=True)

    dataSet.to_csv('pl-sentences.csv')


if __name__ == '__main__':
    createDataSet()
