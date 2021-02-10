# coding=UTF-8
import urllib.request
import re

def getURL(path):
    fp = urllib.request.urlopen(path)
    tobytes = fp.read()
    out = tobytes.decode("utf8")
    return out

def clean_str(text):
    # text cleansing method
    # read the text file and make it into a string
    # original source: https://blog.naver.com/PostView.nhn?blogId=wideeyed&logNo=221347960543
    pattern = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)' # remove E-mail
    text = re.sub(pattern=pattern, repl='', string=text)
    pattern = r'(http|ftp|https)://(?:[-\w.]|(?:%[\da-fA-F]{2}))+' # remove URL
    text = re.sub(pattern=pattern, repl='', string=text)
    pattern = '([ㄱ-ㅎㅏ-ㅣ]+)'  # remove singles
    text = re.sub(pattern=pattern, repl='', string=text)
    pattern = '<[^>]*>'         # remove HTML tags
    text = re.sub(pattern=pattern, repl='', string=text)
    pattern = r'[^\w\s]'         # remove special characters
    text = re.sub(pattern=pattern, repl='', string=text)

    text = re.sub(r'(^[ \t]+|[ \t]+(?=:))', '', text, flags=re.M)
    text = text.replace('\n', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('\r', ' ')
    
    while text.count('  ') != 0:
        text = text.replace('  ',' ')
    return text

url = "https://www.kgnews.co.kr/news/article.html?no=628336"
data = clean_str(getURL(url))
# print(data)
# print(type(data))
f = open("C:/written.txt", 'w', encoding='utf8')
f.write(data.strip())
f.close()
