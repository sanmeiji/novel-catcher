# -*- coding: utf-8 -*-
"""
Created on Sun Mar  4 16:13:28 2018

@author: sanmeiji
"""

#%% library
import re
import pickle
import bs4
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
#import time

#%% Get cookies in terminal with selenium
ChromePath = r"/Users/csq/Documents/python-scrapy-novels/chromedriver" # mac
#ChromePath = r"D:\Documents\python-novels-scrapy\chromedriver.exe" #win
wd = webdriver.Chrome(executable_path = ChromePath)

#%%
loginUrl = "http://www.htwhbook.com/login"
wd.get(loginUrl)

#%%
cookies = wd.get_cookies()
pickle.dump(cookies, open("ht_cookies.pkl","wb"))
    
#%% Get the bookcase contents
req = requests.Session()
cookies = pickle.load(open("ht_cookies.pkl", "rb"))
for cookie in cookies:
    wd.add_cookie(cookie)
    req.cookies.set(cookie['name'], cookie['value'],
                    domain=cookie['domain'],
                    path=cookie['path'],
                    secure=cookie['secure'])
    
#%% Write bookcase contents in file
#file = open("bookcase-content.txt","wb")
#file.write(bookcase_page.content)
#file.close()

#%% Get a specific book from the bookcase
bookcase_url = "http://www.htwhbook.com/mymanagecache?actmode=mybookcase"
bookcase_page = req.get(bookcase_url)
bookcase_soup = BeautifulSoup(bookcase_page.content, "lxml")
books_url = bookcase_soup.find_all(name='a', attrs={"href":re.compile(r'=showbook&bookid=')})
#author_url = bookcase_soup.find_all(name='a', attrs={"href":re.compile(r'=showwriter&writer=')})
#%%

#for index, url in enumerate(books_url):
#    print(index, url.text)
print(len(books_url)-1)
which_book = books_url[6]
which_book.text
#%%
main_url = "http://www.htwhbook.com"
book_url = main_url + which_book.get('href')
book_get = req.get(book_url)

# 小黄书soup
book_soup = BeautifulSoup(book_get.content, "lxml")

# Get author name
book_sidebar = book_soup.select("div[id=sidebar]")
book_sidebar_soup = BeautifulSoup(str(book_soup.select("div[id=sidebar]")), "lxml")
author = book_sidebar_soup.body.h3.get_text().split('的專欄')[0]

# Get book content
book_content_soup = BeautifulSoup(str(book_soup.select("div[id=content]")), 
                                  "lxml").select("table[class='uk-table']")[0]
     
# Get book intro
bk_all = book_content_soup.contents[len(book_content_soup.contents)-2]
bk_intro = BeautifulSoup(str(bk_all), "lxml").body.div.contents[1]
bk_intro_sp = BeautifulSoup(str(bk_intro), "lxml").body.div
bk_intro_ctnt = bk_intro_sp.contents[len(bk_intro_sp.contents)-2]
intro_sp = BeautifulSoup(str(bk_intro_ctnt), "lxml").body

bookname = intro_sp.div.b.text
bk_tag_v = str(intro_sp.div.contents[17])
bk_authorsay_v = BeautifulSoup(str(intro_sp.div.contents[19:]), "lxml").body

for br in bk_authorsay_v.find_all("br"):
    br.replace_with("\n")

# replace symbols
useless_syms = r'[ X]+|\xa0+|\t+|\\u3000+|\\r+|\\t+|\\n+'

bk_tag=re.sub(useless_syms, ' ', bk_tag_v).strip()
bk_authorsay = re.sub(useless_syms, "", bk_authorsay_v.text).strip(("[|]"))
#print(bk_tag)
#print(bk_authorsay_v.text)
authorsay = "".join([str(s) for s in bk_authorsay]).strip("[|]").replace(",", "").replace("'","")
#authorsay = "".join(str(s) for s in bk_authorsay).replace("[,]|[']|[|]", "")
#print(authorsay)

# Get chapters
bk_contents = BeautifulSoup(str(bk_all), "lxml").body.td
bk_ctnt_text = bk_contents.contents[len(bk_contents.contents)-1]
bk_ctnt_sp = BeautifulSoup(str(bk_ctnt_text), "lxml").body.table
for tag in bk_ctnt_sp:
    if isinstance(tag, bs4.element.NavigableString):
        tag.extract()

