from flask import Flask, render_template, request
import pandas as pd
import pickle
import pandas as pd
import re
import os 

df = pd.read_pickle('data.pkl')

with open('model.pkl', 'rb') as pickle_file:
    model = pickle.load(pickle_file)

indices = pd.Series(df.index, index=df['movieNm']).drop_duplicates()

def get_recommendations(title, cosine_sim=model):
    # Get the index of the movie that matches the title
    idx = indices[title]

    # Get the pairwsie similarity scores of all movies with that movie
    sim_scores = list(enumerate(cosine_sim[idx]))

    # Sort the movies based on the similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the scores of the 10 most similar movies
    sim_scores = sim_scores[1:25]

    # Get the movie indices
    movie_indices = [i[0] for i in sim_scores]

    # Return the top 10 most similar movies
    # 'movieCd', 'movieNm', 'genreAlt', 'directors', 'poster', 'age_limit', 'story_title', 'story_content', 'actor1', 'actor2', 'actor3', 'actor4', 'actor5'
    return  df.iloc[movie_indices]

def shorter_content(data):
    p = re.compile('(.{100}[^\s]*)\s')
    if p.match(data) != None:
        info = p.match(data).group() + '...'
    else: 
        info = ''
    return info

def recommend_values(data, i):
    poster1 = data.loc[i, 'poster']
    movienm1 = data.loc[i, 'movieNm']
    story_content1 = shorter_content(data.loc[i, 'story_content'])
    if data.loc[i, 'download'] != None:
        watch1 = data.loc[i, 'download']
    elif data.loc[i, 'reserve'] != None: 
        watch1 = 'https://movie.naver.com' + data.loc[i, 'reserve']
    else:
        watch1 = 'https://movie.naver.com'
    return [poster1, movienm1, story_content1, watch1]
    
app = Flask(__name__)

@app.route('/')
def home(error=False):
    a={}
    soon_releases = df[df['prdtstatnm'] == '개봉예정'].sort_values(by='openedt', ascending=False).iloc[1:15, :].sort_values(by='openedt').reset_index(drop=True)
    for i in range(9):
        a["soon{0}".format(i)]= recommend_values(soon_releases, i)

    new_releases = df[df['prdtstatnm'] == '개봉'].sort_values(by='openedt', ascending=False).reset_index(drop=True)
    b={}
    for i in range(9):
        b["new{0}".format(i)]= recommend_values(new_releases, i)

    action = df[(df['repgenrenm'] == '액션') & (df['netizen_count'] > 300) & (df['netizen_socre'] > 8)].sort_values(by='openedt', ascending=False).reset_index(drop=True)
    c={}
    for i in range(9):
        c["action{0}".format(i)]= recommend_values(action, i)
            
    comedy = df[(df['repgenrenm'] == '코미디') & (df['netizen_count'] > 300) & (df['netizen_socre'] > 8)].sort_values(by='openedt', ascending=False).reset_index(drop=True)
    d={}
    for i in range(9):
        d["comedy{0}".format(i)]= recommend_values(comedy, i)
    return render_template('index.html', a=a, b=b, c=c, d=d, error=error)

@app.route('/recommendation', methods=['POST'])
def recommend_movie():
    try:
        movie_receive = request.form.get('movie_give')
        recommendation_list = get_recommendations(movie_receive).drop_duplicates('movieNm').reset_index(drop=True)
        d = {}
        for i in range(len(recommendation_list)):
            d["string{0}".format(i)]= recommend_values(recommendation_list, i)
        
        return render_template('recommendation.html', list0 = d['string0'], list1 = d['string1'], list2 = d['string2'], list3 = d['string3'], list4 = d['string4'], list5 = d['string5'],
                            list6 = d['string6'], list7 = d['string7'], list8 = d['string8'], list9 = d['string9'], list10 = d['string10'], list11 = d['string11'], list12 = d['string12'],
                            list13 = d['string13'], list14 = d['string14'], list15 = d['string15'], list16 = d['string16'], list17 = d['string17'])
    except:
        return home(error=True)
        

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)