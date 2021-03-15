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
    # print(out) # 포함된 어절을 모두 콘솔에 출력
    return len(out)

# 입력 문자열이 2자가 될 때 까지 오른쪽에서부터 한 문자씩 줄여 리스트로 출력
def eoShortener(word):
    out = []
    max = len(word)
    if max < 3: return []
    # if inputText[-1] == '.': inputText = inputText[:-1]
    for i in range(len(word)-1):
        shortened = word[0:max-i]
        if shortened[-1] not in ['.', '-']: # 필터링
            out.append(word[0:max-i])
    return out

# 최장공통 부분문자열을 추출하는 반복문 (leftSearcher, eoShortener에 의존)
def leftLongestCommonSub(word, eoList, mode=1):
    # mode != 1 : RP 추출
    track = []
    out = [] # mode == 3 전용
    chained = False # mode == 3 전용

    for i in range(len(eoShortener(word))):
        wordCurrent = eoShortener(word)[i]
        wordBefore = eoShortener(word)[i-1]
        freq = leftSearcher(wordCurrent, eoList)

        # mode == 3 한 어절에서 여러개의 명사 추출 시도
        if mode == 3:
            # 한 문자 줄였는데 빈도가 크게 늘지 않는 경우 그 전 부분문자열 채택
            # 문제점: 중복해서 넣게 됨: 미래에셋대우스팩4호 -> 미래에셋대우스팩4 -> 미래에셋대우스팩
            if len(track) > 0:
                # if (freq < track[-1] * 1.1 or freq < track[-1] + 1) and freq > 1:
                if freq < track[-1] * 1.1 and freq > 1:
                    if not chained:
                        out.append(wordBefore)
                        chained = True
                    # while (freq < track[-1] * 1.1 or freq < track[-1] + 1) and freq > 1: continue
                else: chained = False
            if i == len(eoShortener(word))-1:
                return out
            else:
                track.append(freq)
                continue

        if len(track) > 0:
            # if freq == track[-1] and freq > 1: # 한 문자 줄였는데 빈도가 같을 경우 그 전 부분문자열을 채택
            if freq < track[-1] * 1.1 and freq > 1: # 한 문자 줄였는데 빈도가 크게 차이나지 않는 경우 그 전 부분문자열 채택
                if mode != 1:
                    return word[len(wordBefore):]
                else:
                    return wordBefore
        # if len(wordCurrent) == 2:
        #     # 마지막 남은 어절이 2자인 경우:
        #     pass
            
        # if len(word) == 2 and freq > 4: # 4는 말뭉치의 크기에 비례해야 한다.
        #     # 어절이 2자인 경우
        #     return word
        track.append(freq)

def leftLongestCommonSubNew(word, eoList):
    track = []
    iter = len(eoShortener(word))
    for i in range(iter):
        wordCurrent = eoShortener(word)[i]
        wordBefore = eoShortener(word)[i-1]
        freq = leftSearcher(wordCurrent, eoList)

        if len(track) > 0:
            # if freq == track[-1] and freq > 1: # 한 문자 줄였는데 빈도가 같을 경우 그 전 부분문자열을 채택
            if freq < track[-1] * 1.1 and freq > 1: # 한 문자 줄였는데 빈도가 크게 차이나지 않는 경우 그 전 부분문자열 채택
                return wordBefore

        track.append(freq)
        if i == iter-1 : return wordCurrent # 마지막까지 남은 경우 그냥 등록

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
def eoListBuilder(inputPath, index, corpusEoList, mode=1):
    inputPath = inputToFormat(inputPath, index)

    inputPath = cleanText(inputPath)
    temp = inputPath.split(' ')
    eoL = [i for i in temp if len(re.sub(r'[0-9]+', '-', i)) >= 2]

    # mode == 2 : RP 추출
    if mode == 2:
        out = []
        for i in eoL:
            out.append(leftLongestCommonSub(i, corpusEoList, 2))
        out = list(filter(None, out))
        out = list(dict.fromkeys(out))
        return out
        
    # mode == 3 : leftLongestCommonSub mode 3
    if mode == 3:
        out = []
        for i in eoL:
            temp = leftLongestCommonSub(i, corpusEoList, 3)
            if temp != None: out += temp
        # out = list(filter(None, out))
        out = list(dict.fromkeys(out))
        return out

    # 숫자, 단위 필터링 적용
    # unitfilter = re.compile(r'[0-9]+.[0-9]+%|[0-9]+[조억만천원년월달일시분][0-9]+')
    unitfilter = re.compile(r'[0-9]+.[0-9]+%|[0-9]+[조억만천원년월달일시분위여건개층][0-9]*|[0-9]+거래일')

    # 말뭉치 어절 리스트
    out = []
    for i in eoL:
        word = leftLongestCommonSub(i, corpusEoList)
        # if word != None:
        if word != None and not unitfilter.search(word):
            out.append(word)
    # out = list(filter(None, out))
    out = list(dict.fromkeys(out))
    return out

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

