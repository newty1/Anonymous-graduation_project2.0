def highlight_words(text, offsets):
    label_colors = {
    'PERSON': 'red',
    'CODE': 'blue',
    'LOC': 'green',
    'ORG': 'orange',
    'DEM': 'purple',
    'DATETIME': 'brown',
    'QUANTITY': 'pink',
    'MISC': 'gray'
    }
    highlighted_text = ""
    last_index = 0
    for start, end, label in offsets:
        highlighted_text += text[last_index:start]
        color = label_colors.get(label, "black")  # Default to black if label not found
        highlighted_text += f'<span style="color: {color}; text-decoration: underline;">{text[start:end]}</span>'
        last_index = end
    highlighted_text += text[last_index:]
    return highlighted_text
def transform_entity_results(entity_results):#将模型预测格式转化为(开始，结束，预测)
    transformed_results = []
    for entities in entity_results:
        offsets = [(start, end, label) for start, end, _, label in entities]
        transformed_results.append(offsets)
    return transformed_results
    highlighted_text = ""
    last_index = 0
    for start, end, label in offsets:
        highlighted_text += text[last_index:start]
        color = label_colors.get(label, "black")  # Default to black if label not found
        highlighted_text += f'<span style="color: {color}; text-decoration: underline;">{text[start:end]}</span>'
        last_index = end
    highlighted_text += text[last_index:]
    return highlighted_text