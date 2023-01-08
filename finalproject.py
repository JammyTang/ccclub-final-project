'''

套件

'''
#下載套件
import requests
from bs4 import BeautifulSoup
import time
import datetime
import pandas as pd
import csv
from typing import List
import asyncio
import json
import re
import sys
import os
from urllib.parse import urlencode
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import concurrent.futures


'''

資料處理模組(薪資、地點)

'''

#地點
city = ['基隆','新北','台北','桃園','新竹','苗栗','台中','彰化','南投','雲林','嘉義','台南','高雄','屏東','宜蘭','花蓮','台東','澎湖','金門','馬祖']
city_e = ['Keelung','NewTaipei','Taipei','Taoyuan','Hsinchu','Miaoli','Taichung','Changhua','Nantou','Yunlin','Chiayi','Tainan','Kaohsiung','Pingtung','Yilan','Hualien','Taitung','Penghu','Kinmen','Matsu']
city_yourator = ['基隆','新北','臺北','桃園','新竹','苗栗','臺中','彰化','南投','雲林','嘉義','臺南','高雄','屏東','宜蘭','花蓮','臺東','澎湖','金門','馬祖']


#薪水轉換成月薪的最高和最低(Yourator)
def process_salary_yourator(s):
  m = s.split()
  s = s.replace(",","")
  salary1 = [int(x) for x in s.split() if x.isdigit()]

  if '年薪' in m[-1]:
      for i in range(len(salary1)):
        salary1[i] = int(salary1[i]/12)
  elif '時薪' in m[-1]:
      for i in range(len(salary1)):
        salary1[i] = int(salary1[i]*8*22)
  elif '月薪' in m[-1]:
      salary1 = salary1
  
  return salary1

#薪水轉換成月薪的最高和最低(104)
def process_salary_104(s):
  s = s.replace(",","")
  salary1 = [int(x) for x in re.findall(r'-?\d+',s)]
  if '年薪' in s:
      for i in range(len(salary1)):
        salary1[i] = int(salary1[i]/12)
  elif '時薪' in s:
      for i in range(len(salary1)):
        salary1[i] = int(salary1[i]*8*22)
  elif '月薪' in s:
      salary1 = salary1
  
  return salary1


#薪水轉換成月薪的最高和最低(cakeresume)
def process_salary_cake(s):
  num_replace = {
    'K' : 1000,
    'B' : 1000000000,
    'M' : 1000000,
    }

  time = s.strip().split("/")[-1].strip()
  s = s.split("/")[0].split()

  if '+' in s[0]:
    number1 = s[0].replace('+','').strip()
    number2 = number1
  else:
    number1 = s[0]
    number2 = s[2]

#薪水轉換成純數字
  def pure_number(s2):
      mult = 1.0
      while s2[-1] in num_replace:
          mult *= num_replace[s2[-1]]
          s2 = s2[:-1]
      return int(float(s2) * mult)
  
  if 'year' in time:
    pure_number1 = str(int(pure_number(number1)/12))
    pure_number2 = str(int(pure_number(number2)/12))
  elif 'hour' in time:
    pure_number1 = str(int(pure_number(number1)*8*22))
    pure_number2 = str(int(pure_number(number2)*8*22))
  elif 'month' in time:
    pure_number1 = str(pure_number(number1))
    pure_number2 = str(pure_number(number2))

  pure_list = [pure_number1,pure_number2]
  
  return pure_list

