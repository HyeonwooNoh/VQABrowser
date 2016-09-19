## Basic Usage

You can see the following interface when you open the VQA Broswer.
![default image](../assets/default.png)

### Loading Files
The first thing you need to do is loading result, question and annotation files.
* **result file**: result file is a json file containing model's prediction results for questions in VQA dataset. 
Detailed format is descrived in [http://www.visualqa.org/evaluation.html]
  * You should load result file for [Visualization, Evaluation]
* **question file**: VQA quesiton file which can be downloaded from [http://www.visualqa.org/download.html].
Question file is used to construct list of questions for visualization.
  * You should load question file for [Visualization, Evaluation, Browse Question, Search]
* **annotation file**: VQA annotation file which can be downloaded from [http://www.visualqa.org/download.html].
Annotation file is used for the quantitative evaluation and for comparison with the correct answer.
  * You should load annotation file for [Evaluation, Search]

### Choose Tab
After loading files, you can click one of the visible tabs to use the required function.

![visible tabs](../assets/visible_tabs.png)

* **[Analysis](/doc/analysis.md)**
  * Comparision of different models's scores
  * Plotting comparison results
* **[Visualization](/doc/visualization.md)**
  * Visualization of image, question, answers and the model's prediction results
  * Additional results can be displayed too.
* **[Evaluation](/doc/evaluation.md)**
  * Computation of VQA evaluation score
  * VQA score per each question
  * Downloading evaluation results of the model (which can be used for the model comparision)
  * Downloading pre-processed results of the model (which can be used for prediction results merging)
* **[Browse Question](/doc/browse_question.md)**
  * Lists of questions and there occurrences
  * Link to visualization of specific question
* **[Search Questions](/doc/search_questions.md)**
  * Search question in the dataset
  * Question, answer, occurrence and model's prediction score for searched question
  * Link to visualization of searched question
* **[Oracle Merge](/doc/oracle_merge.md)**:
  * Merging predictions of two models
  * Downloading results file for merged model prediction
