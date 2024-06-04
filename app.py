
import os
import json
import atexit
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from markupsafe import Markup
import highlight
from pii import pii_single,pii_batch
from pse import pse_single,pse_batch
from werkzeug.utils import secure_filename
from runround import configure_rotation_dict

app = Flask(__name__)
#配置上传文件目录
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['BATCH_UPLOAD_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'batch')
app.config['CONFIG_UPLOAD_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'config')
app.config['PROCESSED_FOLDER'] = 'processed'
os.makedirs(app.config['BATCH_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CONFIG_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/process_choice', methods=['POST'])
def process_choice():
    choice = request.form['choice']
    if choice == 'pii':
        return redirect(url_for('pii'))
    elif choice == 'pse':
        return redirect(url_for('pse'))
    elif choice == 'config':
        return redirect(url_for('config'))
    elif choice == 'batch':
        return redirect(url_for('batch'))
    elif choice == 'piifl':
        return redirect(url_for('piifl'))

@app.route('/pii', methods=['GET', 'POST'])
def pii():
    input_text = ''
    dropdown1_value = ''
    output_text1 = ''

    if request.method == 'POST':
        input_text = request.form['input_text']
        dropdown1_value = request.form['dropdown1']
        output_text1 = process_Pii(input_text, dropdown1_value)

    return render_template('pii.html', input_text=input_text, dropdown1_value=dropdown1_value, output_text1=Markup(output_text1))

@app.route('/piifl', methods=['GET', 'POST'])
def piifl():
    input_text = ''
    dropdown1_value = ''
    output_text1 = ''

    if request.method == 'POST':
        input_text = request.form['input_text']
        dropdown1_value = request.form['dropdown1']
        output_text1 = process_Pii(input_text, dropdown1_value)

    return render_template('piifl.html', input_text=input_text, dropdown1_value=dropdown1_value, output_text1=Markup(output_text1))

@app.route('/pse', methods=['GET', 'POST'])
def pse():
    input_text = ''
    dropdown2_value = ''
    output_text2 = ''

    if request.method == 'POST':
        input_text = request.form['input_text']
        dropdown1_value = request.form['dropdown1']
        dropdown2_value = request.form['dropdown2']
        output_text2 = process_pse(input_text, dropdown1_value, dropdown2_value)

    return render_template('pse.html', input_text=input_text, dropdown2_value=dropdown2_value, output_text2=Markup(output_text2))

@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        file = request.files['file_input']
        pii_module = request.form['pii_module']
        dictionary_size = int(request.form['dictionary_size'])
       
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['CONFIG_UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # 处理文件，生成轮换字典 读取texts
            with open(file_path, 'r', encoding='utf-8') as f:
                texts = f.readlines()
            rotation_dict = process_configdict(texts, pii_module, dictionary_size)
            # 保存轮换字典为 JSON 文件
            with open('rotation_dict.json', 'w', encoding='utf-8') as f:
                json.dump(rotation_dict, f, ensure_ascii=False, indent=4)

            return jsonify({"message": "配置成功"})

    return render_template('config.html')

@app.route('/batch', methods=['GET', 'POST'])
def batch():
    if request.method == 'POST':
        file = request.files.get('file_input')
        pii_method = request.form.get('pii_method')
        pseudonymization_method = request.form.get('pseudonymization_method')

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['BATCH_UPLOAD_FOLDER'], filename)
            file.save(file_path)
            #读取要处理的文件
            with open(file_path, 'r', encoding='utf-8') as f:
                texts = f.readlines()
            #批量处理后文件
            output_text = process_batch(texts, pii_method, pseudonymization_method)
            processed_file_path = os.path.join(app.config['PROCESSED_FOLDER'], f"processed_{filename}")
            #保存处理后文件
            with open(processed_file_path, 'w', encoding='utf-8') as f:
                output_string = '\n'.join(output_text)
                f.write(output_string)
                
            #提供下载连接
            return redirect(url_for('download_file', filename=f"processed_{filename}"))

    return render_template('batch.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

def process_Pii(input_text, dropdown1_value):
    texts = [input_text]
    return pii_single(texts, dropdown1_value)

def process_piifl(input_text, dropdown1_value):
    texts = [input_text]
    return pii_single(texts, dropdown1_value)

def process_pse(input_text, dropdown1_value, dropdown2_value):
    texts = [input_text]
    return pse_single(texts, dropdown1_value, dropdown2_value)

def process_configdict(texts, pii_module, dictionary_size):
    return configure_rotation_dict(texts, pii_module, dictionary_size)

def process_batch(texts, pii_module, pse_module):
    result_entities = pii_batch(texts, pii_module)
    
    pse_results = pse_batch(texts,pse_module,result_entities)
    return pse_results

def clear_uploads_and_processed():
    # 用户结束访问时清空上传和处理文件夹中的文件
    folders = [app.config['BATCH_UPLOAD_FOLDER'], app.config['CONFIG_UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER']]
    for folder in folders:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

    # 删除特定的 rotation_dict.json 文件，轮换字典文件
    rotation_dict_path = 'rotation_dict.json'
    if os.path.exists(rotation_dict_path):
        try:
            os.remove(rotation_dict_path)
        except Exception as e:
            print(f'Failed to delete {rotation_dict_path}. Reason: {e}')
#网站关闭时清理文件
atexit.register(clear_uploads_and_processed)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
