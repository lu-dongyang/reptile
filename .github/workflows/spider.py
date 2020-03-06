import json
import os
from urllib.parse import urlencode
from requests.exceptions import RequestException
import pymongo
import requests
from bs4 import BeautifulSoup
import re
from multiprocessing import Pool
from hashlib import md5
from json.decoder import JSONDecodeError
from config import *

'''
# 建立数据库的链接对象
# 数据库的名称
'''
client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]

#获取索引页内容
'''
加入请求头
并进行异常处理
'''
def get_page_index(offest,keyword):
    data = {
        "aid": "24",
        "app_name": "web_search",
        "offset": offest,
        "format": "json",
        "keyword": keyword,
        "autoload": "true",
        "count": "20",
        "en_qc": "1",
        "cur_tab": "1",
        "from": "search_tab",
        "pd": "synthesis",
        "timestamp": "1568883030289"
    }

    params = urlencode(data)
    base = 'https://www.toutiao.com/api/search/content/'
    url = base + '?' + params
    try:
        response = requests.get(url,headers=headers,cookies=cookies)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求失败')
        return None

#解析提取网页代码
'''
将html转为json格式
判断data是否在json中（data是网页中存放图片的地方）
找到article_url :详情页的url
构造一个生成器
'''
def parse_page_index(html):
    data = json.loads(html)
    if data and 'data' in data.keys():
        for item in data.get("data"):    #字典获取键的值的get方法
            if "article_url" in item.keys():
                url = item.get("article_url")
                yield url

#对抓取图片的异常处理
'''

'''
def get_page_detial(url):
    try:  # 知识点4：请求的异常处理方式
        response = requests.get(url, headers=headers, cookies=cookies)
        if response.status_code == 200:
            content = response.content.decode()
            return content
        return None
    except RequestException:
        print("请求详情页出错")
        return None

'''
解析详情页方法
BeautifulSoup解析标题
正则解析图片
'''
def parse_page_detial(html, url):
    soup = BeautifulSoup(html, "lxml")
    title = soup.select("title")[0].get_text()
    images_pattern = re.compile('gallery: JSON.parse\("(.*?)"\),', re.S)
    result = re.search(images_pattern, html)
    if result:
        ret = result.group(1)
        # {\"count\":11,\"sub_images\":[{\"url\":\"http:\\\u002F\\\u002Fp3.pstatp.com\\...}
        # 在进行loads转换时，报错json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
        # 因此需要替换\为空字符串
        ret = ret.replace("\\", "")
        ret = ret.replace("u002F", "/")
        data = json.loads(ret)  #把字符串转成json对象
        if data and 'sub_images' in data.keys():
            sub_images = data.get("sub_images")
            images = [item.get("url") for item in sub_images]
            for img in images:
                download(img)
            return {
                "title": title,  #标题
                "images": images, #列表形式的数组
                "url": url  #网页
            }

#存储到数据库
def save_to_mongo(ret_dict):
    if db[MONGO_TABLE].insert(ret_dict): # 知识点8：mongodb数据库的链接，配置文件方式传入
        print("插入数据到数据库成功", ret_dict["title"])
        return True
    return False

#下载图片
def download(url):
    print("正在下载图片",url)
    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        if response.status_code == 200:
            content = response.content
            saveimg(content)
        return None
    except RequestException:
        print("请求出错")
        return None

#保存图片
def saveimg(content):
    file_path = "{0}/{1}.{2}".format(os.getcwd(),md5(content).hexdigest(),"jpg")  # 知识点9：运用md5进行去重，md5的简单回顾
    if not os.path.exists(file_path):  # 知识点10:os方法的使用
        with open(file_path,"wb") as f:
            f.write(content)
            f.close()
#主函数
'''


'''
def main():
    for offset in range(GROUP_START, GROUP_END, 20):
        html = get_page_index(offset, KEYWORD)
    if html:
        for url in parse_page_index(html):  #提取url
            html = get_page_detial(url)
            if html:
                ret = parse_page_detial(html, url)
                if ret:
                    save_to_mongo(ret)

if __name__ == '__main__':
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36'
    }
    cookies = {
        'cookie': 'tt_webid=6800050326885369357; WEATHER_CITY=%E5%8C%97%E4%BA%AC; SLARDAR_WEB_ID=df4d30e8-31e8-410e-8ec6-3976ce21d323; tt_webid=6800050326885369357; csrftoken=f4c236ce7196221f7f8d9da38770eaa2; ttcid=71aba31b552d4df59c97d64ce7301cca14; s_v_web_id=verify_k7co3vj8_06SKOnme_2RBk_4SAS_AxS5_IC5RvTNbJe2k; __tasessionId=ds299u6d11583295365643; tt_scid=sj2lJXErealSUzO5TJFoJFxMaah8h2th9aAqWK42Hsl7khyzpgNtakiS2iU8gYlcec7c'
    }
   # group = [x for x in range(GROUP_START,GROUP_END+1)]
    pool =  Pool()
    pool.map(main())