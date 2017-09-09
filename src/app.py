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
        self.show_docids_btn = Button(self.tools_frame, text="Show all results", command=self.open_docidsfile)
        self.prev_res_btn = Button(self.tools_frame, text="Prev page")
        self.next_res_btn = Button(self.tools_frame, text="Next page")
        self.show_docs_btn = Button(self.tools_frame, text="Show all documents", command=self.open_docsfile)
        self.prev_doc_btn = Button(self.tools_frame, text="Prev doc")
        self.next_doc_btn = Button(self.tools_frame, text="Next doc")
        self.tip = Message(self.tools_frame, text="*click on the number in the results list to display the document")

        # defining positions and sizes of frames
        self.results_frame.place(x=20, y=80, width=760, height=200)
        self.tools_frame.place(x=610, y=80, width=180, height=200)

        # placing elements in frames
        self.search_input.place(x=95, y=20, width=500)
        self.search_btn.place(x=605, y=20, width=100)
        self.search_status.place(x=95, y=50, width=500)
        self.document.place(x=20, y=290, width=580, height=290)

        # setting actions for search button
        self.search_btn.bind("<Button-1>", self.process_input)
        self.search_input.bind("<Return>", self.process_input)

        # variables used to store intermediate data
        self.retrieved_docids = []
        self.current_docid_index = -1
        self.current_docid = -1
        self.links = {}

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

        # cleaning any previous results
        self.clean_env()

        # searching results for the query
        result = search(docs, index, query)

        if 'error_message' in result:
            self.status.set(result['error_message'])
        elif 'docids' in result:
            if len(result['docids']) > 0:
                # working with results
                self.status.set("Results found: " + str(len(result['docids'])))
                self.retrieved_docids = list(result['docids'])
                self.current_docid_index = 0

                # turning all necessary elements on
                self.tools_label.grid(row=0, column=0, columnspan=2, sticky="we")
                self.show_docids_btn.grid(row=1, column=0, columnspan=2, sticky="we")
                self.prev_res_btn.grid(row=2, column=0, sticky="we")
                self.next_res_btn.grid(row=2, column=1, sticky="we")
                self.show_docs_btn.grid(row=3, column=0, columnspan=2, sticky="we")
                self.prev_doc_btn.grid(row=4, column=0, sticky="we")
                self.next_doc_btn.grid(row=4, column=1, sticky="we")
                self.tip.grid(row=5, column=0, columnspan=2, sticky="we")

                # displaying results
                self.show_results(None, 0)
            else:
                self.status.set("Nothing found. Try another query")

    def show_results(self, event, page):
        """
        Showing results of the search on the main window
        :param page: current page of the results
        """
        docids = self.retrieved_docids

        # cleaning up previous results
        elems = self.results_frame.grid_slaves()
        for e in elems:
            e.destroy()
        self.links = {}

        # removing highlighting
        if self.links and int(self.current_docid) > 0:
            self.links[self.current_docid].config(bg="white")

        # showing docids for the current results page
        row, rows, column, columns = 1, 8, 1, 15
        items_number = rows * columns
        for docid in docids[page * items_number: min((page + 1) * items_number, len(self.retrieved_docids))]:
            link = Label(self.results_frame, text=docid, fg="blue", cursor="hand2", font=(None, 13))
            link.grid(row=row, column=column)
            link.bind("<Button-1>", lambda event, doc_id=docid: self.show_doc(event, doc_id))
            self.links[docid] = link
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

        if page < int(len(self.retrieved_docids) / items_number):
            self.next_res_btn.config(state="normal")
            self.next_res_btn.bind("<Button-1>", lambda event: self.show_results(event, page + 1))
        else:
            self.next_res_btn.config(state="disabled")
            self.next_res_btn.unbind("<Button-1>")

        self.show_doc(None, docids[self.current_docid_index])

    def show_doc(self, event, docid):
        """
        Showing content of the document
        :param docid: id of the document
        """

        # removing highlighting
        if self.current_docid in self.links:
            self.links[self.current_docid].config(bg="white")

        try:
            self.current_docid_index = self.retrieved_docids.index(docid)
        except ValueError:
            return

        # highlighting current document id
        self.current_docid = docid
        self.links[self.current_docid].config(bg="red")

        # configuring documents navigation buttons
        if self.current_docid_index > 0:
            self.prev_doc_btn.config(state="normal")
            self.prev_doc_btn.bind("<Button-1>",
                            lambda event: self.show_doc(event, self.retrieved_docids[self.current_docid_index - 1]))
        else:
            self.prev_doc_btn.config(state="disabled")
            self.prev_doc_btn.unbind("<Button-1>")

        if self.current_docid_index < len(self.retrieved_docids) - 1:
            self.next_doc_btn.config(state="normal")
            self.next_doc_btn.bind("<Button-1>",
                            lambda event: self.show_doc(event, self.retrieved_docids[self.current_docid_index + 1]))
        else:
            self.next_doc_btn.config(state="disabled")
            self.next_doc_btn.unbind("<Button-1>")

        txt = "Document " + docid
        txt += "\n" + docs[docid]['title'] + "\n" + docs[docid]['content']
        self.document.delete(1.0, END)
        self.document.insert(END, txt)

    def open_docsfile(self):
        os.system("open " + '../results/lastquery.txt')

    def open_docidsfile(self):
        os.system("open " + '../results/lastqueryids.txt')


if __name__ == '__main__':
    dictionary_file = postings_file = queries_file = output_file = None

    guimode = None
    if len(sys.argv) == 1:
        guimode = True
    elif sys.argv[1] == 'gui':
        guimode = False
    elif sys.argv[1] == 'console':
        guimode = False
    else:
        print("ERROR: Incorrect arguments supplied")
        print("Run either app.py or app.py console")
        sys.exit(2)

    docs = read_data()
    index = build_index(docs, from_dump=True)

    if guimode:
        gui = GUI()
    else:
        while True:
            print("Enter query: ", end="")
            result = search(docs, index, input())

            if 'error_message' in result:
                print("ERROR: " + result['error_message'])
            elif 'docids' in result:
                if len(result['docids']) > 0:
                    # working with results
                    print("Results found: " + str(len(result['docids'])))
                    print(">to show all document ids type 'ids'")
                    print(">to show all documents type 'docs'")
                    print(">to write another query type anything else")
                    txt = input()
                    if txt == 'ids':
                        for docid in result['docids']:
                            print(docid, end=" ")
                        print()
                    elif txt == 'docs':
                        os.system("open " + '../results/lastquery.txt')
                else:
                    print("Nothing found. Try another query")
