import re
import nltk
import string
import json
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer

stemmer = PorterStemmer()
STOP_WORDS = list(string.punctuation) + ["'a", "'s"]


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


def build_index(docs, from_dump=False, positional=False):
    """
    Build inverted index from given documents
    :param docs: dictionary of documents
    :param from_dump: reading index from 'indexfile' or building from scratch
    :param positional: type of index
    :return: built index
    """

    # adding path of preloaded nltk data
    nltk.data.path.append("../nltk_data")
    index = {}

    # checking existence of 'indexfile'
    try:
        open('../results/indexfile', 'r')
    except FileNotFoundError:
        from_dump = False

    if from_dump:
        with open('../results/indexfile', 'r') as indexfile:
            index = json.loads(indexfile.read())
    else:
        # building an index
        print('building an index...')
        for docid in docs:
            doc = docs[docid]
            text = doc['title'] + " " + doc['content']
            tokens = text2tokens(text, True)

            if positional:
                for pos in range(len(tokens)):
                    token = tokens[pos]
                    if token not in index:
                        index[token] = {docid: [pos]}
                    elif docid not in index[token]:
                        index[token][docid] = [pos]
                    else:
                        index[token][docid].append(pos)
            else:
                for token in tokens:
                    if token not in index:
                        index[token] = [docid]
                    elif docid not in index[token]:
                        index[token].append(docid)

        sorted_index = {}
        for k, v in sorted(index.items()):
            sorted_index[k] = v

        index = sorted_index

        # dumping index
        with open('../results/indexfile', 'w+') as indexfile:
            indexfile.write(json.dumps(index))

        print('index is successfully built')

    return index
