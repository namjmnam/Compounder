# coding=UTF-8
import math
import re

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

class Splitter:
    def __init__(self, inputText, inputCorpus=None):
        
        # 원문 문서에서 신조어 추출
        # 파이썬 버전 3.6
        # 설치할 패키지: eunjeon, pandas
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
        self.rawdoc = self.trim_str(inputText)
        self.doc = self.clean_str(inputText)
        # corpus = 말뭉치. 데이터 형태 미정 (사용불가능, 비활성)
        if inputCorpus == None: self.corpus = ' ' + self.doc
        else: self.corpus = self.clean_str(' ' + inputCorpus)

        # wTotal = 말뭉치 총 어절 수
        self.wTotal = self.corpus.count(' ')

        l = self.doc.split(' ')
        self.eoList = [i for i in l if len(re.sub(r'[0-9]+', '-', i)) >= 3]

        # 괄호가 포함된 어절 출력
        missed = []
        for i in self.eoList:
            if i.count("(") > 0 and i.count(")") > 0:
                missed.append(i[i.find("(")+1:i.find(")")])
                continue
            if i.count("(") > 0:
                missed.append(i.split("(",1)[1])
            if i.count(")") > 0:
                missed.append(i[:-1])
        parenthesisless = [x for x in self.eoList if  not '(' in x and not ')' in x] + [x for x in self.eoList if '(' in x and ')' in x]
        parenthesisless += missed
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
                # 현재는 단순히 말뭉치에 띄어쓰기+단어가 검색된 갯수만 찾지만 본래 어절의 좌측부분만 검색하도록 해야 함
                # 문제점1: 말뭉치는 클렌징이 되어있지 않음
                # 문제점2: 기존에 이미 발견된 명사를 제외한 말뭉치에서 검색해야 함
                scores.append(self.corpus.count(' ' + i[j]) / self.wTotal)
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
            if finalscore >= 2 / self.wTotal: self.extnouns.append(chosen)
        self.extnouns = list(dict.fromkeys(self.extnouns))

        # 여기서 Mecab은 기존에 등록된 명사인지 아닌지 판단하기 위해 + 끝에 조사가 오는 단어를 제거하기 위해 사용
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

        # 단어 주변 문자열을 수집
        self.surroundings = []
        sentList = self.splitSentences(self.doc)
        self.ndistance = 10
        for i in self.extnouns:
            addedstr = ""
            for j in sentList:
                temp = j
                while i in temp:
                    search = re.search(i, temp)
                    if (search.start()-self.ndistance < 0): l = temp[0:search.start()]
                    else: l = temp[search.start()-self.ndistance:search.start()]
                    l += temp[search.end():search.end()+self.ndistance]
                    temp = temp.replace(i, '', 1)
                    addedstr += l
            self.surroundings.append(addedstr)
        self.conndict = dict(zip(self.extnouns, self.surroundings))

        # 복합단어 추출 프로토타입
        self.pairList = []
        for i in self.extnouns:
            for j in self.extnouns:
                # rawdoc으로 검색할 수도 있고 corpus로 검색할 수도 있음
                if self.searchSpaceless([i, j], self.rawdoc): self.pairList.append([i ,j])

        cwlist = []
        for i in self.pairList:
            cwlist.append(' '.join(i))
        pmiList = []
        for i in self.pairList:
            pmiList.append(self.getPMI(i, self.wTotal, self.rawdoc))        
        self.cwdict = dict(zip(cwlist, pmiList))

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
        text = re.sub('\b[0-9]+\b\s*', '', text)
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
        if eojeol[-1] == '.': eojeol = eojeol[:-1]
        for i in range(2, len(eojeol)+1):
            out.append(eojeol[:i])
        return out

    # 클렌징된 텍스트를 문장 단위로 분리
    def splitSentences(self, doc):
        return doc.split('. ')

    # 리스트 형태의 복합단어를 문서 전체에서 검색
    def searchSpaceless(self, wordpair, target):
        # 본문에서 띄어쓰기를 제외한 채로 검색할 경우:
        return target.replace(' ','').count(''.join(wordpair))

    # 리스트 형태의 복합단어를 문서 전체에 대해서 PMI 계산
    def getPMI(self, wordpair, wordcount, target):
        # 분자 = p(w1, w2, ...)
        numerator = self.searchSpaceless(wordpair, target) / wordcount
        if numerator == 0: return 0
        # 분모 = p(w1) * p(w2) * ...
        denominator = 1
        for i in wordpair:
            denominator *= target.count(i) / wordcount
        # print(numerator)
        # print(denominator)
        pmi = math.log(numerator / denominator)
        return pmi

