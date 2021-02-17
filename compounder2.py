# coding=UTF-8
import math
import kss
from eunjeon import Mecab
import re
import pandas

class Corpus:
    def __init__(self, inputPath, outputPath, index=3, words=2, standard=0.3):

        # CVS 또는 TXT 파일에서 복합단어를 추출
        # 파이썬 버전 3.6
        # 설치할 패키지: kss, eunjeon or konlpy

        # 입력변수
        # inputPath: CSV 또는 TXT 파일의 위치
        # outputPath: 출력할 텍스트 파일의 위치
        # index: CSV 테이블에서 불러올 텍스트의 행 번호
        # words: 복합단어를 이루는 단어 갯수 (기본:2)
        # standards: 요구사항을 충족하는 TR+PMI 점수의 최소치 (기본:0.3)

        self.data = self.extractText(inputPath)
        txt = self.clean_str(self.readValue(self.data, index))
        # CSV 파일을 호출해서 행 번호(index)에 있는 값을 txt에 저장

        self.target = self.clean_str(txt)
        tokenizer = Mecab()
        self.nouns = tokenizer.nouns(self.target)
        self.sList = kss.split_sentences(self.target)
        self.fList = self.nounExt(self.sList)
        # txt에 포함된 모든 명사를 mecab을 이용하여 추출 후 문장별로 나눈 리스트
        # target = "문서전체내용"
        # nouns = ["명사1", "명사2", "명사3", ...]
        # sList = ["문장1", "문장2", "문장3", ...]
        # fList = [["문장1명사1", "문장1명사2", ...], ["문장2명사1", "문장2명사2", ...], ...]

        self.nOfWords = words
        # 복합단어를 이룰 단어의 갯수
        self.df = 0.85
        # 제동변수
        self.defIteration = 16
        # 텍스트랭크 이터레이션 수 (임시=16)

        self.masterList = []
        for i in self.fList:
            self.masterList += i
        self.masterList = list(dict.fromkeys(self.masterList))

        self.allCW = []
        for i in range(len(self.fList)):
            n = self.genCW(self.fList[i])
            for j in n:
                if self.searchSpaceless(j, self.target) > 1 and j not in self.allCW:
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
        # 텍스트 파일로 출력

    def extractText(self, inputPath):
        # CSV가 아닐 경우 txt로 취급
        if inputPath[-4:] != ".csv":
            f = open(inputPath, 'r', encoding='utf8')
            out = f.read()
            f.close()
            return out
        return pandas.read_csv(inputPath)

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

    def searchSpaceless(self, cList, target):
        # 리스트 형태의 복합단어를 문서 전체에서 검색
        return target.count(''.join(cList))

    def getPMI(self, wordpair, nouns, target):
        # 리스트 형태의 복합단어를 문서 전체에 대해서 PMI 계산
        wTotal = len(nouns)
        numerator = self.searchSpaceless(wordpair, target) / wTotal
        # 분자 = p(w1, w2, ...)
        denominator = 1
        for i in wordpair:
            denominator *= target.count(i) / wTotal
        # 분모 = p(w1) * p(w2) * ...
        pmi = math.log(numerator / denominator)
        return pmi

    def wordMapTo(self, word, map):
        # 입력된 단어에 간선으로 연결된 모든 단어를 리스트로 출력 (같은 문장에 등장하는 단어들)
        out = []
        for i in map:
            # 문장별
            if word in i:
                for j in i:
                    # if j not in out:
                    #     # 중복을 방지하여 간선의 가중치를 배제하는 방식
                    #     out.append(j)
                    out.append(j)
                    # 같은 단어가 여러 번 등장할 경우 간선의 가중치가 증가하는 방식
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
        # 입력된 CSV 파일의 행의 갯수 (정적 메소드) 
        if inputPath[-4:] != ".csv": return 1
        # 입력된 파일이 CSV가 아닐 경우 txt로 취급하여 1회 실행 유도
        return len(pandas.read_csv(inputPath))

    def readValue(self, data, index):
        # CSV가 아닐 경우 입력된 값 그대로 리턴
        if isinstance(data, str): return data
        # NEWS_BODY 열이 없을 경우
        if "NEWS_BODY" not in data.columns:
            long = max(data.loc[index].tolist(), key=len)
            return long
        # NEWS_BODY 열만 불러오기
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

inputFile = "C:/comfinder/text.csv"
# inputFile = "C:/comfinder/inputDoc.txt"
outputFile = "C:/comfinder/output.txt"
sortedOutputFile = "C:/comfinder/sortedoutput.txt"
# 입출력 파일 위치 선언

f = open(outputFile, 'w', encoding='utf8')
f.write("")
f.close()
# 출력 파일 초기화

iterNum = Corpus.totalDocs(inputFile)
# iterNum = 10
for i in range(iterNum):
    c = Corpus(inputFile, outputFile, i)
# CSV파일의 행 수 만큼 코드 실행

f = open(sortedOutputFile, 'w', encoding='utf8')
f.write("")
f.close()
# 정리된 출력 파일 초기화

lines_seen = set()
outfile = open(sortedOutputFile, "w")
for line in open(outputFile, "r", encoding='utf8'):
    if line not in lines_seen:
        outfile.write(line)
        lines_seen.add(line)
outfile.close()
# 출력 파일의 중복을 제거하여 따로 출력
