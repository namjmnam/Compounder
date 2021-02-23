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
Searches for new words in a string of a document. Under development
* simplersplitter.py
Attempted to create a compound word generator independent from Mecab. Under development

## Test Files (input)
* inputDoc.txt
* text.csv
