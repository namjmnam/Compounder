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
        self.doc = self.clean_str(inputText)
        # corpus = 말뭉치. 데이터 형태 미정 (사용불가능, 비활성)
        if inputCorpus == None: self.corpus = self.doc
        else: self.corpus = inputCorpus

        # eoList = ["어절1", "어절2", "어절3", ...] 한 문서 내 4자 이상의 어절 리스트, 숫자는 한 문자로 취급
        # 괄호 속 문장 추출하여 문서에 추가, 현재 첫 번째 괄호 외 추출 안 되고 있음 (사용불가, 비활성)
        # s = self.doc + ' '
        # missed = ' '
        # while s.count("(") > 0 and s.count(")") > 0:
        #     p = s[s.find("(")+1:s.find(")")]
        #     missed += p
        # s += missed
        # tempdoc = s
        l = self.doc.split(' ')
        self.eoList = [i for i in l if len(re.sub(r'[0-9]+', '-', i)) >= 4]

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
        self.eoList = parenthesisless

        # [LP, UM, RP] 형태가 가능한 모든 조합을 리스트로 구축
        self.posUMpairList = []
        for i in range(len(self.eoList)):
            for j in self.splitEojeol(self.eoList[i]):
                # RP가 알려진 단어로 이루어져있는지 확인(확인된 경우 KRP라고 부름) 후 등록
                if self.isKnown(j[2]):
                    self.posUMpairList.append(j)

        # partialEoList: 모든 부분어절의 리스트: ["어절1부분1", "어절1부분2", ...] # (사용가능, 비활성)
        # self.partialEoList = []
        # for i in self.eoList:
        #     for j in self.eojeolPart(i):
        #         self.partialEoList.append(j)

        # lplist: 모든 어절의 2자 이상의 LP부분 리스트: [["어절1LP1", "어절1LP2", ...], ["어절2LP1", "어절2LP2", ...], ...]
        self.lplist = []
        iter = self.eoList[:]
        iter = list(dict.fromkeys(iter))
        for i in iter:
            if len(i) > 1: self.lplist.append(self.genLP(i))

        # 디버깅용
        # for i in self.genLP("마스턴투자운용의"):
        #     print(i + " : " + str(self.corpus.count(i) / len(self.eoList)))
        # for i in self.genLP("업무시설이다"):
        #     print(i + " : " + str(self.corpus.count(i) / len(self.eoList)))

        # 명사로 추정되는 문자열 리스트 추출 -> extnouns
        self.extnouns = []
        for i in self.lplist:
            scores = []
            finalscore = 0
            chosen = ''
            for j in range(len(i)):
                scores.append(self.corpus.count(i[j]) / len(self.eoList))
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
            # 빈도율이 4% 이상인 경우 채택
            if finalscore > 0.04: self.extnouns.append(chosen)
        self.extnouns = list(dict.fromkeys(self.extnouns))

        m = Mecab()
        # m = Mecab(dicpath='C:/mecab/mecab-ko-dic') # (사용불가능, 비활성)
        # m = Mecab(dicpath='/usr/local/lib/mecab/dic/mecab-ko-dic') # (사용불가능, 비활성)
        # 한글이 아닌 문자가 갈라지는 경우 제외
        # 예: ['신한BN', 'P파리', '바자산운용으로부터'], ['', '320', '0억원에'] 등
        temp = self.posUMpairList[:]
        for i in self.posUMpairList:
            # LP가 빈 문자열이 아니고 LP의 마지막 글자와 UM의 첫 글자가 모두 한글이외 문자일 경우 후보에서 제거
            if len(i[0]) > 0 and m.pos(i[0][-1])[0][1][0] == 'S' and m.pos(i[1][0])[0][1][0] == 'S': temp.remove(i)
            # RP가 빈 문자열이 아니고 UM의 마지막 글자와 RP의 첫 글자가 모두 한글이외 문자일 경우 후보에서 제거
            elif len(i[2]) > 0 and m.pos(i[1][-1])[0][1][0] == 'S' and m.pos(i[2][0])[0][1][0] == 'S': temp.remove(i)
        # 결과물은 LP+UM+KRP의 리스트
        self.posUMpairList = temp

        # candidates: 신조어 최종 후보 리스트
        self.candidates = []
        for i in self.posUMpairList:
            # KRP가 비어있는 경우: UM을 말뭉치에 대해 검색하여 3번 이상 등장할 경우 LP+UM 등록
            if i[2] == '' and self.corpus.count(i[1]) >= 3:
                self.candidates.append(i[0]+i[1])
            # KRP가 비어있지 않은 경우: UM+KRP[0](KRP의 첫 형태소)를 말뭉치에 대해 검색하여 3번 이상 등장할 경우 LP+UM 등록
            elif i[2] != '' and self.corpus.count(i[1]+m.morphs(i[2])[0]) >= 3:
                self.candidates.append(i[0]+i[1])
        self.candidates = list(dict.fromkeys(self.candidates))

        # 기타 아이디어
        # RP를 말뭉치에 대해서 검색하고 UM을 말뭉치에 대해서 검색하여 RP의 비율이 더 많은 경우 KRP로 가정할 수 있는지?
        # m.morphs(eojeol)로 분리시킨 뒤 그 모든 조합을 나열(self.combinePart)하여 그 안에 특정 부분어절이 없는 경우 UM 후보로 등록하는지?
        # 그리고 그 안에 ULP(LP+UM)가 포함되어있다면 어떻게 할지?
        # UM+KM(KRP[0], KRP의 첫번째 형태소)의 조합을 말뭉치에 대해 검색?
        # 아니면 ULP+KM을 말뭉치에 대해 검색?
        # RP가 명사 다음에 올 수 있는 경우 KRP로 인정?
        
        # print(self.isKnown("벫뗗"))

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
        pattern = r'([ㄱ-ㅎ|ㅏ-ㅣ|가-힣].[ㄱ-ㅎ|ㅏ-ㅣ|가-힣]*)\.'
        text = re.sub(pattern=pattern, repl=r'\1 ', string=text)

        text = re.sub(r'(^[ \t]+|[ \t]+(?=:))', '', text, flags=re.M)
        text = text.replace('\n', ' ')
        text = text.replace('\t', ' ')
        text = text.replace('\r', ' ')
        text = re.sub(r'\b[0-9]+\b\s*', '', text)
        text = text.upper()

        while text.count('  ') != 0:
            text = text.replace('  ',' ')
        return text

    # 어절 분리가 가능한 모든 조합 나열 리스트 [[LP1, UM1, RP1], [LP2, UM2, RP2], ...] UM은 사전에 등록되지 않은 부분
    def splitEojeol(self, eojeol):
        out = []
        m = Mecab()
        # m = Mecab(dicpath='C:/mecab/mecab-ko-dic') # (사용불가능, 비활성)
        # m = Mecab(dicpath='/usr/local/lib/mecab/dic/mecab-ko-dic') # (사용불가능, 비활성)
        if eojeol[-1] == '.': eojeol = eojeol[:-1]
        for i in range(len(eojeol)):
            for j in range(len(eojeol)-i):
                k = eojeol[i:j+i+1]
                # k가 두 글자 이상이고 형태소 태그가 여럿인 경우 or 하나라도 명사가 아닌 경우 UM으로 등록
                if len(k)>1 and (len(m.pos(k))>1 or m.pos(k)[0][1][0:2] != 'NN'):
                    out.append([eojeol[0:i], k, eojeol[i+j+1:]])
        return out

    # 한 어절에 대해서 모든 가능한 부분어절 나열 리스트 (현재 미사용)
    def eojeolPart(self, eojeol):
        out = []
        if eojeol[-1] == '.': eojeol = eojeol[:-1]
        for i in range(len(eojeol)):
            for j in range(len(eojeol)-i):
                out.append(eojeol[i:j+i+1])
        return out

    # 한 어절에 대해서 모든 2자 이상의 LP 나열 리스트 (현재 미사용)
    def genLP(self, eojeol):
        # 괄호 뒤에 오는 어절도 인풋으로 받을 방법 필요?
        out = []
        if eojeol[-1] == '.': eojeol = eojeol[:-1]
        for i in range(2, len(eojeol)+1):
            out.append(eojeol[:i])
        return out

    # 분리된 형태소를 조합하여 나올 수 있는 모든 단어 어절 리스트 (현재 미사용)
    def combinePart(self, subeolist):
        # 인풋은 기본적으로 m.morphs(eojeol)을 받음
        out = []
        for i in range(len(subeolist)):
            for j in range(i, len(subeolist)):
                out.append(''.join(subeolist[i:j+1]))
        return out
    
    # 문자열이 알려진 형태소만으로 이루어져있는지 확인
    def isKnown(self, text):
        if len(text) == 0: return True
        m = Mecab()
        # m = Mecab(dicpath='C:/mecab/mecab-ko-dic') # (사용불가능, 비활성)
        # m = Mecab(dicpath='/usr/local/lib/mecab/dic/mecab-ko-dic') # (사용불가능, 비활성)
        for i in m.morphs(text):
            if m.pos(i)[0][1] == 'UNKNOWN': # or maybe include when first letter is 'S' too?
                # print(i)
                # it is not RP
                return False
        return True

    # n개의 문자 사이에 띄어쓰기가 들어올 수 있는 모든 경우의 수를 리스트로 출력 (코드 다소 조잡)
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

    # 어절 내 띄어쓰기가 가능한 모든 문자열을 리스트로 출력 (현재 미사용)
    # 예: ['경기신문', '경기신 문', '경기 신문', '경기 신 문', '경 기신문', '경 기신 문', '경 기 신문', '경 기 신 문']
    def splitWays(self, text):
        if text == '.' or len(text) == 0: return []
        if text[-1] == '.': text = text[:-1]
        n = len(text)
        out = []
        for i in range(len(self.per(n))):
            w = ""
            for j in range(n):    
                w += text[j]+self.per(n)[i][j]
            out.append(w)
        return out

    # RP가 명사 다음에 올 수 있는지 확인 (첫 형태소의 태그가 N,V,J,E,X로 시작하는 경우) (현재 미사용)
    def isAfterNoun(self, rp):
        if rp == '': return True
        m = Mecab()
        # m = Mecab(dicpath='C:/mecab/mecab-ko-dic') # (사용불가능, 비활성)
        # m = Mecab(dicpath='/usr/local/lib/mecab/dic/mecab-ko-dic') # (사용불가능, 비활성)
        if m.pos(rp)[0][1][0] in ['N', 'V', 'J', 'E', 'X']: return True
        return False

    # RP가 등록된 형태소만으로 이루어졌는지 확인 (현재 미사용)
    def isKRP(self, spacedrplist):
        # 기본적으로 self.splitWays(RP)를 인풋으로 받음
        m = Mecab()
        # m = Mecab(dicpath='C:/mecab/mecab-ko-dic') # (사용불가능, 비활성)
        # m = Mecab(dicpath='/usr/local/lib/mecab/dic/mecab-ko-dic') # (사용불가능, 비활성)
        if len(spacedrplist) == 0: return True
        # 각 조합을 모두 확인
        for i in spacedrplist:
            # 가능한 하나의 조합을 리스트로 변형시킨 후 각 마디가 모두 사전에 등록되어있는지 확인
            for j in range(len(i.split())):
                # j번째 마디를 morph로 간략화
                morph = i.split()[j]
                # j번쨰 마디의 형태소분석 결과가 여러개이거나, 한글이 아니거나, UNKNOWN이거나, 감탄사이거나 여러 태그가 있는 경우
                # if len(m.pos(morph))>1 or m.pos(morph)[0][1][0] == 'S' or m.pos(morph)[0][1] == "UNKNOWN" or m.pos(morph)[0][1] == "IC" or m.pos(morph)[0][1].count("+")>0:
                # j번쨰 마디의 형태소분석 결과가 여러개이거나, 한글이 아니거나, UNKNOWN인 경우
                if len(m.pos(morph))>1 or m.pos(morph)[0][1][0] == 'S' or m.pos(morph)[0][1] == "UNKNOWN":
                    # j번쨰 마디는 KM이 아님
                    break
                # j번째가 마지막이면(마지막까지 if문을 통과한 경우) KRP로 인정.
                if j == len(i.split())-1:
                    return True
        return False

    # 클래스의 입력변수를 구축 (정적 메소드) 
    def sortInput(inputPath, index):
        # 입력변수가 50자 이상일 경우 스트링으로 취급
        if len(inputPath) >= 50: return inputPath
        # 입력된 파일이 CSV가 아닐 경우 TXT로 취급하여 1회 실행 유도
        if inputPath[-4:] != ".csv":
            f = open(inputPath, 'r', encoding='utf8')
            out = f.read()
            f.close()
            return out
        data = pandas.read_csv(inputPath, encoding='utf8')
        # NEWS_BODY 열이 없을 경우
        if "NEWS_BODY" not in data.columns:
            l = data.loc[index].tolist()
            l = [str(i) for i in l]
            long = max(l, key=len)
            return long
        # NEWS_BODY 열만 불러오기
        return data.at[index, 'NEWS_BODY']

    # 입력된 CSV 파일의 행의 갯수 (정적 메소드) 
    def totalDocs(inputPath):
        # 입력된 파일이 CSV가 아닐 경우 TXT로 취급하여 1회 실행 유도
        if inputPath[-4:] != ".csv": return 1
        return len(pandas.read_csv(inputPath))

    # 입력된 CSV 파일로 말뭉치 구축 (정적 메소드) 
    def constructCorpus(inputPath, index):
        # CSV가 아닐 경우 TXT로 취급
        # index는 입력된 CSV의 파일 행의 갯수
        if inputPath[-4:] != ".csv":
            f = open(inputPath, 'r', encoding='utf8')
            out = f.read()
            f.close()
            return out
        data = pandas.read_csv(inputPath, encoding='utf8')
        out = ""
        # NEWS_BODY 열이 없을 경우
        if "NEWS_BODY" not in data.columns:
            # for i in range(len(pandas.read_csv(inputPath))):
            for i in range(index):
                l = data.loc[i].tolist()
                l = [str(i) for i in l]
                long = max(l, key=len)
                out += long + ' '
            return out
        # NEWS_BODY 열만 불러오기
        # for i in range(len(pandas.read_csv(inputPath))):
        for i in range(index):
            out += data.at[i, 'NEWS_BODY'] + ' '
        return out

