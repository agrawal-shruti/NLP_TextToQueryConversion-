# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 17:23:43 2019

@author: Shruti
"""
from QueryGeneratorUtils import data_lemmatizer, get_database_info
from textblob.classifiers import NaiveBayesClassifier
from sklearn.externals import joblib 

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

#Extracting the list of measures from the database
measures, measures_with_cubes, cubes_of_measures, dims, unsplit_dims, dims_with_cubes, cubes_of_dims = get_database_info()

#lemmatizing the data
lem_measures=[data_lemmatizer(sentence) for sentence in measures]
lem_dims=[data_lemmatizer(sentence) for sentence in dims]

#creating the input for the Classifier
meas_list=[(measure.lower(),'1') for measure in measures]
dim_list=[]
for dim in dims:
    dim_list.append((dim.lower(),'2'))
column_list = meas_list + dim_list # tagged input for Bayes Classifier

#Creating and saving the model
cl = NaiveBayesClassifier(column_list) # Classify as measure or dimension
joblib.dump(cl, 'naive_bayes.pkl') 

