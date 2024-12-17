from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta
import imaplib
import email
import logging
import os
import sys

from classifier_by_subject import subject_classifier

from move_email import move_email
from get_subject_from_uid import get_subject_from_uid

    #'start_date': None,
    #'start_date': "2024-12-10 07:00:00",
default_args = {
    'start_date': None,
    'schedule_interval': None,
    'catchup': False,
    'retries': 1,
}

dag = DAG(
    'sort-emails-by-subject-llm1',
    description='Sort emails by body subject - account llm1',
    default_args=default_args,
)
    #schedule = '20 7-21 * * *',

#   timetable=cron_timetable(cron_expression='55 7-21 * * *'),

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
        connection = BaseHook.get_connection('imap_g1_llm1')
        #connection = BaseHook.get_connection('imap_frizzantemysliwitz_gmail.com')

        imap = open_imap_session(connection)

        # Connect to IMAP server
        #mail = imaplib.IMAP4_SSL(connection.host)
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




def process_emails(**context):

    try:
        connection = BaseHook.get_connection('imap_g1_llm1')
        #connection = BaseHook.get_connection('imap_frizzantemysliwitz_gmail.com')

        imap = open_imap_session(connection)
        #imap = imaplib.IMAP4(connection.host, connection.port)
        imap.login(connection.login, connection.password)

        email_info = context['task_instance'].xcom_pull(
        task_ids='fetch_emails',
        key='email_info'
        )
        imap.select('inbox',  readonly=False)
        
        if email_info:
            print(f"Processing {len(email_info)} emails")
            for info in email_info:
                message_id = info['message_id']
                uid = info['uid']
                subject = get_subject_from_uid(imap, uid)

                print(f"Processing subject {subject}, message-ID: {message_id}")
                result = subject_classifier( subject ).split(" ")
                print(f"result: {result}")
        
                folder = 'inbox.ai-filtered.'

                classification = result[0]
                quality = int(result[1])

                print(f"classified as: {classification}")
                print(f"quality: {quality}")
        
                if( quality > 50):
                    move_email( imap, uid, folder + classification)
                else:
                    move_email( imap, uid, folder + 'other')

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