'''

CakeResume爬蟲

'''
def get_one_page_1(URL):
    data = {}
    re = requests.get(URL)
    soup_cakeresume = BeautifulSoup(re.text,"html.parser")

    for job_introduce in soup_cakeresume.findAll("div",{"class":"JobSearchItem_headerTitle__k_1FH"}):
        #職位名稱
        name = job_introduce.a.text
        print(job_introduce)
        #點進網站
        url_job = "https://www.cakeresume.com" + job_introduce.a["href"]      
        re_job = requests.get(url_job)
        soup_job = BeautifulSoup(re_job.text,"html.parser")
        
        #公司名稱
        company = soup_job.find("div",{"class":"JobDescriptionLeftColumn_companyInfo__WRlaG"}).text       
                      
        #薪資
        salary = soup_job.find("div",{"class":"JobDescriptionRightColumn_salaryWrapper__mYzNx"}).text
        
        #更新時間
        times = soup_job.find("div",{"class":"InlineMessage_label__hP3Fk"}).text
        
        #職缺地點
        job_info = soup_job.find("div",{"class":"JobDescriptionRightColumn_jobInfo__8_M8K"})
        infos = []
        for i in range(len(job_info.findAll("div",{"class":"JobDescriptionRightColumn_row__uGTdT"}))):
          info = job_info.findAll("div",{"class":"JobDescriptionRightColumn_row__uGTdT"})[i].text
          infos.append(info)
        for i in city:
          if i in infos[1]:
            infos[1] = i
            break
          else:
            continue
        #產業
        pre_industry = soup_job.find("div",{"class":"JobDescriptionBlock_mainContainer__4fOMV"})
        industry = pre_industry.find("span",{"class":"Breadcrumbs_labelText__LW0fe"}).text

        #處理薪資
        try:
          salary = salary
          salary_num = process_salary_cake(salary)
          salary_low = salary_num[0]
          salary_high = salary_num[-1] 
        except:
          salary = salary
          salary_low = ''
          salary_high = ''
        
        if '面議' in salary:
          discuss_salary = '面議'
        else:
          discuss_salary = ''
        
        #新增只有縣市的欄位
        location_title = '其他'

        try:
          location = infos[1]
          for i in range(len(city_e)):
            if city_e[i] in location:
              location_title = city[i]
              break
            elif city[i] in location:
              location_title = city[i]
              break
            else:
              continue
        except:
          location = infos[1]
        
        #將縣市欄位為「其他」轉換成公司地址的縣市
        if location_title == '其他':
          location_title = soup_job.find("a",{"class":"CompanyInfoItem_link__E841d"}).text
          for i in range(len(city_e)):
            if city_e[i] in location_title:
              location_title = city[i]
              break
            elif city[i] in location_title:
              location_title = city[i]
              break
            else:
              continue

        #處理時間(年分、月份)
        parsed_s = [times.split()[-3:-1]]

        time_dict = dict((fmt,float(amount)) for amount,fmt in parsed_s)

        dt = datetime.timedelta(**time_dict)
        past_time = datetime.datetime.now() - dt
        update_date = past_time.date().strftime("%m/%d")

        
        
        #建立data字典
        data = {
            'title': name,
            'company': company,
            'salary': salary,
            'salary_low' : salary_low,
            'salary_high' : salary_high,
            'discuss_salary' : discuss_salary,
            'location' : location,
            'industry': industry,
            'location_title' : location_title,
            'update_date' : update_date,
            'website' : 'CakeResume'
            }
        
        #放入資料
        job_list.append(data)        
    
'''

Yourator爬蟲

'''
def get_one_page_2(URL):
    data = {}
    re = requests.get(URL)
    preuse_dict = re.json()
    list_of_dicts = preuse_dict["jobs"]
    for i in list_of_dicts:
      soup_cakeresume = BeautifulSoup(re.text,"html.parser")
      url_job = "https://www.yourator.co" + i["path"]
      re_job = requests.get(url_job)
      soup_job = BeautifulSoup(re_job.text,"lxml")
      
      #職位名稱
      name = soup_job.find("h1",{"class","basic-info__title__text"}).text
      
      #公司名稱
      company = soup_job.find("h4",{"class":"flex-item"}).a.text       
        
      #薪資
      job_info = soup_job.find("div",{"class":"col-md-9 col-sm-12 job__content"})
      salary = job_info.findAll("section",{"class":"content__area"})[-2].text
      
      #更新時間
      times = soup_job.find("p",{"class","basic-info__last_updated_at"}).text

      #處理薪資
      m = salary.split()

      try:
        salary = salary
        salary_list = process_salary_yourator(salary)
        if len(salary_list) == 1:
          salary_list.append(salary_list[0])
        else:
          salary_list = salary_list
        salary_low = salary_list[0]
        salary_high = salary_list[-1]

      except:
        salary = salary
        salary_low = ''
        salary_high = ''
      if '面議' in salary:
        discuss_salary = '面議'
      else:
        discuss_salary = ''
      
      #地點
      location = soup_job.find("p",{"class":"basic-info__address inline-flex flex-wrap"}).text
      
      #新增只有縣市的欄位
      location_title = '其他'

      try:
        location = location
        for i in range(len(city_yourator)):
          if city_yourator[i] in location:
            location_title = city[i]
            break
          else:
            continue
      except:
        location = location
      
      #處理時間
      up_times = times.replace("最近更新於","").strip()

      struct_time = time.strptime(up_times, "%Y-%m-%d") 

      update_date = time.strftime("%m/%d",struct_time)
      
      
      #產業
      try:
        job_classification = soup_job.find("p",{"class":"basic-info__tag inline-flex flex-wrap"}).text.strip('\n').replace('\n',',')
      except:
        job_classification = 'others'
      
      
      #建立data字典
      data = {
            'title': name,
            'company': company,
            'salary': salary,
            'salary_low': salary_low,
            'salary_high': salary_high,
            'discuss_salary' : discuss_salary,
            'location' : location,
            'industry': job_classification,
            'location_title' : location_title,
            'update_date' : update_date,
            'website' : 'Yourator'
            }
      #放入資料
      job_list.append(data)

