


def get_subject_from_uid(imap, uid):
    """assumes folder is selected"""

    from email.header import decode_header
    print('get_subject_from_uid: {}'.format(uid))

    #ok, msg_data = imap.uid('fetch', uid, '(UID BODY[HEADER.FIELDS (SUBJECT)])')
    ok, msg_data = imap.uid('fetch', uid, '(UID BODY.PEEK[HEADER.FIELDS (SUBJECT)])')
    
    str1=msg_data[0][1]
    decoded_parts = decode_header(str1.decode('ascii'))
    print("decoded parts: {}".format(decoded_parts))

    subject = str('')
    for part, charset in decoded_parts:
        if charset:  # If there's an encoding specified
            # Decode the bytes using the specified charset
            print(f"1 Encoded Part: {part}")
            decoded_part = part.decode(charset)
            subject += decoded_part
            print(f"1 Decoded Part: {decoded_part}")
        else:
            print('2 unencoded, part: {}'.format(part))
            str1 = part
            # evil hack
            try:
                str1 = str1.decode('utf-8')
            except:
                pass

            subject += str1
            if subject.startswith('Subject:'):
                subject = subject[8:]
            # This part wasn't encoded or is in ASCII
            #print(f"Unencoded Part: {part}")


    print("get_subject_from_uid returning: {}".format(subject))
    return subject

