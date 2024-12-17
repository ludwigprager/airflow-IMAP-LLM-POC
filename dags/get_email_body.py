import email
from bs4 import BeautifulSoup

# https://thepythoncode.com/code/reading-emails-in-python
def get_message_body_by_message_id(imap_server, message_id):
    
    # Search for message by Message-ID
    print('searching for message-id: {} '.format(message_id))
    status, messages = imap_server.search(None, f'HEADER Message-ID "{message_id}"')
    
    # Get the message
    if status == 'OK' and messages[0]:
        status, msg_data = imap_server.fetch(messages[0].split()[0], '(RFC822)')

        raw_message = msg_data[0][1]
        message = email.message_from_bytes(raw_message)

        # print('Message: {}'.format(message))

        if message.is_multipart():
            # iterate over email parts
            print('multipart message')
           
            concatenated_text = ""
            body = ""
            for part in message.walk():
                # extract content type of email
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                print('content type: {}, content disposition: {}'.format(content_type, content_disposition))
                try:
                    # get the email body
                    body = part.get_payload(decode=True).decode()
                    #print(body)
#                   concatenated_text += body
                except:
                    body = part.get_payload()
                    #pass
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    # print text/plain emails and skip attachments
                    #print(body)
                    concatenated_text += body
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    soup = BeautifulSoup(body)
                    concatenated_text += soup.get_text()
                elif "attachment" in content_disposition:
                    print('not processing attachment')
                    # download attachment
#                   filename = part.get_filename()
#                   if filename:
#                       folder_name = clean(subject)
#                       if not os.path.isdir(folder_name):
                        # make a folder for this email (named after the subject)
#                       os.mkdir(folder_name)
#                       filepath = os.path.join(folder_name, filename)
                        # download attachment and save it
#                       open(filepath, "wb").write(part.get_payload(decode=True))
            return concatenated_text
        else:
            # extract content type of email
            content_type = message.get_content_type()
            print('not a multipart message, type: {}'.format(content_type))
            # get the email body
            try:
                body = message.get_payload(decode=True).decode()
            except:
                body = message.get_payload(decode=True)

            if content_type == "text/plain":
                print('is text/plain')
                return body

            if content_type == "text/html":
                print('is text/html')
                soup = BeautifulSoup(body)
                return soup.get_text()

            print('error in get-email-body')