'''

104爬蟲

'''
def get_one_page_3(URL):
    data = {}
    title_lst = []
    company_lst = []
    salary_lst = []
    company_address_lst = []
    company_cate_lst = []
    date_lst = []
    location_title_lst = []
    salary_detail_list = []
    salary_low_lst = []
    salary_high_lst = []
    discuss_salary_lst = []

    re = requests.get(URL)
    soup_104 = BeautifulSoup(re.text,"html.parser")


    #職缺名稱
    for job in soup_104.findAll("a",{"data-qa-id":"jobSeachResultTitle"}):
        name = job.text
        title_lst.append(name)

    for companies in soup_104.findAll("ul",{"class":"b-list-inline b-clearfix"}):
    #公司名稱
        company_name = companies.a.text.replace('\n', '').replace('                    ','')
        company_lst.append(company_name)

    #公司資訊
    #薪水、公司規模、是否上市櫃、詳細地址
    for companies in soup_104.findAll("div",{"class":"job-list-tag b-content"}):
        #薪水
        company_info = [] #薪水 = company_info[0]
    #合併 『明確薪水』與『待遇面議』
        for i in range(len(companies.findAll("span",{"class":"b-tag--default"}))):
            salary_1 = companies.findAll("span",{"class":"b-tag--default"})[i].text
            if '面議' in salary_1:
              company_info.append(salary_1)
                
        for i in range(len(companies.findAll("a",{"class":"b-tag--default"}))):
            salary_2 = companies.findAll("a",{"class":"b-tag--default"})[i].text
            company_info.append(salary_2)
            
        if len(company_info) > 1:
            salary_lst.append(company_info[0])

    for companies in soup_104.findAll("ul",{"class":"b-list-inline b-clearfix job-list-intro b-content"}):
        #地點
        company_address = companies.li.text[0:3]
        #新增只有縣市的欄位
        location_title = company_address
        try:
          company_address = company_address
          for i in range(len(city)):
            if city[i] in company_address:
              location_title = city[i]
              break
            else:
              continue
        except:
          company_address = company_address
          location_title = '其他'
                
        company_address_lst.append(company_address)
        location_title_lst.append(location_title)
        

    for companies in soup_104.findAll("article",{"class":"b-block--top-bord job-list-item b-clearfix js-job-item js-job-item--focus b-block--ad"}):
        # 產業-無
        company_cate1 = companies["data-indcat-desc"]
        company_cate_lst.append(company_cate1)
    for companies in soup_104.findAll("article",{"class":"b-block--top-bord job-list-item b-clearfix js-job-item"}):
        # 產業-有
        company_cate2 = companies["data-indcat-desc"]
        company_cate_lst.append(company_cate2)

    for companies in soup_104.findAll("span",{"class":"b-tit__date"}):
        # 更新時間
        date_update = companies.text
        date_lst.append(date_update)
    

    for n, c, s, ca, cc, ll, d in zip(title_lst, company_lst, salary_lst, company_address_lst, company_cate_lst, location_title_lst, date_lst):
        #處理薪資
        #薪資最低值
        #薪資最高值
        salary = s
        try:
          salary = s
          salary_list = process_salary_104(salary)
          if len(salary_list) == 1:
            salary_list.append(salary_list[0])
          else:
            salary_list = salary_list
          salary_low = salary_list[0]
          salary_high = salary_list[-1]

        except:
          salary = s
          salary_low = ''
          salary_high = ''

        if '面議' in salary:
          discuss_salary = '面議'
        else:
          discuss_salary = ''
        
        data = {'title':n, 
                'company':c,
                'salary':s,
                'salary_low':salary_low,
                'salary_high':salary_high,
                'discuss_salary':discuss_salary,
                'location':ca,
                'industry':cc,
                'location_title':ll,
                'update_date':d,
                'website':'104'
                }
        #放入資料
        job_list.append(data)

