# coding=UTF-8
import math

class Corpus:
    def __init__(self, inputDoc, inputNouns):
        self.target = inputDoc
        # inputDoc is the whole document
        self.nouns = inputNouns
        self.fList = self.paragFormatter(inputNouns)
        # inputNouns is cleansed document which only contains lists of nouns with space in between them with sections divided by full stop followed by a space
        # self.fList is the list of lists which contains all nouns in each sentences. this is also the map
        self.nOfWords = 2
        # default is 2, meaning only looking for compound words with 2 words in them
        self.df = 0.85
        # damping factor
        self.defIteration = 10
        # no of iteration on TR

        self.masterList = []
        # list of all words in the whole paragraph or document
        for i in self.fList:
            self.masterList += i
        self.masterList = list(dict.fromkeys(self.masterList))
        # constructing the master noun list

        self.allCW = []
        self.allPCW = []
        # these two are lists of compoun words(CW) and more probably compound words(PCW)

        # print(self.fList)
        # print(len(self.fList))
        # print(self.genCompoundWords(self.fList[0]))

        for i in range(len(self.fList)):
            o = self.genCompoundWords(self.fList[i])
            # print(o)
            self.allCW.extend(o)
        self.allCW = list(dict.fromkeys(self.allCW))
        # print(self.allCW)
        # this loop completes the list of all possible CW's

        for i in self.allCW:
            if self.searchCorpus(i, self.target) > 1:
                self.allPCW.append(i)
        # print(self.allPCW)
        # this creates PCW out of CW's that occur more than once
        # self.allCW is technically not really used, it is only used to generate PCW

        for i in self.allPCW:
            # print(self.getPMI(i, self.nouns, self.target))
            # this outputs all relevant PMI's
            pass

        for i in self.masterList:
            # print(i)
            # print(self.noOfConnections(i, self.fList))
            # this outputs all the connections of each nouns
            pass
        # print(self.wordMapTo("이낙연", self.fList))

        # print(self.calculateTR(self.masterList, self.fList, self.defIteration))
        # this outputs TR dictionary

        ###############################
        #### here is how it's used ####
        ###############################

        finaldict = []
        finallist = []
        trdic = self.calculateTR(self.masterList, self.fList, self.defIteration)
        pmilist = []
        for i in self.allPCW:
            pmilist.append(self.getPMI(i, self.nouns, self.target))

        for i in range(len(self.allPCW)):
            k = self.allPCW[i].split(' ')
            key = 1
            for j in k:
                key *= trdic[j]
            key **= (1 / len(k))
            key *= pmilist[i]
            finallist.append(key)
        finaldict = dict(zip(self.allPCW, finallist))
        print(finaldict)

        ###############################
        ########### the end ###########
        ###############################

    def paragFormatter(self, paragraph):
        # this divides the paragraph into list of all sentences and then...
        n = paragraph.replace('. ','.').replace('.\n','.').replace(',','')
        sList = n.split('.')
        while '' in sList:
            sList.remove('')
        out = []
        for i in sList:
            # this then converts all the sentences into a list
            t = i.split(' ')
            t = list(dict.fromkeys(t))
            out.append(t)
        return out
        # neglected ! or ?

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

    def searchCorpus(self, word, target):
        # this method searches the word by the corpus(target)
        # word is a string of series of words split by space
        n = target.count(word)
        if word.count(' ') != 0:
            n += target.count(word.replace(' ',''))
        # this loop means it's searching for the usages of combined word
        return n

    def getPMI(self, cword, nouns, target):
        # cword is the compound word
        wTotal = len(nouns.split(' '))
        # wTotal is supposed to count number of all words out of target, but it's simplified here
        w = cword.split(' ')
        numerator = self.searchCorpus(cword, target) / wTotal
        # numerator = p(w1,w2)
        denominator = 1
        for i in w:
            denominator *= self.searchCorpus(i, target) / wTotal
        # denominator = p(w1) * p(w2) * ...
        pmi = math.log(numerator / denominator)
        return pmi


    def wordMapTo(self, word, map):
        # this method tries to list all the words that have connections to the given word (meaning they present in the same sentence)
        # map is the formatted list
        l = []
        for i in map:
            if word in i:
                for j in i:
                    if j not in l:
                        l.append(j)
        l.remove(word)
        return l
    
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

