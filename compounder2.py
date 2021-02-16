# coding=UTF-8
import math
import kss
from eunjeon import Mecab
import re
import pandas

class Corpus:
    def __init__(self, inputPath, outputPath, index=3, words=2, standard=0.3):

        # CVS파일에서 복합단어를 추출
        # 파이썬 버전 3.6
        # 설치할 패키지: kss, eunjeon or konlpy

        self.data = pandas.read_csv(inputPath)
        txt = self.clean_str(self.readCSV(self.data, index))
        # CSV 파일을 호출해서 행 번호(index)에 있는 값을 txt에 저장

        self.target = self.clean_str(txt)
        tokenizer = Mecab()
        self.nouns = tokenizer.nouns(self.target)
        self.sList = kss.split_sentences(self.target)
        self.fList = self.nounExt(self.sList)
        # txt에 포함된 모든 명사를 mecab을 이용하여 추출 후 문장별로 나눈 리스트

        self.nOfWords = words
        # 복합단어를 이룰 단어의 갯수
        self.df = 0.85
        # 제동변수
        self.defIteration = 10
        # 텍스트랭크 이터레이션 수

        self.masterList = []
        for i in self.fList:
            self.masterList += i
        self.masterList = list(dict.fromkeys(self.masterList))

        self.allCW = []
        for i in range(len(self.fList)):
            n = self.genCW(self.fList[i])
            for j in n:
                if self.searchImproved(j, self.target) > 1 and j not in self.allCW:
                    self.allCW.append(j)

        self.finaldict = []
        finallist = []
        trdic = self.calculateTR(self.masterList, self.fList, self.defIteration)

        pmilist = []
        for i in self.allCW:
            pmilist.append(self.getPMI(i, self.nouns, self.target))

        for i in range(len(self.allCW)):
            k = self.allCW[i]
            key = 1
            for j in k:
                key *= trdic[j]
            key **= (1 / len(k))
            key *= pmilist[i]
            finallist.append(key)

        gluedCW = []
        for i in self.allCW:
            gluedCW.append(''.join(i))
            
        self.finaldict = dict(zip(gluedCW, finallist))

        out = []
        for i in self.finaldict.items():
            if i[1] > standard:
                out.append(i[0])

        if len(out) > 0:
            f = open(outputPath, 'a', encoding='utf8')
            print(out)
            f.write('\n'.join(out))
            f.write("\n")
            f.close()

    def nounExt(self, sentList):
        # tokenizer = Mecab(dicpath='C:/mecab/mecab-ko-dic')
        tokenizer = Mecab()
        n = []
        for i in sentList:
            n.append(tokenizer.nouns(i))
        return n

    def genCW(self, wList):
        # 단어 리스트를 받아 붙어있는 복합단어를 모두 종합하여 리스트로 출력
        out = []
        wordpair = []
        for i in range(len(wList) - self.nOfWords + 1):
            for j in range(i, i + self.nOfWords):
                wordpair.append(wList[j])
            out.append(wordpair)
            wordpair = []
        return out

    def search(self, word, target):
        out = target.count(word)
        return out

    def per(self, n):
        out = []
        for i in range(1<<n-1):
            s=bin(i)[2:]
            s='0'*(n-1-len(s))+s
            coms = []
            for i in list(s):
                if i == '0': coms.append('')
                if i == '1': coms.append(' ')
            coms.append('')
            out.append(coms)
        return out

    def searchImproved(self, cList, target):
        # 리스트 형태의 복합단어를 문서 전체에서 검색
        out = 0
        spaces = self.per(len(cList))
        cwList = []
        for i in range(len(spaces)):
            w = ''
            for j in range(len(cList)):
                w += cList[j]
                w += spaces[i][j]
            cwList.append(w)
        for i in cwList:
            out += target.count(i)
        return out

    def getPMI(self, wordpair, nouns, target):
        # 리스트 형태의 복합단어를 문서 전체에 대해서 PMI 계산
        wTotal = len(nouns)
        numerator = self.searchImproved(wordpair, target) / wTotal
        # 분자 = p(w1,w2)
        denominator = 1
        for i in wordpair:
            denominator *= self.search(i, target) / wTotal
        # 분모 = p(w1) * p(w2) * ...
        pmi = math.log(numerator / denominator)
        return pmi


    def wordMapTo(self, word, map):
        # 입력된 단어에 간선으로 연결된 모든 단어를 리스트로 출력 (같은 문장에 등장하는 단어들)
        out = []
        for i in map:
            if word in i:
                for j in i:
                    if j not in out:
                        out.append(j)
        out.remove(word)
        return out
    
    def noOfConnections(self, word, map):
        # 입력단 단어에 간선으로 연결된 모든 단어 갯수 출력
        return len(self.wordMapTo(word, map))

    def calculateTR(self, wordList, map, iteration):
        # 모든 단어에 대해서 텍스트랭크를 입력된 이터레이션 만큼 계산하여 단어:TR의 사전으로 출력
        values = [1 / len(wordList)] * len(wordList)
        newValue = [0] * len(wordList)
        node = dict(zip(wordList, values))

        for _ in range(iteration):
            for i in range(len(wordList)):
                key = wordList[i]
                for j in self.wordMapTo(key, map):
                    newValue[i] += node[j] / self.noOfConnections(j, map)
            values = newValue
            newValue = [0] * len(wordList)
            node = dict(zip(wordList, values))

        for i in range(0, len(values)):
            values[i] = (1-self.df) + self.df * values[i]
        node = dict(zip(wordList, values))
        # 제동변수 계산
        return node
    
    def totalDocs(inputPath):
        # 입력된 CSV 파일의 행의 갯수
        return len(pandas.read_csv(inputPath))

    def readCSV(self, data, index):
        return data.at[index, 'NEWS_BODY']

    def clean_str(self, text):
        # 텍스트 클렌징
        text = text.replace(u'\xa0', u' ')
        text = text.strip()

        pattern = '([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
        text = re.sub(pattern=pattern, repl=' ', string=text)
        pattern = '(http|ftp|https)://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        text = re.sub(pattern=pattern, repl=' ', string=text)
        pattern = '([ㄱ-ㅎㅏ-ㅣ]+)'
        text = re.sub(pattern=pattern, repl=' ', string=text)
        pattern = '<[^>]*>'
        text = re.sub(pattern=pattern, repl=' ', string=text)
        pattern = '[^-/.\w\s]'
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

csvFile = "C:/comfinder/text.csv"
outputFile = "C:/comfinder/output.txt"
sortedOutputFile = "C:/comfinder/sortedoutput.txt"

f = open(outputFile, 'w', encoding='utf8')
f.write("")
f.close()
# 출력 파일 초기화

for i in range(Corpus.totalDocs(csvFile)):
    c = Corpus(csvFile, outputFile, i)

f = open(sortedOutputFile, 'w', encoding='utf8')
f.write("")
f.close()
# 정리된 출력 파일 초기화

lines_seen = set()
outfile = open(sortedOutputFile, "w")
for line in open(outputFile, "r", encoding='utf8'):
    if line not in lines_seen: # not a duplicate
        outfile.write(line)
        lines_seen.add(line)
outfile.close()
# 출력 파일을 정리하여 출력