# 어절 리스트에서 명사 리스트 출력 (클래스에 의존: cb.exclude, cb.m)
def extractList(eoList, mode=1):
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
    # mode=1 명사 리스트
    # mode=2 제거된 리스트
    if mode == 1: return eoList
    else: return banned

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
# inputPath = r"C:/comfinder/longtext.csv"

# 인스턴스 생성
# cb = CorpusBuilder(inputPath, 1)
# cb = CorpusBuilder(inputPath, 100)
# cb = CorpusBuilder(inputPath)

# 말뭉치 대상 단어추출 프로세스
# 문제점1: 2자 명사는 추출하기 힘듬: leftLongestCommonSub에서 수정
# 문제점2: leftLongestCommonSub에서 명사여도 줄인 문자열이 매우 흔한 경우(예: 네이버 -> 네이, 코스피 -> 코스) 줄인 문자열을 채택함
# 문제점3: extractList에서 너무 많은것들이 걸러짐
# for i in cb.corpusDocList:
#     eoL = eoListBuilder(i, 0, cb.corpusEoList)
#     temp = []
#     # 추출된 단어
#     for j in extractList(eoL):
#         if calcTFIDF(j, i, cb.corpusDocList) > 8: temp.append(j)
#     # 조사가 제거된 단어
#     for j in extractList(eoL, 2):
#         # # Old method
#         # eo = removeTransitive(j)
#         # # if calcTFIDF(eo, i, cb.corpusDocList) > 8 and not isTransitive(eo) and eo not in temp and len(re.sub(r'[0-9]+', '-', eo)) >= 3:
#         # # if not isTransitive(eo) and eo not in temp:
#         # # if len(re.sub(r'[0-9]+', '-', eo)) >= 3 and not isTransitive(eo) and eo not in temp:
#         # if calcTFIDF(eo, i, cb.corpusDocList) > 8 and not isTransitive(eo) and eo not in temp:
#         #     temp.append(eo)

#         # New method
#         while isTransitive(j): j = removeTransitive(j)
#         if j != "" and calcTFIDF(j, i, cb.corpusDocList) > 8 and j not in temp: temp.append(j)
#     print(temp)

# # extractList를 사용하지 않은 결과
# for i in cb.corpusDocList:
#     eoL = eoListBuilder(i, 0, cb.corpusEoList, 3)
#     temp = []
#     for j in eoL:
#         if calcTFIDF(j, i, cb.corpusDocList) > 8: temp.append(j)
#     print(temp)

