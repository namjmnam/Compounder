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
* csvreader.py (deprecated)
Gets texts from a column named NEWS_BODY from C:\comfinder\text.csv and saves it in C:\comfinder\inputDoc.txt
* compounder.py (deprecated)
Looks for compound words from C:\comfinder\inputDoc.txt and display on command line
* compounder2.py
Looks for compound words from C:\comfinder\text.csv and saves it in C:\comfinder\output.txt and C:\comfinder\sortedoutput.txt
* wordsplitter.py
Splits words, still in development

Rest aren't really used
