# VQA Browser


VQA Browser is web browser based tool for evaluating and visualizing your algorithm on [VQA dataset](http://www.visualqa.org/)
Once you build a [VQA result file](http://www.visualqa.org/evaluation.html) of your model, getting quantitative evaluation and browsing the model's prediction resutls are much easier with VQA Browser. 


## Functions


* Qualitative Evaluation
 * Browsing qualitative results
 * Visualizing additional results (e.g. attention map)
 * Searching questions
* Quantitative Evaluation & Comparison
 * Computing VQA score on validation set
 * Score comparison of multiple models
 * Plotting comparison results
 * Merging two model's results (picking the best answer for each question)


## Setting


Clone our repository.
```
git clone https://github.com/HyeonwooNoh/VQABrowser.git
```
Run the following script.
```
./setup.sh
```
This script will download [MSCOCO images](http://mscoco.org/dataset/#download) and create simulink.
If you have MSCOCO images in your local machine already, you can simply create a simulink.


## Running
Launch the server
```
python browser.py --host [host] --port [port]
```
Open ```http://[host]:[port]``` with your web browser to interface the VQA Browser.


## Screenshot
![Image of overview](./assets/overview.png)
