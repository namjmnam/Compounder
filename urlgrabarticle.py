from bs4 import BeautifulSoup
from numpy.lib.utils import source
import requests
import re

def clean_str(text):
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
    pattern = "[^-/.()&*+%$\w\s]"
    text = re.sub(pattern=pattern, repl=' ', string=text)

    text = text.replace('\n', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('\r', ' ')

    # pattern = "[0-9]+\.[0-9]+\.[0-9]+\..*여기를 누르시면 크게 보실 수 있습니다" # 매일경제 전용
    # text = re.sub(pattern=pattern, repl=' ', string=text)

    text = re.sub(' +', ' ', text)
    return text

# url = "https://news.naver.com/main/read.nhn?mode=LSD&mid=shm&sid1=100&oid=366&aid=0000681992" # 네이버 뉴스
# url = "https://news.naver.com/main/read.nhn?mode=LSD&mid=shm&sid1=104&oid=001&aid=0012250993" # 네이버 뉴스
# url = "https://www.mk.co.kr/news/politics/view/2021/03/229098/" # 매일경제
url = "https://www.mk.co.kr/news/politics/view/2021/02/194316/" # 매일경제
# url = "https://www.hankyung.com/politics/article/202103098029i" # 한국경제
# url = "https://news.mt.co.kr/mtview.php?no=2021031015184171199" # 머니투데이

# source_code = requests.get(url, headers = {"User-Agent" : "Mozilla/5.0"}).text # 미사용, 문자 깨져 나옴
source_code = requests.get(url, headers = {"User-Agent" : "Mozilla/5.0"}).content
html = BeautifulSoup(source_code, 'html.parser')


# article = html.find('div', attrs = {'id':'articleBodyContents'}) # 네이버 뉴스
article = html.find('div', attrs = {'class':'art_txt'}) # 매일경제
# article = html.find('div', attrs = {'id':'article_body'}) # 매일경제2
# article = html.find('div', attrs = {'id':'articletxt'}) # 한국경제
# article = html.find('div', attrs = {'id':'textBody'}) # 머니투데이

article_str = str(article)
article_str = clean_str(article_str)
print(article_str)

# sentList = re.findall('.*?다\.+', article_str) # 문장분리
# print(sentList)
# for i in sentList:
#     print(i)

# f = open("C:/comfinder/crawled.html", 'w', encoding='utf8')
# f = open("C:/comfinder/crawled.html", 'w', encoding='euc-kr')
# f.write(article_str)
# f.close()
