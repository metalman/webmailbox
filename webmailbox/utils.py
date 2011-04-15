import email
try:
    import chardet
except ImportError:
    chardet = None

def decode_text(text):
    text_encoding = None
    if chardet:
        text_encoding = chardet.detect(text)['encoding']
    if not text_encoding:
        text_encoding = 'gb18030'   # default for chinese text
    try:
        return text.decode(text_encoding).encode('utf-8')
    except UnicodeDecodeError:
        return text_encoding

def decode_mail_header(header_string):
    try:
        header_items = email.Header.decode_header(header_string)
        if header_items:
            decoded_header_values = []
            for header_item in header_items:
                item_text, item_encoding = header_item
                if item_encoding:
                    item_text = item_text.decode(item_encoding)
                decoded_header_values.append(item_text)
            return " ".join(decoded_header_values).encode('utf-8')
    except:
        pass

    try:
        return decode_text(header_string)
    except:
        return header_string
