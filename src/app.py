from datareader import read_data
from indexer import build_index
from search import search
from tkinter import *
import os
import sys

class GUI:
    def __init__(self):
        # main window of the application interface
        self.root = Tk()
        self.root.title('Search Engine')
        self.root.geometry('800x600')
        self.root.resizable(0, 0)

        # frames used for displaying and managing search results
        self.results_frame = Frame(self.root)
        self.tools_frame = Frame(self.root)

        # search elements
        self.search_input = Entry(self.root, width=40)
        self.search_btn = Button(self.root, text="Search")
        self.status = StringVar()
        self.search_status = Label(self.root, textvariable=self.status, padx=20)
        self.document = Text(self.root, width=40, height=200)

        # search tools buttons
        self.tools_label = Label(self.tools_frame, text="Tools")
        self.rankedmode = BooleanVar()
        self.rankedmode.set(True)
        self.rankedmode_che = Checkbutton(self.tools_frame, text="Ranked Retrieval", variable=self.rankedmode,
                                          onvalue=True, offvalue=False)
        self.show_docids_btn = Button(self.tools_frame, text="Show all results", command=self.open_docidsfile,
                                      font=(None, 13, "bold"))
        self.prev_res_btn = Button(self.tools_frame, text="Prev page")
        self.next_res_btn = Button(self.tools_frame, text="Next page")
        self.show_docs_btn = Button(self.tools_frame, text="Show all documents", command=self.open_docsfile,
                                    font=(None, 13, "bold"))
        self.prev_doc_btn = Button(self.tools_frame, text="Prev doc")
        self.next_doc_btn = Button(self.tools_frame, text="Next doc")
        self.tip = Message(self.tools_frame, text="*click on the number in the results list to display the document")

        # defining positions and sizes of frames
        self.results_frame.place(x=20, y=80, width=760, height=200)
        self.tools_frame.place(x=610, y=80, width=180, height=240)

        # placing elements in frames
        self.search_input.place(x=95, y=20, width=500)
        self.search_btn.place(x=605, y=20, width=100)
        self.search_status.place(x=95, y=50, width=500)
        self.document.place(x=20, y=290, width=580, height=290)

        # setting actions for search button
        self.search_btn.bind("<Button-1>", self.process_input)
        self.search_input.bind("<Return>", self.process_input)

        # variables used to store intermediate data
        self.retrieved_docs = []
        self.current_docid_index = -1
        self.current_docid = -1
        self.links = {}
        self.query = ''

        # running main window
        self.root.mainloop()

    def clean_env(self):
        """
        Cleaning up the window from previous results
        """
        lst = self.results_frame.grid_slaves()
        for l in lst:
            l.destroy()
        self.tools_label.grid_remove()
        self.rankedmode_che.grid_remove()
        self.show_docids_btn.grid_remove()
        self.prev_res_btn.grid_remove()
        self.next_res_btn.grid_remove()
        self.show_docs_btn.grid_remove()
        self.prev_doc_btn.grid_remove()
        self.next_doc_btn.grid_remove()
        self.tip.grid_remove()
        self.document.delete(1.0, END)

    def process_input(self, event):
        """
        Processing input query
        """
        # getting input from user
        query = self.search_input.get()
        self.query = query

        # cleaning any previous results
        self.clean_env()

        # searching results for the query
        result = search(docs, index, query, rankedmode=self.rankedmode.get())

        if 'error_message' in result:
            self.status.set(result['error_message'])
        elif 'results' in result:
            if len(result['results']) > 0:
                # working with results
                if self.rankedmode.get():
                    self.status.set("Results found: %d. Showing TOP %d:"
                                    % (len(result['results']), len(result['results'][:20])))
                    self.retrieved_docs = result['results'][:20]
                else:
                    self.status.set("Results found: %d" % len(result['results']))
                    self.retrieved_docs = result['results']
                self.current_docid_index = 0

                # turning all necessary elements on
                self.tools_label.grid(row=0, column=0, columnspan=2, sticky="we")
                self.rankedmode_che.grid(row=1, column=0, columnspan=2, sticky="we")
                self.show_docids_btn.grid(row=2, column=0, columnspan=2, rowspan=2, sticky="we")
                self.prev_res_btn.grid(row=4, column=0, sticky="we")
                self.next_res_btn.grid(row=4, column=1, sticky="we")
                self.show_docs_btn.grid(row=5, column=0, columnspan=2, sticky="we")
                self.prev_doc_btn.grid(row=6, column=0, sticky="we")
                self.next_doc_btn.grid(row=6, column=1, sticky="we")
                self.tip.grid(row=7, column=0, columnspan=2, sticky="we")

                # displaying results
                self.show_results(None, 0)
            else:
                self.status.set("Nothing found. Try another query")

    def show_results(self, event, page):
        """
        Showing results of the search on the main window
        :param page: current page of the results
        """
        docs = self.retrieved_docs

        # cleaning up previous results
        elems = self.results_frame.grid_slaves()
        for e in elems:
            e.destroy()
        self.links = {}

        # removing highlighting
        if self.links and int(self.current_docid) > 0:
            self.links[self.current_docid].config(bg="white")

        # showing docids for the current results page
        if self.rankedmode.get():
            row, rows, column, columns = 1, 5, 1, 4
        else:
            row, rows, column, columns = 1, 8, 1, 15
        items_number = rows * columns

        rank = 1
        for doc in docs[page * items_number: min((page + 1) * items_number, len(self.retrieved_docs))]:
            docid = doc[0]
            score = doc[1]
            link_text = " " * (4 - len(docid))
            link_text += "%4d" % int(docid)
            if self.rankedmode.get():
                link_text = "%4d. " % rank + link_text
                rank += 1
                link_text += " (%.5s)" % score
            link = Label(self.results_frame, text=link_text, fg="blue", cursor="hand2", font=(None, 13))
            link.grid(row=row, column=column, sticky="e")
            link.bind("<Button-1>", lambda event, doc_=doc: self.show_doc(event, doc_))
            self.links[docid] = link

            if self.rankedmode.get():
                if row == rows:
                    column += 1
                    row = 1
                else:
                    row += 1
            else:
                if column == columns:
                    row += 1
                    column = 1
                else:
                    column += 1

        self.current_docid_index = page * items_number

        # configuring results navigation buttons
        if page > 0:
            self.prev_res_btn.config(state="normal")
            self.prev_res_btn.bind("<Button-1>", lambda event: self.show_results(event, page - 1))
        else:
            self.prev_res_btn.config(state="disabled")
            self.prev_res_btn.unbind("<Button-1>")

        if (page + 1) < len(self.retrieved_docs) / items_number:
            self.next_res_btn.config(state="normal")
            self.next_res_btn.bind("<Button-1>", lambda event: self.show_results(event, page + 1))
        else:
            self.next_res_btn.config(state="disabled")
            self.next_res_btn.unbind("<Button-1>")

        self.show_doc(None, docs[self.current_docid_index])

    def show_doc(self, event, doc):
        """
        Showing content of the document
        :param docid: id of the document
        """

        # removing highlighting
        if self.current_docid in self.links:
            self.links[self.current_docid].config(bg="white")

        try:
            self.current_docid_index = self.retrieved_docs.index(doc)
        except ValueError:
            return

        # highlighting current document id
        self.current_docid = doc[0]
        self.links[self.current_docid].config(bg="red")

        # configuring documents navigation buttons
        if self.current_docid_index > 0:
            self.prev_doc_btn.config(state="normal")
            self.prev_doc_btn.bind("<Button-1>",
                            lambda event: self.show_doc(event, self.retrieved_docs[self.current_docid_index - 1]))
        else:
            self.prev_doc_btn.config(state="disabled")
            self.prev_doc_btn.unbind("<Button-1>")

        if self.current_docid_index < len(self.retrieved_docs) - 1:
            self.next_doc_btn.config(state="normal")
            self.next_doc_btn.bind("<Button-1>",
                            lambda event: self.show_doc(event, self.retrieved_docs[self.current_docid_index + 1]))
        else:
            self.next_doc_btn.config(state="disabled")
            self.next_doc_btn.unbind("<Button-1>")

        txt = "Document %s" % doc[0]
        if self.rankedmode.get():
            txt += " (%.5s)" % doc[1]
        txt += "\n" + docs[doc[0]]['title'] + "\n" + docs[doc[0]]['content']
        self.document.delete(1.0, END)
        self.document.insert(END, txt)

        # highlighting search query terms in the document
        self.document.tag_config('query', background='yellow')
        query_tokens = self.query.split()
        for token in query_tokens:
            pos = '1.0'
            while True:
                keyword = r'' + token.upper() + '\W'
                idx = self.document.search(keyword, pos, END, regexp=True)
                if not idx:
                    break
                pos = '{}+{}c'.format(idx, len(token))
                self.document.tag_add('query', idx, pos)

    def open_docsfile(self):
        os.system("open " + '../results/lastquery.txt')

    def open_docidsfile(self):
        os.system("open " + '../results/lastqueryids.txt')


