from __future__ import annotations

import pickle
import re
import pandas
import spacy

from typing import List

from wordnet import settings


def get_serialized_dictionary():
    with open('dictionary.bin', 'rb') as f:
        return pickle.load(f)


class SentimentsDictionary:

    class Fields:
        sentiment = 'sentiment'
        pos = 'pos'

    def __init__(self, dictionary):
        self._dictionary = dictionary

    def __getitem__(self, word: str):
        try:
            return self._dictionary[word][0][self.Fields.sentiment]
        except KeyError:
            return None

    def get_sentiment(self, regex):
        result = {}
        for word in self._dictionary:
            if re.match(regex, word):
                result[word] = self[word]
        return result

    @staticmethod
    def from_data_frame(
            data_frame: pandas.DataFrame,
            lemma_column: str,
            pos_column: str,
            sentiment_column: str) -> SentimentsDictionary:

        missing_columns = {lemma_column, pos_column, sentiment_column} - set(data_frame.columns)
        if len(missing_columns) != 0:
            raise Exception(f'Missing columns in data frame: {missing_columns}')

        dictionary = {}
        for index, row in data_frame.iterrows():
            key = row[lemma_column]
            if key not in dictionary:
                dictionary[key] = []
            entry = {
                SentimentsDictionary.Fields.pos: row[pos_column],
                SentimentsDictionary.Fields.sentiment: row[sentiment_column]
            }
            dictionary[key].append(entry)

        return SentimentsDictionary(dictionary)


class SpacyPipeline:

    def __init__(self, dictionary: SentimentsDictionary):
        nlp = spacy.load("pl_core_news_sm")
        disabled = set(nlp.component_names) - {'tok2vec', 'morphologizer', 'tagger', 'lemmatizer'}
        nlp.select_pipes(
            disable=disabled)
        self._nlp = nlp
        self._dictionary = dictionary

    def retrieve_sentiments(self, text: str) -> List[str]:
        doc = self._nlp(text)
        lemmas = [token.lemma_ for token in doc]
        sentiments = [self._dictionary[lemma] for lemma in lemmas]
        return sentiments


# noinspection PyTypeChecker
pipeline: SpacyPipeline = None


def get_pipeline() -> SpacyPipeline:
    global pipeline
    if pipeline is None:
        data_frame = pandas.read_csv(str(settings.SENTIMENTS_DICTIONARY))
        dictionary = SentimentsDictionary.from_data_frame(
            data_frame=data_frame,
            lemma_column='lemat',
            pos_column='czesc_mowy',
            sentiment_column='stopien_nacechowania'
        )
        pipeline = SpacyPipeline(dictionary)
    return pipeline
