from __future__ import print_function
import pickle
import os
import pprint
import json
import threading
import queue
import time

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import click

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class EmailCollector(object):
    """
    Collects emails into a queue to be processed
    """
    emails_queue = queue.Queue()
    collected_count = 0

    def __init__(self, num_emails):

        self.num_emails = num_emails

        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server()

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)
        self.messages = self.service.users().messages()
        self.request = self.messages.list(userId='me')

        self.get_emails_thread = threading.Thread(
            target=self.collect_emails,
            args=[num_emails],
            name='get_emails_thread')

    
    def collect_emails(self, num_emails):

        # Collect emails if there are more to be collected and we're not at
        # our limit
        while self.request is not None:

            try:
                messages_json = self.request.execute()
            except Exception as e:
                print(e)
                time.sleep(15)
                continue

            for message_record in messages_json['messages']:

                message = self.messages.get(userId='me', id=message_record['id']).execute()

                try:
                    email = Email(message)
                    self.emails_queue.put(email)
                    self.collected_count += 1

                    if self.collected_count >= num_emails:
                        return

                except Exception as e:
                    print('Error making email object from email with id: {}'.format(message_record['id']))
                    print(e)

            self.request = self.messages.list_next(self.request, messages_json)


class EmailProcessor(object):
    """
    Processes emails that are in the collected queue
    """

    processed_emails = {}
    senders = {}

    def __init__(self, email_collector, email_print):
        self.email_collector = email_collector
        self.email_print = email_print
        self.pp = pprint.PrettyPrinter(indent=4)

        self.process_emails_thread = threading.Thread(
            target=self.process_email_messages,
            name='process_emails_thread')

    def process_email_messages(self):

        while self.email_collector.get_emails_thread.isAlive() or not self.email_collector.emails_queue.empty():

            email = self.email_collector.emails_queue.get()
            if self.email_print:
                self.pp.pprint(email.to_json())                

            # Strip the email domain to see the sender
            sender = email._from[email._from.index('@') + 1:]
            try:
                self.senders[sender] += 1
            
            except KeyError as ke:
                self.senders[sender] = 1

            self.processed_emails[email.email_id] = email


    def store_email_data(self):

        email_data = {
            'emails': [email.to_json() for email_id, email in self.processed_emails.items()],
            'senders': self.senders
            }

        with open('email_data.json', 'w') as f:
            json.dump(email_data, f, indent=4)



class Email(object):
    """
    Object that holds onto selected info from an email message json
    """

    attributes = [
        'email_id',
        'thread_id',
        'label_ids',
        'date',
        'to',
        '_from',
        'subject'
    ]

    # def __init__(self, email_id, thread_id, label_ids, date,
    #              to, _from, subject):

    #     self.email_id = email_id
    #     self.thread_id = thread_id
    #     self.label_ids = label_ids
    #     self.date = date
    #     self.to = to
    #     self._from = _from
    #     self.subject = subject

    def __init__(self, message_json):

        self.email_id = message_json['id']
        self.thread_id = message_json['threadId']
        self.label_ids = message_json['labelIds']

        headers = message_json['payload']['headers']
        self.date = self._get_header(headers, 'Date')
        self.to = self._extract_email_address(self._get_header(headers, 'To'))
        self._from = self._extract_email_address(self._get_header(headers, 'From'))
        self.subject = self._get_header(headers, 'Subject')

    def _get_header(self, headers, name):
        return [header['value'] for header in headers if header['name'] == name][0]

    def _extract_email_address(self, email_address):
        try:
            opening_carrot = email_address.index('<')
            closing_carrot = email_address.index('>')
            return email_address[opening_carrot + 1:closing_carrot].lower()
        except Exception as e:
            return email_address.lower()

    # def save(self, base_dir='email_data'):
    #     with open('{}/{}.json'.format(base_dir, self.email_id), 'w') as f:
    #         json.dump(self.to_json(), f, indent=4)

    def to_json(self):
        return {
            'email_id': self.email_id,
            'thread_id': self.thread_id,
            'label_ids': self.label_ids,
            'subject': self.subject,
            'date': self.date,
            'to': self.to,
            'from': self._from,
            'subject': self.subject
        }


# @click.command()
# @click.option('--num_emails', type=click.INT, default=10000, help='Number of emails to collect. Default is 10,000.')
# @click.option('--email_print', type=click.BOOL, default=False, help='Select whether to print email data as they\'re being saved. Default is False.')
def whomail(num_emails, email_print):

    start_time = time.time()
    email_collector = EmailCollector(num_emails)
    email_processor = EmailProcessor(email_collector, email_print)

    email_collector.get_emails_thread.start()
    email_collector.get_emails_thread.join()

    email_processor.process_emails_thread.start()
    email_processor.process_emails_thread.join()

    email_processor.store_email_data()
    print('Processed {} emails in {} seconds.'.format(len(email_processor.processed_emails), time.time() - start_time))

if __name__ == '__main__':
    whomail(10, True)