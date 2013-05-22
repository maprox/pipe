# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Controller
@copyright 2009-2012, Maprox LLC
'''

from datetime import datetime
import kernel.pipe as pipe
from kernel.config import conf
from kernel.logger import log
from kernel.dbmanager import db
from lib.handlers.list import handlersList

# ===========================================================================
class Controller(object):
    '''
     Pipe-server controller
    '''

    __handlerTranslation = {
       'tr600': 'globalsat.tr600',
       'tr203': 'globalsat.tr203',
       'tr206': 'globalsat.tr206',
       'tr151': 'globalsat.tr151',
       'globalsat_gtr128': 'globalsat.gtr128',
       'naviset-gt10': 'naviset.gt10',
       'naviset-gt20': 'naviset.gt20',
       'galileo': 'galileo.firmware0119',
       'teltonika_fmxxxx': 'teltonika.fmxxxx',
       'atrack-ax5': 'atrack.ax5'
    }

    def __init__(self):
        """
         Controller constructor
        """
        log.debug('Controller::__init__')

    def run(self):
        """
         Starting check of execution commands
        """
        log.debug('Controller::run()')
        try:
            commands = db.getController().getCommands()
            store = pipe.Manager()
            for command in commands:
                handler = 'lib.handlers.' \
                  + self.__handlerTranslation[command['handler']]
                for HandlerClass in handlersList:
                    if HandlerClass.__module__ == handler:
                        handler = HandlerClass(store, False)
                        handler.uid = command['uid']
                        function_name = 'processCommand' \
                          + command['action'][0].upper() \
                          + command['action'][1:]
                        log.debug('Command is: ' + function_name)
                        function = getattr(handler, function_name)
                        if 'value' in command:
                            function(command['id'], command['value'])
                        else:
                            function(command['id'], None)
        except Exception as E:
            log.critical(E)

# ===========================================================================
import imaplib
import email
import kernel.pipe

class CameraChecker(object):
    '''
     Camera checker temp class
    '''
    def __init__(self):
        """
         CameraChecker constructor
        """
        log.debug('CameraChecker::__init__')
        self.store = kernel.pipe.Manager()

    def run(self):
        """
         Starting check for incoming emails
        """
        log.debug('CameraChecker::run()')
        for email in self.getEmails():
            data = self.parseEmail(email)
            if not data:
                continue
            log.debug('Data found: %s, %s', data["uid"], data["time"])
            self.store.send(data)

    def getEmails(self):
        """
         Retrieves emails from IMAP connection
         @return: List of email bodies
        """
        list = []

        host = conf.get("imap", "host")
        port = conf.get("imap", "port")
        username = conf.get("imap", "username")
        password = conf.get("imap", "password")
        filter = conf.get("imap", "filter")

        if not host:
            log.error('IMAP / No host specified! Exiting')
            return list

        log.info('IMAP / Connecting to %s:%s', host, port)
        M = imaplib.IMAP4_SSL(host, port)
        M.login(username, password)
        log.debug("IMAP / Logged in as %s", username)

        try:
            M.select('INBOX', readonly=False) # select INBOX mailbox
            res, data = M.uid('search', filter or '(unseen)')
            nums = data[0].split()

            if len(nums) > 0:
                log.info('IMAP / There are %s new message(s)', len(nums))
            else:
                log.info('IMAP / There are no new messages')

            for num in nums:
                res, data = M.uid('fetch', num, '(RFC822)')
                raw_email = data[0][1]

                msg = email.message_from_bytes(raw_email)
                list.append(msg)
        finally:
            try:
                M.close()
            except:
                pass
            M.logout()

        return list

    def parseEmail(self, msg):
        """
         Parses email body to find an image from camera
         @param msg: Email raw body
         @return: dict or False
        """
        emailFrom = email.utils.parseaddr(msg['From'])
        emailFromAddress = emailFrom[1]
        emailFromAddressParts = emailFromAddress.split('@')
        emailFromAddressHost = None
        if len(emailFromAddressParts) > 1:
            emailFromAddressHost = emailFromAddressParts[1]

        if (emailFromAddress != 'esbreceiver@yandex.ru') and
           (emailFromAddressHost != 'mail.messages.megafon.ru'):
            return False

        images = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue

                if part.get('Content-Disposition') is None:
                    continue

                filename = part.get_filename()
                if not(filename): continue

                if filename.upper() in ['PIC.JPG', 'IMAGE0.JPG']:
                    images.append({
                        'mime': 'image/jpeg',
                        'content': part.get_payload()
                    })

        if len(images) == 0:
            return False

        return {
            "uid": email.utils.parseaddr(msg['To'])[1],
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f'),
            "images": images
        }
