# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 17:56:52 2019

@author: Shruti Agrawal, Raghav Mallampalli
"""

from QueryGeneratorUtils import data_lemmatizer, get_database_info, finder, get_parser, create_connection, close_connection
from sklearn.externals import joblib
import nltk
 
#The extract() function return the key noun phrases from the question as well as the list of all measures, dimesnsions and cubes from the database.
#The extract() function also classifies the noun phrases as either measure, dimension or cube.
#List of returned dimension may also include filter keywords and cube names.
def extract(test_question):

    word_tokenize=nltk.word_tokenize
    
    #using POS tagging and regex patterns to extract custom noun phrases
    test_question=nltk.pos_tag(word_tokenize(test_question.lower()))
    cp = get_parser()
    noun_phrases_list = [' '.join(leaf[0] for leaf in tree.leaves()) 
                          for tree in cp.parse(test_question).subtrees() 
                          if tree.label()=='NP']
    print(cp.parse(test_question))
    
    #load the model and classify the extracted noun phrases
    cl = joblib.load('naive_bayes.pkl') 
    noun_phrases=list(zip(noun_phrases_list,[cl.classify(noun_phrase) for noun_phrase in noun_phrases_list]))
    print(noun_phrases)
    
    #extracting the list of measures from the database
    measures, measures_with_cubes, cubes_of_measures, dims, unsplit_dims, dims_with_cubes, cubes_of_dims = get_database_info()
    
    return measures, measures_with_cubes, cubes_of_measures, dims, unsplit_dims, dims_with_cubes, cubes_of_dims, noun_phrases

#identify() function identifies the cube name if it is present, and creates a list of dims and mesaures in the question.
def identify(noun_phrases, cubes_of_dims, cubes_of_measures):
    present_measure=[] # measure name extracted from query
    present_dim=[] # dimension name extracted from query
    cube="" # stores name of cube
    cubes = set(cubes_of_dims+cubes_of_measures) # list of all cubes

    
    #separate into measure, cube and dimension/filter
    for phrase,tag in noun_phrases:
        if tag == '1':
            present_measure.append(phrase)
        elif tag =='2':
            for word in cubes: # replace with finder() with high threshold?
                if phrase.lower() in word.lower():
                    cube=word
                    break
            else:
                present_dim.append(phrase)
    return present_measure, present_dim, cube

#If the cube name was specified in the question and is known the find_measure_given_cube() function is called.
def find_measure_given_cube(measures, present_measure, cube, cubes_of_measures):
    measure_index=[] # stores index of measures (based on full list) found in query
    lem_measures=[data_lemmatizer(sentence) for sentence in measures] #lemmatizing the measures
    c = create_connection()
    
    for measure in present_measure:
        first_index_measure=1
        last_index_measure=-1
        threshold=0.7
        allowed_measures=lem_measures[first_index_measure:last_index_measure]
    
        temp=finder(measure,allowed_measures,threshold)
        if temp!=-1: # measure identified
            measure_index.append(temp+first_index_measure)
        else: # no measure identified
            measure_index.append(-1)
        close_connection(c)
    
    return measure_index

#If the cube name was not specified in the question and is not known the find_measure_and_cube function is called.
def find_measure_and_cube(measures, present_measure, cube, cubes_of_measures):
    measure_index=[] # stores index of measures (based on full list) found in query
    possible_cubes = [] # stores the list of possible cubes that the measure might belong to
    lem_measures=[data_lemmatizer(sentence) for sentence in measures] #lemmatizing the measures
    c = create_connection()
    for measure in present_measure:
        first_index_measure=1
        last_index_measure=-1
        threshold=0.7
        allowed_measures=lem_measures[first_index_measure:last_index_measure]
    
        temp=finder(measure,allowed_measures,threshold)
        if temp!=-1: # measure has been identified
            measure_index.append(temp+first_index_measure)
            # fetch all possible cubes for identified measure
            c.execute("SELECT CUBE FROM Measures WHERE MEASURE LIKE '{measure}'".format(measure=measure)) # find cube using database
            possible_cubes=c.fetchall()
            possible_cubes=[elt for (elt,) in possible_cubes]
            #print(len(possible_cubes))
            if len(possible_cubes)>1: #multiple cubes identified
                print("possible cubes" + possible_cubes[0])
            elif len(possible_cubes) == 1: #single cube identified
                cube=possible_cubes[0]
            else: #no cube identified, also idicates that  measure is incorrect
                measure_index.append(-1)
                possible_cubes.append("None")
        else: # no measure identified
            measure_index.append(-1)
            possible_cubes.append("None")
            #print("None")
    close_connection(c)
    return measure_index, possible_cubes, cube
# maybe instead of initialising all dimensions using SQL query before, initialise only those from the relevant cube

#The find_dim_given_measure() function is used to obtain the dimension and a filter heirarchy that stores all possible paths to the filter
#The final_filter_heir variable stores list of each dimension, sub-dimension and filter heirarchy
def find_dim_given_measure(measure_index, dims, present_dim, unsplit_dims, cube, cubes_of_dims): 
    lem_dims=[data_lemmatizer(sentence) for sentence in dims]
    dim_index=[] # stores index of dimensions (based on full list) found in query
    filter_strings=[] #stores list of filters identified
    print(cube)
    for dim in present_dim:
        first_index_dim=cubes_of_dims.index(cube)
        last_index_dim=max(idx for idx,val in enumerate(cubes_of_dims) if val == cube)+1
        threshold=0.4
        
        allowed_dims=lem_dims[first_index_dim:last_index_dim]
        temp=finder(dim,allowed_dims,threshold)
        if temp!=-1: #string is identified as dimension
            dim_index.append(temp+first_index_dim)
        else: #string is not identified as dimension
            filter_strings.append(dim)
    print(filter_strings)
    final_filter_heir=[]

    if filter_strings != []:
        c = create_connection()
        dim_filters=[]
        filters_to_remove=[]
        #obtain all dimension - filter heirarchies for the recognised filter string
        for string in filter_strings:
            root_query=r"WHERE MEMBERS LIKE '%"+string+"%'" #will fetch all entries containing the keyword equivalent to "string"
            #b=r"WHERE DIMENSION LIKE '"+dimension+"'"
            c.execute("SELECT * FROM [{}] {}".format(cube, root_query))
            dim_filters.extend(c.fetchall())
        print(dim_filters)
        close_connection(c)
        for di in dim_index:
            d=unsplit_dims[di]
            flag=1
            for (df,t,f) in dim_filters:
                if d==df:
                    if flag!=0:
                        final_filter_heir.append((df,t,f))
                        flag=0
                        filters_to_remove.append(f)
        for (df,t,f) in dim_filters:
            if f not in filters_to_remove:
                final_filter_heir.append((df,t,f))
                
    return dim_index, final_filter_heir