# get folder-chapter contents and urls
fold_chap_name=[]
chap_urls=[]
#folder = bk_ctnt_sp.contents[4]

for folder in bk_ctnt_sp.contents:
    folder_soup = BeautifulSoup(str(folder), "lxml")
    folder_text = re.sub(useless_syms, "", folder_soup.body.tr.td.contents[4]).strip("\r\n")
    if folder_text == '這個作品的章節內容即將推出...':
        continue
    else:
        for tag in folder_soup.body.tr.td.div.div.table:
            if isinstance(tag, bs4.element.NavigableString):
                tag.extract()
        folder_name = str(folder_soup.body.b.text)
#       print(folder_name)
        chapters = folder_soup.body.tr.td.div.div.table
        for chap in chapters.contents:
            chap_soup = BeautifulSoup(str(chap), "lxml").body.tr.td
            for tag in chap_soup:
                if isinstance(tag, bs4.element.NavigableString):
                    tag.extract()
        
            chap_free = chap_soup.select("font[color='#008080']")
            chap_purchased = chap_soup.select("font[color='#800080']")
            if len(chap_free) != 0:
#               print(chap_free)
                chap_loc = chap_soup.find_all(name='a', attrs={"href":re.compile(r'paperid=')})
                chap_url = main_url + chap_loc[0].get('href')
                chap_name = chap_loc[0].text + " 【" + folder_name + "】 " 
                chap_urls.append(chap_url)
                fold_chap_name.append(chap_name)
            elif len(chap_purchased) != 0:
#               print(chap_purchased)
                chap_loc = chap_soup.find_all(name='a', attrs={"href":re.compile(r'paperid=')})
                chap_url = main_url + chap_loc[0].get('href')
                chap_name = chap_loc[0].text + "【" + folder_name + "】 " 
                chap_urls.append(chap_url)
                fold_chap_name.append(chap_name)
            else:
#               print("[]")
                continue
        
#for name in fold_chap_name:
#    print(name)
print(str(len(chap_urls)) + " chapters need to be downloaded...")

#%% Download chapters
chapters = []
for index, chap in enumerate(chap_urls):
    wd.get(chap)
#    time.sleep(5)
    chap_source = wd.page_source
    chap_soup = BeautifulSoup(chap_source, "lxml")
    chapters.append(chap_soup)
    print(index + 1, "of", len(chap_urls), "done")

# Get ebook contents
ebooks = []
for chapter in chapters:
    ebook = BeautifulSoup(str(chapter.select('div[id="ebookcontent"]')), "lxml")
    chapter_writersay = BeautifulSoup(str(chapter.select('div[id="writersaya"]')), "lxml").text.strip("[|]")
    if type(ebook.body.div) != type(None):
        for tag in ebook.body.div:
            if not isinstance(tag, bs4.element.NavigableString):
                tag.extract()
        for br in ebook.body.div.find_all("br"):
            br.replace_with("\n")
        ebook_text = re.sub(r'\n+', '\n\n', ebook.body.div.text.replace("\u3000", "").replace(" ", ""))
#        ebook_text=re.sub('\n+', '\n', ebook.body.div.text).strip().replace("\u3000", "")
#        ebooks.append(ebook_text)
        ebooks.append(ebook_text + "\n---\n作者要说的话：" + chapter_writersay + "\n---\n")
    else:
        continue

#
file_name = bookname.replace("/", "_") + " by " + author
file = open("books/" + file_name + ".txt", "w")
file.write(file_name)
file.write('\n\n')
file.write("======== 标签 ========\n")
file.write('\n')
file.write(bk_tag)
file.write('\n\n')
file.write("======== 说明 ========\n")
file.write('\n')
file.write(authorsay)
file.write('\n\n')
file.write("======== 正文 ========\n")
file.write('\n')
for i in range(len(ebooks)):
    chap_index = "[Chapter " + str(i+1) + "] "
    file.write(chap_index)
    file.write(fold_chap_name[i])
    file.write('\n\n')
    file.write(ebooks[i])
    file.write('\n\n\n')
file.close()

print("【" + file_name + "】" + "存好辣咩哈哈哈")