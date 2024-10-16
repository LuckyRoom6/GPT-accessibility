from bs4 import BeautifulSoup

def generate_aria_tags_for_elements(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    aria_tags = []
    
    # インタラクティブ要素に対するARIAタグの提案
    interactive_elements = soup.find_all(['img', 'button', 'a', 'input'])
    for elem in interactive_elements:
        # ARIA属性やroleが設定されていない場合のみ抽出
        if not any(attr in elem.attrs for attr in ['aria-label', 'aria-labelledby', 'role']):
            # 要素の情報を特定するための情報を追加
            element_info = str(elem)[:100]  # 要素のHTMLの一部を取得（100文字以内）
            
            if elem.name == 'button':
                aria_tags.append({
                    'element': 'button',
                    'info': element_info,
                    'suggested_aria_tag': 'role="button" aria-label="ボタンの機能を説明してください。"'
                })
            # 入力フィールドの場合のARIA属性の提案
            elif elem.name == 'input':
                aria_tags.append({
                    'element': 'input',
                    'info': element_info,
                    'suggested_aria_tag': 'role="textbox" aria-label="入力フィールドの説明を追加してください。"'
                })
    
    return aria_tags
