# coding=UTF-8
import re
# for text cleansing

import sys
platform = sys.platform
if platform.startswith('win32'):
    from eunjeon import Mecab # type: ignore
    # pip install eunjeon
elif platform.startswith('linux') or platform.startswith('darwin'):
    from konlpy.tag import Mecab # type: ignore
    # pip install konlpy
else:
    raise NotImplementedError
# for extracting nouns

class Splitter:
    def __init__(self, inputPath, inputCorpus=None):
        
        # This program attempts to find new nouns
        # Works best with python version 3.6
        # Need to implement Corpus input and put it together into one string, or find other way to search the corpus

        self.doc = self.clean_str(inputPath)
        # doc is the whole document
        self.corpus = self.doc
        # Corpus input is not yet establishsed
        l = self.doc.split(' ')
        self.eoList = [i for i in l if len(re.sub(r'[0-9]+', '-', i)) >= 4]
        # eoList is the list of all eojeols that is longer than 3 letters while counting digits as one letter 
        # print(self.eoList)

        # print(self.splitEojeol(self.eoList[1]))
        # print(self.splitEojeol(self.eoList[1])[1])
        # print(self.splitEojeol(self.eoList[1])[1][1])
        # print(self.splitWays(self.splitEojeol(self.eoList[1])[1][1]))
        # for i in self.splitWays(self.splitEojeol(self.eoList[1])[1][1]):
        #     print(i.split(" "))

    def clean_str(self, inputPath):
        # text cleansing method
        # read the text file and make it into a string
        text = open(inputPath, 'rt', encoding='UTF8').read().replace('\n',' ')
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

    def splitEojeol(self, eojeol):
        # this method splits eojeol to all possible combinations(more than one letter) to be checked by Mecab
        # should counts digits, alphabets, and symbols as one character?
        # also watches out for Unknown tags, multiple tags, 감탄사tag, 부호tags, 한글이외tags?
        out = []
        m = Mecab()
        # If possibly, Mecab(dicpath='C:/mecab/mecab-ko-dic') but not working at the moment
        for i in range(len(eojeol)):
            for j in range(len(eojeol)-i):
                k = eojeol[i:j+i+1]
                if len(k)>1 and len(m.pos(k))>1:
                    # out.append([k, i, j])
                    out.append([k, eojeol[i+j+1:]])
                elif len(k)>1 and (m.pos(k)[0][1] == 'SL' or m.pos(k)[0][1] == "UNKNOWN" or m.pos(k)[0][1] == "IC" or m.pos(k)[0][1].count("+")>0):
                    # out.append([k, i, j])
                    out.append([k, eojeol[i+j+1:]])
                # print(k)
                # print(eojeol[i+j+1:])
                # The string above is the rest of the right part
        # print(out)
        return out
        # outputs all combinations that is not recognized by Mecab along with coordiates of start and end of substring

    def per(self, n):
        # original code: https://stackoverflow.com/questions/17656825/python-replacing-characters-in-a-list
        # n is the number of words
        out = []
        for i in range(1<<n-1):
            s=bin(i)[2:]
            s='0'*(n-1-len(s))+s
            # s = s.replace('0','').replace('1',' ')
            coms = []
            for i in list(s):
                if i == '0': coms.append('')
                if i == '1': coms.append(' ')
            coms.append('')
            # print(coms)
            out.append(coms)
            # coms is the possible space allocation after nth word
        return out
        # out is list of all possible coms

    def splitWays(self, text):
        # this method lists possible ways to split a string into many words
        n = len(text)
        out = []
        for i in range(len(self.per(n))):
            w = ""
            for j in range(n):    
                w += text[j]+self.per(n)[i][j]
            out.append(w)
        # print(out)
        # print(len(out))
        return out

    def splitKRP(self, text):
        # this method outputs all possible combinations of a text
        pass

path = "C:/comfinder/inputDoc.txt"
s = Splitter(path)