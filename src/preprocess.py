import re
import string
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords

stemmer = PorterStemmer()
STOP_WORDS = list(string.punctuation) + ["'a", "'s"] + list(stopwords.words('english'))


def preprocess_word(word, stem=False):
    """
    Preprocesses word to fit in the index scheme
    :param word: word to be preprocessed
    :param stem: condition on applying the stemmer
    :return: preprocessed word
    """
    word = word_tokenize(word.lower())[0]
    if stem:
        return stemmer.stem(word)
    return word


def text2tokens(text, stem=False):
    """
    Transforms text into tokens using 'nltk.tokenize'
    :param text: text to be tokenized
    :param stem: condition on applying the stemmer
    :return: list of tokens
    """
    text = re.sub(r" '(\w{2,})", r' "\1', text.replace('\n', ' ')).lower()
    tokens = list(filter(lambda t: t not in STOP_WORDS, word_tokenize(text)))
    if stem:
        return [stemmer.stem(token) for token in tokens]
    return tokens