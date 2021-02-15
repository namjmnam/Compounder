# coding=UTF-8
import re
import pandas
# for reading CSV files.
# pip install pandas

class Reader:
    def __init__(self, inputPath, index=3):
        
        # This program tries to read CSV file and write into inputDoc.txt

        self.data = pandas.read_csv(inputPath)
        # self.data is the csv file with only NEW_BODY column
        self.masterString = self.corpusBuilder(self.data)
        # this is the collection of all docs from csv into one string

        txt = self.clean_str(self.readCSV(self.data, index))
        f = open("C:/comfinder/inputDoc.txt", 'w', encoding='utf8')
        f.write(txt)
        f.close()
        # print(txt)

        # print(self.corpusBuilder(self.data).count('SK네트웍스'))

    def readCSV(self, data, index):
        return data.at[index, 'NEWS_BODY']

    def clean_str(self, text):
        # text cleansing method
        # read the text file and make it into a string
        # original source: https://blog.naver.com/PostView.nhn?blogId=wideeyed&logNo=221347960543

        text = text.replace(u'\xa0', u' ')  # this is due to Latin1 ISO 8859-1
        text = text.strip()

        pattern = '([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)' # remove E-mail
        text = re.sub(pattern=pattern, repl=' ', string=text)
        pattern = '(http|ftp|https)://(?:[-\w.]|(?:%[\da-fA-F]{2}))+' # remove URL
        text = re.sub(pattern=pattern, repl=' ', string=text)
        pattern = '([ㄱ-ㅎㅏ-ㅣ]+)'  # remove singles
        text = re.sub(pattern=pattern, repl=' ', string=text)
        pattern = '<[^>]*>'         # remove HTML tags
        text = re.sub(pattern=pattern, repl=' ', string=text)
        pattern = '[^-/.\w\s]'         # remove special characters except for -/.
        text = re.sub(pattern=pattern, repl=' ', string=text)
            
        text = re.sub(r'(^[ \t]+|[ \t]+(?=:))', '', text, flags=re.M)
        text = text.replace('\n', ' ')
        text = text.replace('\t', ' ')
        text = text.replace('\r', ' ')
        text = re.sub(r'\b[0-9]+\b\s*', '', text)
        text = text.upper()

        while text.count('  ') != 0:
            text = text.replace('  ',' ')
        return text

    def corpusBuilder(self, csv):
        allrows = len(csv)
        out = ""
        for i in range(allrows):
            out += ' ' + self.clean_str(self.readCSV(csv, i))
        return out

path = "C:/comfinder/text.csv"
r = Reader(path)