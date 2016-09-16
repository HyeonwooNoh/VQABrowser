from flask import Flask, render_template, request
from flask import redirect, url_for, send_file
from flask import jsonify
try:
    import simplejson as json
except ImportError:
    import json

from vqaTools.vqa import VQA
from vqaTools.vqaEval import VQAEval

from itertools import islice

import StringIO
import copy

import operator
import os
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def take(n, iterable):
    "Return first n items of the iterable as a list"
    return dict(islice(iterable, n))

dataList = {}
# result file 
dataList['res'] = {}
dataList['res']['loaded'] = False
dataList['res']['fn'] = 'none'
dataList['res']['data'] = {}
# question file
dataList['que'] = {}
dataList['que']['loaded'] = False
dataList['que']['fn'] = 'none'
dataList['que']['data'] = {}
# annotation file
dataList['ann'] = {}
dataList['ann']['loaded'] = False
dataList['ann']['fn'] = 'none'
dataList['ann']['data'] = {}
# visualization is prepared
dataList['visable'] = False
dataList['evaluable'] = False
dataList['evaluated'] = False
dataList['qamatch'] = False
# score analysis list
dataList['scores'] = {}
dataList['scores']['fn'] = []
dataList['scores']['lists'] = []
dataList['scores']['loadstate'] = ''
dataList['scores']['idx'] = 0
dataList['scores']['batch'] = 20
# evalres list
dataList['evalres'] = {}
dataList['evalres']['data'] = {}
dataList['evalres']['fn'] = []
dataList['evalres']['loadstate'] = ''
# additional image dir
dataList['adddir'] = ''

i = 1
annoFileName = ''
annFile = {}

app = Flask(__name__)

@app.route('/test/')
def test():
    global i
    app.logger.debug('test')
    i = i+2
    new_dict = {1:i, 2:'bec', 3:'dfe'}
    return jsonify(new_dict)

@app.route('/postresult/')
def postresult():
    global annFile
    return jsonify(annFile)

@app.route('/postanno', methods=['GET','POST'])
def postanno():
    global annFile
    app.logger.debug('postanno')
    f = request.files['fileToUpload']
    temp = json.loads(f.read())
    app.logger.debug('postann2')
    #return f.filename
    return jsonify(temp)

@app.route('/unloadres', methods=['GET'])
def unloadres():
    dataList['res']['fn'] = 'none'
    dataList['res']['data'] = {}
    dataList['res']['loaded'] = False
    dataList['visable'] = False
    dataList['evaluable'] = False

    return redirect(url_for('index'))

@app.route('/loadres', methods=['POST'])
def loadres():
    global dataList
    app.logger.debug('loadres')
    f = request.files['loadres']
    try:
        res_json = json.loads(f.read())
    except:
        dataList['res']['fn'] = 'improper json file..'
        dataList['res']['loaded'] = False
        return redirect(url_for('index'))
    if not isProperResJson(res_json):
        dataList['res']['fn'] = 'improper json file..'
        dataList['res']['loaded'] = False
        return redirect(url_for('index'))
    dataList['res']['fn'] = f.filename
    dataList['res']['data'] = res_json
    dataList['res']['loaded'] = True
    dataList['visable'] = checkVisPrepared()
    dataList['evaluable'] = dataList['visable'] and dataList['qamatch']
    if dataList['evaluable']:
        prepareEval()
    if dataList['visable']:
        constructVisRes()
        constructQuestions()
    dataList['adddir'] = ''
    return redirect(url_for('index'))

def isProperResJson(fjson):
    if type(fjson) != list:
        return False
    if len(fjson) <= 0:
        return False
    if type(fjson[0]) != dict:
        return False
    if not (set(fjson[0].keys()) >= set(['question_id', 'answer'])):
        return False
    return True

@app.route('/unloadque', methods=['GET'])
def unloadque():
    dataList['que']['fn'] = 'none'
    dataList['que']['data'] = {}
    dataList['que']['loaded'] = False
    dataList['visable'] = False
    dataList['qamatch'] = False
    dataList['evaluable'] = False
    return redirect(url_for('index'))

@app.route('/loadque', methods=['POST'])
def loadque():
    global dataList
    app.logger.debug('loadque')
    f = request.files['loadque']
    try:
        que_json = json.loads(f.read()) 
    except:
        dataList['que']['fn'] = 'improper json file..'
        dataList['que']['loaded'] = False
        return redirect(url_for('index'))
    if not isProperQueJson(que_json):
        dataList['que']['fn'] = 'improper json file..'
        dataList['que']['loaded'] = False
        return redirect(url_for('index'))
    dataList['que']['fn'] = f.filename
    dataList['que']['data'] = que_json
    dataList['que']['loaded'] = True
    dataList['visable'] = checkVisPrepared()
    qaMatch = checkQAPair()
    dataList['qamatch'] = qaMatch
    dataList['evaluable'] = dataList['visable'] and dataList['qamatch']
    if dataList['qamatch']:
        prepareVQA()
    if dataList['evaluable']:
        prepareEval()
    if dataList['visable']:
        constructVisRes()
    if dataList['visable'] or dataList['qamatch']:
        constructQuestions()
    return redirect(url_for('index'))

def isProperQueJson(fjson):
    if type(fjson) != dict:
        return False
    app.logger.debug(fjson.keys())
    if not (set(fjson.keys()) >= set(['task_type', 'data_subtype', 'questions'])):
        return False
    if type(fjson['questions']) != list:
        return False
    if len(fjson['questions']) <= 0:
        return False
    if type(fjson['questions'][0]) != dict:
        return False
    if not (set(fjson['questions'][0].keys()) >= set(['image_id', 'question', 'question_id'])):
        return False
    return True

@app.route('/unloadann', methods=['GET'])
def unloadann():
    dataList['ann']['fn'] = 'none'
    dataList['ann']['data'] = {}
    dataList['ann']['loaded'] = False
    dataList['qamatch'] = False
    dataList['evaluable'] = False
    return redirect(url_for('index'))
       
@app.route('/loadann', methods=['POST'])
def loadann():
    global dataList
    app.logger.debug('loadann')
    f = request.files['loadann']
    try:
        ann_json = json.loads(f.read())
    except:
        dataList['ann']['fn'] = 'improper json file..'
        dataList['ann']['loaded'] = False
        return redirect(url_for('index'))
    if not isProperAnnJson(ann_json):
        dataList['ann']['fn'] = 'improper json file..'
        dataList['ann']['loaded'] = False
        return redirect(url_for('index'))
    dataList['ann']['fn'] = f.filename
    dataList['ann']['data'] = ann_json
    dataList['ann']['loaded'] = True
    qaMatch = checkQAPair()
    dataList['qamatch'] = qaMatch
    dataList['evaluable'] = dataList['visable'] and dataList['qamatch']
    if dataList['qamatch']:
        prepareVQA()
    if dataList['evaluable']:
        prepareEval()
    if dataList['visable']:
        constructVisRes()
    if dataList['visable'] or dataList['qamatch']:
        constructQuestions()
    return redirect(url_for('index'))

def prepareVQA():
    global dataList
    dataList['vqa']=VQA(dataList['ann']['data'], dataList['que']['data'])

def prepareEval():
    global dataList
    dataList['vqaRes']=dataList['vqa'].loadRes(copy.deepcopy(dataList['res']['data']), dataList['que']['data'])
    # n is precision of accuracy (number of places after decimal)
    dataList['vqaEval'] = VQAEval(dataList['vqa'], dataList['vqaRes'], n=2)
    dataList['evaluated'] = False

def isProperAnnJson(fjson):
    if type(fjson) != dict:
        return False
    if not (set(fjson.keys()) >= set(['data_subtype', 'annotations'])):
        return False
    if type(fjson['annotations']) != list:
        return False
    if len(fjson['annotations']) <= 0:
        return False
    if type(fjson['annotations'][0]) != dict:
        return False
    if not (set(fjson['annotations'][0].keys()) >= \
       set(['question_type', 'multiple_choice_answer', 'answers', \
            'image_id', 'answer_type', 'question_id'])):
        return False
    return True

@app.route('/downloadevalres/')
def downloadevalres():
    global dataList
    accuracyfn = dataList['evalresfn']
    return send_file(accuracyfn, as_attachment=True)

@app.route('/downloadscore/')
def downloadscore():
    global dataList
    accuracyfn = dataList['accuracyfn']
    return send_file(accuracyfn, as_attachment=True)