if __name__ == '__main__':
    guimode = None
    rankedmode = True

    if len(sys.argv) == 1:
        guimode = True
    elif sys.argv[1] == 'gui':
        guimode = True
    elif sys.argv[1] == 'console':
        guimode = False
        if len(sys.argv) == 3 and sys.argv[2] == 'bool':
            rankedmode = False
    else:
        print("ERROR: Incorrect arguments supplied")
        print("Run either 'app.py', 'app.py console' or 'app.py console bool'")
        sys.exit(2)

    docs = read_data()
    index = build_index(docs, from_dump=True)
    query = ''

    if guimode:
        gui = GUI()
    else:
        # console mode logic
        while True:
            if query == '':
                print('Enter query: ', end='')
                query = input()

            # termination condition of console mode
            if query == '\q':
                sys.exit(0)

            last_query = query

            result = search(docs, index, query, rankedmode=rankedmode)

            if 'error_message' in result:
                print("ERROR: %s" % result['error_message'])
            elif 'results' in result:
                if len(result['results']) > 0:
                    # working with results
                    if rankedmode:
                        outresults = result['results'][:20]
                        print("Found: %d documents" % len(result['results']))
                        print("Top %d documents with scores: \n" % len(outresults))
                    else:
                        outresults = result['results'][:20]
                        print("Results found: %d" % len(result['results']))

                    command = '\ids'
                    while command in ['\ids', '\docs', '\docsfile']:
                        if command == '\ids':
                            print('Document ids:')
                            rank = 1
                            for doc in outresults:
                                if rankedmode:
                                    print("%2d. " % rank, end='')
                                    print('%4s (%.5s)' % (doc[0], doc[1]))
                                    rank += 1
                                else:
                                    print('%s ' % doc[0])
                            print()
                        elif command == '\docs':
                            rank = 1
                            for doc in outresults:
                                if rankedmode:
                                    print("%d. " % rank, end='')
                                    rank += 1
                                print("Document %s " % doc[0], end='')
                                if rankedmode:
                                    print("(%.5s)" % doc[1], end='')
                                print("\n" + docs[doc[0]]['title'] + "\n" + docs[doc[0]]['content'], end='')
                                print("********************************************")
                            print()
                        elif command == '\docsfile':
                            os.system("open " + '../results/lastquery.txt')

                        print(">to display all document ids type '\ids'")
                        print(">to display all documents type '\docs'")
                        print(">to display all documents in a file type '\docsfile'")
                        print(">to write another query type anything else")
                        print(">to finish execution type '\q")

                        print('Enter query: ', end='')
                        command = input()
                    query = command
                else:
                    print("Nothing found. Try another query")
