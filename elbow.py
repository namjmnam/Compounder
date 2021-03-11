# coding=UTF-8
import re
import pandas

class CorpusBuilder:
    def __init__(self, inputPath):
        self.corpusDocList = list(pandas.read_csv(inputPath)['NEWS_BODY'])
        self.corpusText = ' '.join(self.corpusDocList)
        temp = cleanText(self.corpusText).split(' ')
        self.corpusEoList = [i for i in temp if len(re.sub(r'[0-9]+', '-', i)) >= 3] # 3자 이상의 어절만

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

# 추출 프로세스
def extOutput(corpusText, corpusDocList, corpusEoList, index=0):
    rawDocument = corpusDocList[index]

    # eoList: 어절 리스트
    cleansedDocument = cleanText(rawDocument)
    temp = cleansedDocument.split(' ')
    eoList = [i for i in temp if len(re.sub(r'[0-9]+', '-', i)) >= 3] # 3자 이상의 어절만

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
            scores.append(leftSearcher(i[j], corpusEoList))
        scores.append(scores[-1] * 0.8) # 임시방편1
        # 빈도수의 엘보 포인트(elbow point)에서 명사로 등록
        if scores[0] > scores[1] * 1.1: chosen.append(i[0]) # 임시방편2
        # if scores[-1] > scores[-2] * 0.9: chosen.append(i[-1])
        for j in range(1, len(i)):
            scoreBefore = scores[j-1]
            scoreCurrent = scores[j]
            scoreAfter = scores[j+1]
            if scoreBefore - scoreCurrent < scoreCurrent - scoreAfter: chosen.append(i[j])

        for j in range(len(chosen)):
            if rawDocument.count(chosen[j]) >= 2: extractedNouns.append(chosen[j])
    extractedNouns = list(dict.fromkeys(extractedNouns))
    return extractedNouns

inputPath = r"C:/comfinder/longtext.csv"
cb = CorpusBuilder(inputPath)

for i in range(10):
    print(extOutput(cb.corpusText, cb.corpusDocList, cb.corpusEoList, i))
