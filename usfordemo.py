# coding=UTF-8
import math
import re
import pandas

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

class CorpusBuilder:
    def __init__(self, inputPath, corpusSize=0):

        # 말뭉치 구축
        self.corpus = ""
        if corpusSize == 0:
            iterNum = totalDocs(inputPath)
        else:
            iterNum = corpusSize # 임시
        for i in range(iterNum):
            self.corpus += inputToFormat(inputPath, i)

        # 말뭉치 어절 리스트 구축
        corpustext = cleanText(self.corpus)
        temp = corpustext.split(' ')
        self.corpusEoList = [i for i in temp if len(re.sub(r'[0-9]+', '-', i)) >= 2]

        # 문서 리스트 구축 (for TF-IDF)
        # 문제점: 칼럼에 'NEWS_BODY'가 없을 경우 오류
        self.corpusDocList = list(pandas.read_csv(inputPath)['NEWS_BODY'])
        for i in range(len(self.corpusDocList)):
            doc = self.corpusDocList[i]
            self.corpusDocList[i] = cleanText(doc)

        # 필터 리스트
        self.exclude = ['NR', 'NNB', 'VV', 'VA', 'VX', 'VCP', 'VCN', 'MAG', 'MAJ', 'JKS', 'JKC', 'JKG', 'JKO', 'JKB', 'JKQ', 'JX', 'JC', 'EP', 'EF', 'EC', 'ETM', 'XSV', 'XSA', 'XR']

        # Mecab
        self.m = Mecab()

# 어절 리스트를 대상으로 입력 문자열을 각 어절의 좌측에서 검색하여 나온 결과를 출력
def leftSearcher(word, eoList):
    out = []
    max = len(word)
    for i in eoList:
        if len(i) >= max and i[0:max] == word: out.append(i)
    return len(out)

# 입력 문자열이 2자가 될 때 까지 오른쪽에서부터 한 문자씩 줄여 리스트로 출력
def eoShortener(word):
    out = []
    max = len(word)
    if max < 3: return []
    for i in range(len(word)-1):
        shortened = word[0:max-i]
        if shortened[-1] not in ['.', '-']: # 필터링
            out.append(word[0:max-i])
    return out

# 최장공통 부분문자열을 추출하는 반복문 (leftSearcher, eoShortener에 의존)
def leftLongestCommonSub(word, eoList):
    track = []

    for i in range(len(eoShortener(word))):
        wordCurrent = eoShortener(word)[i]
        wordBefore = eoShortener(word)[i-1]
        freq = leftSearcher(wordCurrent, eoList)

        if len(track) > 0:
            # if freq == track[-1] and freq > 1: # 한 문자 줄였는데 빈도가 같을 경우 그 전 부분문자열을 채택
            if freq < track[-1] * 1.1 and freq > 1: # 한 문자 줄였는데 빈도가 크게 차이나지 않는 경우 그 전 부분문자열 채택
                return wordBefore
        track.append(freq)

# 입력인자를 형식에 맞게 고침
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

# 입력된 파일이 CSV가 아닐 경우 TXT로 취급하여 1회 실행 유도
def totalDocs(inputPath):
    if inputPath[-4:] != ".csv": return 1
    return len(pandas.read_csv(inputPath))

