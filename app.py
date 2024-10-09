import openai
from bottle import *
from bs4 import BeautifulSoup
from utils.token_calculator import count_tokens
from bottle import static_file
import json
import markdown
import time
import re

# APIキーとエンドポイントURLの設定
api_key = 'jstmHGqjkR5ak8Zq5LaRsI8VwsVMpyjOgoKn9W3OzmCy6dRS8MLbfMe1iufAxsmNCVSwtIO7TXwNXMIAEbGUUxA'
openai.api_key = api_key
openai.api_base = 'https://api.openai.iniad.org/api/v1'

BaseRequest.MEMFILE_MAX = 1024 * 1024

# --- CORSへの対応
@hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'

@route('/', method='OPTIONS')
def response_for_options(**kwargs):
    return {}

# --- CORSへの対応ここまで

# トークン制限を設定
TOKEN_LIMIT = 2000  # 最大トークン数

@post('/')
def index():
    try:
        html_content = request.json['page']
        page_text = html_to_text(html_content)

        # ARIAロールの提案
        elements_without_aria = extract_elements_without_aria(html_content)
        aria_role_suggestions = suggest_aria_roles(elements_without_aria)

        # トークン数が制限を超えた場合のエラーハンドリング
        if count_tokens(page_text) > TOKEN_LIMIT:
            response.content_type = 'application/json'
            response.status = 400
            return json.dumps({'error': 'Request exceeds the token limit.'})

        description_md = gpt(page_text)
        description_html = markdown.markdown(description_md)

        # `alt` タグがない画像を抽出して説明文を生成
        image_sources = extract_images_without_alt(html_content)
        image_descriptions = []
        for src in image_sources:
            description = generate_image_description(src)
            image_descriptions.append({'src': src, 'description': description})

        response.content_type = 'application/json'
        return json.dumps({
            'description': description_html,
            'aria_role_suggestions': aria_role_suggestions,
            'images_without_alt': image_descriptions  # `alt` タグがない画像とその説明文
        }, ensure_ascii=False)
    except openai.error.APIConnectionError as e:
        response.status = 500
        return json.dumps({'error': 'API connection error', 'details': str(e)})
    except Exception as e:
        response.status = 500
        return json.dumps({'error': 'Internal server error', 'details': str(e)})

@route('/favicon.ico')
def favicon():
    return ''

@route('/', method='GET')
def get_request():
    return "Server is running. Please use POST method."

# ChatGPTのAPIを使う準備
def message(role, text):
    return {'role': role, 'content': text}

system = message('system', """
以下はあるウェブページのHTML、JavaScript、およびCSSの内容です。この内容を元に最新のWCAG 2.2ガイドラインに基づいてアクセシビリティの評価を行い、発見されたアクセシビリティの問題について詳細なレポートと改善提案を提供してください。特に、以下の点に留意してください：

1. ARIAタグが不足している箇所について具体的なタグの提案を行ってください。
2. 画像に対して適切なARIAタグを提案してください。

内容は以下の通りです：

### HTMLコンテンツ\n{HTML_CONTENT}\n\n### JavaScriptコンテンツ\n{JS_CONTENT}\n\n### CSSコンテンツ\n{CSS_CONTENT}\n\n評価とWCAG 2.2に基づく改善提案をお願いします。
""")

def gpt(text):
    for attempt in range(3):  # 最大3回リトライ
        try:
            response = openai.ChatCompletion.create(
                model='gpt-4o-mini',  # モデル名を必要に応じて変更
                messages=[system] + [message('user', text)]
            )
            return response.choices[0].message['content']
        except openai.error.APIConnectionError as e:
            if attempt < 2:  # 最大リトライ回数未満ならリトライ
                time.sleep(2)  # 2秒待機
                continue
            else:
                raise e  # 最大リトライ回数を超えた場合は例外を再度スロー

# HTMLファイルの加工
def html_to_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    return '\n'.join(soup.stripped_strings)

# 画像の `alt` タグがないものを抽出する関数
def extract_images_without_alt(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    images = soup.find_all('img', alt=False)  # `alt` がない、もしくは空の画像を抽出
    image_sources = [img['src'] for img in images if 'src' in img.attrs]
    return image_sources

# GPTを使って画像の説明文を取得する関数
def generate_image_description(image_url):
    prompt = f"以下の画像URLの内容を説明してください.さらにこの画像のAltタグを生成してください: {image_url}"
    response = openai.ChatCompletion.create(
        model='gpt-4o',
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        },
                    },
                ],
            }
        ],
        max_tokens=1200,
    )
    return response.choices[0].message.content

# ARIAロールがない要素を抽出する関数
def extract_elements_without_aria(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    elements_without_aria = []

    # セマンティックな要素のリスト
    semantic_elements = ['header', 'nav', 'footer', 'main', 'section', 'article', 'aside']

    for element in semantic_elements:
        tags = soup.find_all(element)
        for tag in tags:
            if not tag.has_attr('role'):  # 既にroleがない場合のみ追加
                elements_without_aria.append(tag)

    return elements_without_aria

# 要素ごとのARIAロールを提案する関数
def suggest_aria_roles(elements):
    role_suggestions = []

    for element in elements:
        if element.name == 'nav':
            role_suggestions.append({'element': str(element), 'suggested_aria_role': 'role="navigation"'})
        elif element.name == 'header':
            role_suggestions.append({'element': str(element), 'suggested_aria_role': 'role="banner"'})
        elif element.name == 'footer':
            role_suggestions.append({'element': str(element), 'suggested_aria_role': 'role="contentinfo"'})
        elif element.name == 'main':
            role_suggestions.append({'element': str(element), 'suggested_aria_role': 'role="main"'})
        elif element.name == 'section':
            role_suggestions.append({'element': str(element), 'suggested_aria_role': 'role="region"'})
        elif element.name == 'article':
            role_suggestions.append({'element': str(element), 'suggested_aria_role': 'role="article"'})
        elif element.name == 'aside':
            role_suggestions.append({'element': str(element), 'suggested_aria_role': 'role="complementary"'})
    
    return role_suggestions

# run localhost
try:
    run(host='127.0.0.1', port=8000, reloader=True)
except KeyboardInterrupt:
    pass