# # <--- CLI 전용 ---> (사용가능, 비활성)
# # sys.argv[1]: 입력파일
# # sys.argv[2]: 출력파일
# if __name__ == "__main__":
#     # 출력 파일 초기화
#     f = open(sys.argv[2], 'w', encoding='utf8')
#     f.write("")
#     f.close()

#     # CSV파일의 행 수 만큼 코드 실행
#     iterNum = Splitter.totalDocs(sys.argv[1])
#     # CSV파일로부터 말뭉치 구축
#     corpus = Splitter.constructCorpus(sys.argv[1], iterNum)
#     lst = []
#     for i in range(iterNum):
#         s = Splitter(sys.argv[1], corpus)
#         if len(s.candidates) > 0:
#             lst.append(s.candidates)
#             print(s.candidates)

#     final = list(dict.fromkeys([item for sublist in lst for item in sublist]))
#     f = open(sys.argv[2], 'w', encoding='utf8')
#     f.write('\n'.join(final))
#     f.close()

# <--- IDE 전용 ---> (활성)
# 입력 선언
# path = "C:/comfinder/inputDoc.txt"
# text = open(path, 'rt', encoding='utf8').read().replace('\n',' ')
text = r"11월 입찰 예정서울시 구로구 구로동에 위치한 `센터포인트 웨스트(구 서부금융센터)` 마스턴투자운용은 서울시 구로구 구로동 '센터포인트 웨스트(옛 서부금융센터)' 매각에 속도를 낸다.27일 관련업계에 따르면 마스턴투자운용은 지난달 삼정KPMG·폴스트먼앤코 아시아 컨소시엄을 매각 주관사로 선정한 후 현재 잠재 매수자에게 투자설명서(IM)를 배포하고 있는 단계다. 입찰은 11월 중순 예정이다.2007년 12월 준공된 '센터포인트 웨스트'는 지하 7층~지상 40층, 연면적 9만5000여㎡(약 2만8000평) 규모의 프라임급 오피스다. 판매동(테크노마트)과 사무동으로 이뤄졌다. 마스턴투자운용의 소유분은 사무동 지하 1층부터 지상 40층이다. 지하 1층과 지상 10층은 판매시설이고 나머지는 업무시설이다. 주요 임차인으로는 삼성카드, 우리카드, 삼성화재, 교보생명, 한화생명 등이 있다. 임차인의 대부분이 신용도가 높은 대기업 계열사 혹은 우량한 금융 및 보험사 등이다.'센터포인트 웨스트'는 서울 서남부 신도림 권역 내 최고층 빌딩으로 초광역 교통 연결성을 보유한 오피스 입지를 갖췄다고 평가받는다. 최근 신도림·영등포 권역은 타임스퀘어, 영시티, 디큐브시티 등 프라임급 오피스들과 함께 형성된 신흥 업무 권역으로 주목받고 있다고 회사 측은 설명했다.마스턴투자운용 측은   2021년 1분기를 클로징 예상 시점으로 잡고 있다  며   신도림 권역의 랜드마크로서 임대 수요가 꾸준해 안정적인 배당이 가능한 투자상품이 될 것  이라고 설명했다.한편 마스턴투자운용은 지난 2017년 말 신한BNP파리바자산운용으로부터 당시 '서부금융센터'를 약 3200억원에 사들였으며 이후 '센터포인트 웨스트'로 이름을 바꿨다.[김규리 기자 wizkim61@mkinternet.com]"
s = Splitter(text)
# print(s.eoList)
# print(s.posUMpairList)
# print(s.partialEoList[125:145])
print(s.candidates)
# print(s.lplist)
# print(s.extnouns)
