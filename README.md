# Compounder

## General info
This project aims to search compound words and new words from various types of text sources
	
## Compatibility
* Python version: 3.6
	
## Setup
It is highly recommended to use Visual Studio Code with Anaconda. (This can be a bit difficult at first)
Set up your own conda env with Python version 3.6.

```
pip install eunjeon
pip install kss
pip install pandas
```

## How to use each scripts
* compounder.py
Looks for compound words from a csv file, txt file or document string and saves it as a single txt file or prints results on command line
* wordsplitter.py
Searches for possible new words in a string of a document.
* simplersplitter.py
Attempts to generate a list of nouns and compound words composed of the found nouns independent from Mecab.

## Test Files (input)
* inputDoc.txt
* text.csv
