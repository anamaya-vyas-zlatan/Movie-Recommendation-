#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as mp
import pandas as pd

# In[2]:


movies = pd.read_csv('tmdb_5000_movies.csv')
credits = pd.read_csv('tmdb_5000_credits.csv')

# In[3]:


movies.head(1)

# In[4]:


credits.head(1)

# In[5]:


movies = movies.merge(credits, on='title')
# merged credits and movies csv file on the basis on title


# In[6]:


movies.head(1)

# In[7]:


# We will create tags
# genres
# id
# keywords
# overview
# title
# cast
# crew
movies = movies[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew']]

# In[8]:


movies.head()

# In[11]:


movies.isnull().sum()

# In[10]:


# Remove the incomplete data-movies
movies.dropna(inplace=True)

# In[12]:


movies.duplicated().sum()

# In[13]:


import ast


# In[14]:


def convert(obj):
    L = []
    for i in ast.literal_eval(obj):
        L.append(i['name'])
    return L


# In[15]:


movies['genres'] = movies['genres'].apply(convert)

# In[16]:


movies['keywords'] = movies['keywords'].apply(convert)


# In[17]:


def convert3(obj):
    L = []
    count = 0
    for i in ast.literal_eval(obj):
        if count != 3:
            L.append(i['name'])
            count = count + 1
        else:
            break
    return L


# In[18]:


movies['cast'] = movies['cast'].apply(convert3)


# In[19]:


def fetch_director(obj):
    L = []
    count = 0
    for i in ast.literal_eval(obj):
        if i['job'] == 'Director':
            L.append(i['name'])
            break
    return L


# In[20]:


movies['crew'] = movies['crew'].apply(fetch_director)

# In[21]:


movies['overview'] = movies['overview'].apply(lambda x: x.split())

# In[22]:


movies['genres'] = movies['genres'].apply(lambda x: [i.replace(" ", "") for i in x])
movies['keywords'] = movies['keywords'].apply(lambda x: [i.replace(" ", "") for i in x])
movies['cast'] = movies['cast'].apply(lambda x: [i.replace(" ", "") for i in x])
movies['crew'] = movies['crew'].apply(lambda x: [i.replace(" ", "") for i in x])

# In[23]:


movies.head()

# In[24]:


movies['tags'] = movies['overview'] + movies['genres'] + movies['keywords'] + movies['cast'] + movies['crew']

# In[25]:


movies.head()

# In[40]:


new_df = movies[['movie_id', 'title', 'tags']]

# In[41]:


new_df

# In[42]:


new_df['tags'] = new_df['tags'].apply(lambda x: " ".join(x))

# In[43]:


import nltk

# In[44]:


from nltk.stem.porter import PorterStemmer

ps = PorterStemmer()


# In[45]:


def stem(text):
    y = []
    for i in text.split():
        y.append(ps.stem(i))
    return " ".join(y)


# In[46]:


new_df['tags'] = new_df['tags'].apply(stem)

# In[29]:


new_df['tags'] = new_df['tags'].apply(lambda x: x.lower())

# In[47]:


new_df.head()

# In[48]:


new_df['tags'][0]

# In[51]:


from sklearn.feature_extraction.text import CountVectorizer

cv = CountVectorizer(max_features=5000, stop_words='english')

# In[52]:


vectors = cv.fit_transform(new_df['tags']).toarray()

# In[53]:


vectors

# In[54]:


cv.get_feature_names()

# In[56]:


from sklearn.metrics.pairwise import cosine_similarity

# In[59]:


similarity = cosine_similarity(vectors)


# In[60]:


# In[61]:


def recommend(movie):
    movie_index = new_df[new_df['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:10]

    for i in movie_list:
        print(new_df.iloc[i[0]].title)


# In[62]:


recommend('Batman Begins')

import pickle

# pickle.dump(new_df.to_dict(), open('movies_dict.pkl','wb'))

pickle.dump(similarity,open('similarity.pkl','wb'))



