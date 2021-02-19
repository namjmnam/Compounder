# Compounder

## General info
This project aims to search compound words from various types of text sources
	
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
* csvreader.py (deprecated)
Gets texts from a column named NEWS_BODY from C:\comfinder\text.csv and saves it in C:\comfinder\inputDoc.txt
* compounder.py (deprecated)
Looks for compound words from C:\comfinder\inputDoc.txt and display on command line
* compounder-cli.py
Looks for compound words from a csv file, txt file or document string and saves it as a single txt file or prints results on command line
* wordsplitter.py
Splits words, not functional, under development

## Test Files (input)
* inputDoc.txt
* text.csv