@app.route('/downloadoracle/')
def downloadoracle():
    global dataList
    accuracyfn = dataList['oraclefn']
    return send_file(accuracyfn, as_attachment=True)

def packAccuracy(accuracy, quenums):
    packed = {'accuracy':accuracy, 'quenums':quenums}
    return packed

def parseAccuracy(acc):
    buf = StringIO.StringIO()
    buf.write('overall: %.2f\n' % acc['overall'])
    buf.write('perAnswerType\n')
    for k, v in sorted(acc['perAnswerType'].iteritems()):
        buf.write('\t%s: %.2f\n' % (k, v))
    buf.write('perQuestionType\n')
    for k, v in sorted(acc['perQuestionType'].iteritems()):
        buf.write('\t%s: %.2f\n' % (k, v))
    return buf.getvalue()

@app.route('/evalprogress')
def evalprogress():
    evalstate = {}
    evalstate['processing'] = dataList['vqaEval'].evaluating
    evalstate['text'] = dataList['vqaEval'].progress_text
    return jsonify(evalstate)

@app.route('/setadditional', methods=['POST'])
def setadditional():
    global dataList
    app.logger.debug('setadditional: before form')
    adddir = request.data
    app.logger.debug('setadditional: %s before' % (adddir))
    adddir = os.path.abspath(adddir)
    if os.path.isdir(adddir):
       if os.path.islink('static/addimgs'):
          app.logger.debug('setadditional remove simulink')
          os.remove('static/addimgs')
       dataList['adddir'] = adddir
       os.system('ln -s %s %s' % (adddir, 'static/addimgs'))
       app.logger.debug('setadditional: %s good' % (adddir))
       send_data = {}
       send_data['adddir'] = dataList['adddir']
       return jsonify(send_data)
    app.logger.debug('setadditional: %s bad' % (adddir))
    send_data = {}
    send_data['adddir'] = dataList['adddir']
    return jsonify(send_data)

def constructOracle():
    global dataList
    oracle = [{'question_id':qid,'answer':etr['answer']} for qid, etr in dataList['evalres']['data'].iteritems()]
    accs = [etr['accuracy'] for qid, etr in dataList['evalres']['data'].iteritems()]
    acc = sum(accs)/len(accs)
    return oracle, acc

def constructEvalRes(resAccQA):
    global dataList
    evalRes = copy.deepcopy(dataList['res']['data'])
    for res in evalRes:
        res['accuracy'] = resAccQA[res['question_id']]
    return evalRes

@app.route('/getscore/')
def getscore():
    global dataList
    if not dataList['evaluated']:
        resAccQA = dataList['vqaEval'].evaluate()
        dataList['evaluated'] = True

        constructQuestions()
        packed = packAccuracy(dataList['vqaEval'].accuracy, dataList['quenums'])
        fn, ext = os.path.splitext(dataList['res']['fn'])
        fn = 'temporary/scorenew_%s_%.2f%s' % (fn, dataList['vqaEval'].accuracy['overall'],ext)
        f = open(fn, 'w')
        f.write(json.dumps(packed))
        f.close()
        dataList['accuracyfn'] = fn

        evalRes = constructEvalRes(resAccQA)
        fn, ext = os.path.splitext(dataList['res']['fn'])
        fn = 'temporary/evalres_%s_%.2f%s' % (fn, dataList['vqaEval'].accuracy['overall'],ext)
        f = open(fn, 'w')
        f.write(json.dumps(evalRes))
        f.close()
        dataList['evalresfn'] = fn
        
    accresp = {}    
    accresp['fn'] = dataList['accuracyfn']
    accresp['accuracy']=dataList['vqaEval'].accuracy
    return jsonify(accresp)


@app.route('/addevalres', methods=['POST'])
def addevalres():
    global dataList
    app.logger.debug('addevalres')
    f = request.files['addevalres']
    try:
        evalres_json = json.loads(f.read())
    except:
        app.logger.debug('addscore-except')
        dataList['evalres']['loadstate'] = 'improper json file..'
        return redirect(url_for('index'))
    if not isProperEvalResJson(evalres_json):
        app.logger.debug('addevalres-notproper')
        dataList['evalres']['loadstate'] = 'improper json file..'
        return redirect(url_for('index'))
    dataList['evalres']['loadstate'] = ''
    dataList['evalres']['fn'].append(f.filename)
    pushEvalResJson(evalres_json)
    oracle, acc = constructOracle()

    fn, ext = os.path.splitext(f.filename)
    fn = 'temporary/oracle_%s_%.2f%s' % (fn, acc, ext)
    f = open(fn, 'w')
    f.write(json.dumps(oracle))
    f.close()
    dataList['oraclefn'] = fn

    return redirect(url_for('index'))

@app.route('/addscore', methods=['POST'])
def addscore():
    global dataList
    app.logger.debug('addscore')
    f = request.files['addscore']
    try:
        score_json = json.loads(f.read())
    except:
        app.logger.debug('addscore-except')
        dataList['scores']['loadstate'] = 'improper json file..'
        return redirect(url_for('index'))
    if not isProperScoreJson(score_json):
        app.logger.debug('addscore-notproper')
        dataList['scores']['loadstate'] = 'improper json file..'
        return redirect(url_for('index'))
    dataList['scores']['loadstate'] = ''
    dataList['scores']['fn'].append(f.filename)
    pushScoreJson(score_json)
    return redirect(url_for('index'))

@app.route('/resetevalres/')
def resetevalres():
    global dataList
    dataList['evalres']={}
    dataList['evalres']['data'] = {}
    dataList['evalres']['fn'] = []
    dataList['evalres']['loadstate'] = ''

    return redirect(url_for('index'))

@app.route('/removescore/')
def removescore():
    global dataList
    if len(dataList['scores']['fn']) == 1:
        dataList['scores']['fn'] = []
        dataList['scores']['lists'] = []
        dataList['scores']['keyidx'] = {}
    elif len(dataList['scores']['fn']) > 1:
        dataList['scores']['fn'].pop()
        for listetr in dataList['scores']['lists']:
            listetr['scores'].pop()
            if listetr.has_key('floatscores'):
                listetr['floatscores'].pop()
    return redirect(url_for('index'))

@app.route('/getanalyzeprev/')
def getanalyzeprev():
    global dataList
    send_data = {}
    if len(dataList['scores']['fn']) > 0:
        batch = dataList['scores']['batch']
        scorelen = len(dataList['scores']['lists'])
        curidx = dataList['scores']['idx']
        if curidx == 0:
            dataList['scores']['idx'] = scorelen-(batch- (scorelen % batch))
        else:
            dataList['scores']['idx'] = curidx - batch
        sidx = dataList['scores']['idx']
        eidx = min(sidx+batch,scorelen)
        send_data['scorelists'] = dataList['scores']['lists'][sidx:eidx]
        send_data['scores_fn'] = dataList['scores']['fn']
    else:
        send_data['scorelists'] = []
        send_data['scores_fn'] = []
    return jsonify(send_data)

@app.route('/getanalyzenext/')
def getanalyzenext():
    global dataList
    send_data = {}
    if len(dataList['scores']['fn']) > 0:
        batch = dataList['scores']['batch']
        scorelen = len(dataList['scores']['lists'])
        curidx = dataList['scores']['idx']
        if curidx + batch > scorelen:
            dataList['scores']['idx'] = 0
        else:
            dataList['scores']['idx'] = curidx + batch
        sidx = dataList['scores']['idx']
        eidx = min(sidx+batch,scorelen)
        send_data['scorelists'] = dataList['scores']['lists'][sidx:eidx]
        send_data['scores_fn'] = dataList['scores']['fn']
    else:
        send_data['scorelists'] = []
        send_data['scores_fn'] = []
    return jsonify(send_data)

