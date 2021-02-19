# coding=UTF-8
import math
import kss
from eunjeon import Mecab
# from konlpy.tag import Mecab
import re
import sys
import pandas
from collections import Counter

class Corpus:
    def __init__(self, inputPath, index=3, words=2, standard=0.3):

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

        # inputPath가 길 경우 원문으로 인식
        if len(inputPath) > 50: self.data = inputPath
        else: self.data = self.extractText(inputPath)

        # 파일을 호출해서 행 번호(index)에 있는 값을 TXT에 저장
        txt = self.clean_str(self.readValue(self.data, index))

        # target = "문서전체내용"
        self.target = self.clean_str(txt)
        m = Mecab()
        # m = Mecab(dicpath='C:/mecab/mecab-ko-dic') # (사용불가능, 비활성)

        # wTotal = (int)문서 내 명사 갯수
        # fList = [["문장1명사1", "문장1명사2", ...], ["문장2명사1", "문장2명사2", ...], ...]
        # mList = ["문장1명사1", "문장1명사2", ..., "문장2명사1", "문장2명사2" ...] 중복 제거
        # lList = [["문장1형태소1", "문장1형태소2", ...], ["문장2형태소1", "문장2형태소2", ...], ...]
        self.wTotal = len(m.nouns(self.target))
        self.fList = self.nounExt(kss.split_sentences(self.target))
        self.mList = list(dict.fromkeys([item for sublist in self.fList for item in sublist]))
        self.lList = []
        for i in kss.split_sentences(self.target):
            l = []
            for j in m.morphs(i):
                l.append(j)
            self.lList.append(l)
        
        # N그램 변수
        self.ngram = 8
        # 복합단어를 이룰 단어의 갯수
        self.nOfWords = words
        # 제동변수
        self.df = 0.85
        # 텍스트랭크 반복횟수 (임시:16)
        self.defIteration = 16

        # allCW = [["단어1", "단어2", ...], ["단어a", "단어b", ...], ...] 복합단어의 가능성이 있는 모든 명사 리스트의 리스트
        self.allCW = []
        for i in range(len(self.fList)):
            n = self.genCW(self.fList[i])
            for j in n:
                # 문서를 검색하는 방식
                # if self.complexSearch(j, self.target) > 1 and j not in self.allCW: # 띄어쓰기 경우의 수를 모두 검색 (사용가능, 비활성)
                if self.searchSpaceless(j, self.target) > 1 and j not in self.allCW: # 본문 그대로 검색 (활성)
                    self.allCW.append(j)
        # 일부분 중복되는 복합단어를 탐지한 뒤 추가
        # self.allCW += self.detectRedundant(self.allCW) # (사용가능, 비활성)

        # trdic = {"단어1": TR1, "단어2": TR2, ...} (기존방식) (활성))
        self.trdic = self.calculateTROld(self.mList, self.fList, self.defIteration)

        # trdic = {"단어1": TR1, "단어2": TR2, ...} (N그램 방식) (사용가능, 비활성)
        # self.trdic = self.calculateTR(self.mList, self.lList, self.ngram, self.defIteration)

        # pmiList = [PMI1, PMI2, ...] allCW의 복합단어의 PMI 점수 리스트
        pmiList = []
        for i in self.allCW:
            pmiList.append(self.getPMI(i, self.wTotal, self.target))

        # trmpiList = [TRPMI1, TRPMI2, ...] 복합단어를 구성하는 TR의 기하평균 곱하기 복합단어의 PMI
        trpmiList = []
        for i in range(len(self.allCW)):
            k = self.allCW[i]
            key = 1
            for j in k:
                key *= self.trdic[j]
            key **= (1 / len(k))
            key *= pmiList[i]
            trpmiList.append(key)

        #gluedCW = ["복합단어1", "복합단어2", ...] allCW의 단어 구성 리스트를 합친 스트링 리스트
        gluedCW = []
        for i in self.allCW:
            gluedCW.append(''.join(i))
        
        # compDict = {"복합단어1": 1.11, "복합단어2": 2.22, ...}
        # 중복된 복합단어가 없는 경우
        if len(self.detectDuplicates(gluedCW)) == 0:
            self.compDict = dict(zip(gluedCW, trpmiList))
        # 중복된 복합단어가 있는 경우
        else: self.compDict = self.eliminateDuplicates(gluedCW, trpmiList)

        self.out = []
        for i in self.compDict.items():
            if i[1] > standard:
                self.out.append(i[0])

        # # 화면 출력 이후 텍스트 파일로 출력
        # if len(self.out) > 0:
        #     f = open(outputPath, 'a', encoding='utf8')
        #     print(self.out)
        #     f.write('\n'.join(self.out))
        #     f.write("\n")
        #     f.close()

    # 중복되는 단어를 찾아서 묶어준다. 예를 들어서 2번째와 5번째, 8번째와 10번째가 같을 경우 [[1,4],[7,9]]
    def detectDuplicates(self, wordlist):
        # wordlist는 기본적으로 gluedCW를 인풋으로 받음
        getlist = wordlist[:]
        c = Counter(getlist)
        out = []
        sublist = []
        for i in getlist:
            if c[i] > 1:
                for _ in range(c[i]):
                    n = getlist.index(i)
                    getlist[n] = ""
                    sublist.append(n)
                out.append(sublist)
                sublist = []
        return(out)

    # compDict로 종합하기 전 동일한 점수를 가진 두 리스트 제거하여 compDict를 리턴
    def eliminateDuplicates(self, wordlist, scorelist):
        # 기본적으로 wordlist는 gluedCW, scorelist는 trpmiList를 인풋으로 받음 
        duplicateslist = self.detectDuplicates(wordlist)
        for i in duplicateslist:
            # wordlist[i[0]]만 남기고 모두 빈 스트링 처리
            score = scorelist[i[0]]
            for j in i[1:]:
                wordlist[j] = ''
                score *= scorelist[j]
                scorelist[j] = ''
            # trpmiList는 기하평균값으로 계산하여 scorelist[i[0]]만 남기고 모두 빈 스트링 처리
            score **= 1/len(i)
            scorelist[i[0]] = score
            # 빈 스트링 모두 제거
            wordlist = list(filter(('').__ne__, wordlist))
            scorelist = list(filter(('').__ne__, scorelist))
            return dict(zip(wordlist, scorelist))

    # 리스트의 두 번째부터 마지막 엘리먼트가 리스트의 첫 번째부터 마지막 두 번째 엘리먼트까지 같은 경우를 모두 찾아냄
    def detectRedundant(self, cwlist):
        out = []
        indexchain = []
        inchain = False
        chainlist = []
        # 리스트 길이-1번 반복
        for i in range(len(cwlist)-1):
            # 첫 번째를 제거한 i리스트와 마지막을 제거한 i+1리스트가 같은 경우
            if cwlist[i][1:] == cwlist[i+1][:-1]:
                # 체인이 끊겨있는 상태인 경우 (머리)
                if inchain == False:
                    inchain = True
                    indexchain.append(i)
                # 체인을 연결 (몸통)
                else:
                    indexchain.append(i)
            # 체인이 끊기는 경우 (꼬리)
            elif inchain == True:
                inchain = False
                indexchain.append(i)
                chainlist.append(indexchain)
                indexchain = []
        # 출력 리스트 구축
        added = []
        for i in chainlist:
            added = cwlist[i[0]][:]
            if len(i) > 1:
                for j in i:
                    if j < i[-1]:
                        added.append(cwlist[j+1][-1])
            out.append(added)
        return out

    # 파일 위치 입력값에서 CSV 또는 스트링 추출
    def extractText(self, inputPath):
        # CSV가 아닐 경우 TXT로 취급
        if inputPath[-4:] != ".csv":
            f = open(inputPath, 'r', encoding='utf8')
            out = f.read()
            f.close()
            return out
        return pandas.read_csv(inputPath, encoding='utf8')

    # ["문장1", "문장2", ...] 형태의 리스트를 fList 형태로 변환
    def nounExt(self, sentlist):
        m = Mecab()
        # m = Mecab(dicpath='C:/mecab/mecab-ko-dic') # (사용불가능, 비활성)
        out = []
        for i in sentlist:
            out.append(m.nouns(i))
        return out

    # 단어 리스트를 받아 붙어있는 복합단어를 모두 종합하여 리스트로 출력
    def genCW(self, wList):
        out = []
        wordpair = []
        for i in range(len(wList) - self.nOfWords + 1):
            for j in range(i, i + self.nOfWords):
                wordpair.append(wList[j])
            out.append(wordpair)
            wordpair = []
        return out

    # n개의 단어 사이에 띄어쓰기가 들어올 수 있는 모든 경우의 수를 리스트로 출력 (코드 다소 조잡)
    # 예: per(3) = [['','',''], ['',' ',''], [' ','',''], [' ', ' ', '']] (마지막 단어는 띄어쓰기가 없음)
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

    # 모든 띄어쓰기의 경우의 수를 합산하여 검색
    def complexSearch(self, wordpair, target):
        out = 0
        spaces = self.per(len(wordpair))
        spacedwordpair = []
        for i in range(len(spaces)):
            w = ''
            for j in range(len(wordpair)):
                w += wordpair[j]
                w += spaces[i][j]
            spacedwordpair.append(w)
        for i in spacedwordpair:
            out += target.count(i)
        return out

    # 리스트 형태의 복합단어를 문서 전체에서 검색
    def searchSpaceless(self, wordpair, target):
        # 본문에서 띄어쓰기를 제외한 채로 검색할 경우:
        # return target.replace(' ','').count(''.join(wordpair))

        # 본문에서 띄어쓰기를 제외하지 않은 채로 띄어쓴 채로 검색할 경우
        # return target.count(' '.join(wordpair)))

        # 본문에서 띄어쓰기를 제외하지 않은 채로 검색할 경우:
        return target.count(''.join(wordpair))

    # 리스트 형태의 복합단어를 문서 전체에 대해서 PMI 계산
    def getPMI(self, wordpair, wordcount, target):
        # 분자 = p(w1, w2, ...)
        numerator = self.searchSpaceless(wordpair, target) / wordcount
        if numerator == 0:
            numerator = self.complexSearch(wordpair, target) / wordcount
            if numerator == 0: return 0
        # 분모 = p(w1) * p(w2) * ...
        denominator = 1
        for i in wordpair:
            denominator *= target.count(i) / wordcount
        # print(numerator)
        # print(denominator)
        pmi = math.log(numerator / denominator)
        return pmi

    # 입력된 단어에 간선으로 연결된 모든 단어를 리스트로 출력 (같은 문장에 등장시 연결)
    def wordMappingOld(self, word, flist):
        out = []
        # 문장별 반복작업
        for i in flist:
            if word in i:
                for j in i:
                    # 같은 단어가 여러 번 등장할 경우 중복으로 입력 -> 간선의 가중치가 증가
                    out.append(j)
        # 중복을 제거하여 가중치를 배제
        # list(dict.fromkeys(out))
        # 리스트에 포함된 자기 자신 단 한 번만 제거
        out.remove(word)
        return out

    # 입력된 단어에 간선으로 연결된 모든 단어를 리스트로 출력 (ngram 방식)
    def wordMapping(self, word, wordlist, lexlist, ngram):
        # word는 기본적으로 wordlist에 포함되어있는 명사를 인풋으로 받음
        # wordlist는 mList를, lexlist는 lList를 인풋으로 받음
        # ngram은 인덱스 최대거리 허용 수치
        out = []
        # 문장별 반복작업
        for i in lexlist:
            if word in i:
                for j in i:
                    if j in wordlist and self.nGram(i, word, j) <= ngram: out.append(j)
        # 리스트에 포함된 자기 자신 단 한 번만 제거
        out.remove(word)
        return out
    
    # 주어진 list 내 i와 j 사이의 인덱스 거리 계산
    def nGram(self, list, i, j):
        return abs(list.index(i) - list.index(j))

    # 입력단 단어에 간선으로 연결된 모든 단어 갯수 출력 (기존방식)
    def nOfConnectionsOld(self, word, flist):
        return len(self.wordMappingOld(word, flist))
    
    # 입력단 단어에 간선으로 연결된 모든 단어 갯수 출력
    def nOfConnections(self, word, wordlist, lexlist, ngram):
        return len(self.wordMapping(word, wordlist, lexlist, ngram))

    # 모든 단어에 대해서 텍스트랭크를 입력된 이터레이션 만큼 계산하여 단어:TR의 사전으로 출력 (기존방식)
    def calculateTROld(self, wordlist, flist, iteration):
        values = [1 / len(wordlist)] * len(wordlist)
        newValues = [0] * len(wordlist)
        node = dict(zip(wordlist, values))

        for _ in range(iteration):
            for i in range(len(wordlist)):
                key = wordlist[i]
                if self.wordMappingOld(key, flist) == []: newValues[i] = values[i]
                for j in self.wordMappingOld(key, flist):
                    # TR을 간선으로부터 끌어모으는 방식:
                    # newValues[i] += node[j] / self.nOfConnections(j, map)
                    # TR을 간선을 통해 분배하는 방식:
                    newValues[wordlist.index(j)] += node[key] / self.nOfConnectionsOld(key, flist)
            values = newValues
            newValues = [0] * len(wordlist)
            node = dict(zip(wordlist, values))

        # 제동변수 계산
        for i in range(0, len(values)):
            values[i] = (1-self.df) + self.df * values[i]
        node = dict(zip(wordlist, values))
        return node

    # 모든 단어에 대해서 텍스트랭크를 입력된 이터레이션 만큼 계산하여 단어:TR의 사전으로 출력
    def calculateTR(self, wordlist, lexlist, ngram, iteration):
        values = [1 / len(wordlist)] * len(wordlist)
        newValues = [0] * len(wordlist)
        node = dict(zip(wordlist, values))

        for _ in range(iteration):
            for i in range(len(wordlist)):
                key = wordlist[i]
                if self.wordMapping(key, wordlist, lexlist, ngram) == []: newValues[i] = values[i]
                for j in self.wordMapping(key, wordlist, lexlist, ngram):
                    # TR을 간선을 통해 분배하는 방식:
                    newValues[wordlist.index(j)] += node[key] / self.nOfConnections(key, wordlist, lexlist, ngram)
            values = newValues
            newValues = [0] * len(wordlist)
            node = dict(zip(wordlist, values))

        # 제동변수 계산
        for i in range(0, len(values)):
            values[i] = (1-self.df) + self.df * values[i]
        node = dict(zip(wordlist, values))
        return node
    
    # 입력된 CSV 파일의 행의 갯수 (정적 메소드) 
    def totalDocs(inputPath):
        # 입력된 파일이 CSV가 아닐 경우 TXT로 취급하여 1회 실행 유도
        if inputPath[-4:] != ".csv": return 1
        return len(pandas.read_csv(inputPath))

    # CSV 테이블에서 스트링 추출
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

    # 텍스트 클렌징
    def clean_str(self, text):
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

