from selenium import webdriver
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
# import time
# from lxml import etree
from time import sleep
import random
from selenium.webdriver.support import expected_conditions as EC
import pymongo
from config import *
from pyquery import PyQuery as pq
from multiprocessing import Pool

#创建MONGOdb数据库
client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]
#请求访问网页
browser = webdriver.Chrome()
wait = WebDriverWait(browser, 3)
'''
用selenium请求网页
模拟点击
查看源代码右键copy 可以复制路径
'''
def search():


    browser.get('https://www.taobao.com')
    browser.find_element_by_name('q').send_keys('美食')
    sleep(2)
    browser.find_element_by_xpath('//*[@id="J_TSearchForm"]/div[1]/button').click()  ##搜索按钮
    sleep(3)
    browser.find_element_by_xpath('//*[@id="J_QRCodeLogin"]/div[5]/a[1]').click()  #密码登录
    sleep(3)
    browser.find_element_by_xpath('//*[@id="J_OtherLogin"]/a[1]').click() #点击微博登录
    sleep(3)
    browser.find_element_by_name('username').send_keys('13241530124') #输入账户密码
    browser.find_element_by_name('password').send_keys('ldy..123')

    browser.find_element_by_xpath('//*[@id="pl_login_logged"]/div/div[7]/div[1]/a').click() #登录按钮
    # pl_login_logged > div:nth-child(2) > div:nth-child(7) > div:nth-child(1) > a > span
    sleep(2)


    total=browser.find_element_by_xpath('//*[@id="mainsrp-pager"]/div/div/div/div[1]') #页数100
    print(total.text)
    sleep(3)
    get_products(1)
    return total.text
'''
存到mongodb数据库

'''
def save_to_mongo(product):
    if db[MONGO_TABLE].insert(product):
        print("插入数据到数据库成功")
        return True
    return False

'''
查找价格，标题，地点等信息
css选择器找到

'''
def get_products(page):

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            '图片': item.find('.pic .img').attr('src'),
            '价格': item.find('.price').text(),
            '销量': item.find('.deal-cnt').text()[:-3],
            '商品': item.find('.title').text(),
            '店铺': item.find('.shop').text(),
            '产地': item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)
        # price = browser.find_elements_by_xpath('//div[@class="price g_price g_price-highlight"]/strong')
        # title = browser.find_elements_by_xpath('//*[@id="mainsrp-itemlist"]/div/div/div[1]/div/div[2]/div[2]/a')
        # place = browser.find_elements_by_xpath('//div[@class="row row-3 g-clearfix"]/div[2]')
        # buy_num = browser.find_elements_by_xpath('//div[@class="row row-1 g-clearfix"]/div[2]')
        # shop=browser.find_elements_by_xpath('//div[@class="shop"]/a/span[2]')
       #  print('第', page, '页,共有---', len(price), '个数据')
       #
       #  prices = []
       #  for i in price:
       #      try:
       #          price1 = i.text
       #      except:
       #          price1 == None
       #      prices.append(price1)
       #  #print(prices)
       #  titles=[]
       #  for i in title:
       #      try:
       #          title1 = i.text
       #      except:
       #          title1==None
       #      titles.append(title1)
       #  #print(titles)
       #
       #  places = []
       #  for i in place:
       #      try:
       #          place1 = i.text
       #      except:
       #          price1 == None
       #      places.append(place1)
       # # print(places)
       #
       #  buy_nums = []
       #  for i in buy_num:
       #      try:
       #          buy_num1 = i.text
       #      except:
       #          buy_num1 == None
       #      buy_nums.append(buy_num1)
       #  #print(buy_nums)
       #
       #  shops = []
       #  for i in shop:
       #      try:
       #          shop1 = i.text
       #      except:
       #          shop1 == None
       #      shops.append(shop1)
       #
        # for i in range(len(price)):
        #     product ={
        #         '店铺': shops[i],
        #         '商品':titles[i],
        #         '价格':prices[i],
        #         '产地':places[i],
        #         '购买人数':buy_nums[i]
        #     }
        #     save_to_mongo(product)
        #     print(str(product))
            # try:
            #     shop=shops[i]
            #     buy_num=buy_nums[i]
            #     price=prices[i]
            #     title=titles[i]
            #     place=places[i]
            #     ss = (str(shop),str(title), str(price), str(place), str(buy_num))
            #     print(ss)
            #     sql = "insert into taobao_food(shop,title,price,place,buy_num) VALUE('%s','%s','%s','%s','%s')" % ss
            # #    cur.execute(sql)
            # except:
            #     pass
       # coon.commit()
       #  print('------------------------------页数-------------------------------------')



'''
翻页，第一页已经爬取

'''
def next_page(page_number):
    try:
        input=browser.find_element_by_xpath('//*[@id="mainsrp-pager"]/div/div/div/div[2]/input')#填写页数
        submit=browser.find_element_by_xpath('//*[@id="mainsrp-pager"]/div/div/div/div[2]/span[3]')#确定键
        input.clear()
        input.send_keys(page_number)
        submit.click()
        print('第' + str(page_number) + '页正在翻------------')
        #print(browser.find_element_by_css_selector('#mainsrp-pager > div > div > div > ul > li.item.active > span'))
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number)))
        get_products(page_number)
    except TimeoutError:
        next_page(page_number)
def main():
    total=search()
    sleep(random.uniform(8, 0))
    total=int(re.compile('(\d+)').search(total).group(1))  #根据网页找页数 也就是100页
    #print(total)
    for i  in range(2,total+1):
        next_page(i)
        sleep(random.uniform(8, 10))

if __name__ == '__main__':
    main()
    # pool = Pool()
    # pool.map(main())