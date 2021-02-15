# Compounder

## General info
This project aims to search 
	
## Compatibility
* Python version: 3.6
	
## Setup
It is highly recommended to use Visual Studio Code with Anaconda. (This can be a bit difficult at first)
Set up your own conda env with Python version 3.6.

```
pip install eunjeon
pip install kss
pip install pandas
C:
mkdir comfinder
```

## How to use each scripts
* autoextractor.py
Extracts text from online article(URL) and saves in C:\comfinder\inputDoc.txt 
* compounder.py
Looks for compound words from C:\comfinder\inputDoc.txt and display on command line
* csvreader.py
Gets texts from a column named NEWS_BODY from C:\comfinder\text.csv and saves it in C:\comfinder\inputDoc.txt
* wordsplitter.py
Splits words, still in development

Rest aren't really used
