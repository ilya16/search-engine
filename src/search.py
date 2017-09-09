from indexer import preprocess_word
import sys

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
    (currently suuports only 'AND' operation)
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
            result.append(preprocess_word(token, True))

    while operator_stack:
        # popping all operators into the result list
        result.append(operator_stack.pop())

    return result


def search(docs, index, query, guimode=True):
    """
    Main function of search engine. Searches documents according to the query
    :param docs: dictionary of documents on which search is being applied
    :param index: index built for the documents collection
    :param query: string value on which search is being applied
    :param guimode: mode of the application
    :return:
    """

    # query modification
    init_query = query
    query = query.replace('(', '( ').replace(')', ' )').split()

    # empty query
    if not query:
        return {}

    # termination condition of console mode
    if not guimode and query[0] == '\q':
        sys.exit(2)

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
        if guimode:
            return {'error_message': error_message}
        else:
            print("ERROR: " + error_message)

    # print(query)

    # searching for unknown terms in the query
    unknown_terms = []
    for word in list(query):
        if word not in index and word not in OPERATORS:
            unknown_terms.append(word)

    if unknown_terms:
        error_message = "Query contains unknown term(s): {}. Please, try again".format('and '.join(unknown_terms))
        if guimode:
            return {'error_message': error_message}
        else:
            print("ERROR: " + error_message)
            return

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
                left_term = results_stack.pop(0)
                right_term = results_stack.pop(0)
                result = intersect(left_term, right_term, token)

            # applying 'NOT' operation for the term
            if token == 'NOT':
                term = results_stack.pop(0)
                result = []
                for docid in docs:
                    if docid not in term:
                        result.append(docid)
        except IndexError:
            error_message = "Query is not correct. Modify it by adding/removing operators 'AND'/'OR'/'NOT'"
            if guimode:
                return {'error_message': error_message}
            else:
                print("ERROR: " + error_message)

        results_stack.append(result)

    if len(results_stack) != 1:
        error_message = "Query is not correct. Modify it by adding/removing operators 'AND'/'OR'/'NOT'"
        if guimode:
            return {'error_message': error_message}
        else:
            print("ERROR: " + error_message)
            return

    docids = results_stack.pop()

    with open('../results/lastqueryids.txt', 'w+') as f:
        f.write('Query: "' + init_query + '"\n')
        f.write("Found: " + str(len(docids)) + " documents\n")
        f.write("Document ids:\n\n")
        for docid in docids:
            f.write(docid + " ")

    with open('../results/lastquery.txt', 'w+') as f:
        f.write('Query: "' + init_query + '"\n')
        f.write("Found: " + str(len(docids)) + " documents\n")
        f.write("Documents:\n\n")
        for docid in docids:
            f.write("Document " + docid)
            f.write("\n" + docs[docid]['title'] + "\n" + docs[docid]['content'])
            f.write("********************************************\n")

    return {'docids': docids}