'''

主程式-爬蟲

'''
#主要網站:CakeResume、Yourator、104
#可以讓使用者輸想要的條件
#測試時請輸入關鍵字
#本次專案將以「數據分析」為關鍵字搜尋資料       
word = input("請輸入搜尋關鍵字:")
#最大頁數100頁
end = int(input("請輸入往後找尋到第幾頁(最大值為100):"))
if end > 100:
    while end > 100:
        end = int(input("請再輸入一次(最大值為100)"))

#建立資料串列
#主要放入爬蟲搜尋的資料
job_list = []


#執行CakeResume爬蟲
link1 = "https://www.cakeresume.com/jobs/" + str(word)
URL1 = [f"{link1}?order=latest&page={page}" for page in range(1,end+1)]

#執行Yourator爬蟲
link2 = "https://www.yourator.co/api/v2/jobs?term[]=" + str(word)
URL2 = [f"{link2}&sort=newest&page={page}" for page in range(1,end+1)]

#執行104爬蟲
link3 = "https://www.104.com.tw/jobs/search/?ro=0&kwop=7&keyword="+str(word)
URL3 = [f"{link3}&expansionType=area%2Cspec%2Ccom%2Cjob%2Cwf%2Cwktm&order=12&asc=0&page={page}" for page in range(1,end+1)]


#計算爬蟲時間
#開始執行時間
start_time = time.time()

#同時建立和啟用10個執行續，加快爬蟲速度
with concurrent.futures.ThreadPoolExecutor(max_workers = 10) as executor:
  executor.map(get_one_page_1,URL1)
with concurrent.futures.ThreadPoolExecutor(max_workers = 10) as executor:
  executor.map(get_one_page_2,URL2)
with concurrent.futures.ThreadPoolExecutor(max_workers = 10) as executor:
  executor.map(get_one_page_3,URL3)

#結束執行時間
end_time = time.time()


#將串列轉成資料表格式
df1 = pd.DataFrame(job_list)

#計時時間
print(f'總共花費{end_time-start_time}秒')


'''

主程式-資料前處理&資料清洗

'''
#薪資
#薪資欄位的「字串」格式轉成「數值」格式
df1["salary_low"] = pd.to_numeric(df1["salary_low"])
df1["salary_high"] = pd.to_numeric(df1["salary_high"])
#去除低於基本薪資的職缺、保留有面議的職缺
df1 = df1[(df1['salary_low'] >= 26250) |  (df1['salary_high'] >= 26250) | (df1['discuss_salary'] == '面議')]

#更新時間
#轉換非日期格式為空白
#去除空白
df1['update_date'].replace(r'\s+|\\n', '', regex=True, inplace=True)
df1 = df1[(df1['update_date'] != '')] 

#縣市
#去除非台灣城市
for i in df1['location_title']:
    if i not in city:
        df_drop = df1[df1["location_title"] == i].index
        df1 = df1.drop(df_drop)
    else:
        continue

#去除地點、薪資
#保留縣市、最低薪資、最高薪資
df1 = df1.drop(['location','salary'],axis = 1)

#重新排列順序
#刪除舊的索引值
#新的資料表
df1 = df1.reset_index(drop=True)

#轉換成csv檔案
df1.to_csv("job_search_dashboard_any.csv")

print("若想檢視資料表請執行下列「資料表結果」程式碼")


#薪水總攬
'''
(已經去除科學記號)
'''
#轉成數值格式
df1["salary_low"] = pd.to_numeric(df1["salary_low"])
df1["salary_high"] = pd.to_numeric(df1["salary_high"])
df1.describe()


#圓餅圖 面議/非面議比例
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
#下載台北黑體的中文字型
!wget -O TaipeiSansTCBeta-Regular.ttf https://drive.google.com/uc?id=1eGAsTN1HBpJAkeVM57_C7ccp7hbgSz3_&export=download
fm.fontManager.addfont('TaipeiSansTCBeta-Regular.ttf')
mpl.rc('font', family='Taipei Sans TC Beta')

