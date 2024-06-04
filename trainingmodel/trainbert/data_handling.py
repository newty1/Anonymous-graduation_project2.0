from typing_extensions import TypedDict
import torch.nn.functional as F
from typing import List,Any
from transformers import BatchEncoding
from tokenizers import Encoding
import itertools
from torch import nn
from dataclasses import dataclass
from torch.utils.data import Dataset
from transformers import PreTrainedTokenizerFast
import json
import torch
from torch.utils.data.dataloader import DataLoader
from transformers import BertForTokenClassification, AdamW
from transformers import get_linear_schedule_with_warmup
from sklearn.metrics import classification_report
import tqdm
import numpy as np
import matplotlib.pyplot as plt
"""加载和预处理数据"""
device = 'cuda' if torch.cuda.is_available() else 'cpu'

## Adapted from https://www.lighttag.io/blog/sequence-labeling-with-transformers/example

IntList = List[int] # A list of token_ids #别名
IntListList = List[IntList] # A List of List of token_ids, e.g. a Batch


class LabelSet:
    def __init__(self, labels: List[str]):
        self.labels_to_id = {}#将标签映射到唯一的整数标识符。
        self.ids_to_label = {}#将整数标识符映射回相应的标签。
        self.labels_to_id["O"] = 0
        self.ids_to_label[0] = "O"
        num = 0 
        for _num, (label, s) in enumerate(itertools.product(labels, "BI")):
            num = _num + 1
            l = f"{s}-{label}"
            self.labels_to_id[l] = num
            self.ids_to_label[num] = l

    def get_aligned_label_ids_from_annotations(self, tokenized_text, annotations, ids):
        raw_labels, identifier_types, offsets, ids = align_tokens_and_annotations_bilou(tokenized_text, annotations, ids)
        return list(map(self.labels_to_id.get, raw_labels)), identifier_types, offsets, ids
        #分词后tokenized_text
@dataclass
class TrainingExample:
    input_ids: IntList
    attention_masks: IntList
    labels: IntList
    identifier_types: IntList
    offsets:IntList

class Dataset(Dataset):
    #继承pyTorch的Dataset类,预处理、标注对齐、分批次处理
    def __init__(
        self,
        data: Any,
        label_set: LabelSet,
        tokenizer: PreTrainedTokenizerFast,
        tokens_per_batch=32,
        window_stride=None,
    ):
        self.label_set = label_set
        if window_stride is None:
            self.window_stride = tokens_per_batch #步幅
        self.tokenizer = tokenizer
    
        self.texts = []
        self.annotations = []
        ids = []

        for example in data:
            self.texts.append(example["text"])#保存语料的文本
            self.annotations.append(example["annotations"])#保存整个注释
            ids.append(example['doc_id'])#保存语料的id

        ###TOKENIZE All THE DATA
        tokenized_batch = self.tokenizer(self.texts, add_special_tokens=True, return_offsets_mapping=True)
        #对所有文本语料进行分词
        ## This is used to keep track of the offsets of the tokens, and used to calculate the offsets on the entity level at evaluation time.
        ## 用于跟踪token的偏移量，并在评估时计算entity的偏移量
        offset_mapping = []#其中包含了每个 token 在原始文本中的偏移信息
        for x,y in zip(ids, tokenized_batch.offset_mapping):
            l = []#用来存储当前文档的偏移信息
            for tpl in y:#tpl是token在原始文本中起始位置和技术位置
                l.append((x, tpl[0], tpl[1]))#三元组 起始id 开始位置，结束位置
            offset_mapping.append(l)

        ###ALIGN LABELS ONE EXAMPLE AT A TIME
        ##对每个样本进行标签对齐操作，将标注信息与分词后的文本对齐
        aligned_labels = []#存储标签对齐后结果
        identifiers = []#表示符类型
        o = []#其他输出信息
        for ix in range(len(tokenized_batch.encodings)):#遍历所有分词
            encoding = tokenized_batch.encodings[ix]
            raw_annotations = self.annotations[ix]#原始标注信息
            aligned, identifier_types, outs, ids= label_set.get_aligned_label_ids_from_annotations(
                encoding, raw_annotations, ids
            )#对齐后的标签序列，标识符类型，其他输入信息，文档ID列表
            aligned_labels.append(aligned)
            identifiers.append(identifier_types)
            o.append(outs)
        ###END OF LABEL ALIGNMENT

        ###MAKE A LIST OF TRAINING EXAMPLES.
        self.training_examples: List[TrainingExample] = []
        empty_label_id = "O"
        for encoding, label, identifier_type, mapping  in zip(tokenized_batch.encodings, aligned_labels, identifiers, offset_mapping):
            length = len(label)  # How long is this sequence
            for start in range(0, length, self.window_stride):
                end = min(start + tokens_per_batch, length)
                padding_to_add = 0
                self.training_examples.append(
                    TrainingExample(
                        # Record the tokens
                        input_ids=encoding.ids[start:end]  # The ids of the tokens 词表
                        + [self.tokenizer.pad_token_id]
                        * padding_to_add,  # padding if needed
                        labels=(
                            label[start:end]
                            + [-1] * padding_to_add  # padding if needed
                        ),
                        attention_masks=(
                            encoding.attention_mask[start:end]#告诉哪些位置是填充的
                            + [0]
                            * padding_to_add  # 0'd attention masks where we added padding
                        ),
                        identifier_types=(identifier_type[start:end]
                            + [-1] * padding_to_add ##Not used 
                        
                        ),
                        offsets=(mapping[start:end]
                            + [-1] * padding_to_add
                        ),

                    )
                )

    def __len__(self):
        return len(self.training_examples)

    def __getitem__(self, idx) -> TrainingExample:

        return self.training_examples[idx]

