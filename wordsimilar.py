# coding=UTF-8
import re

from numpy import dot
from numpy.linalg import norm
import numpy as np

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

def containIndex(wordlist, word):
    return [i for i in range(len(wordlist)) if word in wordlist[i]]

def aroundIndex(indexlist, maxindex, distance=2):
    out = []
    for i in indexlist:
        temp = list(range(i-distance,i+1+distance))
        for j in temp:
            # if j >=0 and j < maxindex and j not in indexlist: out.append(j) # 자신이 포함된 어절의 인덱스 포함 안함
            if j >=0 and j < maxindex: out.append(j)
    out = list(dict.fromkeys(out))
    out.sort()
    return out

def wordEmbedding(eojeollist, nounlist, word, distance=2):
    out = []
    wordindices = containIndex(eojeollist, word)
    aroundindices = aroundIndex(wordindices, len(eojeollist), distance)
    stringaround = ' '.join([eojeollist[i] for i in aroundindices])
    # print(stringaround)
    for i in nounlist:
        if i in stringaround: out.append(1)
        else: out.append(0)
    # print(out)
    return(out)

def cosineSimilarity(A, B):
    return dot(A, B)/(norm(A)*norm(B))

text = r"11월 입찰 예정서울시 구로구 구로동에 위치한 `센터포인트 웨스트(구 서부금융센터)` 마스턴투자운용은 서울시 구로구 구로동 '센터포인트 웨스트(옛 서부금융센터)' 매각에 속도를 낸다.27일 관련업계에 따르면 마스턴투자운용은 지난달 삼정KPMG·폴스트먼앤코 아시아 컨소시엄을 매각 주관사로 선정한 후 현재 잠재 매수자에게 투자설명서(IM)를 배포하고 있는 단계다. 입찰은 11월 중순 예정이다.2007년 12월 준공된 '센터포인트 웨스트'는 지하 7층~지상 40층, 연면적 9만5000여㎡(약 2만8000평) 규모의 프라임급 오피스다. 판매동(테크노마트)과 사무동으로 이뤄졌다. 마스턴투자운용의 소유분은 사무동 지하 1층부터 지상 40층이다. 지하 1층과 지상 10층은 판매시설이고 나머지는 업무시설이다. 주요 임차인으로는 삼성카드, 우리카드, 삼성화재, 교보생명, 한화생명 등이 있다. 임차인의 대부분이 신용도가 높은 대기업 계열사 혹은 우량한 금융 및 보험사 등이다.'센터포인트 웨스트'는 서울 서남부 신도림 권역 내 최고층 빌딩으로 초광역 교통 연결성을 보유한 오피스 입지를 갖췄다고 평가받는다. 최근 신도림·영등포 권역은 타임스퀘어, 영시티, 디큐브시티 등 프라임급 오피스들과 함께 형성된 신흥 업무 권역으로 주목받고 있다고 회사 측은 설명했다.마스턴투자운용 측은   2021년 1분기를 클로징 예상 시점으로 잡고 있다  며   신도림 권역의 랜드마크로서 임대 수요가 꾸준해 안정적인 배당이 가능한 투자상품이 될 것  이라고 설명했다.한편 마스턴투자운용은 지난 2017년 말 신한BNP파리바자산운용으로부터 당시 '서부금융센터'를 약 3200억원에 사들였으며 이후 '센터포인트 웨스트'로 이름을 바꿨다.[김규리 기자 wizkim61@mkinternet.com]"
eoList = cleanText(text).split(' ')
# eojeols = ['11월', '입찰', '예정서울시', '구로구', '구로동에', '위치한', '센터포인트', '웨스트', '구', '서부금융센터', '마스턴투자운용은', '서울시', '구로구', '구로동', '센터포인트', '웨스트', '옛', '서부금융센터', '매각에', '속도를', '낸다.', '27일', '관련업계에', '따르면', '마스턴투자운용은', '지난달', '삼정KPMG', '폴스트먼앤코', '아시아', '컨소시엄을', '매각', '주관사로', '선정한', '후', '현재', '잠재', '매수자에게', '투자설명서', 'IM', '를', '배포하고', '있는', '단계다.', '입찰은', '11월', '중순', '예정이다.', '2007년', '12월', '준공된', '센터포인트', '웨스트', '는', '지하', '7층', '지상', '40층', '연면적', '9만5000여', '약', '2만8000평', '규모의', '프라임급', '오피스다.', '판매동', '테크노마트', '과', '사무동으로', '이뤄졌다.', '마스턴투자운용의', '소유분은', '사무동', '지하', '1층부터', '지상', '40층이다.', '지하', '1층과', '지상', '10층은', '판매시설이고', '나머지는', '업무시설이다.', '주요', '임차인으로는', '삼성카드', '우리카드', '삼성화재', '교보생명', '한화생명', '등이', '있다.', '임차인의', '대부분이', '신용도가', '높은', '대기업', '계열사', '혹은', '우량한', '금융', '및', '보험사', '등이다.', '센터포인트', '웨스트', '는', '서울', '서남부', '신도림', '권역', '내', '최고층', '빌딩으로', '초광역', '교통', '연결성을', '보유한', '오피스', '입지를', '갖췄다고', '평가받는다.', '최근', '신도림', '영등포', '권역은', '타임스퀘어', '영시티', '디큐브시티', '등', '프라임급', '오피스들과', '함께', '형성된', '신흥', '업무', '권역으로', '주목받고', '있다고', '회사', '측은', '설명했다.', '마스턴투자운용', '측은', '2021년', '1분기를', '클로징', '예상', '시점으로', '잡고', '있다', '며', '신도림', '권역의', '랜드마크로서', '임대', '수요가', '꾸준해', '안정적인', '배당이', '가능한', '투자상품이', '될', '것', '이라고', '설명했다.', '한편', '마스턴투자운용은', '지난', '2017년', '말', '신한BNP파리바자산운용으로부터', '당시', '서부금융센터', '를', '약', '3200억원에', '사들였으며', '이후', '센터포인트', '웨스트', '로', '이름을', '바꿨다.', '김규리', '기자']
nouns = ['예정', '구로', '센터포인트', '웨스트', '서부금융센터', '마스턴투자운용', '서울시', '투자', '프라임급', '오피스', '판매', '사무동', '1층', '임차인', '삼성', '있다', '신도림', '권역', '설명했다.']

# containindexlist = containIndex(eoList, '센터')
# aroundindexlist = aroundIndex(containindexlist, len(eoList))
# print(containindexlist)
# print(aroundindexlist)

listofwordvectors = [wordEmbedding(eoList, nouns, i) for i in nouns]
for i in listofwordvectors:
    s = [cosineSimilarity(i, j) for j in listofwordvectors]
    out = sorted(range(len(s)), key=lambda k: s[k])
    # print(out[-1])
    print(nouns[out[-1]] + ' ' + nouns[out[-2]])
    # foobar = [nouns[j] for j in out]
    # print(foobar)
