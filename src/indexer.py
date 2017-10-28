import nltk
import json
from time import time
from preprocess import text2tokens


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
        print("'indexfile' file is not found")
        from_dump = False

    if from_dump:
        with open('../results/indexfile', 'r') as indexfile:
            index = json.loads(indexfile.read())
    else:
        # building an index
        print('building an index...')
        starttime = time()
        token_stats = []
        for docid in docs:
            doc = docs[docid]
            text = doc['title'] + " " + doc['content']
            tokens = text2tokens(text, stem=False)

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
                    token_stats.append((token, docid))

        if positional:
            sorted_index = {}
            for k, v in sorted(index.items()):
                sorted_index[k] = v

            index = sorted_index
        else:
            token_stats.sort(key=lambda term: term[0])

            lasttoken = ''
            lastid = 0
            for token in token_stats:
                if token[0] != lasttoken:
                    if lasttoken != '':
                        index[lasttoken] = posting
                    posting = {token[1]: 1}
                    lasttoken = token[0]
                    lastid = token[1]
                elif token[1] != lastid:
                    posting[token[1]] = 1
                    lastid = token[1]
                else:
                    posting[token[1]] += 1

        # dumping index
        with open('../results/indexfile', 'w+') as indexfile:
            indexfile.write(json.dumps(index))

        print('index is successfully built in %.3f ms' % (time() - starttime))

    return index
