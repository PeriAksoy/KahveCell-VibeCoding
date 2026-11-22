_TR_TO_ASCII = str.maketrans("ışğüöç", "isguoc")


def fold(text: str) -> str:
    """Arama için metni sadeleştirir: büyük/küçük harf ve Türkçe karakter farkını yok sayar.
    'KIZILAY', 'Kızılay' ve 'kizilay' aynı sonucu verir. (SQLite'ın kendi LIKE'ı Türkçe harflerde bunu yapamaz.)"""
    return text.replace("İ", "i").replace("I", "ı").lower().translate(_TR_TO_ASCII)
