from googletrans import Translator

translator = Translator()

def translate(text, source="auto", target="en"):
    try:
        return translator.translate(text, src=source, dest=target).text
    except Exception as e:
        print("TRANSLATION ERROR:", e)
        return text
