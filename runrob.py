
from robert_model import Model
from transformers import RobertaTokenizerFast
from data_handling import *
from typing import List, Tuple
from highlight import highlight_words,transform_entity_results
def predict_entities_roberta(texts, model_path):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    label_set = LabelSet(labels=['PERSONMASK', 'CODEMASK', 'LOCMASK', 'ORGMASK',
                                 'DEMMASK', 'DATETIMEMASK', 'QUANTITYMASK', 'MISCMASK'])
    model_name = "roberta-base"
    
    model = Model(
        model=model_name,
        num_labels=len(label_set.ids_to_label.values())
    )
    model.load_state_dict(torch.load(model_path))
    model = model.to(device)
    model.eval()
    tokenizer = RobertaTokenizerFast.from_pretrained(model_name)

    examples = []
    for text in texts:
        encoding = tokenizer(text, add_special_tokens=True, return_offsets_mapping=True)
        examples.append({
            'text': text,
            'encoding': encoding,
            'offset_mapping': encoding['offset_mapping']
        })

    predictions = []
    offsets = []
    tokens = []
    for example in tqdm.tqdm(examples):
        input_ids = torch.LongTensor([example['encoding'].input_ids])
        attention_mask = torch.LongTensor([example['encoding'].attention_mask])
        batch = {'input_ids': input_ids.to(device), 'attention_masks': attention_mask.to(device)}
        with torch.no_grad():
            outputs = model(batch)
            logits = outputs.permute(0, 2, 1)
            preds = logits.argmax(dim=1).squeeze().tolist()
            predictions.append(preds)
            offsets.append(example['offset_mapping'])
            tokens.append(example['encoding'].tokens())

    entity_results = []
    for example_idx, (preds, offsets, tokens) in tqdm.tqdm(enumerate(zip(predictions, offsets, tokens))):
        text = examples[example_idx]['text']
        entities = []
        entity_start = None
        mentionpred = None
        for token_idx, (pred, offset) in enumerate(zip(preds, offsets)):
            token = tokens[token_idx]
            if pred % 2 == 1:  # B-标签
                entity_start = offset
                mentionpred = pred
            elif pred == 0:  # O-标签
                if entity_start is not None:
                    entity_end = offset[0]
                    if entity_end==0:#处理transformer的占位符
                        entity_end=offsets[-2][1]
                    entity_label = label_set.ids_to_label[mentionpred].replace("MASK", "").replace("B-", "")
                    entities.append((entity_start[0], entity_end, text[entity_start[0]:entity_end], entity_label))
                    entity_start = None
        
        # 确保捕获最后一个实体,即使最后一个token是O标签
        if entity_start is not None:
            
            entity_end = offsets[-1][1]  # 最后一个token的结束位置
            entity_label = label_set.ids_to_label[mentionpred].replace("MASK", "").replace("B-", "")
            entities.append((entity_start[0], entity_end, text[entity_start[0]:entity_end], entity_label))
        entity_results.append(entities)
    
    return entity_results

def myrunrob(texts,model_path):
    highlighted_text=[]
    entity_results =predict_entities_roberta(texts, model_path) #预测模型
    transformed_results = transform_entity_results(entity_results)#将模型预测格式转化为(开始，结束，预测)

    for idx, (text, offsets) in enumerate(zip(texts, transformed_results)):
        highlighted_text.append(highlight_words(text, offsets))#返回下划线高亮后的文本
    return highlighted_text 

if __name__ == '__main__':
    texts = ["On 21 February 2020, Italian teacher Ms. Giulia Romano filed an application against Germany (case no. 67890/56)."]
    model_path = "myrob_model.pt"
    entity_results = predict_entities_roberta(texts, model_path)
    transformed_results = transform_entity_results(entity_results)

    for idx, (text, offsets) in enumerate(zip(texts, transformed_results)):
        highlighted_text = highlight_words(text, offsets, label_colors)
        print(f"Highlighted Text {idx}:\n{highlighted_text}")

    entity_results = predict_entities_roberta(texts, model_path)
    for idx, entities in enumerate(entity_results):
            print(f"Text {idx}:")
            for entity in entities:
                print(f"  Entity: {entity[2]} (Start: {entity[0]}, End: {entity[1]}, Label: {entity[3]})")

