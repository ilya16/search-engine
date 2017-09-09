import re

DATA_FILES = ["../dataset/LISA{}.{}01".format(*[i, j]) for i in range(6) for j in [0, 5]] \
             + ["../dataset/LISA5.627", "../dataset/LISA5.850"]


def read_data():
    """
    Opens all files with documents and processes content in them
    :return: dictionary of all read documents
    """
    docs = {}
    for file in DATA_FILES:
        with open(file, "r") as f:
            doc, content, doc_id = {}, '', 0
            for line in f:
                if re.match(r'Document[ ]+\d+', line):
                    doc_id = re.search(r'\d+', line).group(0)
                elif re.match(r'[ ]*[\n]', line):
                    doc['title'] = content
                    content = ''
                elif re.match(r'[*]{3,}', line):
                    doc['content'] = content
                    content = ''
                    docs[doc_id] = doc
                    doc = {}
                else:
                    content += line
    return docs
