# coding=UTF-8
import re
import pandas

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

# 텍스트 클렌징
def cleanText(text):
    text = text.replace(u'\xa0', u' ')

    pattern = '([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
    text = re.sub(pattern=pattern, repl=' ', string=text)
    pattern = '<script.*script>'
    text = re.sub(pattern=pattern, repl=' ', string=text)
    pattern = '(http|ftp|https)://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    text = re.sub(pattern=pattern, repl=' ', string=text)
    pattern = '([ㄱ-ㅎㅏ-ㅣ]+)'
    text = re.sub(pattern=pattern, repl=' ', string=text)
    pattern = '<[^>]*>'
    text = re.sub(pattern=pattern, repl=' ', string=text)
    # pattern = '''[^-/.()&*+%$·,`'"‘’▶\w\s]''' # 좀 더 관대한 필터링
    # pattern = "[^-/.()&*+%$\w\s]" # 관대한 필터링
    pattern = "[^\w\s]"
    text = re.sub(pattern=pattern, repl=' ', string=text)

    text = text.replace('\n', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('\r', ' ')

    # pattern = "[0-9]+\.[0-9]+\.[0-9]+\..*여기를 누르시면 크게 보실 수 있습니다" # 매일경제 전용
    # text = re.sub(pattern=pattern, repl=' ', string=text)

    text = re.sub(' +', ' ', text)
    return text

# 한 어절에 대해서 모든 2자 이상의 LP를 나열한 리스트
def genLP(eojeol):
    out = []
    # 추출된 어절 끝에 마침표가 오는 경우 제거
    if eojeol[-1] == '.': eojeol = eojeol[:-1]
    for i in range(2, len(eojeol)+1):
        if len(eojeol[:i].replace('.', '')) > 1 and eojeol[:1][-1] != '.':
            out.append(eojeol[:i])
    return out

# 어절 리스트를 대상으로 입력 문자열을 각 어절의 좌측에서 검색하여 나온 결과를 출력
def leftSearcher(word, eoList):
    out = []
    max = len(word)
    for i in eoList:
        if len(i) >= max and i[0:max] == word: out.append(i)
    return len(out)


inputPath = r"C:/comfinder/longtext.csv"
rawDocument = inputToFormat(inputPath)
corpusDocList = list(pandas.read_csv(inputPath)['NEWS_BODY'])
corpusText = ' '.join(corpusDocList)

# rawDocument = r"11월 입찰 예정 서울시 구로구 구로동에 위치한 `센터포인트 웨스트(구 서부금융센터)` 마스턴투자운용은 서울시 구로구 구로동 '센터포인트 웨스트(옛 서부금융센터)' 매각에 속도를 낸다.27일 관련업계에 따르면 마스턴투자운용은 지난달 삼정KPMG·폴스트먼앤코 아시아 컨소시엄을 매각 주관사로 선정한 후 현재 잠재 매수자에게 투자설명서(IM)를 배포하고 있는 단계다. 입찰은 11월 중순 예정이다.2007년 12월 준공된 '센터포인트 웨스트'는 지하 7층~지상 40층, 연면적 9만5000여㎡(약 2만8000평) 규모의 프라임급 오피스다. 판매동(테크노마트)과 사무동으로 이뤄졌다. 마스턴투자운용의 소유분은 사무동 지하 1층부터 지상 40층이다. 지하 1층과 지상 10층은 판매시설이고 나머지는 업무시설이다. 주요 임차인으로는 삼성카드, 우리카드, 삼성화재, 교보생명, 한화생명 등이 있다. 임차인의 대부분이 신용도가 높은 대기업 계열사 혹은 우량한 금융 및 보험사 등이다.'센터포인트 웨스트'는 서울 서남부 신도림 권역 내 최고층 빌딩으로 초광역 교통 연결성을 보유한 오피스 입지를 갖췄다고 평가받는다. 최근 신도림·영등포 권역은 타임스퀘어, 영시티, 디큐브시티 등 프라임급 오피스들과 함께 형성된 신흥 업무 권역으로 주목받고 있다고 회사 측은 설명했다.마스턴투자운용 측은   2021년 1분기를 클로징 예상 시점으로 잡고 있다  며   신도림 권역의 랜드마크로서 임대 수요가 꾸준해 안정적인 배당이 가능한 투자상품이 될 것  이라고 설명했다.한편 마스턴투자운용은 지난 2017년 말 신한BNP파리바자산운용으로부터 당시 '서부금융센터'를 약 3200억원에 사들였으며 이후 '센터포인트 웨스트'로 이름을 바꿨다.[김규리 기자 wizkim61@mkinternet.com]"
# corposText = rawDocument # 현재 말뭉치 부재

# eoList: 어절 리스트
cleansedDocument = cleanText(rawDocument)
temp = cleansedDocument.split(' ')
eoList = [i for i in temp if len(re.sub(r'[0-9]+', '-', i)) >= 3] # 3자 이상의 어절만

# corpusEoList: 말뭉치 어절 리스트
# corpusEoList = eoList # 현재 말뭉치 부재

temp = cleanText(corpusText).split(' ')
corpusEoList = [i for i in temp if len(re.sub(r'[0-9]+', '-', i)) >= 3] # 3자 이상의 어절만

# lplist: 모든 어절의 2자 이상의 LP부분 리스트: [["어절1LP1", "어절1LP2", ...], ["어절2LP1", "어절2LP2", ...], ...]
lplist = []
iter = eoList[:]
iter = list(dict.fromkeys(iter))
for i in iter:
    if len(i) > 1: lplist.append(genLP(i))

# 명사로 추정되는 문자열 리스트 추출 -> extractednouns
extractedNouns = []
for i in lplist:
    scores = []
    chosen = []
    for j in range(len(i)):
        # 말뭉치 내 단어 수 산출
        scores.append(corpusText.count(i[j]))
    scores.append(scores[-1] * 0.8) # 마지막 임시방편

    # 빈도수의 엘보 포인트(elbow point)에서 명사로 등록
    if scores[0] > scores[1] * 1.1: chosen.append(i[0])
    # if scores[-1] > scores[-2] * 0.9: chosen.append(i[-1])
    for j in range(1, len(i)): # 단점: 처음과 마지막(?) LP neglected - need a solution 위 코드는 임시방편
        scoreBefore = scores[j-1]
        scoreCurrent = scores[j]
        scoreAfter = scores[j+1]
        if scoreBefore - scoreCurrent < scoreCurrent - scoreAfter: chosen.append(i[j])

    for j in range(len(chosen)):
        if rawDocument.count(chosen[j]) >= 2: extractedNouns.append(chosen[j])
extractedNouns = list(dict.fromkeys(extractedNouns))

print(extractedNouns)
# print(leftSearcher("서울", corpusEoList))
print(len(corpusEoList))
# print(len(corpusText))