@app.route('/questiontypeplot')
def questionstypeplot():
    global dataList
    quesidx = dataList['scores']['qtypesidx']
    queeidx = dataList['scores']['qtypeeidx']
    quesdata = dataList['scores']['lists'][quesidx:queeidx]

    if quesdata[0]['hasoccur']:
        app.logger.debug('hasoccur')
        nNonQues = 0
        nQues = 0
        for que in quesdata:
            nQues += que['occurrence']
    else:
        nNonQues = 0
        nQues = 0
        app.logger.debug('hasnotoccur')

    scorefn = dataList['scores']['fn']
    for que in quesdata:
        npscore = np.array(que['floatscores'])
        que['var'] = npscore.var()
        que['max'] = npscore.max()
        que['showlabel'] = False

    quesdata = sorted(quesdata, key=lambda x:x['var'], reverse=True)
    for qi, que in enumerate(quesdata[0:min(100,len(quesdata))]):
        que['varrank'] = qi
        que['showlabel'] = True
    quesdata = sorted(quesdata, key=lambda x:x['max'], reverse=True)

    figfns = []
    figfns.append(drawquestiontype(quesdata, scorefn, 'compare_overall_plot_question_type', 'Question Type'))
    if quesdata[0]['hasoccur']:
        figfns.append(questiontypediff(quesdata, scorefn, 'question_type_plot_differ', 'Question Type Difference', False))
        figfns.append(questiontypediffbar(quesdata, scorefn, 'question_type_plot_diffbar', 'Effect of Question Type on Final Score', False))
    #figfns.append(occurbasedplot(quesdata, scorefn, 'compare_overall_plot_cumulative_reverse', 'cumulative score (Descent order)', True))

    return render_template('questiontype.html',quesdata=quesdata,scorefn=scorefn,figfns=figfns, \
                                               nQues=nQues,nNonQues=nNonQues)

def questiontypediffbar(quesdata, scorefn, plotfn, title, drawreverse):

    # make occurrence based score list
    occur_score = {}
    for qi, que in enumerate(quesdata):
        if not occur_score.has_key(que['occurrence']):
            occur_score[que['occurrence']] = {}
            occur_score[que['occurrence']]['exnum'] = 0
            occur_score[que['occurrence']]['scores'] = []
            occur_score[que['occurrence']]['type'] = que['type']
            for si in range(len(scorefn)):
                occur_score[que['occurrence']]['scores'].append(0.0)

        occur_score[que['occurrence']]['exnum'] += que['occurrence']
        for si, fscr in enumerate(que['floatscores']):
            occur_score[que['occurrence']]['scores'][si] += fscr * que['occurrence']
    # normalize
    for oc, scrs in occur_score.iteritems():
        exnum = scrs['exnum']
        for si, fscr in enumerate(scrs['scores']):
            scrs['scores'][si] /= exnum

    occur_score = [{'occurrence': key, 'scores':val['scores'], 'exnum':val['exnum'], 'type':val['type']} for key, val in occur_score.iteritems()] 
    # sort by occurrence
    occur_score = sorted(occur_score, key=lambda x:x['occurrence'], reverse=drawreverse)

    # cumulate scores
    cum_occurrence = 0
    cum_scores = []
    for si in range(len(scorefn)):
        cum_scores.append(0.0)
    for qi, que in enumerate(occur_score):
        cum_occurrence += que['exnum']
        for si, fscr in enumerate(que['scores']):
            cum_scores[si] += que['exnum'] * fscr    

    # basescore computation
    basescore = np.zeros((1, len(occur_score[0]['scores'])))
    basescore[0] = np.array(cum_scores) / cum_occurrence
    basescore = basescore.repeat(len(occur_score),0)

    # quescore computation
    quesnum = np.arange(len(occur_score))+1
    quescore = np.zeros((len(occur_score), len(occur_score[0]['scores'])))
    quexnum = []
    quexlabel = []
    questions = []
    for qi, que in enumerate(occur_score):
        # exceptscore
        exceptscore = []
        for si, fscr in enumerate(cum_scores):
           exceptscore.append((fscr-que['scores'][si]*que['exnum']) / (cum_occurrence-que['exnum']))

        # make short label
        shortlabel = '%s (%d times)' % (que['type'], que['occurrence'])
        # make labeltxt
        labeltxt = '%s: #occurrence: %d, score: ' % (que['type'],que['occurrence'])
        for si, fscr in enumerate(que['scores']):
            labeltxt += '[%d: %.2f] ' % (si, fscr)
        labeltxt += 'except score: '
        for si, fscr in enumerate(exceptscore):
            labeltxt += '[%d: %.2f] ' % (si, fscr)
        labeltxt += 'diff score: '
        for si, fscr in enumerate(exceptscore):
            labeltxt += '[%d: %.2f] ' % (si, cum_scores[si] -fscr)

        quexnum.append(qi+1)
        quexlabel.append(shortlabel)
        questions.append(labeltxt)
        # assign scores to plot
        quescore[qi]= basescore[qi] - np.array(exceptscore)
        quesnum[qi] = qi+1
    basescore = basescore.transpose()
    quescore = quescore.transpose()

    # plot baseline
#    for i in range(len(basescore)):
#        plt.plot(quesnum, basescore[i], linestyle='-', label=('%d(base): %s' % (i+1, scorefn[i])))
    # plot quescores
    margin = 0
    quesnum = quesnum * (len(quescore)+margin * 2)
    for i in range(len(quexnum)):
        quexnum[i] = (quexnum[i] * (len(quescore)+margin*2)) + (len(quescore) / (float(2))) + margin
    for i in range(len(quescore)):
        plt.bar(quesnum+i+margin,quescore[i],1, color=np.random.rand(3,), label=('%d: %s' % (i+1, scorefn[i])))
#        plt.plot(quesnum, quescore[i], linestyle='-', marker='o', label=('%d: %s' % (i+1, scorefn[i])))
    plt.xticks(quexnum, quexlabel, rotation=-90, fontsize=8)
    legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5,1.05+(0.07*len(quescore))),fontsize=10)
    figfn = 'static/plots/%s.png' % plotfn
    figfns_etr = {}
    figfns_etr['figfn'] = figfn
    figfns_etr['questions'] = questions
    figfns_etr['quexlabel'] = quexlabel
    figfns_etr['title'] = title
    plt.grid()
    plt.savefig(figfn, bbox_extra_artists=(legend,), bbox_inches='tight')
    plt.close()
    return figfns_etr 



def questiontypediff(quesdata, scorefn, plotfn, title, drawreverse):

    # make occurrence based score list
    occur_score = {}
    for qi, que in enumerate(quesdata):
        if not occur_score.has_key(que['occurrence']):
            occur_score[que['occurrence']] = {}
            occur_score[que['occurrence']]['exnum'] = 0
            occur_score[que['occurrence']]['scores'] = []
            occur_score[que['occurrence']]['type'] = que['type']
            for si in range(len(scorefn)):
                occur_score[que['occurrence']]['scores'].append(0.0)

        occur_score[que['occurrence']]['exnum'] += que['occurrence']
        for si, fscr in enumerate(que['floatscores']):
            occur_score[que['occurrence']]['scores'][si] += fscr * que['occurrence']
    # normalize
    for oc, scrs in occur_score.iteritems():
        exnum = scrs['exnum']
        for si, fscr in enumerate(scrs['scores']):
            scrs['scores'][si] /= exnum

    occur_score = [{'occurrence': key, 'scores':val['scores'], 'exnum':val['exnum'], 'type':val['type']} for key, val in occur_score.iteritems()] 
    # sort by occurrence
    occur_score = sorted(occur_score, key=lambda x:x['occurrence'], reverse=drawreverse)

    # cumulate scores
    cum_occurrence = 0
    cum_scores = []
    for si in range(len(scorefn)):
        cum_scores.append(0.0)
    for qi, que in enumerate(occur_score):
        cum_occurrence += que['exnum']
        for si, fscr in enumerate(que['scores']):
            cum_scores[si] += que['exnum'] * fscr    

    # basescore computation
    basescore = np.zeros((1, len(occur_score[0]['scores'])))
    basescore[0] = np.array(cum_scores) / cum_occurrence
    basescore = basescore.repeat(len(occur_score),0)
    basescore = basescore.transpose()

    # quescore computation
    quesnum = np.arange(len(occur_score))+1
    quescore = np.zeros((len(occur_score), len(occur_score[0]['scores'])))
    quexnum = []
    quexlabel = []
    questions = []
    for qi, que in enumerate(occur_score):
        # exceptscore
        exceptscore = []
        for si, fscr in enumerate(cum_scores):
           exceptscore.append((fscr-que['scores'][si]*que['exnum']) / (cum_occurrence-que['exnum']))

        # make short label
        shortlabel = '%s (%d times)' % (que['type'], que['occurrence'])
        # make labeltxt
        labeltxt = '%s: #occurrence: %d, score: ' % (que['type'],que['occurrence'])
        for si, fscr in enumerate(que['scores']):
            labeltxt += '[%d: %.2f] ' % (si, fscr)
        labeltxt += 'except score: '
        for si, fscr in enumerate(exceptscore):
            labeltxt += '[%d: %.2f] ' % (si, fscr)
        labeltxt += 'diff score: '
        for si, fscr in enumerate(exceptscore):
            labeltxt += '[%d: %.2f] ' % (si, cum_scores[si] -fscr)

        quexnum.append(qi+1)
        quexlabel.append(shortlabel)
        questions.append(labeltxt)
        # assign scores to plot
        quescore[qi]= np.array(exceptscore)
        quesnum[qi] = qi+1
    quescore = quescore.transpose()

    # plot baseline
    for i in range(len(basescore)):
        plt.plot(quesnum, basescore[i], linestyle='-', label=('%d(base): %s' % (i+1, scorefn[i])))
    # plot quescores
    for i in range(len(quescore)):
        plt.plot(quesnum, quescore[i], linestyle='-', marker='o', label=('%d: %s' % (i+1, scorefn[i])))
    plt.xticks(quexnum, quexlabel, rotation=-90, fontsize=8)
    legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5,1.05+(0.07*len(quescore))),fontsize=10)
    figfn = 'static/plots/%s.png' % plotfn
    figfns_etr = {}
    figfns_etr['figfn'] = figfn
    figfns_etr['questions'] = questions
    figfns_etr['quexlabel'] = quexlabel
    figfns_etr['title'] = title
    plt.grid()
    plt.savefig(figfn, bbox_extra_artists=(legend,), bbox_inches='tight')
    plt.close()
    return figfns_etr 

