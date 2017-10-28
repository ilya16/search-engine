# Search Engine based on Boolean Retrieval Model
This is a Python implementation of search engine. Index file is built using LISA documents collection and search is based on Boolean Retrieval Model. Search queries support operators `AND`, `OR`, `NOT`, `(` and `)`.

## Installation:
1. Make sure you have a `Python 3` interpreter on your machine. The preferable version is `Python 3.6`, because solution was tested on this version.
2. Install [`nltk`](http://www.nltk.org/) library if you haven't got it on your machine. One way of doing it is running in terminal: `sudo pip3 install -U nltk`
3. Clone the repository by running in terminal 
`git clone https://github.com/ilya16/search-engine` 
or download the archive with the system by following the link [`https://goo.gl/m8yT9q`](https://goo.gl/m8yT9q)
4. In terminal go to the directory with the unzipped solution using `cd` command and then execute `cd src`

    Application supports two modes: GUI and Console.
    
    GUI mode is run by executing `python app.py`
    
    Console mode is run by executing `python app.py console`
    
    Console mode with Boolean Retrieval is run by executing `python app.py console bool`
5. If previous steps are completed without any errors, application should run in one-two seconds. If there is no file `results/indexfile`, index will be built from scratch in up to 20 seconds.