# 새 방식
inputPath = r"C:/comfinder/longtext.csv"
# inputPath = r"C:/comfinder/text.csv"
outputPath = r"C:/comfinder/outcsv.csv"
cb = CorpusBuilder(inputPath, 50)
for i in cb.corpusDocList:
    # eoL 반복되는 문자열 (1c)
    eoL = []
    # i: 개별문서
    for j in eoSplitter(i):
        # j: 개별어절
        eoL.append(leftLongestCommonSubNew(j, cb.corpusEoList))
    eoL = list(filter(None, eoL))
    eoL = list(dict.fromkeys(eoL))
    # print(eoL)
    # print(len(eoL))
    # print(len(eoSplitter(i)))

    # eoLR 반복되는 문자열에서 뒤음절 제거 (2c)
    eoLR = []
    for j in eoL:
        # j: 어절
        while isTransitive(j): j = removeTransitive(j)
        eoLR.append(j)
    # print(eoLR)
    # print(len(eoLR))

    # 문자열/조사제거문자열 페어
    # for j in range(len(eoL)):
    #     print([eoL[j], eoLR[j]])

    # eoL에서 좌측으로부터 가장 긴 등록된 명사 (3c)
    eoLN = []
    for j in eoL:
        l = []
        l.append(j)
        for k in range(1, len(j)-1): # search str-1 to str up to 2 chars
            l.append(j[:-k])
        # print(l)

        for k in l:
            morphan = cb.m.pos(k) # Mecab을 다시 메모리에 넣어야하는지? 다음 테이블을 불러올 시 사전에 변경사항이 적용이 되는지 모르겠음.
            if len(morphan) == 1 and morphan[0][1][0] == 'N':
                eoLN.append(k)
                break
            if k == l[-1]: eoLN.append("") # last of the loop
    # print(eoLN)
    # print(len(eoLN))

    # for i in range(len(eoL)):
    #     print(eoL[i] + " " + eoLR[i] + " " + eoLN[i])

    # TF-IDF (5c?)
    tfidf = []
    for j in range(len(eoL)):
        ti = calcTFIDF(eoL[j], i, cb.corpusDocList)
        tfidf.append(ti)

    # 일치율 (4c)
    score = []
    for j in range(len(eoL)):
        # ratio = int(((len(eoLR[j]) + len(eoLN[j])) / (2 * len(eoL[j]))) * 100)
        ratio = int((max(len(eoLR[j]), len(eoLN[j])) / (len(eoL[j]))) * 100)

        # if len(eoLR[j]) == len(eoLN[j]) or tfidf[j] < 5: score.append(-ratio)
        # if len(eoLR[j]) == len(eoLN[j]): score.append(-ratio)
        # if len(eoL[j]) == len(eoLN[j]) or tfidf[j] < 8: score.append(-ratio)
        # if len(eoL[j]) == len(eoLN[j]): score.append(-1)
        if len(eoL[j]) == len(eoLN[j]) or tfidf[j] < 3.5: score.append(-1)
        else: score.append(ratio)

    # 문맥 (5c?)
    # 단순히 문자열을 검색하는것이기 때문에 우연히 같은 문자열을 찾아 문맥을 출력할 수도 있다는 단점이 있다.
    context = []
    radius = 10
    for j in range(len(eoL)):
        # wordstart = i.index(eoL[j])
        # wordend = wordstart + len(eoL[j])
        # if wordstart-radius < 0: start = 0
        # else: start = wordstart-radius
        # # context.append(i[start:wordend+radius])
        # context.append(i[start:wordstart] + "<" + i[wordstart:wordend] + ">" + i[wordend:wordend+radius])
        
        allIndex = [m.start() for m in re.finditer(eoL[j], i)]
        contextList = []
        for k in allIndex:
            wordstart = k
            wordend = wordstart + len(eoL[j])
            if wordstart-radius < 0: start = 0
            else: start = wordstart-radius
            contextList.append(i[start:wordstart] + "<" + i[wordstart:wordend] + ">" + i[wordend:wordend+radius])
        context.append("..." + "...".join(contextList) + "...")

    # df = DataFrame(eoL, eoLR, eoLN)
    # df = DataFrame(eoL, eoLR)
    # df = DataFrame(list(zip(eoL, eoLR, eoLN, score, tfidf)), columns =['최장일치', '조사제거', '기등록어', '%', 'TF-IDF']) 
    # df = DataFrame(list(zip(eoL, eoLR, eoLN, score)), columns =['최장일치', '조사제거', '기등록어', '%']) 
    df = DataFrame(list(zip(eoL, eoLR, eoLN, score, context)), columns =['최장일치', '조사제거', '기등록어', '%', '문맥']) 
    df = df[df["%"] > 0]
    sorted = df.sort_values(by=['%'], axis=0, ascending=False)
    sorted.to_csv(outputPath, encoding='euc-kr', index=False)
    print(sorted)
    # df.to_csv(r"C:/comfinder/outcsv.csv", encoding='euc-kr', index=False)
    # print(df)
    input("Press Enter to continue...")

