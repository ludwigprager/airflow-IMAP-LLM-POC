from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta
import imaplib
import email
import logging
import os
import sys

from classifier_by_text import email_classifier


from get_email_body import get_message_body_by_message_id
from move_email import move_email


default_args = {
    'start_date': None,
    'schedule_interval': None,
    'catchup': False,
    'retries': 1,
}

dag = DAG(
    'sort-emails-by-text',
    description='Sort emails by body text',
    default_args=default_args,
)

def open_imap_session(connection):
    # Extract connection details
    #logging.info('Host: {}'.format(connection.host))
    #PORT = connection.port # or 143  # Default non-SSL port if not specified
    #logging.info('Port: {}'.format(connection.port))

    extra = connection.extra_dejson  # This will parse the extra field as a dictionary
    use_ssl = extra.get('use_ssl', False)  # Default to False if 'use_ssl' is not provided

    # Open the IMAP connection
    if use_ssl:
        print("Opening IMAP connection with SSL...")
        #imap = imaplib.IMAP4_SSL(connection.host)
        imap = imaplib.IMAP4_SSL('imap.gmail.com')
    else:
        print("Opening IMAP connection without SSL...")
        imap = imaplib.IMAP4(connection.host, connection.port)

    return imap

def get_email_headers(imap_conn):
    emails = []
    
    # Select inbox folder
    imap_conn.select('INBOX', readonly=True)
    
    # Search for all emails
    #_, message_numbers = imap_conn.search(None, 'ALL')
    _, message_numbers = imap_conn.search(None, 'UNSEEN')
    print('message numbers: {}'.format(message_numbers))
    
    for num in message_numbers[0].split():
        # Fetch headers for each email
        _, msg_data = imap_conn.fetch(num, '(UID BODY[HEADER.FIELDS (MESSAGE-ID SUBJECT)])')
        logging.info('struct from fetch: {}'.format(msg_data))
        
        # Get UID
        uid = msg_data[0][0].split()[2]
        
        # Parse headers
        header_data = msg_data[0][1].decode()
        message_id = ''
        subject = ''
        logging.info('header_data: {}'.format(header_data))
        
        for line in header_data.splitlines():
            if line.startswith('Message-ID:'):
                message_id = line[11:].strip()
            elif line.startswith('Subject:'):
                subject = line[8:].strip()
        
        emails.append({
            'uid': uid.decode(),
            'message_id': message_id, 
            'subject': subject
        })
        
    return emails


def fetch_unseen_emails(**context):

    try:
        # Get connection details from Airflow connection
        connection = BaseHook.get_connection('imap_g1_lp')

        imap = open_imap_session(connection)

        # Connect to IMAP server
        #mail = imaplib.IMAP4_SSL(connection.host)
        # alt: imap = imaplib.IMAP4(connection.host, connection.port)
        imap.login(connection.login, connection.password)
        emails = get_email_headers(imap)
        context['task_instance'].xcom_push(key='email_info', value=emails)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure the session is closed if it was created
        try:
            imap.close()
            imap.logout()
            print("IMAP session closed.")
        except Exception:
            pass  # If logout fails, we just ignore it



def fetch_unseen_emails_alt(**context):
    # Get connection details from Airflow connection
    connection = BaseHook.get_connection('imap_g1_lp')

    imap = open_imap_session(connection)

    # Connect to IMAP server
    #mail = imaplib.IMAP4_SSL(connection.host)
    # alt: imap = imaplib.IMAP4(connection.host, connection.port)
    imap.login(connection.login, connection.password)
    imap.select('inbox',  readonly=True)

    # Search for unseen emails
    _, messages = imap.search(None, 'UNSEEN')
    print('message numbers: {}'.format(messages))

    # print('messages: {} '.format(messages))

    email_nums = messages[0].split()
    print(email_nums)

    # Get message IDs and their UIDs
    email_info = []
    for num in email_nums:
        _, msg_data = imap_conn.fetch(num, '(UID BODY[HEADER.FIELDS (MESSAGE-ID SUBJECT)])')

        # Fetch message flags and internal date
        print('num: {} '.format(num))

        #result, data = imap.fetch(num, '(UID BODY[HEADER.FIELDS (MESSAGE-ID)])')
        result, data = imap.fetch(num, '(RFC822])')
        print('fetch result: {} '.format(result))
        print('data: {} '.format(data))


        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
                
        # Get the Message-ID
        message_id = msg['Message-ID']


        result, data = imap.fetch(num, '(BODY[HEADER.FIELDS (MESSAGE-ID)])')
        result, uid_data = imap_connection.uid('fetch', num, '(UID)')
        if result == 'OK':
            uid = uid_data[0][0].split()[2]  # Extract the UID

        # empty message-id is likely spam - and I can't process it anyway
        # for some reason '\r' is always present
        message_id = message_id.rstrip()
        if message_id:
            print("Message-ID:", message_id)
            email_info.append({
                    'num': num.decode(),
                    'uid': uid.decode(),
                    'message_id': message_id
            })
    #   else:
    #      imap.move(uid,'+FLAGS','\\Spam')

    # print("returning:", email_info)
    # Push email information to XCom
    context['task_instance'].xcom_push(key='email_info', value=email_info)

    imap.logout()
    return email_info

#   context['task_instance'].xcom_push(key='email_info', value=email_info)




def process_emails(**context):

    try:
        connection = BaseHook.get_connection('imap_g1_lp')

        imap = open_imap_session(connection)
        #imap = imaplib.IMAP4(connection.host, connection.port)
        imap.login(connection.login, connection.password)

        email_info = context['task_instance'].xcom_pull(
        task_ids='fetch_emails',
        key='email_info'
        )
        
        if email_info:
            print(f"Processing {len(email_info)} emails")
            for info in email_info:
                message_id = info['message_id']
                uid = info['uid']
                print(f"Processing message-ID: {message_id}")
                imap.select('inbox',  readonly=True)
                email_text = get_message_body_by_message_id(imap, message_id)
                # print('email text: ' + email_text)
    
                #print(f"Classifying email ID: {message_id}")
                classification = email_classifier( email_text )
                print(f"classified as: {classification}")
    
                folder = 'inbox.ai-filtered.'
    
                move_email( imap, uid, folder + classification)
    #           except Exception as error:
    #               print('failed to classify and move message-id {}: {}'.format(message_id, error))
             
        else:
            print("No new emails to process")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure the session is closed if it was created
        try:
            imap.close()
            imap.logout()
            print("IMAP session closed.")
        except Exception:
            pass  # If logout fails, we just ignore it



# Define tasks
fetch_emails = PythonOperator(
    task_id='fetch_emails',
    python_callable=fetch_unseen_emails,
    provide_context=True,
    dag=dag,
)

process_emails = PythonOperator(
    task_id='process_emails',
    python_callable=process_emails,
    provide_context=True,
    dag=dag,
)

# Set task dependencies
fetch_emails >> process_emails