#替換薪水形式的值
df9999= df1.copy()
df9999['discuss_salary'] = df9999['discuss_salary'].map({'':'非面議','面議':'面議'})
df9999

#使用風格
plt.style.use('ggplot')

#計算面議/非面議個數
df9999['discuss_salary'].value_counts().plot(kind = 'pie', title = '薪水形式比例', fontsize = 20)
df_discuss__or_not = pd.DataFrame(df9999['discuss_salary'].value_counts())
df_discuss__or_not = df_discuss__or_not.reset_index()
df_discuss__or_not.columns = ['形式','職缺數量']
df_discuss__or_not



#圓餅圖 縣市職缺比例
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
#下載台北黑體的中文字型
!wget -O TaipeiSansTCBeta-Regular.ttf https://drive.google.com/uc?id=1eGAsTN1HBpJAkeVM57_C7ccp7hbgSz3_&export=download
fm.fontManager.addfont('TaipeiSansTCBeta-Regular.ttf')
mpl.rc('font', family='Taipei Sans TC Beta')


#各縣市的職缺數量表
print(df1['location_title'].value_counts())
#各縣市的職缺比例圖
plt.style.use('ggplot')
df1['location_title'].value_counts().plot(kind = 'pie',title = '各縣市的職缺數量',figsize = (12,12))
df123 = pd.DataFrame(df1['location_title'].value_counts())
df123 = df123.reset_index()
df123.columns = ['縣市','職缺數量']
df123


#直方圖 整體薪資分布
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm

#下載台北黑體的中文字型
!wget -O TaipeiSansTCBeta-Regular.ttf https://drive.google.com/uc?id=1eGAsTN1HBpJAkeVM57_C7ccp7hbgSz3_&export=download
fm.fontManager.addfont('TaipeiSansTCBeta-Regular.ttf')
mpl.rc('font', family='Taipei Sans TC Beta')

#可以先去除異常值再作圖

df1["salary_low"] = pd.to_numeric(df1["salary_low"])
df1["salary_high"] = pd.to_numeric(df1["salary_high"])

df2 = df1.copy()
df2.dropna(axis = 0)
df2

#使用風格
plt.style.use('ggplot')
#去除科學記號顯示
plt.ticklabel_format(style='plain')
df_low = df2['salary_low']
df_high = df2['salary_high']
#將薪水上限限制300000
plt.hist(df_low, alpha = 0.5 ,bins = 50,label='a',range=(0,300000))
plt.hist(df_high, alpha = 0.5 ,bins = 50,label='b',range=(0,300000))
plt.title('薪水分布',size = 25)
plt.xlabel('薪水',size=15) # 設置x軸標簽
plt.ylabel('職缺數量',size=15) # 設置y軸標簽


#長條圖 職缺產業類別-CakeResume
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
import seaborn as sns

#提高圖片解析度
%config InlineBackend.figure_format = 'retina'

#下載台北黑體的中文字型
!wget -O TaipeiSansTCBeta-Regular.ttf https://drive.google.com/uc?id=1eGAsTN1HBpJAkeVM57_C7ccp7hbgSz3_&export=download
fm.fontManager.addfont('TaipeiSansTCBeta-Regular.ttf')
mpl.rc('font', family='Taipei Sans TC Beta')

df888 = df1.copy()
df888 = df888[df888['website'] == 'CakeResume']
print(df888)

#使用風格
plt.style.use('ggplot')

#取前十名
df888['industry'].value_counts(ascending = True).head(10).plot(kind = 'barh' , rot = 0 , title = '前十名產業/職缺類別數量-CakeResume' , figsize= (7,7) ,fontsize = 10 )




#職缺產業類別 104
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
import seaborn as sns

#提高圖片解析度
%config InlineBackend.figure_format = 'retina'

#下載台北黑體的中文字型
!wget -O TaipeiSansTCBeta-Regular.ttf https://drive.google.com/uc?id=1eGAsTN1HBpJAkeVM57_C7ccp7hbgSz3_&export=download
fm.fontManager.addfont('TaipeiSansTCBeta-Regular.ttf')
mpl.rc('font', family='Taipei Sans TC Beta')

df555 = df1.copy()
df555 = df555[df555['website'] == '104']
print(df555)

