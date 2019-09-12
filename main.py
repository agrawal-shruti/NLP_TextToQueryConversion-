# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 16:15:47 2019

@author: Shruti Agrawal, Raghav Mallampalli
"""


from flask import Flask,render_template, request, jsonify
from source import extract, identify, find_measure_given_cube, find_measure_and_cube, find_dim_given_measure

#Declaration of global variables to be used in the program
measures = []
measure_index = []
dims = []
present_dim = []
unsplit_dims = []
cube = ''
cubes_of_dims = []
cube_identified = False
dim_detected = ' '
final_filter_heir = []
DimInputFlag = True

#Creation of flask App
app = Flask(__name__)

#Lands to the home page
@app.route("/")
def main():
  return render_template("home.html")

#This is the first method called after user enters their input string.
#This method extracts the keywords from the string, identifies the category of the keyword, saves the measure and its cube into the global variables.
@app.route('/process_measure',methods= ['POST'])
def process_measure():
  #The input string is saves as question
  question = request.form['question']
  #Declaration to use the global value of the variables declared before
  global measures, measure_index, dims, present_dim, unsplit_dims, cube, cubes_of_dims, cube_identified
  if question:
      #The extract() function return the key noun phrases from the question as well as the list of all measures, dimesnsions and cubes from the database.
      #The extract() function also classifies the noun phrases as either measure, dimension or cube.
      #List of returned dimension may also include filter keywords and cube names.
      measures, measures_with_cubes, cubes_of_measures, dims, unsplit_dims, dims_with_cubes, cubes_of_dims, noun_phrases = extract(question)
      #identify() function identifies the cube name if it is present, and creates a list of dims and mesaures in the question.
      present_measure, present_dim, cube = identify(noun_phrases, cubes_of_dims, cubes_of_measures)
      #There can be two cases after identify(). 
      #CASE I: If the cube name was specified in the question and is known the find_measure_given_cube() function is called.
      if cube!='':
          measure_index = find_measure_given_cube(measures, present_measure, cube, cubes_of_measures)
          return jsonify({'CubeName': cube, 'Input':' ','Error' : ' '})
      #CASE II: If the cube name was not specified in the question and is not known the find_measure_and_cube function is called.
      #This section  checks if the measure is identified belongs to multiple cubes or a single cube.
      #If the measure belongs to multiple cubes, the user will be provided with this list and the user has to provide this additional input.
      #If the measure name is incorrect or missing, ERROR is indicated
      else: 
          measure_index, possible_cubes, cube = find_measure_and_cube(measures, present_measure, cube, cubes_of_measures)
          if -1 not in measure_index:    
              if len(possible_cubes)>1 :
                  cubeList = ' ,'.join(possible_cubes)
                  return jsonify({'CubeName': ' ', 'Input': cubeList,'Error' : ' '})
              elif len(possible_cubes)==1:
                  cube_identified = True
                  return jsonify({'CubeName': cube, 'Input':' ','Error' : ' '})
              else: return jsonify({'CubeName': ' ', 'Input':' ','Error' : 'One or more measure missing/incorrect'})

          else: return jsonify({'CubeName': ' ', 'Input':' ','Error' : 'One or more measure missing/incorrect'})


#This method is used to identify the segregate the dimensions and filters
#If the dimension name and filter name is specified, indicate Success
#If there is no dimension and filter specified, indicate Success
#If there is a filter in the question without mentioning the dimension and the filter exists in multiple dimensions, the user is asked to choose from a list of dimensions.
@app.route('/process_dimension',methods = ['POST'])
def process_dimension():
    global cube_identified, cube, final_filter_heir, dim_detected, DimInputFlag, measure_index, dims, present_dim, unsplit_dims, cubes_of_dims
    #cube_identified flag is used to check if the user was asked for the input and this cube is hence used.
    if cube_identified == False:
        cube = request.form['CubeName']    
    
    #The find_dim_given_measure() function is used to obtain the dimension and a filter heirarchy that stores all possible paths to the filter
    #The final_filter_heir variable stores list of each dimension, sub-dimension and filter heirarchy
    dim_index, final_filter_heir = find_dim_given_measure(measure_index, dims, present_dim, unsplit_dims, cube, cubes_of_dims)
    
    #dim_detected stores the final list of dimensions specified by the user in the question
    if dim_index != []:
        dim_detected = ', '.join(unsplit_dims[index] for index in dim_index)
    else:
        dim_detected = " "
    
    #If the filter exists in multiple dimensions, we extract the names of the dimensions from which the user needs to choose.
    if(len(final_filter_heir)>1):
        i=0
        getdims = []
        getindex = []
        final_dims = []
        for d in final_filter_heir:
            getdims.append(d[0])
        getdims = set(getdims)
        if (len(getdims)==1):
            DimInputFlag = False
            del final_filter_heir[1:]
            return jsonify({'Success' : 'Done', 'Input': ' '})
        
        for d in getdims:
            try:
                i = unsplit_dims.index(d)
                getindex.append(i)
                print(i)
            except ValueError:
                continue
    
        for j in getindex:
            final_dims.append(' '.join(dims[j].split()[1:]))
        
        DimInputFlag = True
        return jsonify({'Success' : ' ', 'Input': ' ,'.join(final_dims)})
            

            
    else:
        
        DimInputFlag = False
        
        return jsonify({'Success' : 'Done', 'Input': ' '})

#The final function combines and return the list of measures, cubes, dimension, filters and its heirarchy
@app.route('/resolve_filter',methods = ['POST'])
def resolve_filter():
    selected_dimension = ' '
    global measures, measure_index, dims, unsplit_dims, final_filter_heir, cube, dim_detected, DimInputFlag
    filter_heir_list = []
    data = {}
    data['CubeName'] = cube
    data['Measures'] = ', '.join(measures[index] for index in measure_index)
    data['Dimensions'] = dim_detected
    
    #Check if the user was made to select the dimension of the filter and use that as the final filter heirarchy to be processed.
    #Else, if the dimension is mentioned in the question, it is set as the final filter heirarchy
    if DimInputFlag == False:
        if(len(final_filter_heir)==1):
            data['Filter']=final_filter_heir[0][2]
            filter_heir_list = final_filter_heir[0]
            data['DimensionFilterHeirarchy'] = ','.join(filter_heir_list)
            return jsonify(data)
        else: 
            data["Filter"] = " "
            data['DimensionFilterHeirarchy'] = " "
            return jsonify(data)
    else:
        
        selected_dimension = request.form['DimName']
 
        for d in dims:
            edited_dim = ' '.join(d.split()[1:])
            if edited_dim == selected_dimension:
                dimension_index = dims.index(d)
                selected_dimension = unsplit_dims[dimension_index]
                break
                
        for d in final_filter_heir:
            if selected_dimension == d[0]:
                data['Filter']=final_filter_heir[0][2]
                data['DimensionFilterHeirarchy'] = ','.join(d)
                break
      
        return jsonify(data)

if __name__ == "__main__":
  app.secret_key = 'super secret key'
  app.run()
  app.debug=True