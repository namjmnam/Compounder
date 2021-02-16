# coding=UTF-8
import math
import kss
# for splitting sentences
# pip install kss

import re
# for text cleansing

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
# for extracting nouns

class Corpus:
    def __init__(self, inputPath, words=2):

        # This program extracts possible compound words from a document
        # It does not use the corpus(although some comment says it does) and uses the document itself for searching
        # Works best with python version 3.6
        # Required packages: kss, eunjeon or konlpy
	# Lacking capability: allCW does not check for duplicates

        self.target = self.clean_str(inputPath)
        # target(inputDoc) is the whole document, and cleansed
        tokenizer = Mecab()
        self.nouns = tokenizer.nouns(self.target)
        self.sList = kss.split_sentences(self.target)
        self.fList = self.nounExt(self.sList)
        # self.nouns is cleansed document which only contains lists of nouns with space in between them with sections divided by full stop followed by a space
        # self.sList is the list of sentences from splitting the document
        # self.fList is the list of lists which contains all nouns in each sentences. this is also the map

        self.nOfWords = words
        # default is 2, meaning only looking for compound words with 2 words in them
        self.df = 0.85
        # damping factor
        self.defIteration = 10
        # no of iteration on TR

        self.masterList = []
        for i in self.fList:
            self.masterList += i
        self.masterList = list(dict.fromkeys(self.masterList))
        # constructing the master noun list

        self.allCW = []
        for i in range(len(self.fList)):
            n = self.genCWImporved(self.fList[i])
            for j in n:
                if self.searchImproved(j, self.target) > 1 and j not in self.allCW:
                    self.allCW.append(j)
        # self.allCW = list(dict.fromkeys(self.allCW))
        # this loop completes the list of all possible CW's paired to a list (the code above checks for duplicates but fails

        ##################################
        ###### begin main code here ######
        ##################################

        self.finaldict = []
        finallist = []
        trdic = self.calculateTR(self.masterList, self.fList, self.defIteration)
        pmilist = []
        for i in self.allCW:
            pmilist.append(self.getPMI(i, self.nouns, self.target))

        for i in range(len(self.allCW)):
            k = self.allCW[i]
            key = 1
            for j in k:
                key *= trdic[j]
            key **= (1 / len(k))
            key *= pmilist[i]
            finallist.append(key)

        gluedCW = []
        for i in self.allCW:
            w = ''
            for j in i:
                w += j
                w += ' '
            w = w[:-1]
            gluedCW.append(w)
            
        self.finaldict = dict(zip(gluedCW, finallist))
        
        print(self.finaldict)
        # this is the final output

        # print(self.searchImproved(['개혁', '민생', '법안'], self.target))
        # self.genCWImporved(['홍보', '소통', '위원장', '이낙연', '대표'])

        ##################################
        ######## end of main code ########
        ##################################

    def clean_str(self, inputPath):
        # text cleansing method
        # read the text file and make it into a string
        text = open(inputPath, 'rt', encoding='UTF8').read().replace('\n',' ')
        # original source: https://blog.naver.com/PostView.nhn?blogId=wideeyed&logNo=221347960543

        text = text.replace(u'\xa0', u' ')  # this is due to Latin1 ISO 8859-1
        text = text.strip()

        pattern = '([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)' # remove E-mail
        text = re.sub(pattern=pattern, repl=' ', string=text)
        pattern = '(http|ftp|https)://(?:[-\w.]|(?:%[\da-fA-F]{2}))+' # remove URL
        text = re.sub(pattern=pattern, repl=' ', string=text)
        pattern = '([ㄱ-ㅎㅏ-ㅣ]+)'  # remove singles
        text = re.sub(pattern=pattern, repl=' ', string=text)
        pattern = '<[^>]*>'         # remove HTML tags
        text = re.sub(pattern=pattern, repl=' ', string=text)
        pattern = '[^-/.\w\s]'         # remove special characters except for -/.
        text = re.sub(pattern=pattern, repl=' ', string=text)

        text = re.sub(r'(^[ \t]+|[ \t]+(?=:))', '', text, flags=re.M)
        text = text.replace('\n', ' ')
        text = text.replace('\t', ' ')
        text = text.replace('\r', ' ')
        text = re.sub(r'\b[0-9]+\b\s*', '', text)
        text = text.upper()

        while text.count('  ') != 0:
            text = text.replace('  ',' ')
        return text

    def nounExt(self, sentList):
        # this method extracts all the nouns from the sentence list using mecab
        # tokenizer = Mecab(dicpath='C:/mecab/mecab-ko-dic')
        tokenizer = Mecab()
        # if possible, directory can be provided
        n = []
        for i in sentList:
            n.append(tokenizer.nouns(i))
        return n

    def per(self, n):
        # original code: https://stackoverflow.com/questions/17656825/python-replacing-characters-in-a-list
        # n is the number of words
        out = []
        for i in range(1<<n-1):
            s=bin(i)[2:]
            s='0'*(n-1-len(s))+s
            # s = s.replace('0','').replace('1',' ')
            coms = []
            for i in list(s):
                if i == '0': coms.append('')
                if i == '1': coms.append(' ')
            coms.append('')
            # print(coms)
            out.append(coms)
            # coms is the possible space allocation after nth word
        return out
        # out is list of all possible coms

    def genCompoundWords(self, wList):
        # this method combines self.nOfWords words into one string
        out = []
        word = ''
        for i in range(len(wList) - self.nOfWords + 1):
            for j in range(i, i + self.nOfWords):
                word += wList[j]
                word += ' '
            word = word[:-1]
            out.append(word)
            word = ''
        return out

    def genCWImporved(self, wList):
        # unlike the genCompoundWords, this method generates list of lists comprised of elements of CW
        out = []
        wordpair = []
        for i in range(len(wList) - self.nOfWords + 1):
            for j in range(i, i + self.nOfWords):
                wordpair.append(wList[j])
            out.append(wordpair)
            wordpair = []
        # print(out)
        return out

    def searchCorpus(self, cword, target):
        # this method searches the word by the corpus(target)
        # cword is a string of series of words split by space
        out = target.count(cword)
        if cword.count(' ') != 0:
            out += target.count(cword.replace(' ',''))
        # this loop means it's searching for the usages of combined word
        return out

    def searchImproved(self, cList, target):
        # this method searches the corpus but the input is a list not a string
        out = 0
        spaces = self.per(len(cList))
        cwList = []
        for i in range(len(spaces)):
            w = ''
            for j in range(len(cList)):
                w += cList[j]
                w += spaces[i][j]
            cwList.append(w)
        for i in cwList:
            out += target.count(i)
        # print(cwList)
        # this outputs all tested combinations
        return out

    def getPMI(self, wordpair, nouns, target):
        # cword is the compound word
        wTotal = len(nouns)
        # wTotal is the number of all nouns out of target
        numerator = self.searchImproved(wordpair, target) / wTotal
        # numerator = p(w1,w2)
        denominator = 1
        for i in wordpair:
            denominator *= self.searchCorpus(i, target) / wTotal
        # denominator = p(w1) * p(w2) * ...
        pmi = math.log(numerator / denominator)
        return pmi


    def wordMapTo(self, word, map):
        # this method tries to list all the words that have connections to the given word (meaning they present in the same sentence)
        # map is the formatted list
        out = []
        for i in map:
            if word in i:
                for j in i:
                    if j not in out:
                        out.append(j)
        out.remove(word)
        return out
    
    def noOfConnections(self, word, map):
        # this method outputs int of no of connected words
        return len(self.wordMapTo(word, map))

    def calculateTR(self, wordList, map, iteration):
        # wordList is the master list of the document
        values = [1 / len(wordList)] * len(wordList)
        newValue = [0] * len(wordList)
        # this is in the initial(0th) iteration
        node = dict(zip(wordList, values))

        for _ in range(iteration):
            # this will contain calculations of nth iteration
            for i in range(len(wordList)):
                # this is where textrank individual iteration is contained contains
                key = wordList[i]
                # first deal with ith word
                for j in self.wordMapTo(key, map):
                    # get all the connected words
                    newValue[i] += node[j] / self.noOfConnections(j, map)
                    # map the TR of j and divide by the no of conn and add to new list of value
            values = newValue
            newValue = [0] * len(wordList)
            node = dict(zip(wordList, values))
            # replace the old TR with new TR

        # print(sum(values))
        # this value should be 1 or very close to 1

        for i in range(0, len(values)):
            values[i] = (1-self.df) + self.df * values[i]
        node = dict(zip(wordList, values))
        # this loop counts the damping factor
        return node

