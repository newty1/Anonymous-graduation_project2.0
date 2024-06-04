from highlight import highlight_words,transform_entity_results
def psedirct(texts, results):#直接替换方法,需要对齐文本
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
            PII_placeholder = "****"
            masked_text = masked_text[:start] + PII_placeholder + masked_text[end:]
            new_end = start + len(PII_placeholder)
            entity_offsets.append((start, new_end, label))
            offset += len(PII_placeholder) - len(entity_text)  # 调整偏移量以适应替换后的字符串长度变化
        masked_texts.append(masked_text)
        new_offsets.append(entity_offsets)
    return masked_texts, new_offsets
def myrundirct(texts,entity_results):#将替换后文本转成高亮文本
        highlight_texts=[]
        masked_texts, updated_offsets = psedirct(texts, entity_results)
        for idx, (text, offsets) in enumerate(zip(masked_texts, updated_offsets)):
            highlighted_text = highlight_words(text, offsets)
            highlight_texts.append(highlighted_text)
        return highlight_texts

if __name__ == '__main__':
        # 示例输入
        texts = [
            "John Doe lives at 1234 Elm Street.",
            "Contact Jane at jane.doe@example.com or 555-1234."
        ]
        entity_results = [
            [(0, 8, "John Doe", "PERSON"), (18, 32, "1234 Elm Street", "ADDRESS")],
            [(8, 12, "Jane", "PERSON"), (16, 35, "jane.doe@example.com", "EMAIL"), (39, 47, "555-1234", "PHONE")]
        ]

        # 调用函数
        masked_texts, updated_offsets = pse_pii(texts, entity_results)

        # 打印结果
        for idx, (text, offsets) in enumerate(zip(masked_texts, updated_offsets)):
            print(f"Masked Text {idx}:\n{text}")
            print(f"Offsets {idx}:\n{offsets}")
