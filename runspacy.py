import re
import spacy
from spacy.tokens import Span
import tqdm
from highlight import highlight_words


def extract_entities(texts):
    # 加载英文Spacy模型
    nlp = spacy.load("en_core_web_sm")

    # 自定义CODE匹配模式
    code_patterns = [
        r"\b\+?\d{1,2}?[\s-]?\(?0\d{3,4}\)?\s?\d{3,4}[-\s]?\d{3,4}\b",  # 欧洲电话号码格式
        r"\b\d{3}-\d{2}-\d{4}\b",  # 社会保险号格式 (XXX-XX-XXXX)
        r"\b[a-zA-Z]{2}\d{5}\b|\b\d{7}\b",  # 车牌号格式 (AA12345 或 1234567)
        r"\b[a-zA-Z]{1,2}\d{7}\b",  # 护照号格式 (A1234567 或 AA1234567)
        r"\b\d{9}\b",  # 9位数字码
        r"\b[a-zA-Z]\d{8}\b",  # 1个字母+8位数字

        # 美国
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # 美国电话号码格式
        r"\b\d{3}-\d{2}-\d{4}\b",  # 社会保险号格式 (XXX-XX-XXXX)
        r"\b[a-zA-Z]{2}\d{6}\b",  # 护照号格式 (A1234567 或 AA1234567)
        r"\b[A-Z]{3}\d{3}\b",  # 车牌号格式 (ABC123)

        # 英国
        r"\b\+?\d{1,2}?[\s-]?\(?0\d{3,4}\)?\s?\d{3,4}[-\s]?\d{3,4}\b",  # 欧洲电话号码格式
        r"\b[A-Z]{2}\d{6}[A-Z]\b",  # 社会保险号格式 (NIN)
        r"\b[A-Z]{2}\d{6}\b",  # 护照号格式 (AB123456)
        r"\b[A-Z]{2}\d{2} [A-Z]{3}\b",  # 车牌号格式 (AB12 CDE)

        # 法国
        r"\+\d{2} \d{1,2} \d{2} \d{2} \d{2} \d{2}",  # 法国电话号码格式
        r"\b[A-Z]{2}\d{6}\b",  # 护照号格式 (AB123456)
        r"\b[A-Z]{2}-\d{3}-[A-Z]{2}\b",  # 车牌号格式 (AA-123-AA)

        # 德国
        r"\+\d{2} \d{2,5} \d{9,11}",  # 欧洲电话号码格式
        r"\b\d{10}\b",  # 社会保险号格式 (Personalausweisnummer)
        r"\b[A-Z]{2}\d{6}\b",  # 护照号格式 (AB123456)
        r"\b[A-Z]{2} \d{5}\b",  # 车牌号格式 (AB 12345)

        # 意大利
        r"\+\d{2} \d{2} \d{6,8}",  # 欧洲电话号码格式
        r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b",  # 社会保险号格式 (Codice Fiscale)
        r"\b[A-Z]{2}\d{6}\b",  # 护照号格式 (AB123456)
        r"\b[A-Z]{2}\d{3}[A-Z]{2}\b",  # 车牌号格式 (AB123CD)

        # 波兰
        r"\+\d{2} \d{2,3} \d{3} \d{2} \d{2}",  # 欧洲电话号码格式
        r"\b\d{11}\b",  # 社会保险号格式 (PESEL)
        r"\b[A-Z]{2}\d{6}\b",  # 护照号格式 (AB123456)
        r"\b[A-Z]{3}\d{4}\b",  # 车牌号格式 (ABC1234)

        # 匈牙利
        r"\+\d{2} \d{1,2} \d{3} \d{3,4}",  # 欧洲电话号码格式
        r"\b\d{6}[A-Z]{2}\b",  # 社会保险号格式 (Tajszám)
        r"\b[A-Z]{2}\d{6}\b",  # 护照号格式 (AB123456)
        r"\b[A-Z]{3}-\d{3}\b",  # 车牌号格式 (ABC-123)

        # 西班牙
        r"\+\d{2} \d{3} \d{2} \d{2} \d{2}",  # 欧洲电话号码格式
        r"\b\d{8}[A-Z]\b",  # 社会保险号格式 (DNI)
        r"\b[A-Z]{2}\d{6}\b",  # 护照号格式 (AB123456)
        r"\b\d{4}-[A-Z]{3}\b",  # 车牌号格式 (1234-ABC)

        # 土耳其
        r"\+\d{2} \d{3} \d{3} \d{2} \d{2}",  # 欧洲电话号码格式
        r"\b\d{11}\b",  # 社会保险号格式 (TC Kimlik No)
        r"\b[A-Z]{2}\d{6}\b"  # 护照号格式
    ]
    results = []
    for text in texts:
        doc = nlp(text)
        entities = []
        for ent in doc.ents:
            if ent.label_ in {"PERSON", "LOC", "ORG"}:
                entities.append((ent.start_char, ent.end_char, ent.label_))
        for pattern in code_patterns:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                entities.append((start, end, "CODE"))
        results.append(entities)
    return results

def myrunspacy(texts):
    entities_info = extract_entities(texts)
    highlighted_texts = []
    for text, entities in zip(texts, entities_info):
        highlighted_texts.append(highlight_words(text, entities))
    return highlighted_texts

if __name__ == "__main__":
    # 示例调用
    texts = [
        "John Doe works at OpenAI in San Francisco. His phone number is +1-800-555-1234.",
        "Jane Smith's passport number is A1234567 and she lives in London."
    ]

    entities_info = extract_entities(texts)
    for text, entities in zip(texts, entities_info):
        print(highlight_words(text, entities, label_colors))

