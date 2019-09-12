---Install the following packages. THe commands for installing the same using anaconda prompt are below:

   conda install -c anaconda pymssql
   conda install -c anaconda scikit-learn
   conda install -c anaconda joblib
   conda install -c anaconda flask
   conda install -c conda-forge nltk_data

---For updating the Classifier, more data should be added into the MEASURES and DIMENSIONS tables in the NLP_data database. 
   Following this, open the model_creation.py file and run it. New model will be saved and utilized automatically.

---Important files
   -main.py - contains the application code
   -source.py - contains all necessary functions to be called by main.py
   -QueryGeneratorUtils.py - contains necessary utility functions often called from source.py
   -model_creation.py - is used to create the ML model
   -naive_bayes.pkl - this file contains the trained ML model which is created automatically in model_creation.py
   -templates/home.html - the basic html template created to test the code

---Sample test cases that work:

   1. "what is the actual spend by commodity area in mechanical" --> will list out the measures, dimensions
	and filters without additional input since a dimension is specified in the query
   2. "what is the actual spend in mechanical" --> will ask the dimension for which this filter should be
	applied since it appears in multiple dimensions
   3. "what is the actual ss by commodity area" --> will result in no output since the measure is incorrect
   4. "What is the actual spend and budget spend by commodity area and manufacturer" - multiple dimensions will be identified correctly

---Some issues:

   - It looks like when the data was fetched from Merlin database and fed into NLP_data database some additional characters could have been added. This would result in some additional characters in the "DimensionFilterHeirarchy" for Filter.
   - Some dimensions like DimPart could be missing data in the NLP_data database since the number of values were more than we could accomodate at that time.
   - The naming convention and case of some measures and dimensions is inconsistent. Data needs to be converted to a common convention and should be stored in Camel Case.
   - Data in the Merlin database (and hence in the NLP_data databse) is redundant in many places. Such as a DimPlant dimension has two sub-categories "Plant Cod" and "Plant Code" with the same values.