def drawquestiontype(quesdata, scorefn, plotfn, title):
    quexnum = []
    quexlabel = []
    quesnum = np.arange(len(quesdata))+1
    quescore = np.zeros((len(quesdata), len(quesdata[0]['floatscores'])))
    questions = [''] * len(quesdata)

    for qi, que in enumerate(quesdata):
        labeltxt = '%d (%dth rank): %s ' % (qi, que['varrank'],que['type'])
        if que['hasoccur']:
            labeltxt += '(%d times) ' % (que['occurrence'])
        labeltxt += 'score: '
        for si, fscr in enumerate(que['floatscores']):
            labeltxt += '[%d: %.2f] ' % (si, fscr)
        if que['showlabel']:
            quexnum.append(qi+1)
            shortlabel = '%dth %s' % (que['varrank'], que['type'])
            quexlabel.append(shortlabel)
        quescore[qi]=np.array(que['floatscores'])
        questions[que['varrank']] = labeltxt
    quescore = quescore.transpose()
    for i in range(len(quescore)):
        plt.plot(quesnum, quescore[i], linestyle='-', marker='o', label=('%d: %s' % (i+1, scorefn[i])))
    plt.xticks(quexnum, quexlabel, rotation=-90, fontsize=8)
    legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5,1.05+(0.07*len(quescore))),fontsize=10)
    figfn = 'static/plots/%s.png' % plotfn
    figfns_etr = {}
    figfns_etr['figfn'] = figfn
    figfns_etr['questions'] = questions
    figfns_etr['quexlabel'] = quexlabel
    figfns_etr['title'] = title
    plt.grid()
    plt.savefig(figfn, bbox_extra_artists=(legend,), bbox_inches='tight')
    plt.close()
    return figfns_etr

@app.route('/differenceplot/<occurthres>/<labelthres>')
def differenceplot(occurthres, labelthres):
    global dataList
    quesidx = dataList['scores']['quesidx']
    queeidx = dataList['scores']['queeidx']
    quesdata = dataList['scores']['lists'][quesidx:queeidx]

    nonquesdata = filter(lambda x:x['occurrence'] < int(occurthres), quesdata)
    quesdata = filter(lambda x:x['occurrence'] >= int(occurthres), quesdata)

    nNonQues = 0
    for nque in nonquesdata:
        nNonQues += nque['occurrence']
    nQues = 0
    scorefn = dataList['scores']['fn']
    for que in quesdata:
        nQues += que['occurrence']
        npscore = np.array(que['floatscores'])
        que['var'] = npscore.var()
        que['max'] = npscore.max()
        que['showlabel'] = False
    quesdata = sorted(quesdata, key=lambda x:x['var'], reverse=True)
    for qi, que in enumerate(quesdata[0:int(labelthres)]):
        que['varrank'] = qi
        que['showlabel'] = True

    figfns = []
    figfns.append(diffbasedplot(quesdata, scorefn, 'compare_overall_plot_cumulative', 'cumulative score', False))
    #figfns.append(occurbasedplot(quesdata, scorefn, 'compare_overall_plot_cumulative_reverse', 'cumulative score (Descent order)', True))

    return render_template('difference.html',quesdata=quesdata,scorefn=scorefn,figfns=figfns, \
                                          nQues=nQues, nNonQues=nNonQues)

def diffbasedplot(quesdata, scorefn, plotfn, title, drawreverse):

    # make occurrence based score list
    occur_score = {}
    for qi, que in enumerate(quesdata):
        if not occur_score.has_key(que['occurrence']):
            occur_score[que['occurrence']] = {}
            occur_score[que['occurrence']]['exnum'] = 0
            occur_score[que['occurrence']]['scores'] = []
            for si in range(len(scorefn)):
                occur_score[que['occurrence']]['scores'].append(0.0)

        occur_score[que['occurrence']]['exnum'] += que['occurrence']
        for si, fscr in enumerate(que['floatscores']):
            occur_score[que['occurrence']]['scores'][si] += fscr * que['occurrence']
    # normalize
    for oc, scrs in occur_score.iteritems():
        exnum = scrs['exnum']
        for si, fscr in enumerate(scrs['scores']):
            scrs['scores'][si] /= exnum

    occur_score = [{'occurrence': key, 'scores':val['scores'], 'exnum':val['exnum']} for key, val in occur_score.iteritems()] 
    # sort by occurrence
    occur_score = sorted(occur_score, key=lambda x:x['occurrence'], reverse=drawreverse)

    # cumulate scores
    cum_occurrence = 0
    cum_scores = []
    for si in range(len(scorefn)):
        cum_scores.append(0.0)
    for qi, que in enumerate(occur_score):
        cum_occurrence += que['exnum']
        for si, fscr in enumerate(que['scores']):
            cum_scores[si] += que['exnum'] * fscr    

    # basescore computation
    basescore = np.zeros((1, len(occur_score[0]['scores'])))
    basescore[0] = np.array(cum_scores) / cum_occurrence
    basescore = basescore.repeat(len(occur_score),0)
    basescore = basescore.transpose()

    # quescore computation
    quesnum = np.arange(len(occur_score))+1
    quescore = np.zeros((len(occur_score), len(occur_score[0]['scores'])))
    quexnum = []
    quexlabel = []
    questions = []
    for qi, que in enumerate(occur_score):
        # exceptscore
        exceptscore = []
        for si, fscr in enumerate(cum_scores):
           exceptscore.append((fscr-que['scores'][si]*que['exnum']) / (cum_occurrence-que['exnum']))

        # make labeltxt
        labeltxt = '#occurrence: %d, #example: %d, #cumulative occurrence: %d, score: ' % (que['occurrence'], que['exnum'], cum_occurrence)
        for si, fscr in enumerate(que['scores']):
            labeltxt += '[%d: %.2f] ' % (si, fscr)
        labeltxt += 'except score: '
        for si, fscr in enumerate(exceptscore):
            labeltxt += '[%d: %.2f] ' % (si, fscr)
        labeltxt += 'diff score: '
        for si, fscr in enumerate(exceptscore):
            labeltxt += '[%d: %.2f] ' % (si, cum_scores[si] -fscr)

        quexnum.append(qi)
        quexlabel.append(labeltxt)
        questions.append(labeltxt)
        # assign scores to plot
        quescore[qi]= np.array(exceptscore)
        quesnum[qi] = qi+1
    quescore = quescore.transpose()

    # plot baseline
    for i in range(len(basescore)):
        plt.plot(quesnum, basescore[i], linestyle='-', label=('%d(base): %s' % (i+1, scorefn[i])))
    # plot quescores
    for i in range(len(quescore)):
        plt.plot(quesnum, quescore[i], linestyle='-', marker='o', label=('%d: %s' % (i+1, scorefn[i])))
    
    #plt.xticks(quexnum, quexlabel, rotation=-90, fontsize=8)
    legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5,1.05+(0.07*len(quescore))),fontsize=10)
    figfn = 'static/plots/%s.png' % plotfn
    figfns_etr = {}
    figfns_etr['figfn'] = figfn
    figfns_etr['questions'] = questions
    figfns_etr['quexlabel'] = quexlabel
    figfns_etr['title'] = title
    plt.savefig(figfn, bbox_extra_artists=(legend,), bbox_inches='tight')
    plt.close()
    return figfns_etr 




