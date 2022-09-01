from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

# API 파라미터 설정
key = '01b64a6426989a6552a89311fbaebff8'
itemperpage='100'

movie_list = []
for i in range(520, 535):
# API JSON데이터 변수에 저장
    API_URL = f'https://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json?key={key}&itemPerPage={itemperpage}&movieTypeCd=220101&curPage={i}'
    data = requests.get(API_URL)
    movie_list_100 = json.loads(data.text)['movieListResult']['movieList']
    movie_list.extend(movie_list_100)

# 특정 장르 데이터 제거
Matching = [s for s in movie_list if "성인물(에로)" not in s['genreAlt']
            if "멜로/로맨스" not in s['genreAlt']
            if "" !=  s['openDt']
            if "" != s['prdtYear']]

# 감독 데이터 따로 변수에 저장
director_list = []
for i in range(len(Matching)):
    director = Matching[i]['directors']
    if len(director) == 1:
        director_list.append(director[0]['peopleNm'])
    else:
        l = []
        for i in director:
            l.append(i['peopleNm'])
        b = ", ".join(l)
        director_list.append(b)

# 특정 키값 제거
for items in Matching:
    del items['companys']
    del items['directors']
    del items['nationAlt']

# JSON 데이터에 감독 데이터 추가
for i in range(len(Matching)):
    Matching[i].update( {'directors' : director_list[i]} )

option = webdriver.ChromeOptions()
option.add_argument('headless')
driver = webdriver.Chrome('chromedriver',options=option)

BASE_URL = "https://movie.naver.com/movie"
def get_movie_code(movie_title, movie_director):
    movie_title.replace('#', '%23')
    search_url = f'{BASE_URL}/search/result.naver?section=movie&query={movie_title}'
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    
    page = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')

    title_list = soup.select('#old_content > .search_list_1 > li')

    for i in range(len(title_list)):
        director_search = title_list[i].find('dl').find_all(class_ = 'etc')[-1].find('a').text
        index = i
        if (director_search == movie_director):
            break
        else:
            index=1
        
    if soup.find_all(class_ = 'result_thumb') !=[]:
        res = soup.find_all(class_ = 'result_thumb')[index]
        movie_code = int(str(res.find('a')).split('code=')[1].split('"><img')[0])
        
    return movie_code

### main info