#使用風格
plt.style.use('ggplot')

#取前十名
df555['industry'].value_counts(ascending = True).tail(10).plot(kind = 'barh' , rot = 0 , title = '前十名產業/職缺類別數量-104' , figsize= (10,10) ,fontsize = 10 )




#職缺產業類別 yourator
#已下載中文字體
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
import seaborn as sns

#提高圖片解析度
%config InlineBackend.figure_format = 'retina'

#下載台北黑體的中文字型
!wget -O TaipeiSansTCBeta-Regular.ttf https://drive.google.com/uc?id=1eGAsTN1HBpJAkeVM57_C7ccp7hbgSz3_&export=download
fm.fontManager.addfont('TaipeiSansTCBeta-Regular.ttf')
mpl.rc('font', family='Taipei Sans TC Beta')

#利用串列轉換成字典計數
df8889 = df1.copy()
df8889 = df8889[df8889['website']=='Yourator']
a = df8889.loc[:,'industry']
o = []
for i in a:
  b = i.split(',')
  for t in b:
    o.append(t)
industry_dict = {}
for value in o:
  industry_dict[value]= industry_dict.get(value,0)+1
#移除others
industry_dict.pop('others')
#轉換成DataFrame
df777 = pd.DataFrame.from_dict(industry_dict,orient = 'index')
df777.columns = ['職缺數量']
df777
#使用圖形風格
plt.style.use('ggplot')
#數量排序
df777 = df777.sort_values(['職缺數量'],ascending = True)
#長條圖
#取前10名
df_sort_Yourator = df777.tail(10)
#長條圖
#取前十名
df_sort_Yourator.plot(kind = 'barh' , rot = 0 , title = '前十名產業/職缺類別數量-Yourator' , figsize= (10,10) ,fontsize = 10 )
df_sort_Yourator = df_sort_Yourator.reset_index()
df_sort_Yourator.columns = ['產業標籤','職缺數量']
df_sort_Yourator



#yourator 文字雲
!pip install wordcloud
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
import seaborn as sns
from wordcloud import WordCloud

#提高圖片解析度
%config InlineBackend.figure_format = 'retina'
%matplotlib inline

#下載台北黑體的中文字型
!wget -O TaipeiSansTCBeta-Regular.ttf https://drive.google.com/uc?id=1eGAsTN1HBpJAkeVM57_C7ccp7hbgSz3_&export=download
fm.fontManager.addfont('TaipeiSansTCBeta-Regular.ttf')
mpl.rc('font', family='Taipei Sans TC Beta')

#轉換串列
df8889 = df1.copy()
df8889 = df8889[df8889['website']=='Yourator']
a = df8889.loc[:,'industry']
o = []
for i in a:
  b = i.split(',')
  for t in b:
    if t == 'others':
      continue
    else:
      o.append(t)
Stro =  ",".join(o)
print(Stro)

#存成txt檔案
path = 'industry.txt'
f = open(path,'w')
f.write(Stro)
f.close()

# 從 Google 下載的中文字型
font = 'TaipeiSansTCBeta-Regular.ttf'

#製作文字雲
#背景使用白色、設定中文字體
#檔案在左側邊的檔案夾
text = open('industry.txt','r',encoding = 'utf-8').read()
cloud = WordCloud(background_color='white',font_path=font).generate(text)
cloud.to_file("industry_wordcloud.png")



#折線圖 更新時間-職缺數量
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm

#下載台北黑體的中文字型
!wget -O TaipeiSansTCBeta-Regular.ttf https://drive.google.com/uc?id=1eGAsTN1HBpJAkeVM57_C7ccp7hbgSz3_&export=download
fm.fontManager.addfont('TaipeiSansTCBeta-Regular.ttf')
mpl.rc('font', family='Taipei Sans TC Beta')

#複製資料集
df98 = df1.copy()
#根據日期計算職缺數量
date_sum = df98['update_date'].value_counts()
#將計算好的結果轉成資料集形式
date_sum = pd.DataFrame(date_sum)
#依照日期順序重新排列資料集
date_sum = date_sum.sort_index()
#使用風格
plt.style.use("ggplot")
#畫折線圖
date_sum.plot(kind = 'line',title = '每日開立職缺數量變化圖', linewidth = 2.5 , figsize = (8,8) , color = 'red')
#資料呈現
date_sum