# input 단일문서
# input = inputPath
# input = r"11월 입찰 예정 서울시 구로구 구로동에 위치한 `센터포인트 웨스트(구 서부금융센터)` 마스턴투자운용은 서울시 구로구 구로동 '센터포인트 웨스트(옛 서부금융센터)' 매각에 속도를 낸다.27일 관련업계에 따르면 마스턴투자운용은 지난달 삼정KPMG·폴스트먼앤코 아시아 컨소시엄을 매각 주관사로 선정한 후 현재 잠재 매수자에게 투자설명서(IM)를 배포하고 있는 단계다. 입찰은 11월 중순 예정이다.2007년 12월 준공된 '센터포인트 웨스트'는 지하 7층~지상 40층, 연면적 9만5000여㎡(약 2만8000평) 규모의 프라임급 오피스다. 판매동(테크노마트)과 사무동으로 이뤄졌다. 마스턴투자운용의 소유분은 사무동 지하 1층부터 지상 40층이다. 지하 1층과 지상 10층은 판매시설이고 나머지는 업무시설이다. 주요 임차인으로는 삼성카드, 우리카드, 삼성화재, 교보생명, 한화생명 등이 있다. 임차인의 대부분이 신용도가 높은 대기업 계열사 혹은 우량한 금융 및 보험사 등이다.'센터포인트 웨스트'는 서울 서남부 신도림 권역 내 최고층 빌딩으로 초광역 교통 연결성을 보유한 오피스 입지를 갖췄다고 평가받는다. 최근 신도림·영등포 권역은 타임스퀘어, 영시티, 디큐브시티 등 프라임급 오피스들과 함께 형성된 신흥 업무 권역으로 주목받고 있다고 회사 측은 설명했다.마스턴투자운용 측은   2021년 1분기를 클로징 예상 시점으로 잡고 있다  며   신도림 권역의 랜드마크로서 임대 수요가 꾸준해 안정적인 배당이 가능한 투자상품이 될 것  이라고 설명했다.한편 마스턴투자운용은 지난 2017년 말 신한BNP파리바자산운용으로부터 당시 '서부금융센터'를 약 3200억원에 사들였으며 이후 '센터포인트 웨스트'로 이름을 바꿨다.[김규리 기자 wizkim61@mkinternet.com]"
# input = r"글로벌빅데이터연구소,?약?22만개?사이트?대상?9개?증권사?빅데이터?분석투자자?관심도?1위는?하나금융투자,?관심도?상승률?1위는?미래에셋대우  [파이낸셜뉴스]지난해 국내 주요 증권사에 대한 투자자 관심도를 조사한 결과 '하나금융투자'가 가장 높았던 것으로 나타났다. 같은 기간 관심도 상승률은 '미래에셋대우'가 가장 높았다.   5일 글로벌빅데이터연구소는 지난해 온라인 22만개 사이트를 대상으로 국내 9개 증권사에 대해 빅데이터를 분석한 결과, 이 같은 결과가 도출됐다고 밝혔다. 정보량의 경우 2019년과의 비교 분석도 실시했다.   연구소가 임의선정한 분석 대상 증권사는 '정보량 순'으로 △하나금융투자 △미래에셋대우 △NH투자증권 △키움증권 △삼성증권 △신한금융투자 △한국투자증권 △KB증권 △대신증권(대표 오익근) 등 이다.   분석 결과 온라인 게시물 수(총정보량)를 의미하는 '투자자 관심도'의 경우 2020년 '하나금융투자'는 총 30만2318건을 기록, 2019년 21만8533건에 비해 8만3785건 38.34% 늘어나며 1위를 차지했다.   이들 자료를 일일이 클릭한 결과 하나금융투자 정보량 중 '리포트'가 높은 비중을 차지했으며 투자자들은 이들 리포트를 블로그나 커뮤니티 등에 다시 게시하는 경우가 많았다.   정보량 2위는 지난해 총 29만1151건을 기록한 '미래에셋대우'였다. '미래에셋대우'는 지난 2019년 17만4672건에 비해서 11만6479건 66.68% 대폭 급증하며 증가량은 물론 증가율면에서 9개 주요 증권사중 가장 높았다.   2019년 26만3473건으로 가장 높은 관심도를 기록했던 'NH투자증권'은 지난해 2만3795건 9.03% 늘어 28만7268건을 보이는데 그치며 3위를 차지했다.   이어 '키움증권', '삼성증권', '신한금융투자', '한국투자증권', 'KB증권' 등이 20만~26만건 대를 기록하며 큰 차이를 보이지 않았으나 2019년 대비 증가량은 5.97%부터 50.72%까지 천차만별이었다.   관심도가 가장 낮은 '대신증권'은 지난해 총 19만7532건으로 2019년 13만8974건에 비해서는 5만8558건 42.14% 늘었다.   9개 증권사 중 가장 높은 투자자 호감도를 기록한 곳은 '하나금융투자'로 나타났다. 리포트 주목도가 높았던 '하나금융투자'는 긍정률에서 부정률을 뺀 값인 '순호감도'에서 41.94%를 기록, 1위를 차지했다.   정보량 상승률 1위였던 '미래에셋대우'가 28.94%로 순호감도에서 2위를 차지하며 '하나금융투자'와 함께 두 부문 모두 높은 지표를 보였다.   이어 '삼성증권' 25.78%, '한국투자증권' 25.36%, 'NH투자증권' 23.84%, '신한금융투자' 22.97%, '키움증권' 22.50%, 'KB증권' 21.41% 순이었다.   '대신증권'은 15.35%로 순호감도 역시 가장 낮았다"
# input = r"우리나라의 1인가구가 매년 증가세를 보이는 가운데 지난해에는 600만을 넘어섰다. 가구 분포 역시 1인 가구는 30.2%를 차지해 2인 가구(27.8%), 3인 가구(20.7%), 4인 이상(21.2%)를 크게 앞지르며 대세를 이루고 있다. 특히 대전지역의 1인 가구 비율은 33.7%로 전년(32.6%) 대비 1.1% 증가했고 전국 1인 가구 비율보다는 3.5%가 더 높은 것으로 조사됐다. 향후 5년간 1인 가구 수가 매년 15만가구씩 증가할 것이라는 예측이 나오면서 유통업계에서는 1인 가구를 위한 소포장, 1인 메뉴 등을 출시하는데 열을 올리고 있다. 이러한 트렌드에 발맞춰 대전지역 롯데마트 3개 지점에서는 ‘한끼밥상’이라는 테마로 소포장 전문 코너를 만들어 운영 중이다. 농림축산식품부의 GAP(우수관리인증) 농산물을 990원부터 만나볼 수 있어 소비자로부터 좋은 반응을 보이고 있다. 실제로 대전지역 롯데마트 3개 지점(대덕점, 노은점, 서대전점)의 2020년 신선식품 中 소용량 상품군의 매출은 전년대비 12% 가까이 증가했다. 롯데마트 충청호남영업부문 배효권 부문장은 “1인 가구가 유통시장의 새로운 소비 주체로 떠오르면서 1~2인 가구를 겨냥한 소포장, 가정간편식 등과 같은 시장의 규모가 급성장할 것으로 예상된다”며 “롯데마트에서는 지역의 생산자와 손잡고 해당 상품군을 지속적으로 확대∙강화하는데 최선을 다하겠다”고 말했다."
# input = r"정부가 이르면 26일께 3월부터 적용할 새 거리두기 조정안 단계를 발표할 예정이다. 오는 28일 현행 거리두기 단계(수도권 2단계, 비수도권 1.5단계) 종료 이후 사회적 거리두기가 재상향될지 관심이 모아진다.    손영래 중앙사고수습본부 사회전략반장은 23일 코로나19 백브리핑에서  (이번주) 금요일(26일) 또는 토요일(27일) 정도 생각 중인데 내일 정례브리핑 때 정확히 공지하겠다 고 밝혔다.    설 연휴 이후 600명대까지 치솟았던 일일 확진자수가 이틀 연속 300명대를 유지했지만 정부는 다시 증가할 가능성이 크다고 전망했다.    손 반장은  오늘까지는 주말 검사 감소량으로 인한 확진자 감소 현상이 나타났다고 본다 며  내일부터는 조금 증가할 것 같고, 26일까지 증가 추이가 어느 정도 갈지 봐야 한다 고 말했다.    앞서 정부는 지난 18일 다음 달부터 업종별 집합금지를 최소화하는 대신 개인 간 사적모임을 규제하는 자율과 책임에 기반을 골자로 하는 기본 방향을 내놨다.    이번 사회적 거리두기 개편안에는 현행 5단계(1→1.5→2→2.5→3단계)의 단점을 보완하는 대책도 담길 전망이다. 앞서 정부는 지난해 6월 3단계 체계의 거리두기를 적용하다가 같은해 11월 5단계로 개편한 바 있다. 0.5단계 차이로 세분화돼 있는 현행 체계는 단계별 대국민 행동 메시지가 분명하지 않아 위험성을 인지하기가 쉽지 않다는 지적이 제기돼 왔다.    식당이나 카페 등 다중이용시설에 대해서는 영업을 금지하는 집합금지는 최소화할 예정이다. 다만, 시설의 감염 취약 요인을 제거하기 위한 밀집도를 조정하기 위한 '인원제한'은 이어간다는 방침이다.    정세균 국무총리는 이날 중대본 회의에서  방역수칙 위반 업소에 대해서는 현재 시행 중인 '원스트라이크 아웃 제도'를 예외 없이 적용하고 곧 지급할 4차 재난지원금 지원 대상에서도 제외할 것 이라고 강조했다."
# input = r"연초부터 무섭게 솟아오르던 비트코인 가격이 조정을 보이고 있다. 주요 투자 기관들의 잇따른 참여에도 불구, 미국 정부가 비트코인의 안정성과 적법성에 대해 강한 의구심을 표하면서 참여자들 사이에서 거품 논란과 규제 이슈 등으로 불안감이 형성된 탓이다. 그럼에도 이젠 비트코인 투자에 유의해야 할 때란 의견과 단기 조정을 거쳐 재반등할 것이란 주장이 팽팽히 맞서고 있다.    지난주 사상 첫 5만달러대에 진입한 비트코인 가격은 24일 현재 4만달러대로 떨어졌다. 재닛 옐런 미 재무장관이 지난 23일 뉴욕타임스 딜북 콘퍼런스에서 비트코인에 대해 “화폐를 거래하는 데 극도로(extremely) 비효율적인 방법”이라며 “투기성이 강한 자산이며, 극도로(extremely) 변동성이 있단 점을 인지해야 한다”고 말했다.    이처럼 옐런의 입에서 ‘극도로’란 표현을 여러번 사용할 정도로 비트코인에 대해 강한 경계 발언이 나온 것을 기점으로 시장의 우려가 증폭됐다. 안 그래도 일론 머스크 테슬라 최고경영자(CEO)가 가상자산 가격이 높아 보인다고 발언한 상황에서 기름을 끼얹는 격이었다.  마크 해펠 UBS 글로벌 자산운용 최고투자책임자(CIO)는 성명을 통해 “우리는 고객들에게 가상자산 투기에 주의를 기울여야 한다고 조언하고 있다”며 “규제 리스크가 아직 해소되지 않은 상황에서 (비트코인의) 미래는 여전이 불투명하다”고 밝혔다. 미국 투자 전문지 배런스도 비트코인의 버블이 터줄 수 있어 관련주 역풍에 주의해야 한다고 보도했다.    우리나라에서도 비트코인에 대한 우려 목소리가 커지고 있다. 이주열 한국은행 총재는 지난 23일 가상자산에 대해 ‘내재가치(intrinsic value)’가 없다고 평가했다. 내재가치는 자산가치와 수익가치를 아우른 개념으로 우리나라 중앙은행의 수장이 비트코인을 공인 자산으로 인정받기 어렵다는 견해를 밝힌 것이라고 볼 수 있다.  한편 비트코인 강세론자들은 현재의 하락 국면이 추가 매수 유인이 될 수 있다는 입장이다. 캐시 우드 아크 인베스트 CEO는 한 인터뷰에서 “우리는 비트코인에 대해 매우 긍정적이며, 지금 건강한 조정(healthy correction)을 볼 수 있어 매우 행복하다”고 말했다.    전세계 처음으로 캐나다에서 출시된 비트코인 상장지수펀드(퍼포즈 비트코인 ETF)는 흥행 기록을 이어가고 있다. 가상자산 분석업체 글라스노드에 따르면 퍼포즈 ETF로의 자금 유입이 지속되면서 23일 현재 운용규모(AUM)가 5억6400만달러(약 6300억원)에 달하고 있다.  "
# input = r"(서울=뉴스1) = 은성수 금융위원장이 3일 서울 종로구 정부서울청사 합동브리핑실에서 공매도 부분적 재개 관련 내용을 발표하고 있다.  금융위원회는 오는 3월15일 종료 예정인 공매도 금지 조치를 5월2일까지 연장하고 5월3일부터 코스피200·코스닥150 주가지수 구성종목에 대해 공매도를 부분 재개하기로 했다.  (금융위원회 제공) 2021.2.3/뉴스1 한국 정부의 공매도 금지 연장이 유동성 급감 등 부작용을 초래할 수 있다는 우려가 제기된다고 블룸버그통신이 5일 보도했다. 블룸버그통신은 이날 '세계 최장 공매도 금지국이 시장 하락이란 위험을 시장 하락이란 위험을 감수하고 있다'는 제목의 기사에서 한국의 공매도 금지 연장이 역효과를 초래할 수 있다고 전했다. 한국의 공매도 금지 연장이 세계에서 가장 길다는 점을 부각하면서다. 인도네시아는 이번달 연장을 종료할 예정이며, 지난해 초 공매도 금지를 단행한 프랑스는 제한을 몇 달만 유지했다. 통신은 한국의 공매도 금지가 한국 증시 랠리를 인위적으로 지지해 왔다는 데 대한 펀드매니저와 트레이더들의 우려가 늘어나고 있다고 지적했다. 그러면서 공매도 금지를 연장하기로 한 결정이 역효과를 낼 수 있다는 예상이 제기된다고 전했다. 호주 시드니 소재 AMP 캐피탈의 나데르 네이미 다이내믹 마킷 대표는 블룸버그에  한국 증시 강세장 속 공매도 금지 연장은 놀랍다 며  미국에서 일어난 것 같은 숏스퀴즈를 피하기 위한 목적이지만 시장 유동성의 급감이라는 의도치 않은 결과가 일어날 수 있다 고 예상했다.미국 인지브릿지캐피탈의 빈스 로루소 펀드매니저도  공매도 금지가 시장 유동성을 개선하고 변동성을 줄인다는 증거는 많지 않다 며  공매도 금지는 적정 주가를 찾기 위한 중요한 시장 도구들을 빼앗는 것 이라고 했다. 정치적인 고려에 의해 내려진 결정일 수 있다는 점도 지적했다. 전경대 맥쿼리투신운용 주식운용본부장(CIO)은  한국 정치인들에 의한 포퓰리즘이 금지 연장을 이끈 것 같다 며  (감독당국이) 여론에 흔들리고 있다는 점이 유감스럽다 고 밝혔다. 지난 3일 금융위원회는 3월15일 종료가 예정된 공매도 금지조치를 5월2일까지 연장한다고 밝혔다. 5월3일부터 코스피200·코스닥150 대표지수 종목에 한해 부분적으로 공매도를 재개하는 방식이다"
# input = inputToFormat(inputPath, 16)
# input = inputToFormat(inputPath, 45)

# 단일문서 leftLongestCommonSub mode 3 출력
# print(leftLongestCommonSub("미래에셋대우스팩4호", cb.corpusEoList, 3))
# print(leftLongestCommonSub("한샘", cb.corpusEoList, 3))
# print(range(len(eoShortener("한샘"))))
# print(leftLongestCommonSub("---------------------------------------", cb.corpusEoList, 3))

# 단일문서 eoL 출력
# print(eoListBuilder(inputPath, 45, cb.corpusEoList))

# 단일문서 extractList 출력
# print(extractList(eoListBuilder(inputPath, 45, cb.corpusEoList)))

# 단일문서 RP 출력
# print(eoListBuilder(input, 0, cb.corpusEoList, 2))

# 말뭉치 전체 RP 출력
# for i in cb.corpusDocList:
#     print(eoListBuilder(i, 0, cb.corpusEoList, 2))

# 문서(input)와 말뭉치(inputPath)에 대한 단어(text)의 TF-IDF 계산
# text = "미래에셋대우스팩4호"
# print(calcTFIDF(text, input, cb.corpusDocList))

# 모든 조사를 제거
# word = "순이었다"
# while isTransitive(word): word = removeTransitive(word)
# print(word)
