import spacy
nlp = spacy.load("en_core_web_sm")
KEEP_POS = {"NOUN", "PROPN", "VERB", "ADJ"}

def compress_text(text: str) -> str:
    doc = nlp(text)
    kept = []
    for token in doc:
        if token.pos_ in KEEP_POS and not token.is_stop:
            kept.append(token.lemma_)
    return " ".join(kept)