# # <--- CLI 전용 ---> (사용가능, 비활성)
# # sys.argv[1]: 입력파일
# # sys.argv[2]: 출력파일
# if __name__ == "__main__":
#     # 출력 파일 초기화
#     f = open(sys.argv[2], 'w', encoding='utf8')
#     f.write("")
#     f.close()

#     # CSV파일의 행 수 만큼 코드 실행
#     iterNum = Corpus.totalDocs(sys.argv[1])
#     lst = []
#     for i in range(iterNum):
#         c = Corpus(sys.argv[1], i)
#         if len(c.out) > 0:
#             lst.append(c.out)
#             print(c.out)

#     final = list(dict.fromkeys([item for sublist in lst for item in sublist]))
#     f = open(sys.argv[2], 'w', encoding='utf8')
#     f.write('\n'.join(final))
#     f.close()

# <--- IDE 전용 ---> (활성)
# 입력 선언
# inputFile = r"C:/comfinder/longtext.csv"
# inputFile = r"C:/comfinder/text.csv"
# inputFile = r"C:/comfinder/inputDoc.txt"
inputFile = r"11월 입찰 예정서울시 구로구 구로동에 위치한 `센터포인트 웨스트(구 서부금융센터)` 마스턴투자운용은 서울시 구로구 구로동 '센터포인트 웨스트(옛 서부금융센터)' 매각에 속도를 낸다.27일 관련업계에 따르면 마스턴투자운용은 지난달 삼정KPMG·폴스트먼앤코 아시아 컨소시엄을 매각 주관사로 선정한 후 현재 잠재 매수자에게 투자설명서(IM)를 배포하고 있는 단계다. 입찰은 11월 중순 예정이다.2007년 12월 준공된 '센터포인트 웨스트'는 지하 7층~지상 40층, 연면적 9만5000여㎡(약 2만8000평) 규모의 프라임급 오피스다. 판매동(테크노마트)과 사무동으로 이뤄졌다. 마스턴투자운용의 소유분은 사무동 지하 1층부터 지상 40층이다. 지하 1층과 지상 10층은 판매시설이고 나머지는 업무시설이다. 주요 임차인으로는 삼성카드, 우리카드, 삼성화재, 교보생명, 한화생명 등이 있다. 임차인의 대부분이 신용도가 높은 대기업 계열사 혹은 우량한 금융 및 보험사 등이다.'센터포인트 웨스트'는 서울 서남부 신도림 권역 내 최고층 빌딩으로 초광역 교통 연결성을 보유한 오피스 입지를 갖췄다고 평가받는다. 최근 신도림·영등포 권역은 타임스퀘어, 영시티, 디큐브시티 등 프라임급 오피스들과 함께 형성된 신흥 업무 권역으로 주목받고 있다고 회사 측은 설명했다.마스턴투자운용 측은   2021년 1분기를 클로징 예상 시점으로 잡고 있다  며   신도림 권역의 랜드마크로서 임대 수요가 꾸준해 안정적인 배당이 가능한 투자상품이 될 것  이라고 설명했다.한편 마스턴투자운용은 지난 2017년 말 신한BNP파리바자산운용으로부터 당시 '서부금융센터'를 약 3200억원에 사들였으며 이후 '센터포인트 웨스트'로 이름을 바꿨다.[김규리 기자 wizkim61@mkinternet.com]"
# inputFile = r"글로벌빅데이터연구소,?약?22만개?사이트?대상?9개?증권사?빅데이터?분석투자자?관심도?1위는?하나금융투자,?관심도?상승률?1위는?미래에셋대우  [파이낸셜뉴스]지난해 국내 주요 증권사에 대한 투자자 관심도를 조사한 결과 '하나금융투자'가 가장 높았던 것으로 나타났다. 같은 기간 관심도 상승률은 '미래에셋대우'가 가장 높았다.   5일 글로벌빅데이터연구소는 지난해 온라인 22만개 사이트를 대상으로 국내 9개 증권사에 대해 빅데이터를 분석한 결과, 이 같은 결과가 도출됐다고 밝혔다. 정보량의 경우 2019년과의 비교 분석도 실시했다.   연구소가 임의선정한 분석 대상 증권사는 '정보량 순'으로 △하나금융투자 △미래에셋대우 △NH투자증권 △키움증권 △삼성증권 △신한금융투자 △한국투자증권 △KB증권 △대신증권(대표 오익근) 등 이다.   분석 결과 온라인 게시물 수(총정보량)를 의미하는 '투자자 관심도'의 경우 2020년 '하나금융투자'는 총 30만2318건을 기록, 2019년 21만8533건에 비해 8만3785건 38.34% 늘어나며 1위를 차지했다.   이들 자료를 일일이 클릭한 결과 하나금융투자 정보량 중 '리포트'가 높은 비중을 차지했으며 투자자들은 이들 리포트를 블로그나 커뮤니티 등에 다시 게시하는 경우가 많았다.   정보량 2위는 지난해 총 29만1151건을 기록한 '미래에셋대우'였다. '미래에셋대우'는 지난 2019년 17만4672건에 비해서 11만6479건 66.68% 대폭 급증하며 증가량은 물론 증가율면에서 9개 주요 증권사중 가장 높았다.   2019년 26만3473건으로 가장 높은 관심도를 기록했던 'NH투자증권'은 지난해 2만3795건 9.03% 늘어 28만7268건을 보이는데 그치며 3위를 차지했다.   이어 '키움증권', '삼성증권', '신한금융투자', '한국투자증권', 'KB증권' 등이 20만~26만건 대를 기록하며 큰 차이를 보이지 않았으나 2019년 대비 증가량은 5.97%부터 50.72%까지 천차만별이었다.   관심도가 가장 낮은 '대신증권'은 지난해 총 19만7532건으로 2019년 13만8974건에 비해서는 5만8558건 42.14% 늘었다.   9개 증권사 중 가장 높은 투자자 호감도를 기록한 곳은 '하나금융투자'로 나타났다. 리포트 주목도가 높았던 '하나금융투자'는 긍정률에서 부정률을 뺀 값인 '순호감도'에서 41.94%를 기록, 1위를 차지했다.   정보량 상승률 1위였던 '미래에셋대우'가 28.94%로 순호감도에서 2위를 차지하며 '하나금융투자'와 함께 두 부문 모두 높은 지표를 보였다.   이어 '삼성증권' 25.78%, '한국투자증권' 25.36%, 'NH투자증권' 23.84%, '신한금융투자' 22.97%, '키움증권' 22.50%, 'KB증권' 21.41% 순이었다.   '대신증권'은 15.35%로 순호감도 역시 가장 낮았다"
# CSV파일의 행 수 만큼 코드 실행
iterNum = Corpus.totalDocs(inputFile)
# iterNum = 10
# iterNum = 50
for i in range(iterNum):
    c = Corpus(inputFile, i)
    if len(c.out) > 0: print(c.out)
