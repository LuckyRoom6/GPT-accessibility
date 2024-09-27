def count_tokens(text):
    # OpenAI APIのトークン計算方法を反映させる必要があります。
    # ここでは単純に単語数でトークン数を推定しています。
    return len(text.split())