# 텍스트 클렌징
def cleanText(text):
    text = text.replace(u'\xa0', u' ')
    text = re.sub('([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', repl=' ', string=text)
    text = re.sub('(http|ftp|https)://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', repl=' ', string=text)
    text = re.sub('([ㄱ-ㅎㅏ-ㅣ]+)', repl=' ', string=text)
    text = re.sub('<[^>]*>', repl=' ', string=text)
    text = re.sub('[^-/.&*+%$\w\s]', repl=' ', string=text)
    text = re.sub('([가-힣].[가-힣]*)\.', repl=r'\1. ', string=text)
    text = re.sub('(^[ \t]+|[ \t]+(?=:))', '', text, flags=re.M)
    text = text.replace('\n', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('\r', ' ')
    text = re.sub(' +', ' ', text)
    text = text.replace('()', ' ')
    text = text.upper()
    return text

# 문서 단위 어절 리스트 구축 (inputToFormat, cleanText, leftLongestCommonSub에 의존)
def eoListBuilder(inputPath, index, corpusEoList):
    inputPath = inputToFormat(inputPath, index)

    inputPath = cleanText(inputPath)
    temp = inputPath.split(' ')
    eoL = [i for i in temp if len(re.sub(r'[0-9]+', '-', i)) >= 2]

    # 숫자, 단위 필터링 적용
    # unitfilter = re.compile(r'[0-9]+.[0-9]+%|[0-9]+[조억만천원년월달일시분][0-9]+')
    unitfilter = re.compile(r'[0-9]+.[0-9]+%|[0-9]+[조억만천원년월달일시분위여건개층][0-9]*|[0-9]+거래일')

    # 말뭉치 어절 리스트
    out = []
    for i in eoL:
        word = leftLongestCommonSub(i, corpusEoList)
        if word != None and not unitfilter.search(word):
            out.append(word)
    out = list(dict.fromkeys(out))
    return out

# 어절 리스트에서 명사 리스트 출력 (클래스에 의존: cb.exclude, cb.m)
def extractList(eoList):
    temp = []
    banned = []
    for i in eoList: # e.g '설명했다'
        possiblyNoun = True

        # if len(cb.m.pos(i)) == 1 and cb.m.pos(i)[0][1][0] == 'N':
        #     # 이미 등록된 명사일 경우 제외
        #     continue

        for j in cb.exclude:
            # if (j in cb.m.pos(i)[-1][1] or cb.m.pos(i)[-1] == ('의', 'NNG')) and cb.m.pos(i)[-1] != ('도', 'JX') and cb.m.pos(i)[-1] != ('리온', 'EC') and i != '비대면':
                # 가장 마지막 형태소가 조사일 경우(exclude 조건에 해당될 경우) / '의'로 끝날 경우 / '도'로 끝날 경우는 예외 / '리온'으로 끝날 경우도 예외 / '비대면' 예외
                # 예외: 순호감도, 셀트리온, 비대면, 퍼블리싱(퍼블리), 아일리아와
            if j in cb.m.pos(i)[-1][1]:
                possiblyNoun = False
                banned.append(i)
                break
        if possiblyNoun: temp.append(i)
    eoList = temp
    return eoList

# TF-IDF calculation
def calcTFIDF(text, doc, corpusDocList):
    # calculate TF
    tf = doc.count(text)
    if tf == 0: tf = 0.001
    # calculate IDF
    deno = 0
    for i in corpusDocList:
        if text in i:
            deno += 1
    if deno == 0: deno = 0.001
    idf = math.log(len(corpusDocList) / deno)
    return tf*idf

# 말뭉치 입력
inputPath = r"C:/comfinder/longtext.csv"
# cb = CorpusBuilder(inputPath, 1)
cb = CorpusBuilder(inputPath, 100)
# cb = CorpusBuilder(inputPath)

# 말뭉치 대상 단어추출 프로세스
# 문제점1: 2자 명사는 추출하기 힘듬: leftLongestCommonSub에서 수정
# 문제점2: leftLongestCommonSub에서 명사여도 줄인 문자열이 매우 흔한 경우(예: 네이버 -> 네이, 코스피 -> 코스) 줄인 문자열을 채택함
# 문제점3: extractList에서 너무 많은것들이 걸러짐
for i in cb.corpusDocList:
    eoL = eoListBuilder(i, 0, cb.corpusEoList)
    temp = []
    # 추출된 단어
    for j in extractList(eoL):
        if calcTFIDF(j, i, cb.corpusDocList) > 8: temp.append(j)
        # temp.append(j)
    print(temp)