class TrainingBatch:
    def __getitem__(self, item):
        return getattr(self, item)

    def __init__(self, examples: List[TrainingExample]):
        self.input_ids: torch.Tensor
        self.attention_masks: torch.Tensor
        self.labels: torch.Tensor
        self.identifier_types: List
        self.offsets:List
        input_ids: IntListList = []
        masks: IntListList = []
        labels: IntListList = []
        identifier_types: List = []
        offsets: List = []

        for ex in examples:
            input_ids.append(ex.input_ids)
            masks.append(ex.attention_masks)
            labels.append(ex.labels)
            identifier_types.append(ex.identifier_types)
            offsets.append(ex.offsets)
        self.input_ids = torch.LongTensor(input_ids)
        self.attention_masks = torch.LongTensor(masks)
        self.labels = torch.LongTensor(labels)
        self.identifier_types = identifier_types
        self.offsets = offsets

        self.input_ids = self.input_ids.to(device)
        self.attention_masks = self.attention_masks.to(device)
        self.labels = self.labels.to(device)

def align_tokens_and_annotations_bilou(tokenized: Encoding, annotations, ids):
    tokens = tokenized.tokens
    identifier_types = ["O"] * len(
        tokens
    )#句子的长度个0
    aligned_labels = ["O"] * len(
        tokens
    )
    offsets = ["O"] * len(
        tokens
    )
    for anno in annotations:
        ids.append(anno['id'])
        if anno['label'] != 'NO_MASK':
            annotation_token_ix_set = (
                set()
            )  #需要匿名化的token集合# A set that stores the token indices of the annotation
            for char_ix in range(anno["start_offset"], anno["end_offset"]):

                token_ix = tokenized.char_to_token(char_ix)
                if token_ix is not None:#将token添加到该集合
                    annotation_token_ix_set.add(token_ix)
            last_token_in_anno_ix = len(annotation_token_ix_set) - 1
            for num, token_ix in enumerate(sorted(annotation_token_ix_set)):
                if num == 0:
                    prefix = "B"#该实体的第一个token
                else:
                    prefix = "I"  # We're inside of a multi token annotation
                aligned_labels[token_ix] = f"{prefix}-{anno['label']}"#例如B-person I-person
                identifier_types[token_ix] = anno['identifier_type']
                offsets[token_ix] = {anno['id'] : (anno['start_offset'], anno['end_offset'])}

    return aligned_labels, identifier_types, offsets, ids
