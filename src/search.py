from preprocess import preprocess_word
import math

# operators used in search queries with their precedence
OPERATORS = {'NOT': 3, 'AND': 2, 'OR': 1, '(': 0, ')': 0}


def intersect(p1, p2, op='OR'):
    """
    Merges two postings according to the operation
    :param p1: posting of the first term
    :param p2: posting of the second term
    :param op: applied operation (default 'OR')
    :return: resulting posting with document ids
    """

    # list with docids for terms p1 and p2
    # pi[0] - id of current processing doc
    p1, p2 = list(p1), list(p2)
    answer = []
    while p1 and p2:
        if int(p1[0]) == int(p2[0]):
            answer.append(p1[0])
            p1.pop(0)
            p2.pop(0)
        elif int(p1[0]) < int(p2[0]):
            if op == 'OR':
                answer.append(p1[0])
            p1.pop(0)
        else:
            if op == 'OR':
                answer.append(p2[0])
            p2.pop(0)
    if op == 'OR':
        answer += p1
        answer += p2
    return answer


def intersect_pos(p1, p2, k):
    """
    Merges two postings according using positional index
    (currently supports only 'AND' operation)
    :param p1: posting of the first term
    :param p2: posting of the second term
    :param k: distance between terms
    :return: resulting posting with document ids
    """
    answer = []
    p1, p2 = list(p1.items()), list(p2.items())
    while p1 and p2:
        if int(p1[0][0]) == int(p2[0][0]):
            l = []
            pp1, pp2 = p1[0][1], p2[0][1]
            while pp1:
                while pp2:
                    if abs(pp1[0] - pp2[0]) <= k and pp1[0] != pp2[0]:
                        l.append(pp2[0])
                    elif pp2[0] > pp1[0]:
                        break
                    pp2.pop(0)
                while l != [] and abs(l[0] - pp1[0]) > k:
                    l.pop(0)
                for ps in l:
                    answer.append((p1[0][0], pp1[0], ps))
                pp1.pop(0)
            p1.pop(0)
            p2.pop(0)
        elif int(p1[0][0]) < int(p2[0][0]):
            p1.pop(0)
        else:
            p2.pop(0)
    return answer


def intersect_many(terms, operators):
    """
    Merges several terms in a row applying operations
    :param terms: list of terms' postings
    :param operators: operators applied for each pair of terms
    :return: resulting posting with document ids
    """
    # terms = sorted(terms, key=lambda t: len(t))
    result = terms[0]
    terms.pop(0)
    while len(terms) > 0 and result != []:
        result = intersect(result, terms[0], operators[0])
        terms.pop(0)
        operators.pop()
    return result


def shunting_yard(query):
    """
    Parses query from infix notation into Reverse Polish notation which simplifies processing of the query
    :param query: list of operands and operators of the query expression
    :return: query in RPN
    """

    result = []
    operator_stack = []

    # while there are tokens in the query
    for token in query:
        if token == '(':
            operator_stack.append(token)

        elif token == ')':
            # popping all operators from operator stack onto output until left bracket is found
            operator = operator_stack.pop()
            while operator != '(':
                result.append(operator)
                try:
                    operator = operator_stack.pop()
                except IndexError:
                    return {'error_message': "Missing opening bracket '('. Please, try again."}

        elif token in OPERATORS:
            # popping operators from operator stack to result list if they are of higher precedence
            if operator_stack:
                current_operator = operator_stack[-1]
                while operator_stack and OPERATORS[current_operator] > OPERATORS[token]:
                    result.append(operator_stack.pop())
                    if operator_stack:
                        current_operator = operator_stack[-1]

            operator_stack.append(token)  # add token to stack

        else:
            # adding operands to the result list
            result.append(preprocess_word(token, stem=False))

    while operator_stack:
        # popping all operators into the result list
        result.append(operator_stack.pop())

    return result


def boolean_retrieval(docs, index, query):
    """
    Boolean Retrieval search.
    :param docs: dictionary of documents on which search is being applied
    :param index: index built for the documents collection
    :param query: list of query tokens
    :return: ids of found documents or an error message
    """

    # filling query with 'OR' operation between terms without any operation
    i, length = 0, len(query)
    while i < length - 1:
        if query[i] not in OPERATORS and query[i + 1] not in OPERATORS:
            query.insert(i + 1, "OR")
            length += 1
        i += 1

    # changing notation of the query
    query = shunting_yard(query)

    # checking if any errors have occurred
    if 'error_message' in query:
        error_message = query['error_message']
        return {'error_message': error_message}

    # print(query)

    results_stack = []
    while query:
        token = query.pop(0)
        result = []

        # retrieving posting for the term
        if token not in OPERATORS:
            result = index[token]

        try:
            # applying 'AND'/'OR' operation for two terms
            if token == 'AND' or token == 'OR':
                result = intersect(results_stack.pop(), results_stack.pop(), token)

            # applying 'NOT' operation for the term
            if token == 'NOT':
                term = results_stack.pop()
                for docid in docs:
                    if docid not in term:
                        result.append(docid)
        except IndexError:
            error_message = "Query is not correct. Modify it by adding/removing operators 'AND'/'OR'/'NOT'"
            return {'error_message': error_message}

        results_stack.append(result)

    if len(results_stack) != 1:
        error_message = "Query is not correct. Modify it by adding/removing operators 'AND'/'OR'/'NOT'"
        return {'error_message': error_message}

    results = []
    for docid in results_stack.pop():
        results.append((docid, 'N/A'))

    return results


