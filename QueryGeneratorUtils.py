# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 17:39:13 2019

@author: Shruti
"""

# for data_lemmatizer and finder()
import nltk
word_tokenize=nltk.word_tokenize
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# for get_database_info()
import pymssql

# for finder()
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def data_lemmatizer(sentence):
    """
    Input: string (input sentence)
    Output: string (lemmatize sentence)
    Attempts lemmatization by both noun and verb formats
    """
    lem=nltk.WordNetLemmatizer()
    sentence=sentence.capitalize()
    tokens=nltk.word_tokenize(sentence)
    temp=[(lem.lemmatize(lem.lemmatize(token),'v')) for token in tokens]
    return ' '.join(temp)

def get_database_info():
    conn = pymssql.connect(
        host=r'192.168.1.17',
        user=r'NLPtest',
        password=r'Nlp@123',
        database='NLP_data'
    )
    c=conn.cursor()

    measures_with_cubes = []
    measures = []
    cubes_of_measures = []
    dims_with_cubes=[]
    cubes_of_dims = []
    dims =[]
    unsplit_dims=[]
    
    # Extracting the list of measures from the database
    c.execute("SELECT CUBE, MEASURE FROM Measures")
    tuples = c.fetchall()
    for t in tuples:
       measures_with_cubes.append(t)
       measures.append(t[1])
       cubes_of_measures.append(t[0])


    # Extracting the list of dimensions from the database
    c.execute("SELECT * FROM DIMENSIONS")
    tuples = c.fetchall()
    for t in tuples:
      dims_with_cubes.append(t)
      cubes_of_dims.append(t[0])
      unsplit_dims.append(t[1])
      dims.append(t[2]) 

    
    c.close()
    return measures, measures_with_cubes, cubes_of_measures, dims, unsplit_dims, dims_with_cubes, cubes_of_dims

def finder(sent,sentlist,threshold=0.6):
    """
    Input: string (input sent), list (list of checking sentences), float (upper similarity threshold)
    Output: int (index of most similar string in sentlist, -1 if nothing is above threshold)
    uses average result of multiple methods to find most similar string above the given threshold similarity
    """
    def get_jaccard_sim(str1, str2): 
        lem=nltk.WordNetLemmatizer()

        a = set(lem.lemmatize(word,'v') for word in str1.split()) 
        b = set(lem.lemmatize(word,'v') for word in str2.split())
        c = a.intersection(b)

        return float(len(c)) / (len(a) + len(b) - len(c))

    def get_vectors(*strs):
        text = [t for t in strs]
        vectorizer = TfidfVectorizer(text,analyzer='char')
        vectorizer.fit(text)
        return vectorizer.transform(text).toarray()

    def get_cosine_sim(*strs):
        vectors = [t for t in get_vectors(*strs)]
        return cosine_similarity(vectors)
    
    def similarity_checker(sent1,sent2):
        # tweak here to alter weights of jaccard and cosine similarity
        return nltk.edit_distance(sent1,sent2),(0.3*get_jaccard_sim(sent1,sent2)+0.7*get_cosine_sim(sent1,sent2)[0][1])
    
    sent1=data_lemmatizer(sent)
    maximum=[0.0,-1]
    for i,sent2 in enumerate(sentlist):    
        simindex=similarity_checker(sent1,sent2)
        if simindex[0]<3:
            maximum[0]=1
            maximum[1]=i
            break
        if ((simindex[1]>maximum[0]) and (simindex[0]<10)): # upper threshold of edit distance
            maximum[0]=simindex[1]
            maximum[1]=i
        #print(maximum,sent2)
    if maximum[0]>threshold:
        return maximum[1]
    else:
        return -1

#grammar 3 is used to obtain the possible noun phrases of interest. This is the string that needs to be modified for more possible edge cases
def get_parser():
    grammar3 = r"""
      NP: {(?:<JJ.*?><NN.*?>?|<JJ.*?>?<NN.*?><IN>?)<NP|NN|JJ|JJR|JJS|RB>*<CD>?<NN|NNS>} # 1-2 adj, 1-2 nouns,0-1 inj, 0+ of adj/noun, end in sing or plu noun
          #{<NN.*><IN>?<NP|NN|JJ|JJR|JJS|CD>*<NN|NNS>} 
          {<JJ|NN>+<CD>??<NN.*?>?} # without injunction
          {<CD|NN.*?|VBG|VBN>} # single word tags such as filters
    """ # fails on tabulate, sometimes on wise and on very long phrases which include injunctions
    grammar4 = r"""
      NP: {(?:<JJ.*?><NN.*?>?|<JJ.*?>?<NN.*?>{1,2}<IN>?)<NP|NN|JJ|JJR|JJS|RB>*<CD>??<NN|NNS>} 
          {<JJ|NN>+<CD>??<NN.*?>?} 
          {<CD|NN.*?|VBG>} # single word tags such as filters
    """ # fails, do not use
    cp = nltk.RegexpParser(grammar3)
    return cp

def create_connection():
    conn = pymssql.connect(
        host=r'192.168.1.17',
        user=r'NLPtest',
        password=r'Nlp@123',
        database='NLP_data'
    )
    c=conn.cursor()
    return c

def close_connection(c):
    c.close()
    