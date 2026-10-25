from config import MAX_MESSAGE_CHARS


def validate_message(value, max_chars=MAX_MESSAGE_CHARS):
    if value is None:
        text = ''
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()

    if not text:
        return text, 'message is required', 400
    if len(text) > max_chars:
        return text, f'message must be {max_chars} characters or fewer', 413
    return text, '', 0