# doc = "박수현 이낙연 지지 율 하락 빚 청구서. 더불어 민주당 박수현 홍보소통 위원장 왼쪽 이낙연 대표. 사진 국회 의원 선거 운동 당시 이낙연 더불어민주당 상임공동선대위원장 박수현 공주시부여군청양군 후보의 지지를 호소하고 있는 모습. 박수현 더불어민주당 홍보소통위원장은 일 오는 월 임기 종료를 앞둔 이낙연 대표를 향해 대표로서 역대급 성과를 냈는데도 지지율이 하락하는 것을 섭섭해할 이유는 없다며 지지율 하락은 그 빚을 제대로 갚으라는 청구서라고 지적했다. 그러면서도 그동안 입법으로 성과를 말했고 개월이라는 짧은 시간에 그 목표를 달성했다고 했다. 박 위원장은 이날 오전 자신의 페이스북 글을 통해 이 대표는 년 월 대표 취임 이후 개월간 민주당을 이끌어왔다며 당 대표 출마를 선언할 때부터 개월짜리 대표란 꼬리표를 달고 시작을 했기 때문에 이 대표가 대표로서 활동할 시간도 개월밖에 남지 않은 셈이라고 했다. 그는 대권이라는 개인의 정치 목표 때문에 개월짜리 당대표가 된 것은 분명 빚이고 기꺼이 빚을 내어주신 국민과 당과 당원께 진 이 대표의 빚은 결코 작지 않다고 했다. 박 위원장은 이어 년 총선에서 민주당은 석이라는 역사상 유례가 없는 슈퍼정당을 만들었다. 이 대표는 취임 이후 당원들의 열망에 화답하듯 여러 개혁 민생 법안 처리를 이끌었다며 공수처법 개정안 등 권력기관 개혁 법안 공정경제 법 지방자치법 관련 법 법제화 등의 성과를 거론했다. 이뿐만 아니라 여건이 넘는 법안을 처리하며 슈퍼정당의 위력을 보여줬다고 덧붙였다. 박 위원장은 그러면서 개월간 수많은 개혁 민생 법안을 통과시켰음에도 개혁을 열망하는 국민과 당원은 아직도 목이 마르다며 마지막 남은 당대표 개월 당과 당원에게 빚을 갚아야 한다고 했다. 박 위원장은 지난 개월의 성과는 역대 어느 대표와도 견줄 수 없는 역대급이나 이 역시 거대여당을 만들어 준 국민과 당원에게 진 빚이라고 강조했다. 그러면서 개월 시한부 당 대표라는 꼬리표가 더 이상 꼬리표가 아닌 마침표가 될 수 있도록 남은 개월 동안 대한민국 개혁과 민주당 역사에 큰 방점을 찍어주길 바란다며 그것이 국민과 당과 당원에 진 빚을 갚는 유일한 길이라고 덧붙였다."
# original link: https://www.kgnews.co.kr/news/article.html?no=628336
path = "C:/comfinder/inputDoc.txt"
c = Corpus(path)
# c = Corpus(path, 3)
