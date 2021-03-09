# coding=UTF-8
import math
import re
import pandas
from pandas.core.frame import DataFrame

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
        return wordCurrent # 마지막까지 남은 경우 그냥 등록

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

def eoSplitter(doc):
    doc = cleanText(doc)
    temp = doc.split(' ')
    return [i for i in temp if len(re.sub(r'[0-9]+', '-', i)) >= 2]

# 마지막 형태소가 조사일 경우 제거 (클래스에 의존: cb.exclude, cb.m)
def removeTransitive(eo):
    split = cb.m.pos(eo)
    for i in cb.exclude:
        if len(split) > 1 and i in split[-1][1]:
            del split[-1]
        if len(split) == 1 and i in split[-1][1]:
            return ""
    out = ""
    for i in split:
        out += i[0]
    return out

# 끝이 조사인 경우 boolean으로 출력 (클래스에 의존: cb.exclude, cb.m)
def isTransitive(eo):
    split = cb.m.pos(eo)
    for i in cb.exclude:
        if len(split) > 0 and i in split[-1][1]:
            return True
    return False

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

# 단어추출 프로세스
inputPath = r"C:/comfinder/longtext.csv"
outputPath = r"C:/comfinder/outcsv.csv"
cb = CorpusBuilder(inputPath)
# cb = CorpusBuilder(inputPath, 10)
for i in cb.corpusDocList:
    # eoL 반복되는 문자열 (1c)
    eoL = []
    # i: 개별문서
    for j in eoSplitter(i):
        # j: 개별어절
        eoL.append(leftLongestCommonSub(j, cb.corpusEoList))
    eoL = list(filter(None, eoL))
    eoL = list(dict.fromkeys(eoL))

    # eoLR 반복되는 문자열에서 뒤음절 제거 (2c)
    eoLR = []
    for j in eoL:
        # j: 어절
        while isTransitive(j): j = removeTransitive(j)
        eoLR.append(j)

    # eoL에서 좌측으로부터 가장 긴 등록된 명사 (3c)
    eoLN = []
    for j in eoL:
        l = []
        l.append(j)
        for k in range(1, len(j)-1): # 최대 2자까지 검색
            l.append(j[:-k])

        for k in l:
            morphan = cb.m.pos(k)
            if len(morphan) == 1 and morphan[0][1][0] == 'N':
                eoLN.append(k)
                break
            if k == l[-1]: eoLN.append("") # 마지막 반복문

    # TF-IDF
    tfidf = []
    for j in range(len(eoL)):
        ti = calcTFIDF(eoL[j], i, cb.corpusDocList)
        tfidf.append(ti)

    # 일치율 (4c)
    score = []
    for j in range(len(eoL)):
        ratio = int((max(len(eoLR[j]), len(eoLN[j])) / (len(eoL[j]))) * 100)
        if len(eoL[j]) == len(eoLN[j]) or tfidf[j] < 8: score.append(-ratio)
        else: score.append(ratio)

    # 문맥 (5c?)
    context = []
    radius = 10
    for j in range(len(eoL)):
        wordstart = i.index(eoL[j])
        wordend = wordstart + len(eoL[j])
        if wordstart-radius < 0: start = 0
        else: start = wordstart-radius
        # context.append(i[start:wordend+radius])
        context.append(i[start:wordstart] + "<" + i[wordstart:wordend] + ">" + i[wordend:wordend+radius])

    # df = DataFrame(list(zip(eoL, eoLR, eoLN, score)), columns =['최장일치', '조사제거', '기등록어', '%']) 
    df = DataFrame(list(zip(eoL, eoLR, eoLN, score, context)), columns =['최장일치', '조사제거', '기등록어', '%', '문맥']) 
    df = df[df["%"] > 0]
    sorted = df.sort_values(by=['%'], axis=0, ascending=False)
    sorted.to_csv(outputPath, encoding='euc-kr', index=False)
    print(sorted)
    input("Press Enter to continue...")
