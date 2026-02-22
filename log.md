Simple document to log my thoughts during development without structuring too much

# 2026/02/20 16:34

Had my first read of the Candidate project. The gist of it is to develop a ML solution based on a provided model simulating a real estate use case. Just got a new github repo for the project (using a new account - I used my main git account mostly during college and the quality of that code is really a shame).

Due to the confidentiality and proprietary data concern in the emails, I set up a local instance of deepseek-r1 through ollama and Continue extension to use during the development. All uses will be documented here. Some of the uses expected are grammar checks for documentation, ideation for tools where my experience is low, code standardization, and test generation. 

Some points of attention from the original project description:

## Presentation

The results should be presented  as **power point presentation**, structured in:

* 15 mins: presents the solution to the client audience. **Not technical**, see it as presenting to clients.
* 15 mins: explains technical aspects of the solution, which is aimed at engineers and/or scientists.
* 30 mins: questions 

## Scenario

A basic model to estimate value of properties was developed by the staff of Sound Realty. Our job is to create a REST endpoint that serves up model predictions for new data, and to provide guidance on how they could improve the model.

A Python script has been provided (create_model.py) which **trains the basic model**. The data used to train
the model is in the data directory, which includes:

* data/kc_house_data.csv – Data for training the model. Each row corresponds to a sold home. price is the
target column, the rest can be used as features if appropriate.
* data/zipcode_demographics.csv – Additional demographic data from the U.S. Census which are used as
features. This data should be joined to the primary home sales using the zipcode column.
* data/future_unseen_examples.csv – This file contains examples of homes to be sold in the future. It includes
all attributes from the original home sales file, but not the price , date , or id . It also does not include the
demographic data.

The model artifacts will be saved in a directory called model/ with the following contents:

* model/model.pkl – The model serialized in Python Pickle format.
* model/model_features.json – The features required for the model to make a prediction, in the order they were
passed during training.

Anaconda environment YAML has been provided: conda_environment.yml

## Deliverables
*  Deploy the model as an endpoint on a RESTful service which receives JSON POST data
   * Inputs to this endpoint should be the columns in data/future_unseen_examples.csv
   * The endpoint should return a JSON object with a prediction, as well as any metadata necessary.
   * The inputs to the endpoint should not include any of the demographic data.
   * Consider how updated versions of the model will be deployed. If possible, develop a solution that allows new
versions of the model to be deployed without stopping the service.
   * Bonus: the basic model only uses a subset of the columns provided in the house sales data. Create an
additional API endpoint where only the required features have to be provided in order to get a prediction.
* Create a test script which submits examples to the endpoint to demonstrate its behavior. The examples should be
taken from data/future_unseen_examples.csv.
* Evaluate the performance of the model. You should start with the code in create_model.py and try to figure out
how well the model will generalize to new data. Has the model appropriately fit the dataset?
* Improve the model by applying some basic machine-learning principles. We're not interested in getting the
absolute best predictive performance for the model, don't devote too much time to this step. This is not a Kaggle
competition. Rather we're interested in your understanding of data science concepts and your ability explain the
decisions you made.

## Recommendations

* use Docker to containerize and deploy the model.
* do some web searching to figure out what other components are needed to deploy a scalable REST API for a Python application.

# 2026/02/20 17:30

Watching the provided instruction video:

## Annotations: 
* Expectations:
  * simulate real work
  * not a perfect solution
  * how do you communicate
* Make suggestions to improve the model
* presentation
  * business audience
    * real estate professionals
    * explain the value
    * how it will fit in the processes
    * focus on the value and outcomes
  * technical audience
    * have fun
    * dive into details
    * explain API
    * how docker is used
    * How to scale
    * how to update
    * measure performance
    * trade-offs
    * architecture choices
    * real world considerations
    * deployment 
    * security
    * MLOps practices (model registry, CI/CD, feature stores)
  * key takeaways
    * simple first
    * balance your presentation
    * explain the why
    * think real world
    * show mindset 
    * cultural alignment
  * Ask
    * what motivates and interests them

# 2026/02/21 09:13 

Installed the conda environment and executed the `create_model.py` script. 

Checking the .csv files, the data seems ok (clean, no strange data or formatting). I ran a simple exploration to understand it. 


# 2026/02/21 11:49

Just added my data exploration considerations to the exploration folder.

Was looking at the code and saw that there are some strange variable instantiations and uses. Will start to branch out. 


# 2026/02/21 12:38

Just read the create_model.py with care. My considerations:
* there were some unused variables and bad instantiations. I just cleaned that.
* pyright was complaining about iterables and I ignored. Pretty common on pandas.
* The Robust Scaler is a bazooka to kill a fly here, but it managed my worst fear of underfitting with KNN.
* The use of default settings on KNN is amateurish and would be the first thing to try out changing.
* The training step already makes separations for test. But no testing. I will change that later.

# 2026/02/21 16:23
Added a model evaluation step to the current model. Decided to keep it with training as to use same train/test split for reference.

Most of the code was machine generated, for speed reasons. Added a weighted RMSE metric that punishes underpricing (execs love this one trick).

Don't have the area specific knowledge (not much experience in pricing), but 100k of mean error looks bad.

* RMSE (Root Mean Squared Error) - The most common metric for price prediction. Penalizes larger errors more heavily, which matters for price predictions.
* MAE (Mean Absolute Error) - Easier to interpret (average dollar amount the model is off by).
* R2 (Coefficient of Determination) - Shows what percentage of price variance the model explains (0-1 scale, higher is better).
* MAPE (Mean Absolute Percentage Error) - Useful for understanding error as a percentage of actual prices.

Added a release tag so I can return to this point to get data for the presentation.

Made some tests with grid search and ridge regression, but the current model seems a good enough kitchen sink approach. Meddling with hyperparameters seems to worsen too much in the overfitting side. 

Best next step for increase model performance are feature engineering or using a more powerful approach like XGB. Prune the data to not use everything at once can help.

# 2026/02/21 20:18

After a quick research decided to use the fastapi library for the REST API implementation. It was my first time using it, so I gave the directions to copilot, 
and then spent an hour understanding what the code does and how. There are some changes I want to try later.

* reduce latency in the load model. 
* add a more robust approach to the demographics data load
* make a second pass of the code for cleaning
* improve the ability to update the model on the fly

for next step: 
* including proper docker and containerization
* try to improve the model so I have different versions to change 
* Review the tests

Generated a full pytest battery and fixed the issues that showed with testing. Need to comb through the code later.

Been putting half an hour at a time in each log and got a little tired xD.


# 2026/02/22 09:14

Updated the use of the demographics dataframe to a dictionary for optimization. Removed redundant code that validated zip_codes, and reworked the tests to correspond to changes