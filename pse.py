from runbert import predict_entities_bert
from runlong import predict_entitieslongformer
from runrob import predict_entities_roberta
from runflair import myrunflair
from runspacy import myrunspacy
from runfaker import myrunfaker,psefaker
from rundirct import myrundirct,psedirct
from runround import myrunround,pseround,configure_rotation_dict
import json
def pse_single(texts,model1,model2):#文本，pii识别模型，假名化方法
    #先判断model1是 bert还是longformer还是roberta
    predict_results=[]#pii识别结果
    if model1 == 'bert':
        model_path='/root/change/tflask/model/mybert_model.pt'
        predict_results=predict_entities_bert(texts,model_path)
    elif model1 == 'longformer':
        model_path='/root/change/tflask/model/mylong_model.pt'
        predict_results=predict_entitieslongformer(texts,model_path)
    elif model1 == 'roberta':
        model_path='/root/change/tflask/model/myrob_model.pt'
        predict_results=predict_entities_roberta(texts,model_path)
    elif model1 == 'flair':
        piitexts=myrunflair(texts)
    elif model1 == 'spacy':
        piitexts=myrunspacy(texts)
    elif model1 == 'merge':
        bert_entities = myrunbert(texts)
        longformer_entities = myrunlong(texts)
        roberta_entities = myrunrob(texts)
    else:
        raise ValueError(f"Invalid model name: {model1}")
    #再判断model2是哪个假名化方法 是直接替换，还是faker库，还是轮换法
    if model2 == '直接替换':
        psetests=myrundirct(texts, predict_results)
        return psetests[0]
    elif model2 == 'faker库':
        psetests=myrunfaker(texts, predict_results)
        return psetests[0]
    elif model2 == '轮换法':
        psetests=myrunround(texts, predict_results)
        return psetests[0]
    else:
        raise ValueError(f"Invalid model name: {model2}")
 
def pse_batch(texts,model2,result_entities):
    if model2=='直接替换':
        psetests,new_offsets=psedirct(texts, result_entities)
        return psetests
    elif model2=='faker库':
        psetests,new_offsets=psefaker(texts, result_entities)
        return psetests
    elif model2=='轮换法':
        batch_size=int(len(texts)/5)#轮换字典大小设置为文本数的五分之一
        rotation_dict=configure_rotation_dict(texts,None,batch_size,result_entities)#配置轮换字典
    
        with open('rotation_dict.json', 'w', encoding='utf-8') as f:
                json.dump(rotation_dict, f, ensure_ascii=False, indent=4)
        #进行替换
        psetests,new_offsets=pseround(texts, result_entities,rotation_dict_file='rotation_dict.json')

        return psetests

    else:
        raise ValueError(f"Invalid model name: {model2}")
