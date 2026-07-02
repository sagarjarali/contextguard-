from compressor import compress_text

samples = [
    "You are a helpful assistant that answers questions politely and in a friendly manner",
    "Please provide a detailed and comprehensive response to the user query",
    "The farmer needs information about the PM Kisan scheme and how to apply for it",
    "You are an extremely helpful, knowledgeable, and friendly AI assistant. Your job is to always respond to the user in a very detailed, thorough, and comprehensive manner while maintaining a polite and professional tone at all times."
]

for s in samples:
    print(f"ORIGINAL : {s}")
    print(f"COMPRESSED: {compress_text(s)}")
    print()