@app.route('/cumulativeplot/<occurthres>/<labelthres>')
def cumulativeplot(occurthres, labelthres):
    global dataList
    quesidx = dataList['scores']['quesidx']
    queeidx = dataList['scores']['queeidx']
    quesdata = dataList['scores']['lists'][quesidx:queeidx]

    nonquesdata = filter(lambda x:x['occurrence'] < int(occurthres), quesdata)
    quesdata = filter(lambda x:x['occurrence'] >= int(occurthres), quesdata)

    nNonQues = 0
    for nque in nonquesdata:
        nNonQues += nque['occurrence']
    nQues = 0
    scorefn = dataList['scores']['fn']
    for que in quesdata:
        nQues += que['occurrence']
        npscore = np.array(que['floatscores'])
        que['var'] = npscore.var()
        que['max'] = npscore.max()
        que['showlabel'] = False
    quesdata = sorted(quesdata, key=lambda x:x['var'], reverse=True)
    for qi, que in enumerate(quesdata[0:int(labelthres)]):
        que['varrank'] = qi
        que['showlabel'] = True

    figfns = []
    figfns.append(occurbasedplot(quesdata, scorefn, 'compare_overall_plot_cumulative', 'cumulative score', False))
    figfns.append(occurbasedplot(quesdata, scorefn, 'compare_overall_plot_cumulative_reverse', 'cumulative score (Descent order)', True))

    return render_template('cumulative.html',quesdata=quesdata,scorefn=scorefn,figfns=figfns, \
                                          nQues=nQues, nNonQues=nNonQues)

def occurbasedplot(quesdata, scorefn, plotfn, title, drawreverse):

    # make occurrence based score list
    occur_score = {}
    for qi, que in enumerate(quesdata):
        if not occur_score.has_key(que['occurrence']):
            occur_score[que['occurrence']] = {}
            occur_score[que['occurrence']]['exnum'] = 0
            occur_score[que['occurrence']]['scores'] = []
            for si in range(len(scorefn)):
                occur_score[que['occurrence']]['scores'].append(0.0)

        occur_score[que['occurrence']]['exnum'] += que['occurrence']
        for si, fscr in enumerate(que['floatscores']):
            occur_score[que['occurrence']]['scores'][si] += fscr * que['occurrence']
    # normalize
    for oc, scrs in occur_score.iteritems():
        exnum = scrs['exnum']
        for si, fscr in enumerate(scrs['scores']):
            scrs['scores'][si] /= exnum

    occur_score = [{'occurrence': key, 'scores':val['scores'], 'exnum':val['exnum']} for key, val in occur_score.iteritems()] 
    # sort by occurrence
    occur_score = sorted(occur_score, key=lambda x:x['occurrence'], reverse=drawreverse)
    
    quesnum = np.arange(len(occur_score))+1
    quescore = np.zeros((len(occur_score), len(occur_score[0]['scores'])))

    quexnum = []
    quexlabel = []
    questions = []
    cum_idx = 0
    cum_occurrence = 0
    cum_scores = []
    for si in range(len(scorefn)):
        cum_scores.append(0.0)
    for qi, que in enumerate(occur_score):
        # make cumulative scores
        cum_occurrence += que['exnum']
        for si, fscr in enumerate(que['scores']):
            cum_scores[si] += que['exnum'] * fscr    
        # make labeltxt
        labeltxt = '#occurrence: %d, #example: %d, #cumulative occurrence: %d, score: ' % (que['occurrence'], que['exnum'], cum_occurrence)
        for si, fscr in enumerate(que['scores']):
            labeltxt += '[%d: %.2f] ' % (si, fscr)
        labeltxt += 'cumulative score: '
        for si, fscr in enumerate(cum_scores):
            labeltxt += '[%d: %.2f] ' % (si, fscr / cum_occurrence)
        quexnum.append(qi)
        quexlabel.append(labeltxt)
        # assign scores to plot
        quescore[qi]=np.array(cum_scores) / cum_occurrence
        quesnum[qi] = cum_idx
        cum_idx = cum_occurrence
    quescore = quescore.transpose()

    for i in range(len(quescore)):
        plt.plot(quesnum, quescore[i], linestyle='-', marker='o', label=('%d: %s' % (i+1, scorefn[i])))
    #plt.xticks(quexnum, quexlabel, rotation=-90, fontsize=8)
    legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5,1.05+(0.07*len(quescore))),fontsize=10)
    figfn = 'static/plots/%s.png' % plotfn
    figfns_etr = {}
    figfns_etr['figfn'] = figfn
    figfns_etr['questions'] = []
    figfns_etr['quexlabel'] = quexlabel
    figfns_etr['title'] = title
    plt.savefig(figfn, bbox_extra_artists=(legend,), bbox_inches='tight')
    plt.close()
    return figfns_etr 

@app.route('/overallcompare/<occurthres>/<labelthres>')
def overallcompare(occurthres, labelthres):
    global dataList
    quesidx = dataList['scores']['quesidx']
    queeidx = dataList['scores']['queeidx']
    quesdata = dataList['scores']['lists'][quesidx:queeidx]

    nonquesdata = filter(lambda x:x['occurrence'] < int(occurthres), quesdata)
    quesdata = filter(lambda x:x['occurrence'] >= int(occurthres), quesdata)

    nNonQues = 0
    for nque in nonquesdata:
        nNonQues += nque['occurrence']
    nQues = 0
    scorefn = dataList['scores']['fn']
    for que in quesdata:
        nQues += que['occurrence']
        npscore = np.array(que['floatscores'])
        que['var'] = npscore.var()
        que['max'] = npscore.max()
        que['showlabel'] = False
    quesdata = sorted(quesdata, key=lambda x:x['var'], reverse=True)
    for qi, que in enumerate(quesdata[0:int(labelthres)]):
        que['varrank'] = qi
        que['showlabel'] = True
    figfns = []
    quesdata = sorted(quesdata, key=lambda x:x['max'], reverse=True)
    figfns.append(drawfigplot(quesdata, scorefn, 'compare_overall_plot_max', 'sorted by score'))
   
    quesdata = sorted(quesdata, key=lambda x:x['occurrence'], reverse=True)
    figfns.append(drawfigplot(quesdata, scorefn, 'compare_overall_plot_occur', 'sorted by occurrence'))
    if len(scorefn) == 2:
        for que in quesdata:
            que['diff'] = que['floatscores'][0] - que['floatscores'][1]
        quesdata = sorted(quesdata, key=lambda x:x['diff'], reverse=True)
        figfns.append(drawfigplot(quesdata, scorefn, 'compare_overall_plot_diff', 'sorted by difference'))
 
    return render_template('overall.html',quesdata=quesdata,scorefn=scorefn,figfns=figfns, \
                                          nQues=nQues, nNonQues=nNonQues)

def drawfigplot(quesdata, scorefn, plotfn, title):
    questions = []
    quexnum = []
    quexlabel = []
    quesnum = np.arange(len(quesdata))+1
    quescore = np.zeros((len(quesdata), len(quesdata[0]['floatscores'])))

    for qi, que in enumerate(quesdata):
        questions.append(que['question'])
        if que['showlabel']:
            quexnum.append(qi)
            labeltxt = '%d (%dth rank): %s (%d times) score: ' % (qi, que['varrank'],que['question'],que['occurrence'])
            for si, fscr in enumerate(que['floatscores']):
               labeltxt += '[%d: %.2f] ' % (si, fscr)
            quexlabel.append(labeltxt)
        quescore[qi]=np.array(que['floatscores'])
    quescore = quescore.transpose()
    for i in range(len(quescore)):
        plt.plot(quesnum, quescore[i], linestyle='-', marker='o', label=('%d: %s' % (i+1, scorefn[i])))
    plt.xticks(quexnum, quexlabel, rotation=-90, fontsize=8)
    legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5,1.05+(0.07*len(quescore))),fontsize=10)
    figfn = 'static/plots/%s.png' % plotfn
    figfns_etr = {}
    figfns_etr['figfn'] = figfn
    figfns_etr['questions'] = questions
    figfns_etr['quexlabel'] = quexlabel
    figfns_etr['title'] = title
    plt.savefig(figfn, bbox_extra_artists=(legend,), bbox_inches='tight')
    plt.close()
    return figfns_etr

