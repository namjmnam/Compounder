# coding=UTF-8
import math
import re
import pandas

import sys
from typing import Counter
platform = sys.platform
if platform.startswith('win32'):
    from eunjeon import Mecab # type: ignore
    # pip install eunjeon
elif platform.startswith('linux') or platform.startswith('darwin'):
    from konlpy.tag import Mecab # type: ignore
    # pip install konlpy
else:
    raise NotImplementedError

class Splitter:
    def __init__(self, inputText, inputCorpus=None):
        
        # 원문 문서에서 신조어 추출
        # 파이썬 버전 3.6, 3.8(윈도우 + eunjeon으로 실험)
        # 설치할 패키지: eunjeon
        # 차후 eunjeon에서 konlpy로 이전 예정

        # 리눅스 환경 mecab-ko-dic 설치과정
        # wget -c https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/최신버전-mecab-ko-dic.tar.gz
        # tar zxfv  최신버전-mecab-ko-dic.tar.gz
        # cd 최신버전-mecab-ko-dic
        # ./configure
        # make
        # make check
        # sudo make install
        # 위 과정을 거치면 /usr/local/lib/mecab/dic/mecab-ko-dic 경로에 mecab-ko-dic 설치

        # 현 문제점: 말뭉치 인풋을 받지 않음
        # Need to implement Corpus input and put it together into one string, or find other way to search the corpus

        # doc = "원문전체 문자열"
        self.rawdoc = self.trim_str(' ' + inputText) # 문서내 검색용
        self.doc = ' ' + self.clean_str(' ' + inputText) # 텍스트 클렌징용
        # corpus = 말뭉치. 데이터 형태 미정 (사용불가능, 비활성)
        if inputCorpus == None: self.corpus = ' ' + self.doc
        else: self.corpus = self.clean_str(' ' + inputCorpus)

        # wTotal = 말뭉치 총 어절 수
        # 현재 말뭉치 미사용
        # 문제점: 띄어쓰기의 갯수를 검색하고 있음
        # self.wTotal = self.corpus.count(' ')
        # self.wTotal = self.rawdoc.count(' ')
        self.wTotal = len(re.findall(r"""[가-힣]+[ .,`'"‘’()]""", self.rawdoc)) + len(re.findall(r"""[가-힣]$""", self.rawdoc)) # 문제해결, 재확인 필요

        l = self.doc.split(' ')
        self.eoList = [i for i in l if len(re.sub(r'[0-9]+', '-', i)) >= 3]

        # 괄호가 포함된 어절 출력
        missed = []
        for i in self.eoList:
            # if i.count("(") > 0 and i.count(")") > 0:
            #     # l = i[i.find("(")+1:i.find(")")]
            #     # if l != '': missed.append(l)
            #     # l = i[i.find(")")+1:i.find("(")]
            #     # if l != '': missed.append(l)
            #     missed.append(i[i.find("(")+1:i.find(")")])
            #     missed.append(i[i.find(")")+1:i.find("(")])
            #     continue
            # if i.count("(") > 0:
            #     # missed.append(i.split("(",1)[1])
            #     l = i.split("(")
            #     missed += l
            # if i.count(")") > 0:
            #     # missed.append(i[:-1])
            #     l = i.split(")")
            #     missed += l

            # 괄호가 포함된 경우 괄호 뒤에 오는 문자열도 모두 추출
            # 예: (이)(번주) -> ['(이)(번주)', ')(번주)', '(번주)', '번주)', '']
            # 문제점1: '번주)'같은 경우가 명사로 채택될 가능성 있음
            # 문제점2: 이런 경우, 한번만 등장해도 쉽게 명사로 채택됨
            str = i
            l = re.findall('[()]', str)
            for i in l:
                added = str[str.index(i)+1:]
                if self.rawdoc.count(added) >= 2: missed.append(added)
                str = str.replace(i,'',1)

        # 짧은 명사 제거
        temp = missed[:]
        for i in temp:
            if len(i) < 2: missed.remove(i)
        parenthesisless = [x for x in self.eoList+missed if  '(' not in x and ')' not in x] + [x for x in self.eoList+missed if '(' in x and ')' in x]
        # parenthesisless = [x for x in self.eoList if  '(' not in x and ')' not in x] + [x for x in self.eoList if '(' in x and ')' in x]
        # parenthesisless += missed
        self.eoList = parenthesisless # 괄호가 한 쪽만 포함된 어절을 모두 제거하고 괄호 속 어절을 포함

        # lplist: 모든 어절의 2자 이상의 LP부분 리스트: [["어절1LP1", "어절1LP2", ...], ["어절2LP1", "어절2LP2", ...], ...]
        self.lplist = []
        iter = self.eoList[:]
        iter = list(dict.fromkeys(iter))
        for i in iter:
            if len(i) > 1: self.lplist.append(self.genLP(i))

        # 명사로 추정되는 문자열 리스트 추출 -> extnouns
        self.extnouns = []
        for i in self.lplist:
            scores = []
            finalscore = 0
            chosen = ''
            for j in range(len(i)):
                # 문제점1: 말뭉치는 클렌징이 되어있지 않음
                # 문제점2: 기존에 이미 발견된 명사를 제외한 말뭉치에서 검색해야 함
                # 문제점3: 말뭉치에 대하여 검색하고 있지 않음

                # 문서 내 단어 수 산출
                # 문제점: 등장횟수를 띄어쓰기 + 단어에 대해서 검색하고 있음
                # 단순히 대상에 띄어쓰기+단어가 검색된 갯수만 찾음
                # scores.append(self.corpus.count(' ' + i[j]) / self.wTotal)
                # scores.append(self.doc.count(' ' + i[j]) / self.wTotal)
                # scores.append(self.doc.count(' ' + i[j]))

                # 문제점: 너무 조잡함
                str = re.escape(i[j])
                # str = re.sub('[^-/.\w]', repl='', string=i[j])
                # 더 포괄적인 패턴
                # patternone = r"""[ .,!?`'"‘’()]|[^\w]{}""".format(str)
                patternone = r"""[ .,!?`'"‘’()]{}""".format(str)
                patterntwo = r"^{}".format(str)
                # 단어 앞 공백/기호가 오는 갯수 + 맨 처음에 오는 갯수
                wordcount = len(re.findall(patternone, self.rawdoc) + re.findall(patterntwo, self.rawdoc))
                # scores.append(wordcount / self.wTotal)
                # 빈도율 계산 안 하고 빈도수만 계산
                scores.append(wordcount)
            for j in range(len(scores)):
                if j >= len(scores)-1:
                    chosen = i[j]
                    finalscore = scores[j]
                    break
                # 예: 마스터투자운 -> 마스터투자운용 빈도수가 크게 차이가 안 날 경우 넘어가지만
                # 마스터투자운용 -> 마스터투자운용은 빈도수가 크게 차이가 나기 때문에 그 직전에 명사로 채택
                if scores[j] > scores[j+1] * 1.1:
                    chosen = i[j]
                    finalscore = scores[j]
                    break
                finalscore = scores[j]
            # 빈도율이 2/어절수 이상인 경우 채택
            # if finalscore >= 2 / self.wTotal: self.extnouns.append(chosen)
            # 빈도율 계산 안 하고 빈도수만 계산 (2번 이상 등장)
            if finalscore >= 2: self.extnouns.append(chosen)
        self.extnouns = list(dict.fromkeys(self.extnouns))

        # # 괄호가 한 쪽만 포함된 문자열 제거: regex가 에러를 냄
        # temp = self.extnouns[:]
        # for i in temp:
        #     if i.count("(") > 0 and i.count(")") == 0:
        #         self.extnouns.remove(i)
        #         continue
        #     if i.count(")") > 0 and i.count("(") == 0:
        #         self.extnouns.remove(i)
        #         continue
        #     # 예: "이)런경(우" 제외
        #     if i.count("(") > 0 and i.count(")") > 0 and i.index(")") > i.index("("):
        #         self.extnouns.remove(i)
        #         continue

        # 여기서 Mecab은 끝에 조사가 오는 단어를 제거하기 위해 사용
        m = Mecab()
        # m = Mecab(dicpath='C:/mecab/mecab-ko-dic') # (사용불가능, 비활성)
        # m = Mecab(dicpath='/usr/local/lib/mecab/dic/mecab-ko-dic') # (사용불가능, 비활성)
        temp = self.extnouns[:]
        for i in temp:
            # 끝에 조사가 오는 경우 제외
            if m.pos(i)[-1][1][0] in ['E', 'J'] or '+E' in m.pos(i)[-1][1] or '+J' in m.pos(i)[-1][1] and 'ETN' not in m.pos(i)[-1][1]:
                self.extnouns.remove(i)
            #     continue
            # # 기존에 등록된 명사 제외
            # if len(m.pos(i)) == 1 and m.pos(i)[0][1][0] == 'N':
            #     self.extnouns.remove(i)

        # 현재 불필요하나 차후 채용 가능성 있음
        # # 단어 주변 문자열을 수집
        # self.surroundings = []
        # sentList = self.splitSentences(self.doc)
        # self.ndistance = 10
        # for i in self.extnouns:
        #     addedstr = ""
        #     for j in sentList:
        #         temp = j
        #         while i in temp:
        #             search = re.search(re.escape(i), temp)
        #             if (search.start()-self.ndistance < 0): l = temp[0:search.start()]
        #             else: l = temp[search.start()-self.ndistance:search.start()]
        #             l += temp[search.end():search.end()+self.ndistance]
        #             temp = temp.replace(i, '', 1)
        #             addedstr += l
        #     self.surroundings.append(addedstr)
        # self.conndict = dict(zip(self.extnouns, self.surroundings))

        # 간선으로 연결된 단어 dict
        self.conndict = {}
        ndist = 10
        for i in self.extnouns:
            # compounder 방식. weighted, undirected
            self.conndict[i] = self.wordMappingOld(i, self.extnouns, self.rawdoc)
            # 문자열 앞뒤 ndist 개 내 검색 (TR 점수 합산이 1이 안 됨 -> 원인 불명) unweighted, directed
            # self.conndict[i] = self.wordMapping(i, self.extnouns, self.rawdoc, ndist)

        # TR 산출 : 신규/기존 방식 혼용 가능
        self.trdict = self.calculateTextRank(self.extnouns, self.conndict, 16)

        # 복합단어 추출 프로토타입 (신규방식) : 모든 복합단어를 for문으로 돌려서 동시출현하는 경우를 검색
        self.pairListNew = []
        for i in self.extnouns:
            for j in self.extnouns:
                # rawdoc으로 검색할 수도 있고 corpus로 검색할 수도 있음 (기존의 2번과 달리 1번 이상 등장하는 경우 등록)
                if self.searchSpaceless([i, j], self.rawdoc) > 0 or self.searchSpaceless([i, j], self.parenthesisBuster(self.rawdoc)) > 0\
                    and [i, j] not in self.pairListNew : self.pairListNew.append([i ,j])

        # 신규방식으로 추출한 복합단어를 한 문자열로 묶은 리스트
        cwListNew = []
        for i in self.pairListNew:
            cwListNew.append(' '.join(i))

        # 신규방식으로 추출한 복합단어의 PMI 산출
        pmiListNew = []
        for i in self.pairListNew:
            pmiListNew.append(self.getPMI(i, self.wTotal, self.rawdoc))
        self.pmidictnew = dict(zip(cwListNew, pmiListNew))

        # 신규방식으로 추출한 복합단어의 TR+PMI 산출
        trpmiListNew = []
        for i in self.pairListNew:
            trpmi = 1
            for j in i:
                trpmi *= self.trdict[j]
            trpmi **= 1/len(i)
            trpmi *= self.pmidictnew[' '.join(i)]
            trpmiListNew.append(trpmi)
        self.trpmidictnew = dict(zip(cwListNew, trpmiListNew))

        # 기존의 복합단어 추출 (compounder 방식)
        self.fList = self.extractFList(self.extnouns, self.rawdoc)        
        self.pairListOld = []
        for i in range(len(self.fList)):
            n = self.genCW(self.fList[i])
            for j in n:
                # 문서 내에 복합단어 후보가 존재하거나 괄호 내용을 제거한 문서 내에 복합단어 후보가 존재하고 이미 후보가 추가되지 않은 경우
                if (self.searchSpaceless(j, self.rawdoc) > 1 or self.searchSpaceless(j, self.parenthesisBuster(self.rawdoc)) > 1)\
                    and j not in self.pairListOld:
                    self.pairListOld.append(j)
        # 일부분 중복되는 복합단어를 탐지한 뒤 추가
        self.pairListOld += self.detectRedundant(self.pairListOld)

        # 기존방식으로 추출한 복합단어를 한 문자열로 묶은 리스트
        cwListOld = []
        for i in self.pairListOld:
            cwListOld.append(' '.join(i))

        # 기존방식으로 추출한 복합단어의 PMI 산출
        pmiListOld = []
        for i in self.pairListOld:
            pmiListOld.append(self.getPMI(i, self.wTotal, self.rawdoc))
        self.pmidictold = dict(zip(cwListOld, pmiListOld))

        # 기존방식으로 추출한 복합단어의 TR+PMI 산출
        trpmiListOld = []
        for i in self.pairListOld:
            trpmi = 1
            for j in i:
                trpmi *= self.trdict[j]
            trpmi **= 1/len(i)
            trpmi *= self.pmidictold[' '.join(i)]
            trpmiListOld.append(trpmi)
        self.trpmidictold = dict(zip(cwListOld, trpmiListOld))

        # 여기서 Mecab은 기존에 등록된 명사인지 아닌지 판단하기 위해 사용 
        # 기존에 등록되어있는 명사 제외 (가장 마지막에 실행되어야 함)
        temp = self.extnouns[:]
        for i in temp:
            if len(m.pos(i)) == 1 and m.pos(i)[0][1][0] == 'N':
                self.extnouns.remove(i)

    # 리스트의 두 번째부터 마지막 엘리먼트가 리스트의 첫 번째부터 마지막 두 번째 엘리먼트까지 같은 경우를 모두 찾아냄 (기존방식 전용)
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

    # compounder에서 사용하는 복합어일 가능성이 있는 wordpair 추출 방식 (기존방식 전용)
    def genCW(self, nounlist):
        out = []
        wordpair = []
        for i in range(len(nounlist) - 2 + 1):
            for j in range(i, i + 2):
                wordpair.append(nounlist[j])
            out.append(wordpair)
            wordpair = []
        return out

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
        # 특수문자를 단어로 바꿀 수 있는 방식이 있으면 편리할것(ex. $4 -> 4달러, ¢99 -> 99센트)
        # pattern = '[^-/.*\w\s]' # 좀 더 엄격한 필터링: "스탠더드앤드푸어스(S&P) F-22전투기, A/S수리비용 4.5세대 OPEC+ $4 50%" 같은 경우 인식불가
        pattern = '[^-/.()&*+%$\w\s]'
        text = re.sub(pattern=pattern, repl=' ', string=text)
        # 한글 사이에 있는 마침표 제거
        pattern = '([가-힣].[가-힣]*)\.'
        text = re.sub(pattern=pattern, repl=r'\1. ', string=text)

        text = re.sub('(^[ \t]+|[ \t]+(?=:))', '', text, flags=re.M)
        text = text.replace('\n', ' ')
        text = text.replace('\t', ' ')
        text = text.replace('\r', ' ')
        text = re.sub('[0-9]+[개층위건만억조원년월일]', '', text)
        text = re.sub('[0-9]+.[0-9]+%', '', text)
        # text = re.sub('\b[0-9]+\b\s*', '', text)
        text = re.sub(' +', ' ', text)
        text = text.replace('()', ' ')
        text = text.upper()
        return text

    def trim_str(self, text):
        text = text.replace('[\n\t\r]', ' ')
        text = text.upper()
        text = re.sub(' +', ' ', text)
        return text
    
    # 한 단어의 말뭉치에 대한 빈도 수를 계산 (빈도율이 아님)
    def wordFreq(self, word, corpus):
        return corpus.count(word)

    # 한 어절에 대해서 모든 2자 이상의 LP 나열 리스트
    def genLP(self, eojeol):
        out = []
        # 추출된 어절 끝에 마침표가 오는 경우 제거
        if eojeol[-1] == '.': eojeol = eojeol[:-1]
        for i in range(2, len(eojeol)+1):
            if len(eojeol[:i].replace('.', '')) > 1 and eojeol[:1][-1] != '.':
                out.append(eojeol[:i])
        return out

    # 리스트 형태의 복합단어를 문서 전체에서 검색
    def searchSpaceless(self, wordpair, target):
        # 본문에서 띄어쓰기를 제외한 채로 검색할 경우:
        return target.replace(' ','').count(''.join(wordpair))

    # 리스트 형태의 복합단어를 문서 전체에 대해서 PMI 계산
    def getPMI(self, wordpair, wordcount, target):
        # 분자 = p(w1, w2, ...)
        numerator = target.replace(' ','').count(''.join(wordpair)) / wordcount
        if numerator == 0: return 0
        # 분모 = p(w1) * p(w2) * ...
        denominator = 1
        for i in wordpair:
            denominator *= target.count(i) / wordcount
        pmi = math.log(numerator / denominator)
        return pmi

    # 단어에 연결된 명사를 리스트로 출력 (unweighted, directed)
    def wordMapping(self, word, nounlist, doc, ndist):
        out = []
        # 도태된 방식
        # sentList = doc.split('. ')
        # 새로운 방식
        sentList = re.findall('.*?다\.*', doc)
        sentList.append(re.sub('.*?다\.', '', doc))
        # 문장당 해당 단어 주위에 등장하는 문자열 구축
        surrounding = ''
        for i in sentList:
            temp = i
            while word in temp:
                search = re.search(re.escape(word), temp)
                if (search.start()-ndist < 0): l = temp[0:search.start()]
                else: l = temp[search.start()-ndist:search.start()]
                l += temp[search.end():search.end()+ndist]
                temp = temp.replace(word, '', 1)
                surrounding += l
        # 구축된 문자열에 등장하는 모든 명사 리스트 구축
        for i in nounlist:
            if i in surrounding:
                out.append(i)
        if word in out: out.remove(word)
        return out

    # 단어에 연결된 명사를 리스트로 출력 (compounder 방식, weighted, undirected)
    def wordMappingOld(self, word, nounlist, doc):
        out = []
        # 도태된 방식
        # sentList = doc.split('. ')
        # 새로운 방식
        sentList = re.findall('.*?다\.*', doc)
        sentList.append(re.sub('.*?다\.', '', doc))
        # 같은 문장 안에 등장하는 갯수 만큼 등록
        for i in sentList:
            temp = i
            for j in nounlist:
                # 새로운 방식
                if word in temp and j in temp:
                    for i in range(temp.count(j)): out.append(j)
                # 도태된 방식
                # while word in temp and j in temp:
                #     # replace 방식이 아닌 append를 특정 수 만큼 해야
                #     out.append(j)
                #     temp = temp.replace(j, '', 1)
        out.remove(word)
        return out

    def calculateTextRank(self, nounlist, conndict, iteration):
        values = [1 / len(nounlist)] * len(nounlist)
        newValues = [0] * len(nounlist)
        node = dict(zip(nounlist, values))

        for _ in range(iteration):
            for i in range(len(nounlist)):
                key = nounlist[i]
                if conndict[key] == []:
                    newValues[i] = values[i]
                    continue
                for j in conndict[key]:
                    # TR을 간선을 통해 분배하는 방식:
                    newValues[nounlist.index(j)] += node[key] / len(conndict[key])
            values = newValues
            newValues = [0] * len(nounlist)

            node = dict(zip(nounlist, values))

        # 제동변수 계산
        df = 0.85
        for i in range(0, len(values)):
            values[i] = (1-df) + df * values[i]
        node = dict(zip(nounlist, values))
        return node

    # 단어페어 리스트에서 연결고리가 있을 가능성이 있는 경우를 모두 발견 (신규방식용)
    def detectConnection(self, cwlist):
        # 앞뒤 잘린 리스트 구축
        frontshortened = []
        backshortened = []
        for i in cwlist:
            frontshortened.append(i[1:])
        for i in cwlist:
            backshortened.append(i[:-1])
        
        # 사전구축작업
        connectionmap = {}
        for i in range(len(cwlist)):
            connectionmap[i] = []

        for i in range(len(cwlist)):
            for j in range(len(cwlist)):
                if frontshortened[i] == backshortened[j]: connectionmap[i].append(j)
        return connectionmap

    # 명사 리스트와 원문에서 flist 추출 (기존방식용)
    def extractFList(self, nounlist, doc):
        out = []
        templist = []
        # 도태된 방식
        # sentList = doc.split('. ')
        # 새로운 방식
        sentList = re.findall('.*?다\.*', doc)
        sentList.append(re.sub('.*?다\.', '', doc))
        for i in sentList:
            temp = i
            sublist = []
            for j in nounlist:
                while j in temp:
                    index = re.search(re.escape(j), temp).start()
                    temp = temp.replace(j, '', 1)
                    sublist.append([j, index])
            templist.append(sublist)
        
        for i in templist:
            sublist = []
            l = sorted(i, key=lambda x: x[1])
            for j in l: sublist.append(j[0])
            out.append(sublist)
        return out

    # 원문에서 괄호 속에 있는 문자열 제거
    def parenthesisBuster(self, doc):
        # 괄호를 찾아 사이에 있는 모든 문자열(괄호 속 괄호 제외) 모두 제거
        out = doc
        for i in range(doc.count('(')):
            out = re.sub(r"\([^()]*\)", "", out)
        # 남은 괄호 모두 제거
        out = re.sub('[()]', '', out)
        return out