def ranked_retrieval(docs, index, query):
    """
    Ranked Retrieval search.
    :param docs: dictionary of documents on which search is being applied
    :param index: index built for the documents collection
    :param query: list of query tokens
    :return: ids of found documents with scores or an error message
    """

    query.sort()

    ndocs = len(docs)
    scores = {}

    # preprocessing query terms and computing tf values
    query_terms = {}
    for token in query:
        token = preprocess_word(token, stem=False)
        if token not in query_terms:
            query_terms[token] = 1.0
        else:
            query_terms[token] += 1.0

    # computing tf-idf values for query terms and query length
    query_weights = {}
    query_length = 0.0
    for term, tf in query_terms.items():
        ltf = 1 + math.log10(tf)
        df = len(index[term])
        idf = math.log(ndocs / df)

        query_weights[term] = ltf * idf
        query_length += math.pow(query_weights[term], 2)

    query_length = math.sqrt(query_length)

    # computing normalized term weights
    for term, w in query_weights.items():
        query_weights[term] = w / query_length

    # print(query_weights, query_length)

    # computing cosine scores for each document that contains at least one term from the query
    for term, w in query_weights.items():
        posting = index[term]
        for docid, tf in posting.items():
            ltf = 1 + math.log10(int(tf))
            if docid not in scores:
                scores[docid] = w * ltf
            else:
                scores[docid] += w * ltf

    scores = list(scores.items())

    # scores.sort(key=lambda score: score[1], reverse=True)
    # print(scores)

    # normalizing cosine scores by document length
    for i in range(len(scores)):
        scores[i] = (scores[i][0], scores[i][1] / docs[scores[i][0]]['length'])

    scores.sort(key=lambda score: score[1], reverse=True)
    # print(scores)

    # results = []
    # for i in range(min(20, len(scores))):
    #     results.append(scores[i])

    return scores


def search(docs, index, query, rankedmode=True):
    """
    Main function of search engine. Searches documents according to the query
    :param docs: dictionary of documents on which search is being applied
    :param index: index built for the documents collection
    :param query: string value on which search is being applied
    :return:
    """

    # query modification
    init_query = query
    query = query.replace('(', '( ').replace(')', ' )').split()

    # empty query
    if not query:
        return {}

    # searching for unknown terms in the query
    unknown_terms = []
    for word in list(query):
        if preprocess_word(word, stem=False) not in index and word not in OPERATORS:
            unknown_terms.append(word)

    if unknown_terms and not rankedmode:
        error_message = "Query contains unknown term(s): {}. Please, try again".format('and '.join(unknown_terms))
        return {'error_message': error_message}

    if rankedmode:
        query = [token for token in query if token not in unknown_terms and token not in OPERATORS]
        results = ranked_retrieval(docs, index, query)
    else:
        results = boolean_retrieval(docs, index, query)

    if 'error_message' in results:
        return results

    with open('../results/lastqueryids.txt', 'w+') as f:
        f.write('Query: "%s"\n' % init_query)

        if rankedmode:
            outresults = results[:20]
            f.write("Mode: Ranked Retrieval\n")
            f.write("Found: %d documents\n" % len(results))
            f.write("Top %d documents with scores: \n\n" % len(outresults))
        else:
            outresults = results
            f.write("Mode: Boolean Retrieval\n")
            f.write("Found: %d documents\n\n" % len(results))

        rank = 1
        for doc in outresults:
            if rankedmode:
                f.write("%2d. " % rank)
                f.write('%4s (%.5s)\n' % (doc[0], doc[1]))
                rank += 1
            else:
                f.write('%s ' % doc[0])

    with open('../results/lastquery.txt', 'w+') as f:
        f.write('Query: "%s"\n' % init_query)

        if rankedmode:
            outresults = results[:20]
            f.write("Mode: Ranked Retrieval\n")
            f.write("Found: %d documents\n" % len(results))
            f.write("Top %d documents with scores: \n\n" % len(outresults))
        else:
            outresults = results
            f.write("Mode: Boolean Retrieval\n")
            f.write("Found: %d documents\n\n" % len(results))

        rank = 1
        for doc in outresults:
            if rankedmode:
                f.write("%d. " % rank)
                rank += 1
            f.write("Document %s " % doc[0])
            if rankedmode:
                f.write("(%.5s)" % doc[1])
            f.write("\n")
            f.write(docs[doc[0]]['title'] + "\n" + docs[doc[0]]['content'])
            f.write("********************************************\n")

    return {'results': results}
