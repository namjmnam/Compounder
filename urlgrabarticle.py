from bs4 import BeautifulSoup
import requests
import re

def clean_str(text):
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
    pattern = '[^-/.()&*+%$\w\s]'
    text = re.sub(pattern=pattern, repl=' ', string=text)

    text = text.replace('\n', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('\r', ' ')
    text = re.sub(' +', ' ', text)
    return text

# url = "https://news.naver.com/main/read.nhn?mode=LSD&mid=shm&sid1=100&oid=366&aid=0000681992" # 네이버 뉴스
# url = "https://news.naver.com/main/read.nhn?mode=LSD&mid=shm&sid1=104&oid=001&aid=0012250993" # 네이버 뉴스
url = "https://www.mk.co.kr/news/politics/view/2021/03/229098/" # 매일경제
# url = "https://www.hankyung.com/politics/article/202103098029i" # 한국경제
# url = "https://news.mt.co.kr/mtview.php?no=2021031015184171199" # 머니투데이

# source_code = requests.get(url, headers = {"User-Agent" : "Mozilla/5.0"}).text
source_code = requests.get(url, headers = {"User-Agent" : "Mozilla/5.0"}).content
html = BeautifulSoup(source_code, 'html.parser')


# article = html.find('div', attrs = {'id':'articleBodyContents'}) # 네이버 뉴스
article = html.find('div', attrs = {'class':'art_txt'}) # 매일경제
# article = html.find('div', attrs = {'id':'article_body'}) # 매일경제2
# article = html.find('div', attrs = {'id':'articletxt'}) # 한국경제
# article = html.find('div', attrs = {'id':'textBody'}) # 머니투데이

source_code = str(article)
source_code = clean_str(source_code)
print(source_code)
# article = clean_str(article)
# print(article)
# print(str(article))
# print(type(article))
# print(type(str(article)))


# f = open("C:/comfinder/crawled.html", 'w', encoding='utf8')
# f = open("C:/comfinder/crawled.html", 'w', encoding='euc-kr')
# f.write(source_code)
# f.close()