doc = "박수현 이낙연 지지 율 하락 빚 청구서. 더불어 민주당 박수현 홍보소통 위원장 왼쪽 이낙연 대표. 사진 국회 의원 선거 운동 당시 이낙연 더불어민주당 상임공동선대위원장 박수현 공주시부여군청양군 후보의 지지를 호소하고 있는 모습. 박수현 더불어민주당 홍보소통위원장은 일 오는 월 임기 종료를 앞둔 이낙연 대표를 향해 대표로서 역대급 성과를 냈는데도 지지율이 하락하는 것을 섭섭해할 이유는 없다며 지지율 하락은 그 빚을 제대로 갚으라는 청구서라고 지적했다. 그러면서도 그동안 입법으로 성과를 말했고 개월이라는 짧은 시간에 그 목표를 달성했다고 했다. 박 위원장은 이날 오전 자신의 페이스북 글을 통해 이 대표는 년 월 대표 취임 이후 개월간 민주당을 이끌어왔다며 당 대표 출마를 선언할 때부터 개월짜리 대표란 꼬리표를 달고 시작을 했기 때문에 이 대표가 대표로서 활동할 시간도 개월밖에 남지 않은 셈이라고 했다. 그는 대권이라는 개인의 정치 목표 때문에 개월짜리 당대표가 된 것은 분명 빚이고 기꺼이 빚을 내어주신 국민과 당과 당원께 진 이 대표의 빚은 결코 작지 않다고 했다. 박 위원장은 이어 년 총선에서 민주당은 석이라는 역사상 유례가 없는 슈퍼정당을 만들었다. 이 대표는 취임 이후 당원들의 열망에 화답하듯 여러 개혁 민생 법안 처리를 이끌었다며 공수처법 개정안 등 권력기관 개혁 법안 공정경제 법 지방자치법 관련 법 법제화 등의 성과를 거론했다. 이뿐만 아니라 여건이 넘는 법안을 처리하며 슈퍼정당의 위력을 보여줬다고 덧붙였다. 박 위원장은 그러면서 개월간 수많은 개혁 민생 법안을 통과시켰음에도 개혁을 열망하는 국민과 당원은 아직도 목이 마르다며 마지막 남은 당대표 개월 당과 당원에게 빚을 갚아야 한다고 했다. 박 위원장은 지난 개월의 성과는 역대 어느 대표와도 견줄 수 없는 역대급이나 이 역시 거대여당을 만들어 준 국민과 당원에게 진 빚이라고 강조했다. 그러면서 개월 시한부 당 대표라는 꼬리표가 더 이상 꼬리표가 아닌 마침표가 될 수 있도록 남은 개월 동안 대한민국 개혁과 민주당 역사에 큰 방점을 찍어주길 바란다며 그것이 국민과 당과 당원에 진 빚을 갚는 유일한 길이라고 덧붙였다."
nouns = "박수현 이낙연 지지 율 하락 빚 청구서. 더불어 민주당 박수현 홍보 소통 위원장 왼쪽 이낙연 대표. 사진 국회 의원 선거 운동 당시 이낙연 더불어 민주당 상임 공동 선대 위원장 박수현 공주시 부여군 청양군 후보 지지 호소 모습. 박수현 더불어 민주당 홍보 소통 위원장 임기 종료 이낙연 대표 대표 역대 급 성과 지지 율 하락 이유 지지 율 하락 빚 청구서 지적. 입법 성과 시간 목표 달성. 위원장 오전 자신 페이스북 글 대표 대표 취임 민주당 당 대표 출마 선언 대표 꼬리 표 시작 대표 대표 활동 시간. 그 대권 개인 정치 목표 당 대표 빚 빚 국민 당 당 원 대표 빚. 위원장 총선 민주당 역사 유례 슈퍼 정당. 대표 취임 당 원 열망 화답 개혁 민생 법안 처리 공수 처법 개정안 권력 기관 개혁 법안 공정 경제 법 지방 자치 법 관련 법 법제화 성과 거론. 법안 처리 슈퍼 정당 위력. 위원장 개혁 민생 법안 통과 개혁 열망 국민 당 원 당 대표 당 당 원 빚. 위원장 성과 역대 대표 역대 급 거대 여당 국민 당 원 빚 강조. 시한부 당 대표 꼬리 표 꼬리 표 마침표 대한민국 개혁 민주당 역사 방점 국민 당 당 원 빚 길."
c = Corpus(doc, nouns)