def main_info(movie_code):
    movie_url = f'{BASE_URL}/bi/mi/basic.naver?code={movie_code}'
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    page = requests.get(movie_url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')

    # 포스터 링크
    poster = None 
    image = soup.select('.mv_info_area > .poster > a > img')
    if image != []:
        poster = image[0]['src'] ###
    
   # 상영시간
    duration = None
    duration_html = soup.select('.info_spec > dd > p > span')
    if duration_html != []:
        duration = int(re.findall(r"\d+", duration_html[2].text)[0]) ###

    # 나이 등급
    age_limit = None
    age_limit_html = soup.find(class_ = 'step4')
    if age_limit_html is not None:
        age_limit = age_limit_html.next.next.next.next.find('a').text ###

    # 흥행
    viewers = None
    base_date = None 
    viewers_totes = soup.select('.step9_cont > .count')
    if viewers_totes != []:
        viewers = int(viewers_totes[0].text.split('명')[0].replace(',','')) ### 누적관람객 수
        base_date = viewers_totes[0].text.split('(')[1].split(' ')[0] ### 누적관람객 수의 기준이 되는 날짜
    
    # 보러가기 링크
    reserve_html = soup.find(id='reserveBasic')
    reserve = None
    if reserve_html is not None:
        reserve = reserve_html['href'] ### 예매하기 링크

    download = None
    btn_count = soup.select('.btn_sns > .end_btn_area > ul > li')
    if (reserve_html is not None) & (len(btn_count) >= 3): 
        download_html = soup.select('.btn_sns > .end_btn_area > ul > li:nth-of-type(2) > a')
        if download_html is not None:
            download = download_html[0]['href']
            
    if (reserve_html is None) & (len(btn_count) >= 2):
        download_html = soup.select('.btn_sns > .end_btn_area > ul > li:nth-of-type(1) > a')
        if download_html != []:
            download = download_html[0]['href'] ### 다운로드 링크 =
    
    # 줄거리
    story_title = None
    if soup.find(class_ = 'h_tx_story') is not None:
        story_title = soup.find(class_ = 'h_tx_story').text ### 줄거리 제목
        
    story_content = None
    if soup.find(class_ = 'con_tx') is not None:
        story_content = soup.find(class_ = 'con_tx').text ### 줄거리 내용
    
    # 배우
    actor1 = None
    actor2 = None
    actor3 = None
    actor4 = None
    actor5 = None
    actor1_html = soup.select('.people > ul > li:nth-of-type(2) > a:nth-of-type(1)')
    actor2_html = soup.select('.people > ul > li:nth-of-type(3) > a:nth-of-type(1)')
    actor3_html = soup.select('.people > ul > li:nth-of-type(4) > a:nth-of-type(1)')
    actor4_html = soup.select('.people > ul > li:nth-of-type(5) > a:nth-of-type(1)')
    actor5_html = soup.select('.people > ul > li:nth-of-type(6) > a:nth-of-type(1)')
    if actor1_html != []:
        actor1 = actor1_html[0]['title'] ###
    if actor2_html != []:
        actor2 = actor2_html[0]['title'] ###
    if actor3_html != []:
        actor3 = actor3_html[0]['title'] ###
    if actor4_html != []:
        actor4 = actor4_html[0]['title'] ###
    if actor5_html != []:
        actor5 = actor5_html[0]['title'] ###
    
    # 네티즌 평점
    netizen_score = None
    netizen_score_html = soup.select('.netizen_score > .sc_view > .star_score > em')
    if netizen_score_html != []:
        netizen_score = float(netizen_score_html[0].text) ###

    # 네티즌 평점 참여자
    netizen_count = None
    netizen_count_html = soup.select('.netizen_score > .sc_view > .user_count > em')
    if netizen_count_html != []:
        netizen_count = int(netizen_count_html[0].text.replace(',','')) ###
    
    # 기자/평론가 평점
    special_score = None
    special_score_html = soup.select('.special_score > .sc_view > .star_score > em')
    if special_score_html !=[]:
        special_score = float(special_score_html[0].text)

    # 기자/평론가 평점 참여자
    special_count = None
    special_count_html = soup.select('.special_score > .sc_view > .user_count > em')
    if special_count_html !=[]:
        special_count = int(special_count_html[0].text.replace(',',''))
    
    # Beautifulsoup으로는 svg 요소들이 포착되지 않아서 javascript 방법을 사용하는 selenium을 활용
    # 성별 관람 비율
    male_ratio = None
    female_ratio = None
    driver.get(movie_url)
    elements = driver.find_elements(By.ID, "actualGenderGraph")
    gender_html = [WebElement.get_attribute('innerHTML') for WebElement in elements]
    if gender_html != []:
        ### 남자 관람 ratio
        if BeautifulSoup(gender_html[0]).select('svg > text:nth-of-type(1) > tspan') != []:
            male_ratio = int(BeautifulSoup(gender_html[0]).select('svg > text:nth-of-type(1) > tspan')[0].text.replace('%',''))/100
        else:
            male_ratio = 0
        ### 여자 관람 ratio
        if BeautifulSoup(gender_html[0]).select('svg > text:nth-of-type(2) > tspan') != []:
            female_ratio = int(BeautifulSoup(gender_html[0]).select('svg > text:nth-of-type(2) > tspan')[0].text.replace('%',''))/100
        else:
            female_ratio =0
        
    ### 나이별 관람 ratio
    ratio_10 = None
    percentage1 = soup.select('.bar_graph > .graph_box:nth-of-type(1) > strong')
    if percentage1 != []:
        ratio_10 = int(percentage1[0].text.replace('%',''))/100 ### 10대
        
    ratio_20 = None
    percentage2 = soup.select('.bar_graph > .graph_box:nth-of-type(2) > strong')
    if percentage2 != []:
        ratio_20 = int(percentage2[0].text.replace('%',''))/100 ### 20대
        
    ratio_30 = None
    percentage3 = soup.select('.bar_graph > .graph_box:nth-of-type(3) > strong')
    if percentage3 != []:
        ratio_30 = int(percentage3[0].text.replace('%',''))/100 ### 30대
        
    ratio_40 = None
    percentage4 = soup.select('.bar_graph > .graph_box:nth-of-type(4) > strong')
    if percentage4 != []:
        ratio_40 = int(percentage4[0].text.replace('%',''))/100 ### 40대
    
    ratio_50 = None
    percentage5 = soup.select('.bar_graph > .graph_box:nth-of-type(5) > strong')
    if percentage5 != []:
        ratio_50 = int(percentage5[0].text.replace('%',''))/100 ### 50대
    
    return poster, duration, age_limit, viewers, base_date, reserve, download, story_title, story_content, actor1, \
            actor2, actor3, actor4, actor5, netizen_score, netizen_count, special_score, special_count, male_ratio, female_ratio, \
            ratio_10, ratio_20, ratio_30, ratio_40, ratio_50
    
    ### 리턴 25개의 값
    
# 평점 info
def score_info(movie_code):
    # 평점 page
    score_url = f'{BASE_URL}/bi/mi/point.naver?code={movie_code}'
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    page = requests.get(score_url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    #성별 나이별 만족도
    score_m = None
    score_m_html = soup.select('.grp_male > .graph_point')
    if score_m_html != []:
        score_m = float(score_m_html[0].text) ### 남자 평점

    score_f = None
    score_f_html = soup.select('.grp_female > .graph_point')
    if score_f_html != []:
        score_f = float(score_f_html[0].text) ### 여자 평점
    
    score_10 = None
    score_20 = None
    score_30 = None 
    score_40 = None 
    score_50 = None
    score_age = soup.select('.grp_age > .grp_box')

    if score_age != []:
        score_10 = float(score_age[0].select('strong:nth-of-type(2)')[0].text) ### 10대
        score_20 = float(score_age[1].select('strong:nth-of-type(2)')[0].text) ### 20대
        score_30 = float(score_age[2].select('strong:nth-of-type(2)')[0].text) ### 30대
        score_40 = float(score_age[3].select('strong:nth-of-type(2)')[0].text) ### 40대
        score_50 = float(score_age[4].select('strong:nth-of-type(2)')[0].text) ### 50대
    
    # 감상포인트
    driver.get(score_url)
    elements = driver.find_elements(By.ID, "netizenEnjoyPointGraph")
    evaluation = [WebElement.get_attribute('innerHTML') for WebElement in elements]
    
    production = None
    acting = None
    story = None
    aesthetics= None
    OST = None
    if evaluation != []:
        production = float(BeautifulSoup(evaluation[0]).select('svg > text:nth-of-type(1) > tspan')[0].text.replace('%',''))/100 ### 연출
        acting = float(BeautifulSoup(evaluation[0]).select('svg > text:nth-of-type(2) > tspan')[0].text.replace('%',''))/100 ### 연기
        story = float(BeautifulSoup(evaluation[0]).select('svg > text:nth-of-type(3) > tspan')[0].text.replace('%',''))/100 ### 스토리
        aesthetics= float(BeautifulSoup(evaluation[0]).select('svg > text:nth-of-type(4) > tspan')[0].text.replace('%',''))/100 ### 영상미
        OST = float(BeautifulSoup(evaluation[0]).select('svg > text:nth-of-type(5) > tspan')[0].text.replace('%',''))/100 ### OST
    
    return score_m, score_f, score_10, score_20, score_30, score_40, score_50, production, acting, story, aesthetics, OST

### 리턴 12개의 값


import psycopg2
conn = None
cur = None

# 참고: https://www.youtube.com/watch?v=M2NzvnfS-hI&t=3s
try: 
    conn = psycopg2.connect(
    host = "localhost",
    user = "postgres",
    password = "=>mYF38^",
    dbname = "movies",
    port = 5432
)
    cur = conn.cursor()
    
    create_script = ''' CREATE TABLE IF NOT EXISTS basic_info (
                        movieCd  varchar(128) PRIMARY KEY,
                        movieNm    varchar(256),
                        movieNmEn  varchar(256),
                        prdtYear int,
                        openDt  date,
                        typeNm  varchar(256),
                        prdtStatNm  varchar(256),
                        genreAlt    varchar(256),
                        repNationNm varchar(256),
                        repGenreNm  varchar(256),
                        directors   varchar(256),
                        poster varchar(1024),
                        duration int,
                        age_limit varchar(128),
                        viewers int,
                        base_date varchar(256),
                        reserve varchar(1024),
                        download varchar(1024),
                        story_title varchar(1024),
                        story_content varchar(4096),
                        actor1 varchar(128),
                        actor2 varchar(128), 
                        actor3 varchar(128),
                        actor4 varchar(128),
                        actor5 varchar(128),
                        netizen_score float,
                        netizen_count int,
                        special_score float,
                        special_count int,
                        male_ratio float,
                        female_ratio float,
                        ratio_10 float,
                        ratio_20 float,
                        ratio_30 float,
                        ratio_40 float,
                        ratio_50 float,
                        score_m float,
                        score_f float,
                        score_10 float,
                        score_20 float,
                        score_30 float,
                        score_40 float,
                        score_50 float,
                        production float,
                        acting float,
                        story float,
                        aesthetics float,
                        OST float) '''
    
    cur.execute(create_script)

    # poster, duration, age_limit, viewers, base_date, reserve, download, story_title, story_content, actor1, \
    #        actor2, actor3, actor4, actor5, netizen_score, netizen_count, special_score, special_count, male_ratio, female_ratio, \
    #        ratio_10, ratio_20, ratio_30, ratio_40, ratio_50  ### 25
    
    # score_m, score_f, score_10, score_20, score_30, score_40, score_50, production, acting, story, aesthetics, OST ### 12
    
    insert_script = '''INSERT INTO basic_info(movieCd, movieNm, movieNmEn, prdtYear, openDt, typeNm, prdtStatNm, genreAlt, 
    repNationNm, repGenreNm, directors, poster, duration, age_limit, viewers, base_date, reserve, download, story_title, 
    story_content, actor1, actor2, actor3, actor4, actor5, netizen_score, netizen_count, special_score, special_count, 
    male_ratio, female_ratio, ratio_10, ratio_20, ratio_30, ratio_40, ratio_50, 
    score_m, score_f, score_10, score_20, score_30, score_40, score_50, production, acting, story, aesthetics, OST) VALUES 
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

    for i in range(len(Matching)):
        try:
            movie_code =get_movie_code(Matching[i]['movieNm'], Matching[i]['directors'])
            main_infos = main_info(movie_code)
            score_infos = score_info(movie_code)
            insert_value = (Matching[i]['movieCd'], Matching[i]['movieNm'], Matching[i]['movieNmEn'], Matching[i]['prdtYear'],
                    Matching[i]['openDt'], Matching[i]['typeNm'], Matching[i]['prdtStatNm'],
                    Matching[i]['genreAlt'], Matching[i]['repNationNm'], Matching[i]['repGenreNm'], Matching[i]['directors'], 
                    main_infos[0], main_infos[1], main_infos[2], main_infos[3], main_infos[4], main_infos[5], main_infos[6], 
                    main_infos[7], main_infos[8], main_infos[9], main_infos[10], main_infos[11], main_infos[12], main_infos[13], 
                    main_infos[14], main_infos[15], main_infos[16], main_infos[17], main_infos[18], main_infos[19], main_infos[20], 
                    main_infos[21], main_infos[22], main_infos[23], main_infos[24], score_infos[0], score_infos[1], score_infos[2], 
                    score_infos[3], score_infos[4], score_infos[5], score_infos[6], score_infos[7], score_infos[8], score_infos[9], 
                    score_infos[10], score_infos[11])
            cur.execute(insert_script, insert_value)
        except Exception as error:
            print(error)
        else:
            continue
        
    conn.commit()
    
#conn.commit()
except Exception as error:
    print(error)
finally:
    if cur is not None:
        cur.close()
    if conn is not None:
        conn.close()