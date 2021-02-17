# coding=UTF-8
import math
import kss
from eunjeon import Mecab
import re
import pandas

class Corpus:
    def __init__(self, inputPath, outputPath, index=3, words=2, standard=0.3):

        # CSV, TXT 파일, 또는 기사 원문에서 복합단어를 추출
        # 파이썬 버전 3.6
        # 설치할 패키지: kss, eunjeon, pandas
        # 차후 eunjeon에서 konlpy로 이전 예정

        # 입력변수
        # inputPath: CSV 또는 TXT 파일의 위치 (너무 길 경우 원문 스트링으로 인식하여 분석)
        # outputPath: 출력할 텍스트 파일의 위치
        # index: CSV 테이블에서 불러올 텍스트의 행 번호
        # words: 복합단어를 이루는 단어 갯수 (기본:2)
        # standards: 요구사항을 충족하는 TR+PMI 점수의 최소치 (임시:0.3)

        if len(inputPath) > 50: self.data = inputPath
        else: self.data = self.extractText(inputPath)
        txt = self.clean_str(self.readValue(self.data, index))
        # CSV 파일을 호출해서 행 번호(index)에 있는 값을 TXT에 저장
        # inputPath가 길 경우 원문으로 인식

        self.target = self.clean_str(txt)
        # m = Mecab(dicpath='C:/mecab/mecab-ko-dic')
        m = Mecab()
        self.wTotal = len(m.nouns(self.target))
        self.fList = self.nounExt(kss.split_sentences(self.target))
        self.mList = list(dict.fromkeys([item for sublist in self.fList for item in sublist]))
        # target = "문서전체내용"
        # wTotal = (int)문서 내 명사 갯수
        # fList = [["문장1명사1", "문장1명사2", ...], ["문장2명사1", "문장2명사2", ...], ...]
        # mList = ["문장1명사1", "문장1명사2", ..., "문장2명사1", "문장2명사2" ...] 중복 제거

        self.nOfWords = words
        # 복합단어를 이룰 단어의 갯수
        self.df = 0.85
        # 제동변수
        self.defIteration = 16
        # 텍스트랭크 이터레이션 수 (임시:16)

        self.allCW = []
        for i in range(len(self.fList)):
            n = self.genCW(self.fList[i])
            for j in n:
                if self.searchSpaceless(j, self.target) > 1 and j not in self.allCW:
                    self.allCW.append(j)

        self.finaldict = []
        finallist = []
        trdic = self.calculateTR(self.mList, self.fList, self.defIteration)

        pmilist = []
        for i in self.allCW:
            pmilist.append(self.getPMI(i, self.wTotal, self.target))

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
        # CSV가 아닐 경우 TXT로 취급
        if inputPath[-4:] != ".csv":
            f = open(inputPath, 'r', encoding='utf8')
            out = f.read()
            f.close()
            return out
        return pandas.read_csv(inputPath, encoding='utf8')

    def nounExt(self, sentList):
        # m = Mecab(dicpath='C:/mecab/mecab-ko-dic')
        m = Mecab()
        out = []
        for i in sentList:
            out.append(m.nouns(i))
        return out

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

        # 본문에서 띄어쓰기를 제외한 채로 검색할 경우:
        # return target.replace(' ','').count(''.join(cList))

        # 본문에서 띄어쓰기를 제외하지 않은 채로 검색할 경우:
        return target.count(''.join(cList))

    def getPMI(self, wordpair, wordcount, target):
        # 리스트 형태의 복합단어를 문서 전체에 대해서 PMI 계산
        numerator = self.searchSpaceless(wordpair, target) / wordcount
        # 분자 = p(w1, w2, ...)
        denominator = 1
        for i in wordpair:
            denominator *= target.count(i) / wordcount
        # 분모 = p(w1) * p(w2) * ...
        pmi = math.log(numerator / denominator)
        return pmi

    def wordMapTo(self, word, map):
        # 입력된 단어에 간선으로 연결된 모든 단어를 리스트로 출력 (같은 문장에 등장하는 단어들)
        out = []
        for i in map:
            # 문장별 반복작업
            if word in i:
                for j in i:
                    # j가 word에서부터 몇 단어 이내로 떨어진 경우에만 추가하는 방식 검토 중
                    out.append(j)
                    # 같은 단어가 여러 번 등장할 경우 중복으로 입력 -> 간선의 가중치가 증가
        # out = list(dict.fromkeys(out))
        # 중복을 제거하여 가중치를 배제
        out = list(filter(lambda a: a != word, out))
        return out
    
    def nOfConnections(self, word, map):
        # 입력단 단어에 간선으로 연결된 모든 단어 갯수 출력
        return len(self.wordMapTo(word, map))

    def calculateTR(self, wordList, map, iteration):
        # 모든 단어에 대해서 텍스트랭크를 입력된 이터레이션 만큼 계산하여 단어:TR의 사전으로 출력
        values = [1 / len(wordList)] * len(wordList)
        newValues = [0] * len(wordList)
        node = dict(zip(wordList, values))

        for _ in range(iteration):
            for i in range(len(wordList)):
                key = wordList[i]
                if self.wordMapTo(key, map) == []: newValues[i] = values[i]
                for j in self.wordMapTo(key, map):
                    # TR을 간선으로부터 끌어모으는 방식:
                    # newValues[i] += node[j] / self.nOfConnections(j, map)
                    # TR을 간선을 통해 분배하는 방식:
                    newValues[wordList.index(j)] += node[key] / self.nOfConnections(key, map)
            values = newValues
            newValues = [0] * len(wordList)
            node = dict(zip(wordList, values))

        for i in range(0, len(values)):
            values[i] = (1-self.df) + self.df * values[i]
        node = dict(zip(wordList, values))
        # 제동변수 계산
        return node
    
    def totalDocs(inputPath):
        # 입력된 CSV 파일의 행의 갯수 (정적 메소드) 
        if inputPath[-4:] != ".csv": return 1
        # 입력된 파일이 CSV가 아닐 경우 TXT로 취급하여 1회 실행 유도
        return len(pandas.read_csv(inputPath))

    def readValue(self, data, index):
        # CSV가 아닐 경우 입력된 값 그대로 리턴
        if isinstance(data, str): return data
        # NEWS_BODY 열이 없을 경우
        if "NEWS_BODY" not in data.columns:
            l = data.loc[index].tolist()
            l = [str(i) for i in l]
            long = max(l, key=len)
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

