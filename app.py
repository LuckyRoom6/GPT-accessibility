import openai
from bottle import *
from bs4 import BeautifulSoup
from utils.aria_helper import generate_aria_tags_for_elements
from utils.token_calculator import count_tokens
import json
import markdown
import time

# APIキーとエンドポイントURLの設定
openai.api_key = api_key
openai.api_base = 'https://api.openai.com/v1'

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
        aria_tags = generate_aria_tags_for_elements(html_content)

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

        if not image_sources:
            alt_message = "すべての画像にaltタグが設定されています。"
        else:
            for src in image_sources:
                description = generate_image_description(src)
                image_descriptions.append({'src': src, 'description': description})
            alt_message = None

        response.content_type = 'application/json'
        return json.dumps({
            'description': description_html,
            'aria_tags': aria_tags,
            'images_without_alt': image_descriptions,
            'alt_message': alt_message
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
    for attempt in range(3):
        try:
            response = openai.ChatCompletion.create(
                model='gpt-4o-mini',
                messages=[system] + [message('user', text)]
            )
            return response.choices[0].message['content']
        except openai.error.APIConnectionError as e:
            if attempt < 2:
                time.sleep(2)
                continue
            else:
                raise e

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
    openai.api_key = api_key
    prompt = f"以下の画像URLの内容を説明してください.さらにこの画像のAltタグを簡潔で分かりやすく生成してください: {image_url}"
    response = openai.ChatCompletion.create(
        model='gpt-4o-mini',
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

# run localhost
try:
    run(host='127.0.0.1', port=8000, reloader=True)
except KeyboardInterrupt:
    pass
