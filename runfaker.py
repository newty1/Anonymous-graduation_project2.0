from faker import Faker
from highlight import highlight_words,transform_entity_results

def usefaker(entity_text, label,useregion=None):
    #使用faker根据标签和文本生成假数据
    if useregion!=None:
        fake = Faker(useregion) #根据特定地区生成假数据
    else:
        fake = Faker()
    if label == 'PERSON':
        return fake.name()
    elif label == 'ORG':
        return fake.company()
    elif label == 'LOC':
        return fake.country()
    elif label == 'MISC':
        return fake.word()
    elif label == 'CODE':
        return fake.credit_card_number()
    elif label == 'QUANTITY':
        return str(fake.random_int())
    elif label == 'DATETIME':
        return str(fake.date_time())
    elif label == 'DEM':
        return fake.job()


# 输入 texts，entities[（实体开始，结束，实体文本，实体标签）]
def psefaker(texts, results):
    masked_texts = []
    new_offsets = []
    for text, entities in zip(texts, results):
        masked_text = text
        offset = 0
        entity_offsets = []
        for entity in entities:
            start = entity[0] + offset
            end = entity[1] + offset
            entity_text = entity[2]
            label = entity[3]
            fake_data = usefaker(entity_text, label)
            masked_text = masked_text[:start] + fake_data + masked_text[end:]
            new_end = start + len(fake_data)
            entity_offsets.append((start, new_end, label))
            offset += len(fake_data) - len(entity_text)  # 调整偏移量以适应替换后的字符串长度变化
        masked_texts.append(masked_text)
        new_offsets.append(entity_offsets)
    return masked_texts, new_offsets

def myrunfaker(texts,entity_results):
    highlight_texts=[]
    masked_texts, updated_offsets = psefaker(texts, entity_results)
    for idx, (text, offsets) in enumerate(zip(masked_texts, updated_offsets)):
        highlighted_text = highlight_words(text, offsets)
        highlight_texts.append(highlighted_text)
    return highlight_texts

if __name__ == '__main__':
    
    for idx, (text, offsets) in enumerate(zip(masked_texts, updated_offsets)):
        highlighted_text = highlight_words(text, offsets, label_colors)
        print(f"Highlighted Text {idx}:\n{highlighted_text}")