@app.route('/comparision/<occurthres>/<nEntry>')
def comparision(occurthres, nEntry):
    global dataList
    quesidx = dataList['scores']['quesidx']
    queeidx = dataList['scores']['queeidx']
    quesdata = dataList['scores']['lists'][quesidx:queeidx]
    quesdata = filter(lambda x:x['occurrence'] > int(occurthres), quesdata)
    scorefn = dataList['scores']['fn']
    for que in quesdata:
        npscore = np.array(que['floatscores'])
        que['var'] = npscore.var()
        que['max'] = npscore.max()
    quesdata = sorted(quesdata, key=lambda x:x['var'], reverse=True)
  
    nEntry = int(nEntry) 
    figfns = [] 
    nImg = int(np.ceil(len(quesdata) / nEntry))
    for ni in range(nImg):
        sidx = ni * nEntry
        eidx = min(sidx + nEntry, len(quesdata))
        
        squesdata = quesdata[sidx:eidx]
        squesdata = sorted(squesdata, key=lambda x:x['max'], reverse=True)

        questions = []
        quexlabel = []
        quesnum = np.arange(len(squesdata))+1
        quescore = np.zeros((len(squesdata), len(quesdata[0]['floatscores'])))

        for qi, que in enumerate(squesdata):
            questions.append(que['question'])
            quexlabel.append('%d: %s (%d times)' % (qi,que['question'],que['occurrence']))
            quescore[qi]=np.array(que['floatscores'])
        quescore = quescore.transpose()
        for i in range(len(quescore)):
            app.logger.debug('i: %d' % i)
            app.logger.debug('len(quescore[]): %d' % len(quescore))
            app.logger.debug('len(scorefn[]): %d' % len(scorefn))
            plt.plot(quesnum, quescore[i], linestyle='-', marker='o', label=('%d: %s' % (i+1, scorefn[i])))
        plt.xticks(quesnum, quexlabel, rotation=-90)
        legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5,1.05+(0.07*len(quescore))))
        figfn = 'static/plots/comparison_plot_%d.png' % (ni+1)
        figfns_etr = {}
        figfns_etr['figfn'] = figfn
        figfns_etr['questions'] = questions
        figfns.append(figfns_etr)
        plt.grid()
        plt.savefig(figfn, bbox_extra_artists=(legend,), bbox_inches='tight')
        plt.close()
    return render_template('compare.html',quesdata=quesdata,scorefn=scorefn,figfns=figfns)

@app.route('/getoraclemerge/')
def getoraclemerge():
    global dataList
    send_data = {}
    if len(dataList['evalres']['fn']) > 0:
        send_data['evalres_fn'] = dataList['evalres']['fn']
    else:
        send_data['evalres_fn'] = []
    return jsonify(send_data)

@app.route('/getanalyze/')
def getanalyze():
    global dataList
    send_data = {}
    if len(dataList['scores']['fn']) > 0:
        batch = dataList['scores']['batch']
        scorelen = len(dataList['scores']['lists'])
        sidx = dataList['scores']['idx']
        eidx = min(sidx+batch,scorelen)
        send_data['scorelists'] = dataList['scores']['lists'][sidx:eidx]
        send_data['scores_fn'] = dataList['scores']['fn']
    else:
        send_data['scorelists'] = []
        send_data['scores_fn'] = []
    return jsonify(send_data)

def pushEvalResJson(evalresjson):
    global dataList
    initialized = True
    if len(dataList['evalres']['data']) == 0:
        dataList['evalres']['data'] = {}
        initialized = False
    if not initialized:
        for etr in evalresjson:
            dataList['evalres']['data'][etr['question_id']]={'answer':etr['answer'],'accuracy':float(etr['accuracy'])}
    else:
        for etr in evalresjson:
            prevetr = dataList['evalres']['data'][etr['question_id']]
            if etr['accuracy'] > float(prevetr['accuracy']):
                dataList['evalres']['data'][etr['question_id']]={'answer':etr['answer'],'accuracy':float(etr['accuracy'])}

def pushScoreJson(scorejson):
    global dataList
    initialized = True
    keyidx = 0
    if len(dataList['scores']['lists']) == 0:
        dataList['scores']['lists'] = []
        dataList['scores']['keyidx'] = {}
        initialized = False
    # overall accuracy
    if not initialized:
        dataList['scores']['keyidx']['overall'] = keyidx
        dataList['scores']['lists'].append({})
        dataList['scores']['lists'][keyidx]['name']='Overall'
        dataList['scores']['lists'][keyidx]['scores']=[]
        keyidx += 1
    dataList['scores']['lists'][dataList['scores']['keyidx']['overall']]['scores'].append('%.2f' % scorejson['accuracy']['overall'])
    # per answer type accuracy
    for tp, val in scorejson['accuracy']['perAnswerType'].iteritems():
       tpname = 'AnswerType (%s)' % tp
       if not initialized:
           dataList['scores']['keyidx'][tpname] = keyidx
           dataList['scores']['lists'].append({})
           dataList['scores']['lists'][keyidx]['name']=tpname
           dataList['scores']['lists'][keyidx]['type']='%s' % tp
           dataList['scores']['lists'][keyidx]['scores']=[]
           dataList['scores']['lists'][keyidx]['floatscores']=[]
           if scorejson['accuracy'].has_key('occurPerAnswerType'):
               dataList['scores']['lists'][keyidx]['hasoccur'] = True
               dataList['scores']['lists'][keyidx]['occurrence'] = scorejson['accuracy']['occurPerAnswerType'][tp]
           else:
               dataList['scores']['lists'][keyidx]['hasoccur'] = False
           keyidx += 1
           dataList['scores']['qtypesidx'] = keyidx
       dataList['scores']['lists'][dataList['scores']['keyidx'][tpname]]['scores'].append('%.2f' % val)
       dataList['scores']['lists'][dataList['scores']['keyidx'][tpname]]['floatscores'].append(float(val))
    # per question type accuracy
    for tp, val in scorejson['accuracy']['perQuestionType'].iteritems():
       tpname = 'QuestionType (%s)' % tp
       if not initialized:
           dataList['scores']['keyidx'][tpname] = keyidx
           dataList['scores']['lists'].append({})
           dataList['scores']['lists'][keyidx]['name']=tpname
           dataList['scores']['lists'][keyidx]['type']='%s' % tp
           dataList['scores']['lists'][keyidx]['scores']=[]
           dataList['scores']['lists'][keyidx]['floatscores']=[]
           if scorejson['accuracy'].has_key('occurPerQuestionType'):
               dataList['scores']['lists'][keyidx]['hasoccur'] = True
               dataList['scores']['lists'][keyidx]['occurrence'] = scorejson['accuracy']['occurPerQuestionType'][tp]
           else:
               dataList['scores']['lists'][keyidx]['hasoccur'] = False
           keyidx += 1
           dataList['scores']['qtypeeidx'] = keyidx
           dataList['scores']['quesidx'] = keyidx
       dataList['scores']['lists'][dataList['scores']['keyidx'][tpname]]['scores'].append('%.2f' % val)
       dataList['scores']['lists'][dataList['scores']['keyidx'][tpname]]['floatscores'].append(float(val))
    # per question score
    for etr in scorejson['quenums']:
       tpname = '%s (%d times)' % (etr['question'], etr['occurrence'])
       if not initialized:
           dataList['scores']['keyidx'][tpname] = keyidx
           dataList['scores']['lists'].append({})
           dataList['scores']['lists'][keyidx]['name']=tpname
           dataList['scores']['lists'][keyidx]['question']=etr['question']
           dataList['scores']['lists'][keyidx]['occurrence']=etr['occurrence']
           dataList['scores']['lists'][keyidx]['scores']=[]
           dataList['scores']['lists'][keyidx]['floatscores']=[]
           keyidx += 1
           dataList['scores']['queeidx'] = keyidx
       dataList['scores']['lists'][dataList['scores']['keyidx'][tpname]]['scores'].append('%.2f' % etr['score'])
       dataList['scores']['lists'][dataList['scores']['keyidx'][tpname]]['floatscores'].append(float(etr['score']))