text = r"11월 입찰 예정 서울시 구로구 구로동에 위치한 `센터포인트 웨스트(구 서부금융센터)` 마스턴투자운용은 서울시 구로구 구로동 '센터포인트 웨스트(옛 서부금융센터)' 매각에 속도를 낸다.27일 관련업계에 따르면 마스턴투자운용은 지난달 삼정KPMG·폴스트먼앤코 아시아 컨소시엄을 매각 주관사로 선정한 후 현재 잠재 매수자에게 투자설명서(IM)를 배포하고 있는 단계다. 입찰은 11월 중순 예정이다.2007년 12월 준공된 '센터포인트 웨스트'는 지하 7층~지상 40층, 연면적 9만5000여㎡(약 2만8000평) 규모의 프라임급 오피스다. 판매동(테크노마트)과 사무동으로 이뤄졌다. 마스턴투자운용의 소유분은 사무동 지하 1층부터 지상 40층이다. 지하 1층과 지상 10층은 판매시설이고 나머지는 업무시설이다. 주요 임차인으로는 삼성카드, 우리카드, 삼성화재, 교보생명, 한화생명 등이 있다. 임차인의 대부분이 신용도가 높은 대기업 계열사 혹은 우량한 금융 및 보험사 등이다.'센터포인트 웨스트'는 서울 서남부 신도림 권역 내 최고층 빌딩으로 초광역 교통 연결성을 보유한 오피스 입지를 갖췄다고 평가받는다. 최근 신도림·영등포 권역은 타임스퀘어, 영시티, 디큐브시티 등 프라임급 오피스들과 함께 형성된 신흥 업무 권역으로 주목받고 있다고 회사 측은 설명했다.마스턴투자운용 측은   2021년 1분기를 클로징 예상 시점으로 잡고 있다  며   신도림 권역의 랜드마크로서 임대 수요가 꾸준해 안정적인 배당이 가능한 투자상품이 될 것  이라고 설명했다.한편 마스턴투자운용은 지난 2017년 말 신한BNP파리바자산운용으로부터 당시 '서부금융센터'를 약 3200억원에 사들였으며 이후 '센터포인트 웨스트'로 이름을 바꿨다.[김규리 기자 wizkim61@mkinternet.com]"
# text = r"글로벌빅데이터연구소,?약?22만개?사이트?대상?9개?증권사?빅데이터?분석투자자?관심도?1위는?하나금융투자,?관심도?상승률?1위는?미래에셋대우  [파이낸셜뉴스]지난해 국내 주요 증권사에 대한 투자자 관심도를 조사한 결과 '하나금융투자'가 가장 높았던 것으로 나타났다. 같은 기간 관심도 상승률은 '미래에셋대우'가 가장 높았다.   5일 글로벌빅데이터연구소는 지난해 온라인 22만개 사이트를 대상으로 국내 9개 증권사에 대해 빅데이터를 분석한 결과, 이 같은 결과가 도출됐다고 밝혔다. 정보량의 경우 2019년과의 비교 분석도 실시했다.   연구소가 임의선정한 분석 대상 증권사는 '정보량 순'으로 △하나금융투자 △미래에셋대우 △NH투자증권 △키움증권 △삼성증권 △신한금융투자 △한국투자증권 △KB증권 △대신증권(대표 오익근) 등 이다.   분석 결과 온라인 게시물 수(총정보량)를 의미하는 '투자자 관심도'의 경우 2020년 '하나금융투자'는 총 30만2318건을 기록, 2019년 21만8533건에 비해 8만3785건 38.34% 늘어나며 1위를 차지했다.   이들 자료를 일일이 클릭한 결과 하나금융투자 정보량 중 '리포트'가 높은 비중을 차지했으며 투자자들은 이들 리포트를 블로그나 커뮤니티 등에 다시 게시하는 경우가 많았다.   정보량 2위는 지난해 총 29만1151건을 기록한 '미래에셋대우'였다. '미래에셋대우'는 지난 2019년 17만4672건에 비해서 11만6479건 66.68% 대폭 급증하며 증가량은 물론 증가율면에서 9개 주요 증권사중 가장 높았다.   2019년 26만3473건으로 가장 높은 관심도를 기록했던 'NH투자증권'은 지난해 2만3795건 9.03% 늘어 28만7268건을 보이는데 그치며 3위를 차지했다.   이어 '키움증권', '삼성증권', '신한금융투자', '한국투자증권', 'KB증권' 등이 20만~26만건 대를 기록하며 큰 차이를 보이지 않았으나 2019년 대비 증가량은 5.97%부터 50.72%까지 천차만별이었다.   관심도가 가장 낮은 '대신증권'은 지난해 총 19만7532건으로 2019년 13만8974건에 비해서는 5만8558건 42.14% 늘었다.   9개 증권사 중 가장 높은 투자자 호감도를 기록한 곳은 '하나금융투자'로 나타났다. 리포트 주목도가 높았던 '하나금융투자'는 긍정률에서 부정률을 뺀 값인 '순호감도'에서 41.94%를 기록, 1위를 차지했다.   정보량 상승률 1위였던 '미래에셋대우'가 28.94%로 순호감도에서 2위를 차지하며 '하나금융투자'와 함께 두 부문 모두 높은 지표를 보였다.   이어 '삼성증권' 25.78%, '한국투자증권' 25.36%, 'NH투자증권' 23.84%, '신한금융투자' 22.97%, '키움증권' 22.50%, 'KB증권' 21.41% 순이었다.   '대신증권'은 15.35%로 순호감도 역시 가장 낮았다"
# text = r"우리나라의 1인가구가 매년 증가세를 보이는 가운데 지난해에는 600만을 넘어섰다. 가구 분포 역시 1인 가구는 30.2%를 차지해 2인 가구(27.8%), 3인 가구(20.7%), 4인 이상(21.2%)를 크게 앞지르며 대세를 이루고 있다. 특히 대전지역의 1인 가구 비율은 33.7%로 전년(32.6%) 대비 1.1% 증가했고 전국 1인 가구 비율보다는 3.5%가 더 높은 것으로 조사됐다. 향후 5년간 1인 가구 수가 매년 15만가구씩 증가할 것이라는 예측이 나오면서 유통업계에서는 1인 가구를 위한 소포장, 1인 메뉴 등을 출시하는데 열을 올리고 있다. 이러한 트렌드에 발맞춰 대전지역 롯데마트 3개 지점에서는 ‘한끼밥상’이라는 테마로 소포장 전문 코너를 만들어 운영 중이다. 농림축산식품부의 GAP(우수관리인증) 농산물을 990원부터 만나볼 수 있어 소비자로부터 좋은 반응을 보이고 있다. 실제로 대전지역 롯데마트 3개 지점(대덕점, 노은점, 서대전점)의 2020년 신선식품 中 소용량 상품군의 매출은 전년대비 12% 가까이 증가했다. 롯데마트 충청호남영업부문 배효권 부문장은 “1인 가구가 유통시장의 새로운 소비 주체로 떠오르면서 1~2인 가구를 겨냥한 소포장, 가정간편식 등과 같은 시장의 규모가 급성장할 것으로 예상된다”며 “롯데마트에서는 지역의 생산자와 손잡고 해당 상품군을 지속적으로 확대∙강화하는데 최선을 다하겠다”고 말했다."
s = Splitter(text)
# print(s.extnouns)
# print(s.surroundings)
# print(s.pairList)
print(s.cwdict)
