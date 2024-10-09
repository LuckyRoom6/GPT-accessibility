from bs4 import BeautifulSoup
from .image_recognition import recognize_image

def generate_aria_tags_for_images(html):
    soup = BeautifulSoup(html, 'html.parser')
    images = soup.find_all('img')
    
    aria_tags = []
    for img in images:
        if not img.get('alt'):
            # 画像認識
            description = recognize_image(img.get('src'))
            aria_tags.append({
                'img': img.get('src'),
                'description': description,
                'suggested_aria_tag': f'Provide a meaningful description for this image: {description}'
            })
    
    return aria_tags