def inputToFormat(inputPath, index=0):
    # 50자보다 길 경우 문자열로 인식
    if len(inputPath) > 50: return inputPath
    # CVS가 아닐 경우 TXT로 인식
    if inputPath[-4:] != ".csv":
        f = open(inputPath, 'r', encoding='utf8')
        out = f.read()
        f.close()
        return out
    # CVS일 경우 테이블 읽어들이기
    data = pandas.read_csv(inputPath, encoding='utf8')
    # NEWS_BODY 열이 없을 경우
    if "NEWS_BODY" not in data.columns:
        l = data.loc[index].tolist()
        l = [str(i) for i in l]
        long = max(l, key=len)
        return long
    # NEWS_BODY 열만 불러오기
    return data.at[index, 'NEWS_BODY']

def totalDocs(inputPath):
    # 입력된 파일이 CSV가 아닐 경우 TXT로 취급하여 1회 실행 유도
    if inputPath[-4:] != ".csv": return 1
    return len(pandas.read_csv(inputPath))

# # <--- CLI 전용 ---> (사용가능, 비활성)
# # sys.argv[1]: 입력파일
# if __name__ == "__main__":
#     # CSV파일의 행 수 만큼 코드 실행
#     iterNum = totalDocs(sys.argv[1])
#     for i in range(iterNum):
#         input = sys.argv[1]
#         text = inputToFormat(input, i)
#         s = Splitter(text)
#         print(s.extnouns)
#         print([i for i in list(s.trpmidictnew.keys()) if s.trpmidictnew[i] >= 0.3])
#         print([i for i in list(s.trpmidictold.keys()) if s.trpmidictold[i] >= 0.3])

