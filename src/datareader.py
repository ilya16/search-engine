import re
import math
import nltk
import json
from preprocess import text2tokens
from time import time

DATA_FILES = ["../dataset/LISA{}.{}01".format(*[i, j]) for i in range(6) for j in [0, 5]] \
             + ["../dataset/LISA5.627", "../dataset/LISA5.850"]


def read_data():
    """
    Opens all files with documents and processes content in them
    :return: dictionary of all read documents
    """

    docs = {}
    nltk.data.path.append("../nltk_data")
    try:
        for file in DATA_FILES:
            with open(file, "r") as f:
                doc, content, docid = {}, '', 0
                for line in f:
                    if re.match(r'Document[ ]+\d+', line):
                        docid = re.search(r'\d+', line).group(0)
                    elif re.match(r'[ ]*[\n]', line):
                        doc['title'] = content
                        content = ''
                    elif re.match(r'[*]{3,}', line):
                        doc['content'] = content
                        content = ''
                        docs[docid] = doc
                        doc = {}
                    else:
                        content += line
    except FileNotFoundError:
        print("ERROR: Document collection is not found. Make sure that it's located in the directory 'dataset'")

    docs = load_stats(docs)

    return docs


def load_stats(docs, from_dump=True):
    """
    Opens all files with documents and processes content in them
    :return: dictionary of all read documents
    """

    # checking existence of 'datastats' file
    try:
        open('../results/datastats', 'r')
    except FileNotFoundError:
        print("'datastats' file is not found")
        from_dump = False

    stats = {}

    if from_dump:
        with open('../results/datastats', 'r') as datastats:
            stats = json.loads(datastats.read())
    else:
        # loading data stats
        print('collecting data stats...')
        starttime = time()
        for docid in docs:
            doc = docs[docid]
            length = 0.0

            tokens = text2tokens(doc['title'] + " " + doc['content'], stem=True)
            tokens.sort()

            lasttoken = ''
            tf = 1
            for token in tokens:
                if token != lasttoken:
                    if lasttoken != '':
                        length += 1.0 + math.log10(tf)
                    tf = 1
                    lasttoken = token
                else:
                    tf += 1

            length = math.sqrt(length)
            stats[docid] = length

        # dumping index
        with open('../results/datastats', 'w+') as datastats:
            datastats.write(json.dumps(stats))

        print('stats are successfully computed in %.3f ms' % (time() - starttime))

    for docid in docs:
        docs[docid]['length'] = stats[docid]

    return docs
