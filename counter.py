import tiktoken

def count_tokens(messages: list) -> int:
    encoder = tiktoken.get_encoding("cl100k_base")
    total = 0
    for message in messages:
        total = total + len(encoder.encode(message["content"]))

    return total