# <--- IDE 전용 ---> (활성)
# 입력 선언
# input = r"11월 입찰 예정 서울시 구로구 구로동에 위치한 `센터포인트 웨스트(구 서부금융센터)` 마스턴투자운용은 서울시 구로구 구로동 '센터포인트 웨스트(옛 서부금융센터)' 매각에 속도를 낸다.27일 관련업계에 따르면 마스턴투자운용은 지난달 삼정KPMG·폴스트먼앤코 아시아 컨소시엄을 매각 주관사로 선정한 후 현재 잠재 매수자에게 투자설명서(IM)를 배포하고 있는 단계다. 입찰은 11월 중순 예정이다.2007년 12월 준공된 '센터포인트 웨스트'는 지하 7층~지상 40층, 연면적 9만5000여㎡(약 2만8000평) 규모의 프라임급 오피스다. 판매동(테크노마트)과 사무동으로 이뤄졌다. 마스턴투자운용의 소유분은 사무동 지하 1층부터 지상 40층이다. 지하 1층과 지상 10층은 판매시설이고 나머지는 업무시설이다. 주요 임차인으로는 삼성카드, 우리카드, 삼성화재, 교보생명, 한화생명 등이 있다. 임차인의 대부분이 신용도가 높은 대기업 계열사 혹은 우량한 금융 및 보험사 등이다.'센터포인트 웨스트'는 서울 서남부 신도림 권역 내 최고층 빌딩으로 초광역 교통 연결성을 보유한 오피스 입지를 갖췄다고 평가받는다. 최근 신도림·영등포 권역은 타임스퀘어, 영시티, 디큐브시티 등 프라임급 오피스들과 함께 형성된 신흥 업무 권역으로 주목받고 있다고 회사 측은 설명했다.마스턴투자운용 측은   2021년 1분기를 클로징 예상 시점으로 잡고 있다  며   신도림 권역의 랜드마크로서 임대 수요가 꾸준해 안정적인 배당이 가능한 투자상품이 될 것  이라고 설명했다.한편 마스턴투자운용은 지난 2017년 말 신한BNP파리바자산운용으로부터 당시 '서부금융센터'를 약 3200억원에 사들였으며 이후 '센터포인트 웨스트'로 이름을 바꿨다.[김규리 기자 wizkim61@mkinternet.com]"
# input = r"글로벌빅데이터연구소,?약?22만개?사이트?대상?9개?증권사?빅데이터?분석투자자?관심도?1위는?하나금융투자,?관심도?상승률?1위는?미래에셋대우  [파이낸셜뉴스]지난해 국내 주요 증권사에 대한 투자자 관심도를 조사한 결과 '하나금융투자'가 가장 높았던 것으로 나타났다. 같은 기간 관심도 상승률은 '미래에셋대우'가 가장 높았다.   5일 글로벌빅데이터연구소는 지난해 온라인 22만개 사이트를 대상으로 국내 9개 증권사에 대해 빅데이터를 분석한 결과, 이 같은 결과가 도출됐다고 밝혔다. 정보량의 경우 2019년과의 비교 분석도 실시했다.   연구소가 임의선정한 분석 대상 증권사는 '정보량 순'으로 △하나금융투자 △미래에셋대우 △NH투자증권 △키움증권 △삼성증권 △신한금융투자 △한국투자증권 △KB증권 △대신증권(대표 오익근) 등 이다.   분석 결과 온라인 게시물 수(총정보량)를 의미하는 '투자자 관심도'의 경우 2020년 '하나금융투자'는 총 30만2318건을 기록, 2019년 21만8533건에 비해 8만3785건 38.34% 늘어나며 1위를 차지했다.   이들 자료를 일일이 클릭한 결과 하나금융투자 정보량 중 '리포트'가 높은 비중을 차지했으며 투자자들은 이들 리포트를 블로그나 커뮤니티 등에 다시 게시하는 경우가 많았다.   정보량 2위는 지난해 총 29만1151건을 기록한 '미래에셋대우'였다. '미래에셋대우'는 지난 2019년 17만4672건에 비해서 11만6479건 66.68% 대폭 급증하며 증가량은 물론 증가율면에서 9개 주요 증권사중 가장 높았다.   2019년 26만3473건으로 가장 높은 관심도를 기록했던 'NH투자증권'은 지난해 2만3795건 9.03% 늘어 28만7268건을 보이는데 그치며 3위를 차지했다.   이어 '키움증권', '삼성증권', '신한금융투자', '한국투자증권', 'KB증권' 등이 20만~26만건 대를 기록하며 큰 차이를 보이지 않았으나 2019년 대비 증가량은 5.97%부터 50.72%까지 천차만별이었다.   관심도가 가장 낮은 '대신증권'은 지난해 총 19만7532건으로 2019년 13만8974건에 비해서는 5만8558건 42.14% 늘었다.   9개 증권사 중 가장 높은 투자자 호감도를 기록한 곳은 '하나금융투자'로 나타났다. 리포트 주목도가 높았던 '하나금융투자'는 긍정률에서 부정률을 뺀 값인 '순호감도'에서 41.94%를 기록, 1위를 차지했다.   정보량 상승률 1위였던 '미래에셋대우'가 28.94%로 순호감도에서 2위를 차지하며 '하나금융투자'와 함께 두 부문 모두 높은 지표를 보였다.   이어 '삼성증권' 25.78%, '한국투자증권' 25.36%, 'NH투자증권' 23.84%, '신한금융투자' 22.97%, '키움증권' 22.50%, 'KB증권' 21.41% 순이었다.   '대신증권'은 15.35%로 순호감도 역시 가장 낮았다"
input = r"우리나라의 1인가구가 매년 증가세를 보이는 가운데 지난해에는 600만을 넘어섰다. 가구 분포 역시 1인 가구는 30.2%를 차지해 2인 가구(27.8%), 3인 가구(20.7%), 4인 이상(21.2%)를 크게 앞지르며 대세를 이루고 있다. 특히 대전지역의 1인 가구 비율은 33.7%로 전년(32.6%) 대비 1.1% 증가했고 전국 1인 가구 비율보다는 3.5%가 더 높은 것으로 조사됐다. 향후 5년간 1인 가구 수가 매년 15만가구씩 증가할 것이라는 예측이 나오면서 유통업계에서는 1인 가구를 위한 소포장, 1인 메뉴 등을 출시하는데 열을 올리고 있다. 이러한 트렌드에 발맞춰 대전지역 롯데마트 3개 지점에서는 ‘한끼밥상’이라는 테마로 소포장 전문 코너를 만들어 운영 중이다. 농림축산식품부의 GAP(우수관리인증) 농산물을 990원부터 만나볼 수 있어 소비자로부터 좋은 반응을 보이고 있다. 실제로 대전지역 롯데마트 3개 지점(대덕점, 노은점, 서대전점)의 2020년 신선식품 中 소용량 상품군의 매출은 전년대비 12% 가까이 증가했다. 롯데마트 충청호남영업부문 배효권 부문장은 “1인 가구가 유통시장의 새로운 소비 주체로 떠오르면서 1~2인 가구를 겨냥한 소포장, 가정간편식 등과 같은 시장의 규모가 급성장할 것으로 예상된다”며 “롯데마트에서는 지역의 생산자와 손잡고 해당 상품군을 지속적으로 확대∙강화하는데 최선을 다하겠다”고 말했다."
# input = r"정부가 이르면 26일께 3월부터 적용할 새 거리두기 조정안 단계를 발표할 예정이다. 오는 28일 현행 거리두기 단계(수도권 2단계, 비수도권 1.5단계) 종료 이후 사회적 거리두기가 재상향될지 관심이 모아진다.    손영래 중앙사고수습본부 사회전략반장은 23일 코로나19 백브리핑에서  (이번주) 금요일(26일) 또는 토요일(27일) 정도 생각 중인데 내일 정례브리핑 때 정확히 공지하겠다 고 밝혔다.    설 연휴 이후 600명대까지 치솟았던 일일 확진자수가 이틀 연속 300명대를 유지했지만 정부는 다시 증가할 가능성이 크다고 전망했다.    손 반장은  오늘까지는 주말 검사 감소량으로 인한 확진자 감소 현상이 나타났다고 본다 며  내일부터는 조금 증가할 것 같고, 26일까지 증가 추이가 어느 정도 갈지 봐야 한다 고 말했다.    앞서 정부는 지난 18일 다음 달부터 업종별 집합금지를 최소화하는 대신 개인 간 사적모임을 규제하는 자율과 책임에 기반을 골자로 하는 기본 방향을 내놨다.    이번 사회적 거리두기 개편안에는 현행 5단계(1→1.5→2→2.5→3단계)의 단점을 보완하는 대책도 담길 전망이다. 앞서 정부는 지난해 6월 3단계 체계의 거리두기를 적용하다가 같은해 11월 5단계로 개편한 바 있다. 0.5단계 차이로 세분화돼 있는 현행 체계는 단계별 대국민 행동 메시지가 분명하지 않아 위험성을 인지하기가 쉽지 않다는 지적이 제기돼 왔다.    식당이나 카페 등 다중이용시설에 대해서는 영업을 금지하는 집합금지는 최소화할 예정이다. 다만, 시설의 감염 취약 요인을 제거하기 위한 밀집도를 조정하기 위한 '인원제한'은 이어간다는 방침이다.    정세균 국무총리는 이날 중대본 회의에서  방역수칙 위반 업소에 대해서는 현재 시행 중인 '원스트라이크 아웃 제도'를 예외 없이 적용하고 곧 지급할 4차 재난지원금 지원 대상에서도 제외할 것 이라고 강조했다."
# input = r"연초부터 무섭게 솟아오르던 비트코인 가격이 조정을 보이고 있다. 주요 투자 기관들의 잇따른 참여에도 불구, 미국 정부가 비트코인의 안정성과 적법성에 대해 강한 의구심을 표하면서 참여자들 사이에서 거품 논란과 규제 이슈 등으로 불안감이 형성된 탓이다. 그럼에도 이젠 비트코인 투자에 유의해야 할 때란 의견과 단기 조정을 거쳐 재반등할 것이란 주장이 팽팽히 맞서고 있다.    지난주 사상 첫 5만달러대에 진입한 비트코인 가격은 24일 현재 4만달러대로 떨어졌다. 재닛 옐런 미 재무장관이 지난 23일 뉴욕타임스 딜북 콘퍼런스에서 비트코인에 대해 “화폐를 거래하는 데 극도로(extremely) 비효율적인 방법”이라며 “투기성이 강한 자산이며, 극도로(extremely) 변동성이 있단 점을 인지해야 한다”고 말했다.    이처럼 옐런의 입에서 ‘극도로’란 표현을 여러번 사용할 정도로 비트코인에 대해 강한 경계 발언이 나온 것을 기점으로 시장의 우려가 증폭됐다. 안 그래도 일론 머스크 테슬라 최고경영자(CEO)가 가상자산 가격이 높아 보인다고 발언한 상황에서 기름을 끼얹는 격이었다.  마크 해펠 UBS 글로벌 자산운용 최고투자책임자(CIO)는 성명을 통해 “우리는 고객들에게 가상자산 투기에 주의를 기울여야 한다고 조언하고 있다”며 “규제 리스크가 아직 해소되지 않은 상황에서 (비트코인의) 미래는 여전이 불투명하다”고 밝혔다. 미국 투자 전문지 배런스도 비트코인의 버블이 터줄 수 있어 관련주 역풍에 주의해야 한다고 보도했다.    우리나라에서도 비트코인에 대한 우려 목소리가 커지고 있다. 이주열 한국은행 총재는 지난 23일 가상자산에 대해 ‘내재가치(intrinsic value)’가 없다고 평가했다. 내재가치는 자산가치와 수익가치를 아우른 개념으로 우리나라 중앙은행의 수장이 비트코인을 공인 자산으로 인정받기 어렵다는 견해를 밝힌 것이라고 볼 수 있다.  한편 비트코인 강세론자들은 현재의 하락 국면이 추가 매수 유인이 될 수 있다는 입장이다. 캐시 우드 아크 인베스트 CEO는 한 인터뷰에서 “우리는 비트코인에 대해 매우 긍정적이며, 지금 건강한 조정(healthy correction)을 볼 수 있어 매우 행복하다”고 말했다.    전세계 처음으로 캐나다에서 출시된 비트코인 상장지수펀드(퍼포즈 비트코인 ETF)는 흥행 기록을 이어가고 있다. 가상자산 분석업체 글라스노드에 따르면 퍼포즈 ETF로의 자금 유입이 지속되면서 23일 현재 운용규모(AUM)가 5억6400만달러(약 6300억원)에 달하고 있다.  "
# input = r"C:/comfinder/inputDoc.txt"
# input = "C:/comfinder/text.csv"
# input = r"C:/comfinder/longtext.csv"
# CSV파일의 행 수 만큼 코드 실행
iterNum = totalDocs(input)
for i in range(iterNum):
    text = inputToFormat(input, i)
    s = Splitter(text)
    print(s.extnouns)
    print([i for i in list(s.trpmidictnew.keys()) if s.trpmidictnew[i] >= 0.3])
    print([i for i in list(s.trpmidictold.keys()) if s.trpmidictold[i] >= 0.3])


# # 도태됨
# s = Splitter(text)

# # 추출된 명사
# print(s.extnouns)
# # print('추출된 명사 : ' + str(s.extnouns))
# # print(s.conndict)
# # print(s.trdict)
# # TR순 상위 10개 단어 출력
# # print(sorted(s.trdict, key=s.trdict.get, reverse=True)[:10]) # TR순 상위 10개 단어 출력

# # 새 방식
# # print(s.pairListNew)
# # print(s.pmidictnew)
# # print(s.trpmidictnew)
# # print(s.detectConnection(s.pairListNew))
# print([i for i in list(s.trpmidictnew.keys()) if s.trpmidictnew[i] >= 0.3])

# # 기존 방식
# # print(s.pairListOld)
# # print(s.pmidictold)
# # print(s.trpmidictold)
# # print(s.fList)
# print([i for i in list(s.trpmidictold.keys()) if s.trpmidictold[i] >= 0.3])
