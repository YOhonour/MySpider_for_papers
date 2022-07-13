from bs4 import BeautifulSoup
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
import requests
import re
import json
import pymysql
import traceback

driverPath = 'D:\My Codes\MyPythonPrj\chromedriver_win32\chromedriver.exe'
targetUrl = 'https://scholar.google.com/citations?user=d0FzG8YAAAAJ&hl=zh-CN'
save_filepath = './sourse.html'
base_host = 'https://scholar.google.com'

user_ = 'root'
passwd_ = '123456'
db_name_paper_liye = 'papers_liye'
db_tabel_name = 'papers'
host_ = '127.0.0.1'
port_ = 3306

class MySpider:
    driverPath = 'D:\My Codes\MyPythonPrj\chromedriver_win32\chromedriver.exe'
    browser = None
    file = None
    url= None
    pagesource = None
    options = None
    def __init__(self, url=targetUrl,options=None):
        self.url = targetUrl
        if options != None:
            self.options = options
        else:
            self.options = webdriver.ChromeOptions()
            self.options.add_argument('--headless')

        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'

        service_args = [
            # '--proxy=%s' % ip_html,  # 代理 IP：prot  （eg：192.168.0.28:808）
            # '--proxy-type=http',  # 代理类型：http/https
        '--load - images = no' # 关闭图片加载（可选）
        '--disk-cache=yes',  # 开启缓存（可选）
        # '--ignore-ssl-errors=true'  # 忽略https错误（可选）
        ]
        dcap = dict(DesiredCapabilities.CHROME)
        dcap["phantomjs.page.settings.userAgent"] = user_agent
        self.browser = webdriver.Chrome(executable_path=self.driverPath, options=self.options,service_args = service_args,desired_capabilities=dcap)
    def __init_file__(self, pagesource_filepath=save_filepath):
        self.file = open(pagesource_filepath, 'w',encoding="UTF-8")
        self.file.truncate()

    def __del__(self):
        if self.file is None :
            return 
        else:
            self.file.close()
    def getpage(self,target=targetUrl):
        self.browser.get(target)
        self.pagesource = self.browser.page_source
        return
    def save2file(self):
        if self.file == None:
            return 
        self.file.write(self.pagesource)
        return
    def webpost(self,url):
        pass
#初始化数据库，一些准备工作
def init_database():
    connection = pymysql.connect(host=host_, port=port_, user=user_, passwd=passwd_, db=db_name_paper_liye,
                                 charset='utf8mb4')
    cur = connection.cursor()
    sql1 = 'CREATE DATABASE IF NOT EXISTS {};'.format(db_name_paper_liye)
    try:
        cur.execute(sql1)
    except:
        print("数据库创建失败\n")
        traceback.print_exc()
    print("数据库创建成功！\n")
    sql2="CREATE TABLE IF NOT EXISTS %s.%s (id int NOT NULL AUTO_INCREMENT,years varchar(255),quote varchar(255),title varchar(255) NOT NULL," \
         "authers varchar(255) NOT NULL, journal varchar(255) ,google_url text CHARACTER SET utf8mb4,pdf_url text CHARACTER SET utf8mb4,PRIMARY KEY (id))"\
         %(db_name_paper_liye,db_tabel_name)
    try:
        cur.execute(sql2)
    except:
        print("数据表创建失败\n")
        traceback.print_exc()
    print("数据表创建成功\n")
    #每次都清空表
    sql3 = "TRUNCATE TABLE %s.%s"%(db_name_paper_liye,db_tabel_name)
    try:
        cur.execute(sql3)
    except:
        print("TRUNCATE失败\n")
        traceback.print_exc()
    return connection,cur
def insert2table(cur,years_,quote_,title_,authers_,journal_,google_url,pdf_url):
    sql_='INSERT INTO {}.{}( years,quote,title,authers,journal,google_url,pdf_url) VALUES ("{}","{}","{}","{}","{}","{}","{}")'\
        .format(db_name_paper_liye,db_tabel_name,years_,quote_,title_,authers_,journal_.replace("'","\'"),google_url,pdf_url)
    print("SQL: ", sql_)

    try:
        cur.execute(sql_)
    except:
        print("insert失败\n")
        traceback.print_exc()

#在谷歌论文详情页中获取论文PDF的地址
def getPDFUrl(chrome_url):
    # lines[1].contents[0].contents[0].attrs['href']
    sp1 = MySpider()
    sp1.getpage(chrome_url) 
    soup2 = BeautifulSoup(sp1.pagesource, features="html.parser")
    lines2 = soup2.findAll('div', class_='gsc_oci_title_ggi')
    if lines2.__len__() == 0 :
        return ""
    else :
        if lines2.__len__() == 1:
            #正常逻辑
            return lines2[0].contents[0].attrs['href']
        else:
            print("页面错误，gsc_oci_title_ggi 多于1个")
            return ""


def main():
    pagesource = None
    with open('D:/My Codes/MyPythonPrj/MySpider_for_papers/view-source.html','r',encoding="UTF-8") as f:
        pagesource = f.read()
    # print(pagesource)

    soup = BeautifulSoup(pagesource, features="html.parser")
    lines = soup.findAll('tr',class_='gsc_a_tr')
    connection,cur = init_database()
    i = 0
    for s in lines:
        url = s.contents[0].contents[0].attrs['href']
        # 论文题目
        title=s.contents[0].contents[0].text
        # 论文作者)
        authers=s.contents[0].contents[1].text
        # 期刊) 可能为空 lines[31].contents[0].contents[2].contents[0].text
        journal = 'null' if s.contents[0].contents[2].contents.__len__() == 0 else s.contents[0].contents[2].contents[0].text
        # 文章引用数) 638 lines[638].contents[1].contents[0].text
        quote = '0' if s.contents[1].contents[0].text == '' else s.contents[1].contents[0].text
        # 发表年份 531 lines[531].contents[2].contents[0].text
        years = 'null' if s.contents[2].contents[0].text == '' else s.contents[2].contents[0].text
        # years = s.contents[2].contents[0].text
        print('i=',i)
        i = i + 1

        #谷歌学术的页面地址
        chrome_url = s.contents[0].contents[0].attrs['href']
        pdfurl = getPDFUrl(chrome_url)
        insert2table(cur,years,quote,title,authers,journal,chrome_url,pdfurl)
    connection.commit()
    connection.close()



if __name__ == '__main__':
    main()

