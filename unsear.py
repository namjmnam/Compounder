# coding=UTF-8
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

# 어절 리스트를 대상으로 입력 문자열을 각 어절의 좌측에서 검색하여 나온 결과를 출력
def LPSearcher(inputText, eoList):
    out = []
    max = len(inputText)
    for i in eoList:
        if len(i) >= max and i[0:max] == inputText: out.append(i)
    # print(out) # 포함된 어절을 모두 콘솔에 출력
    return len(out)

# 입력 문자열이 2자가 될 때 까지 오른쪽에서부터 한 문자씩 줄여 리스트로 출력
def eoShortener(inputText):
    out = []
    max = len(inputText)
    for i in range(len(inputText)-1):
        out.append(inputText[0:max-i])
    return out

# 최장공통 부분문자열을 추출하는 반복문
def longestSub(inputText, eoList):
    track = []
    for i in range(len(eoShortener(inputText))):
        word = eoShortener(inputText)[i]
        res = LPSearcher(word, eoList)
        wordBefore = eoShortener(inputText)[i-1]
        if len(track) > 0:
            if res == track[-1] and res > 1:
                # 한 문자 줄였는데도 빈도가 같을 경우 그 전 부분문자열을 채택
                # print("found " + wordBefore)
                return wordBefore
        track.append(res)


str = "관심도를"
eoL = ['글로벌빅데이터연구소', '사이트', '증권사', '빅데이터', '분석투자자', '관심도', '하나금융투자', '관심도', '상승률', '미래에셋대우', '파이낸셜뉴스', '지난해', '증권사에', '투자자', '관심도를', '조사한', '하나금융투자', '높았던', '것으로', '나타났다.', '관심도', '상승률은', '미래에셋대우', '높았다.', '글로벌빅데이터연구소는', '지난해', '온라인', '사이트를', '대상으로', '증권사에', '빅데이터를', '분석한', '결과가', '도출됐다고', '밝혔다.', '정보량의', '분석도', '실시했다.', '연구소가', '임의선정한', '증권사는', '정보량', '하나금융투자', '미래에셋대우', 'NH투자증권', '키움증권', '삼성증권', '신한금융투자', '한국투자증권', 'KB증권', '이다.', '온라인', '게시물', '의미하는', '투자자', '관심도', '하나금융투자', '늘어나며', '차지했다.', '자료를', '일일이', '클릭한', '하나금융투자', '정보량', '리포트', '비중을', '차지했으며', '투자자들은', '리포트를', '블로그나', '커뮤니티', '게시하는', '경우가', '많았다.', '정보량', '지난해', '기록한', '미래에셋대우', '였다.', '미래에셋대우', '비해서', '급증하며', '증가량은', '증가율면에서', '증권사중', '높았다.', '관심도를', '기록했던', 'NH투자증권', '지난해', '보이는데', '그치며', '차지했다.', '키움증권', '삼성증권', '신한금융투자', '한국투자증권', 'KB증권', '기록하며', '차이를', '보이지', '않았으나', '증가량은', '천차만별이었다.', '관심도가', '대신증권', '지난해', '비해서는', '늘었다.', '증권사', '투자자', '호감도를', '기록한', '하나금융투자', '나타났다.', '리포트', '주목도가', '높았던', '하나금융투자', '긍정률에서', '부정률을', '순호감도', '차지했다.', '정보량', '상승률', '미래에셋대우', '순호감도에서', '차지하며', '하나금융투자', '지표를', '보였다.', '삼성증권', '한국투자증권', 'NH투자증권', '신한금융투자', '키움증권', 'KB증권', '순이었다.', '대신증권', '순호감도', '낮았다', '수(총정보량)를']

out = []
for i in eoL: # 이 eoList는 문서 단위의 eoList
    # print(longestSub(i, eoL)) # 이 eoList는 corpusEoList를 사용하는것이 맞음
    out.append(longestSub(i, eoL))
print(out)