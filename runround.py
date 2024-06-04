# Description: 该脚本演示了如何使用轮换字典对文本中的实体进行替换，以保护隐私。
from collections import defaultdict
import random
from faker import Faker
from runfaker import usefaker
from pii import pii_batch
import os
import json
from highlight import highlight_words
def configure_rotation_dict(texts, pii_module,batch_size,entity_results=None):#输入文本s，选择模型，字典大小
    if entity_results is None:#如果没有实体结果，调用pii_batch
        entity_results = pii_batch(texts, pii_module)#预测实体
    #有实体结果说明使用batch调用
    entity_dict = defaultdict(list)  # 创建一个字典，键是实体类型，值是实体文本列表
    for idx, entities in enumerate(entity_results):  # 遍历每个文本的实体结果
        for entity in entities:
            if len(entity_dict[entity[3]]) >=batch_size:#创建字典大小
                continue
            else:
                entity_dict[entity[3]].append(entity[2])  # 将实体文本添加到对应的实体类型列表中

    # 对每种类型的实体列表进行随机打乱
    for key in entity_dict.keys():
        random.shuffle(entity_dict[key])
    
    return entity_dict

def load_rotation_dict(file_path='rotation_dict.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            rotation_dict = json.load(file)
            # JSON keys are strings, convert them back to correct types
            rotation_dict = {k: v for k, v in rotation_dict.items()}
            return rotation_dict
    return None

def pseround(texts, entity_results,rotation_dict_file='rotation_dict.json'):
    
    rotation_dict = load_rotation_dict(rotation_dict_file)
    if rotation_dict is None:
        raise FileNotFoundError("没有检测到字典文件，请先配置字典")
    masked_texts = []  # 存储替换后的文本
    new_offsets = []  # 存储新的实体位置信息
    for text, entities in zip(texts, entity_results):  # 遍历每个文本和对应的实体结果
        masked_text = text
        offset = 0
        entity_offsets = []

        for entity in entities:
            start = entity[0] + offset
            end = entity[1] + offset
            entity_text = entity[2]  # 实体文本
            entity_type = entity[3]  # 实体类型

            # 从轮换字典中获取替换项
            if rotation_dict[entity_type]:
                replacement = rotation_dict[entity_type].pop(0)
                if replacement == entity_text:
                    if rotation_dict[entity_type]:  # 再次尝试弹出一个不同的元素
                        replacement = rotation_dict[entity_type].pop(0)
                        rotation_dict[entity_type].append(entity_text)
                    else:  # 如果轮换字典为空，使用faker生成伪数据
                        replacement = usefaker(entity_text, entity_type)
            else:
                # 如果轮换字典为空，使用faker生成伪数据
                replacement = usefaker(entity_text, entity_type)

            masked_text = masked_text[:start] + replacement + masked_text[end:]
            new_end = start + len(replacement)
            entity_offsets.append((start, new_end, entity_type))
            offset += len(replacement) - len(entity_text)

        masked_texts.append(masked_text)
        new_offsets.append(entity_offsets)

    return masked_texts, new_offsets

def myrunround(texts,entity_results):
    highlight_texts=[]
    masked_texts, updated_offsets = pseround(texts, entity_results)
    for idx, (text, offsets) in enumerate(zip(masked_texts, updated_offsets)):
        highlighted_text = highlight_words(text, offsets)
        highlight_texts.append(highlighted_text)
    return highlight_texts
if __name__ == '__main__':
        # 示例文本
        texts = ["John Doe lives at 1234 Elm Street.", "Contact Jane at jane.doe@example.com or 555-1234."]
        entity_results = [
            [(0, 8, "John Doe", "PERSON"), (18, 32, "1234 Elm Street", "LOC")],
            [(8, 12, "Jane", "PERSON"), (16, 35, "jane.doe@example.com", "CODE"), (39, 47, "555-1234", "CODE")]
        ]

        # 配置轮换字典并保存到文件
        rotation_dict = configure_rotation_dict(texts, batch_size=10, results=entity_results)

        # 进行替换
        masked_texts, new_offsets = replace_entities(texts, entity_results)

        for idx, text in enumerate(masked_texts):
            print(f"Anonymized Text {idx}:\n{text}")