def isProperEvalResJson(evalresjson):
    global dataList
    if type(evalresjson) != list:
        app.logger.debug('type(evaljson) != list')
        return False
    if len(evalresjson) == 0:
        app.logger.debug('len(evalresjson) == 0')
        return False
    if not evalresjson[0].has_key('question_id'):
        app.logger.debug('evalres: do not have key [question_id]')
        return False
    if not evalresjson[0].has_key('answer'):
        app.logger.debug('evalres: do not have key [answer]')
        return False
    if not evalresjson[0].has_key('accuracy'):
        app.logger.debug('evalres: do not have key [accuracy]')
        return False
    if len(dataList['evalres']['data']) == 0:
        return True
    loadedqids = [qid for qid, etr in dataList['evalres']['data'].iteritems()]
    newqids = [etr['question_id'] for etr in evalresjson]
    if set(loadedqids) != set(newqids):
        app.logger.debug('qids doesnt match')
        return False
    return True

def isProperScoreJson(scorejson):
    global dataList
    if type(scorejson) != dict:
        app.logger.debug('type(scorejson) != dict')
        return False
    if not scorejson.has_key('accuracy'):
        app.logger.debug('accuracy')
        return False
    if not scorejson.has_key('quenums'):
        app.logger.debug('quenums')
        return False
    if type(scorejson['accuracy']) != dict:
        app.logger.debug('type(scorejson[accuracy]) != dict')
        return False
    if type(scorejson['quenums']) != list:
        app.logger.debug('type(scorejson[quenums]) != list')
        return False
    if not scorejson['accuracy'].has_key('overall'):
        app.logger.debug('not scorejson[accuracy].has_key(overall)')
        return False
    if not scorejson['accuracy'].has_key('perAnswerType'):
        app.logger.debug('not scorejson[accuracy].has_key(perAnswerType)')
        return False
    if not scorejson['accuracy'].has_key('perQuestionType'):
        app.logger.debug('not scorejson[accuracy].has_key(perQuestionType)')
        return False
    if len(scorejson['accuracy']['perAnswerType']) != 3:
        app.logger.debug('per answer type length is: %d' % (len(scorejson['accuracy']['perAnswerType'])))
        app.logger.debug('not len(scorejson[accuracy][perAnswerType]) != 3')
        return False
    if len(scorejson['accuracy']['perQuestionType']) != 65:
        app.logger.debug('not len(scorejson[accuracy][perQuestionType])')
        return False
    if len(dataList['scores']['lists']) == 0:
        return True
    if len(dataList['scores']['lists']) != len(scorejson['quenums'])+69:
        app.logger.debug('len(dataList[scores][lists]) != len(scorejson[accuracy][quenums])+69')
        return False
    return True

@app.route('/getscorepage/')
def getscorepage():
    global dataList
    if not dataList['evaluated']:
        dataList['vqaEval'].evaluate()
        dataList['evaluated'] = True
        fn = 'temporary/score_%.2f_%s' % (dataList['vqaEval'].accuracy['overall'],dataList['res']['fn'])
        f = open(fn, 'w')
        f.write(parsed)
        f.close()
        dataList['accuracyfn'] = fn

    accresp = {}    
    accresp['fn'] = dataList['accuracyfn']
    accresp['accuracy']=dataList['vqaEval'].accuracy
    return render_template('score.html',accuracy=accresp)

@app.route('/searchquestion', methods=['POST'])
def searchquestion():
    global dataList
    quenums = dataList['quenums']
    query = request.data
    app.logger.debug(query)
    # colect questions start with query
    qlist = [{'question':etr['question'], \
              'occurrence':etr['occurrence']} \
             for etr in quenums if query in str(etr['question']).lower()]
    # max 20
    qlist = qlist[0:min(len(qlist),100)]
    searchedlist = []
    for q in qlist:
       question = q['question']
       occurrence = q['occurrence']
       qids = dataList['qidperque'][question]
       tpname = '%s (%d times)' % (question, occurrence)
       qscores = []
       if len(dataList['scores']['lists']) != 0:
          keyidx = dataList['scores']['keyidx'][tpname]
          qscores = dataList['scores']['lists'][keyidx]['scores']
          
       anns =  dataList['vqa'].loadQA(qids)        
       tot_answers = {}
       avgnumans3 = float(0)
       avgnumans2 = float(0)
       avgnumans1 = float(0)
       avgtopratio = float(0)
       for ann in anns:
          answerset = {}
          for ans in ann['answers']:
             if not answerset.has_key(ans['answer']):
                answerset[ans['answer']] = 0
             answerset[ans['answer']]+=1
             if not tot_answers.has_key(ans['answer']):
                tot_answers[ans['answer']] = 0
             tot_answers[ans['answer']]+=1
          numans3 = len([key for key, val in answerset.items() if val >= 3])
          numans2 = len([key for key, val in answerset.items() if val >= 2])
          numans1 = len([key for key, val in answerset.items() if val >= 1])
          avgnumans3 += numans3
          avgnumans2 += numans2
          avgnumans1 += numans1
          answerset = sorted(answerset.items(), key=operator.itemgetter(1), reverse=True)
          topratio = float(answerset[0][1]) / len(ann['answers'])
          avgtopratio += topratio
       avgnumans3 /= len(anns)
       avgnumans2 /= len(anns)
       avgnumans1 /= len(anns)
       avgtopratio /= len(anns)
       tot_answers = sorted(tot_answers.items(), key=operator.itemgetter(1), reverse=True)
       tot_answers = tot_answers[0:min(len(tot_answers),5)]
          
       etr = {}
       etr['question'] = question
       etr['occurrence'] = occurrence
       etr['avgnumans3'] = avgnumans3
       etr['avgnumans2'] = avgnumans2
       etr['avgnumans1'] = avgnumans1
       etr['avgtopratio'] = avgtopratio
       etr['topans'] = tot_answers
       etr['qscores'] = qscores
       searchedlist.append(etr)
    
    if len(searchedlist) > 0: 
       searchedlist = searchedlist[0:min(len(searchedlist),100)] 
    send_data = {}
    send_data['searchedlist'] = searchedlist
    return jsonify(send_data)


@app.route('/searchpreview', methods=['POST'])
def searchpreview():
    global dataList
    quenums = dataList['quenums']
    query = request.data
    app.logger.debug(query)
    # colect questions start with query
    qlist = [etr['question'] for etr in quenums if query in str(etr['question']).lower()]
    # max 20
    qlist = qlist[0:min(len(qlist),20)]
    send_data = {}
    send_data['result'] = 'ok'
    send_data['qlist'] = qlist
    return jsonify(send_data)

@app.route('/initsearch/')
def initsearch():
    global dataList
    quenums = dataList['quenums']
    # collect first words
    words1st = [str.split(str(etr['question']).lower())[0] for etr in quenums if len(etr['question']) > 0]
    seen = set()
    seen_add = seen.add
    unique_1st_words = [x for x in words1st if not (x in seen or seen_add(x))] 
    send_data = {}
    send_data['unique_1st_words'] = unique_1st_words
    return jsonify(send_data)

@app.route('/getquestions/')
def getquestions():
    global dataList
    sidx = dataList['queidx']
    eidx = min(sidx+dataList['quebatch'], len(dataList['quenums']))
    send_data = {}
    send_data['quenums'] = dataList['quenums'][sidx:eidx]
    return jsonify(send_data)

@app.route('/getnextquestions/')
def getnextquestions():
    global dataList
    quenums = dataList['quenums']
    curidx = dataList['queidx']
    batchsz = dataList['quebatch']
    if curidx + batchsz > len(quenums):
        dataList['queidx'] = 0
    else:
        dataList['queidx'] = curidx + batchsz
    send_data = {}
    sidx = dataList['queidx']
    eidx = min(sidx+dataList['quebatch'], len(quenums))
    send_data['quenums'] = quenums[sidx:eidx]
    return jsonify(send_data)

