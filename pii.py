import spacy
import flair
from runrob import myrunrob,predict_entities_roberta
from runbert import myrunbert,predict_entities_bert
from runlong import myrunlong,  predict_entitieslongformer
from runflair import myrunflair
from runspacy import myrunspacy
def pii_single(texts, model):#选择模型 处理单个文本，返回单个高亮文本
    if model == 'bert':
       model_path='/root/change/tflask/model/mybert_model.pt'
       piitexts=myrunbert(texts,model_path)
       return piitexts[0]#单个处理返回第一个高亮文本
    elif model == 'longformer':
       model_path='/root/change/tflask/model/mylong_model.pt'
       piitexts=myrunlong(texts,model_path)
       return piitexts[0]
    elif model == 'roberta':
        model_path='/root/change/tflask/model/myrob_model.pt'
        piitexts=myrunrob(texts,model_path)
        return piitexts[0]#单个处理返回第一个高亮文本
    elif model == 'flair':
        piitexts=myrunflair(texts)
        return piitexts[0]#单个处理返回第一个高亮文本
    elif model == 'spacy':
        piitexts=myrunspacy(texts)
        return piitexts[0]#单个处理返回第一个高亮文本
    elif model == 'merge':#投票算法待续
        pass
        return 
    else:
        raise ValueError(f"Invalid model name: {model}")
def pii_batch(texts, model):#处理多个文本，返回预测结果，不高亮
    if model == 'bert':
        model_path='/root/change/tflask/model/mybert_model.pt'
        entity_results =predict_entities_bert(texts, model_path) #预测模型
        return entity_results

    elif model == 'longformer':
        model_path='/root/change/tflask/model/mylong_model.pt'
        entity_results =predict_entitieslongformer(texts, model_path)
        return entity_results
    elif model == 'roberta':
        model_path='/root/change/tflask/model/myrob_model.pt'
        entity_results =predict_entities_roberta(texts, model_path) #预测模型
        return entity_results
    elif model == 'flair':#使用没有意义
       pass
       return
    elif model == 'spacy':
        pass
        return
    elif model == 'merge':#投票算法待续
        pass
        return 
    else:
        raise ValueError(f"Invalid model name: {model}")