inputFile = r"C:/comfinder/text.csv"
# inputFile = r"C:/comfinder/inputDoc.txt"
# inputFile = r"박수현 이낙연 지지 율 하락 빚 청구서. 더불어 민주당 박수현 홍보소통 위원장 왼쪽 이낙연 대표. 사진 국회 의원 선거 운동 당시 이낙연 더불어민주당 상임공동선대위원장 박수현 공주시부여군청양군 후보의 지지를 호소하고 있는 모습. 박수현 더불어민주당 홍보소통위원장은 일 오는 월 임기 종료를 앞둔 이낙연 대표를 향해 대표로서 역대급 성과를 냈는데도 지지율이 하락하는 것을 섭섭해할 이유는 없다며 지지율 하락은 그 빚을 제대로 갚으라는 청구서라고 지적했다. 그러면서도 그동안 입법으로 성과를 말했고 개월이라는 짧은 시간에 그 목표를 달성했다고 했다. 박 위원장은 이날 오전 자신의 페이스북 글을 통해 이 대표는 년 월 대표 취임 이후 개월간 민주당을 이끌어왔다며 당 대표 출마를 선언할 때부터 개월짜리 대표란 꼬리표를 달고 시작을 했기 때문에 이 대표가 대표로서 활동할 시간도 개월밖에 남지 않은 셈이라고 했다. 그는 대권이라는 개인의 정치 목표 때문에 개월짜리 당대표가 된 것은 분명 빚이고 기꺼이 빚을 내어주신 국민과 당과 당원께 진 이 대표의 빚은 결코 작지 않다고 했다. 박 위원장은 이어 년 총선에서 민주당은 석이라는 역사상 유례가 없는 슈퍼정당을 만들었다. 이 대표는 취임 이후 당원들의 열망에 화답하듯 여러 개혁 민생 법안 처리를 이끌었다며 공수처법 개정안 등 권력기관 개혁 법안 공정경제 법 지방자치법 관련 법 법제화 등의 성과를 거론했다. 이뿐만 아니라 여건이 넘는 법안을 처리하며 슈퍼정당의 위력을 보여줬다고 덧붙였다. 박 위원장은 그러면서 개월간 수많은 개혁 민생 법안을 통과시켰음에도 개혁을 열망하는 국민과 당원은 아직도 목이 마르다며 마지막 남은 당대표 개월 당과 당원에게 빚을 갚아야 한다고 했다. 박 위원장은 지난 개월의 성과는 역대 어느 대표와도 견줄 수 없는 역대급이나 이 역시 거대여당을 만들어 준 국민과 당원에게 진 빚이라고 강조했다. 그러면서 개월 시한부 당 대표라는 꼬리표가 더 이상 꼬리표가 아닌 마침표가 될 수 있도록 남은 개월 동안 대한민국 개혁과 민주당 역사에 큰 방점을 찍어주길 바란다며 그것이 국민과 당과 당원에 진 빚을 갚는 유일한 길이라고 덧붙였다."
outputFile = r"C:/comfinder/output.txt"
sortedOutputFile = r"C:/comfinder/sortedoutput.txt"
# 입출력 파일 위치 선언

f = open(outputFile, 'w', encoding='utf8')
f.write("")
f.close()
# 출력 파일 초기화

iterNum = Corpus.totalDocs(inputFile)
# iterNum = 10
# iterNum = 50
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