@app.route('/getprevquestions/')
def getprevquestions():
    global dataList
    quenums = dataList['quenums']
    curidx = dataList['queidx']
    batchsz = dataList['quebatch']
    if curidx == 0:
        dataList['queidx'] = len(quenums)-(batchsz- (len(quenums) % batchsz))
    else:
        dataList['queidx'] = curidx - batchsz
    send_data = {}
    sidx = dataList['queidx']
    eidx = min(sidx+dataList['quebatch'], len(quenums))
    send_data['quenums'] = quenums[sidx:eidx]
    return jsonify(send_data)

@app.route('/getnextdata/')
def getnextdata():
    global dataList
    visres = dataList['visres']
    curidx = dataList['visidx']
    batchsz = dataList['visbatch']
    if curidx + batchsz > len(visres):
        dataList['visidx'] = 0
    else:
        dataList['visidx'] = curidx + batchsz
    send_data = {}
    sidx = dataList['visidx']
    eidx = min(sidx+dataList['visbatch'],len(visres))
    send_data['visres'] = visres[sidx:eidx]
    return jsonify(send_data)

@app.route('/getprevdata/')
def getprevdata():
    global dataList
    visres = dataList['visres']
    curidx = dataList['visidx']
    batchsz = dataList['visbatch']
    if curidx == 0:
        dataList['visidx'] = len(visres)-(batchsz- (len(visres) % batchsz))
    else:
        dataList['visidx'] = curidx - batchsz
    send_data = {}
    sidx = dataList['visidx']
    eidx = min(sidx+dataList['visbatch'],len(visres))
    send_data['visres'] = visres[sidx:eidx]
    return jsonify(send_data)

@app.route('/getvisdata/')
def getvisdata():
    global dataList
    visres = dataList['visres']
    send_data = {}
    sidx = dataList['visidx']
    eidx = min(sidx+dataList['visbatch'],len(visres))
    send_data['visres'] = visres[sidx:eidx]
    return jsonify(send_data)

@app.route('/getvispage/')
def getvispage():
    global dataList
    is_item = dataList['visable']
    if is_item == False:
        return redirect(url_for('index'))
    app.logger.debug('getvispage')
    visres=dataList['visres']
    few_res = visres[0:10]

    return render_template('result.html',results=few_res, is_item=is_item)

@app.route('/getdata/')
def getdata():
    global i
    app.logger.debug('getdata')
    resultData = dataList['res']
    new_dict = {1:i, 2:'bec', 3:'dfe'}

    return jsonify(dataList)

def constructVisRes():
    global dataList
    visres = copy.deepcopy(dataList['que']['data']['questions'])
    preds =  {etr['question_id']:etr['answer'] for etr in dataList['res']['data']}
    dtype = dataList['que']['data']['data_subtype']
    if dtype == 'test-dev2015':
        dtype = 'test2015'
    imgpath = 'static/images/%s/COCO_%s_%012d.jpg'
    stdqididx = {}
    for i, etr in enumerate(visres):
        stdqididx[etr['question_id']] = i
        etr['prediction'] = preds[etr['question_id']]
        etr['imgpath'] = imgpath % (dtype,dtype,etr['image_id'])
        if dataList['evaluable']:
            ann = dataList['vqa'].loadQA([etr['question_id']])[0]
            etr['multiple_choice_answer'] = ann['multiple_choice_answer']
            etr['answers'] = ann['answers']
            etr['question_type'] = ann['question_type']
            etr['answer_type'] = ann['answer_type']
    dataList['stdqididx'] = stdqididx 
    dataList['stdres'] = visres
    dataList['visres'] = dataList['stdres']
    dataList['visidx'] = 0
    dataList['visbatch'] = 10

def constructQuestions():
    global dataList
    questions = {}
    quescore = {}
    for q in dataList['que']['data']['questions']:
        if not questions.has_key(q['question']):
            questions[q['question']] = []
        questions[q['question']].append(q['question_id'])
        if dataList['evaluated']:
            if not quescore.has_key(q['question']):
                quescore[q['question']]=0
            quescore[q['question']] += dataList['vqaEval'].evalQA[q['question_id']]

    que_nums = {k:len(v) for (k,v) in questions.iteritems()}
    que_nums = sorted(que_nums.items(), key=operator.itemgetter(1), reverse=True)
    dict_que_nums = []
    for e in que_nums:
        etr = {}
        etr['question'] = e[0]
        etr['occurrence'] = e[1]
        if dataList['evaluated']:
           etr['score'] = quescore[e[0]] / e[1]
        dict_que_nums.append(etr)
    dataList['qidperque'] = questions
    dataList['quenums'] = dict_que_nums
    dataList['queidx'] = 0
    dataList['quebatch'] = 50

@app.route('/visquestion/<qidx>')
def visquestion(qidx):
    global dataList
    qidx = int(qidx)
    app.logger.debug(qidx)
    q = dataList['quenums'][dataList['queidx']+qidx]
    app.logger.debug(q['question'])
    qids = dataList['qidperque'][q['question']]
    dataList['visres'] = []
    for qid in qids:
       dataList['visres'].append(dataList['stdres'][dataList['stdqididx'][qid]])
    dataList['visidx'] = 0
    dataList['visbatch'] = 10 
    send_data = {}
    visres = dataList['visres']
    sidx = dataList['visidx']
    eidx = min(sidx+dataList['visbatch'],len(visres))
    send_data['visres'] = visres[sidx:eidx]
    return jsonify(send_data)

@app.route('/showquestion', methods=['POST'])
def showquestion():
    global dataList
    question = request.data
    app.logger.debug(question)
    qids = dataList['qidperque'][question]
    dataList['visres'] = []
    for qid in qids:
       dataList['visres'].append(dataList['stdres'][dataList['stdqididx'][qid]])
    dataList['visidx'] = 0
    dataList['visbatch'] = 10 
    visres = dataList['visres']
    sidx = dataList['visidx']
    eidx = min(sidx+dataList['visbatch'],len(visres))

    send_data = {}
    send_data['visres'] = visres[sidx:eidx]
    return jsonify(send_data)

def checkQAPair():
    global dataList 
    # existence
    if len(dataList['que']['data']) == 0 or \
       len(dataList['ann']['data']) == 0:
        return False
    # number of entries
    if dataList['que']['data']['data_subtype'] != \
       dataList['ann']['data']['data_subtype']:
        return False
    # question id
    ann_list = dataList['ann']['data']['annotations']
    que_list = dataList['que']['data']['questions']
    ann_qids = [etr['question_id'] for etr in ann_list]
    que_qids = [etr['question_id'] for etr in que_list]
    if set(ann_qids) != set(que_qids):
        return False
    return True


def checkVisPrepared():
    global dataList
    # existence
    if len(dataList['res']['data']) == 0 or \
       len(dataList['que']['data']) == 0:
        return False
    # number of entries
    if len(dataList['res']['data']) != len(dataList['que']['data']['questions']):
        return False
    # question id
    res_list = dataList['res']['data']
    que_list = dataList['que']['data']['questions']
    res_qids = [entry['question_id'] for entry in res_list]
    que_qids = [entry['question_id'] for entry in que_list]
    if set(res_qids) != set(que_qids):
        return False
    return True


@app.route('/')
def index():
    global dataList
    app.logger.debug('index')
    state = {}
    state['res_fn']=dataList['res']['fn']
    state['que_fn']=dataList['que']['fn']
    state['ann_fn']=dataList['ann']['fn']
    state['scores_fn']=dataList['scores']['fn']
    state['score_loadstate']=dataList['scores']['loadstate']
    state['evalres_fn']=dataList['evalres']['fn']
    state['evalres_loadstate']=dataList['evalres']['loadstate']
    state['res_loaded']=dataList['res']['loaded']
    state['que_loaded']=dataList['que']['loaded']
    state['ann_loaded']=dataList['ann']['loaded']
    state['visable']=dataList['visable']  
    state['evaluable']=dataList['evaluable']
    state['evaluated']=dataList['evaluated']
    state['qamatch'] = dataList['qamatch']
    state['adddir']=dataList['adddir']   

    return render_template('index.html', state=state)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost', \
       help='Host ip address for running VQA browser')
    parser.add_argument('--port', default=8888, type=int, \
       help='Port number')
    args = parser.parse_args()
    params = vars(args) # conver to ordinary dict
    print json.dumps(params, indent = 2)

    app.run(threaded=True, host=params['host'], port=params['port'])
