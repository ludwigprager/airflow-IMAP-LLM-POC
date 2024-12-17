#from airflow import DAG
#from airflow.operators.python import PythonOperator
##from airflow.hooks.base import BaseHook
#from datetime import datetime, timedelta
import imaplib
#import email
import logging
import os
import sys


#from move-email import move_email


def move_email( imap, uid: int, folder: str):
    print("copying uid {} to {}".format(uid, folder))
    imap.select('inbox',  readonly=False)
    imap.create(folder)
    status, detail = imap.uid('COPY', uid, folder)
    print('copy status: ' + status)
    if (status == "OK"):
        imap.uid('STORE', uid, "+FLAGS", "\\Deleted")
    imap.expunge()
    imap.subscribe(folder)

