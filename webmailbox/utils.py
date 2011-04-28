import email
import mimetypes
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

def _get_cleaned_header_string(s):
    if not isinstance(s, str):
        return s
    cleaned_pieces = []
    for piece in s.split():
        if (piece.startswith('"=?') and piece.endswith('?="')) or \
            (piece.startswith('\'=?') and piece.endswith('?=\'')):
            piece = piece[1:-1]
        cleaned_pieces.append(piece)
    return ' '.join(cleaned_pieces)

def decode_mail_header(header_string):
    header_string = _get_cleaned_header_string(header_string)
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

def unpack_mail(msg, only_headers=False, exclude_headers=True):
    # TODO: headers, msg_text, msg_html, attachments
    msg_text = ""
    msg_html = ""
    if not msg.is_multipart():
        msg_payload = msg.get_payload(decode=True)
        msg_payload = decode_text(msg_payload)
        if msg.get_content_type == 'text/html':
            msg_html = msg_payload
        else:   # text/plain. or other?
            msg_text = msg_payload
        return msg_text, msg_html, []

    attachments = []
    counter = 1
    for part in msg.walk():
        # multipart/* are just containers
        if part.get_content_maintype() == 'multipart':
            continue

        is_multipart = part.is_multipart()
        filename = part.get_filename()
        filename = decode_mail_header(filename)
        content_type = part.get_content_type()

        if is_multipart or filename:    # an attachment
            if not filename:    # maybe not possible
                ext = mimetypes.guess_extension(content_type)
                if not ext:
                    ext = '.bin'
                filename = 'part-%03d%s' % (counter, ext)
            attachments.append({
                "data": part.get_payload(),
                "filename": filename,
                "content_type": content_type,
                "is_multipart": is_multipart,
            })
        else:
            part_payload = part.get_payload(decode=True)
            part_payload = decode_text(part_payload)
            if content_type == 'text/plain':
                msg_text = part_payload
            elif content_type == 'text/html':
                msg_html = part_payload
            else:   # maybe not possible
                ext = mimetypes.guess_extension(content_type)
                if not ext:
                    ext = '.bin'
                filename = 'part-%03d%s' % (counter, ext)
                attachments.append({
                    "data": part.get_payload(),
                    "filename": filename,
                    "content_type": content_type,
                    "is_multipart": is_multipart(),
                })

        counter += 1

    return msg_text, msg_html, attachments
