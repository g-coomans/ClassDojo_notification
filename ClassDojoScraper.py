from Scraper import Scraper
import json
import datetime
import configparser
import smtplib
from email.message import EmailMessage

URL_TO_SCRAP = "https://www.classdojo.com/"

class ClassDojoScraper(Scraper):
    
    def __init__(self, verify=True, config_ini='config.ini', days=0):
        # Load configuration
        Config = configparser.ConfigParser()
        Config.read(config_ini)
        try: 
            self.load_variables(Config)
        except configparser.NoSectionError as err:
            print(f'Configuration file is not well completed ({err}). Please review it or generate a new one.')
            
        self.days = days
   
        # headers from curl when browsing with Edge
        headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/json',
                'dnt': '1',
                'origin': 'https://home.classdojo.com',
                'priority': 'u=1, i',
                'referer': 'https://home.classdojo.com/',
                'sec-ch-ua': '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
                'x-client-identifier': 'Web',
                'x-sign-attachment-urls': 'true',
            }
        Scraper.__init__(self,headers=headers,verify=verify)
        
    def load_variables(self,Config):
        self.user = Config.get('ClassDojo','user')
        self.password = Config.get('ClassDojo', 'password')
        self.smtp_url = Config.get('Email','smtp')
        self.smtp_port = Config.get('Email','smtp_port')
        self.smtp_user = Config.get('Email','user')
        self.smtp_password = Config.get('Email','password')
        self.smtp_from = Config.get('Email','from')
        self.smtp_to = Config.get('Email','to')
        self.smtp_subject = Config.get('Email','subject')
        self.smtp_text = Config.get('Email','text')
    
    def connect(self, user:str=None, password:str=None):
        # if user and/or password is not given, use those in config.ini 
        if user is None:
            user = self.user
        else:
            self.user = user
        if password is None:
            password = self.password
        else:
            self.password = password
        
        # Connect to create a session
        self.get_page('https://home.classdojo.com/')
        
        # Login
        params = {
            'duration': 'long',
        }

        json_data = {
            'login': user,
            'password': password,
        }
        connection = self.conn.post('https://home.classdojo.com/api/session', params=params, json=json_data)
        
        # Retrieve user_id for personnel message
        self.user_id = connection.json()['parent']['_id']
    
        return connection
    
    def get_feed(self):
        # Get main feed
        params = {
            'withStudentCommentsAndLikes': 'true',
        }
        list_entries = self.conn.get('https://home.classdojo.com/api/storyFeed', params=params).json()
        return list_entries
    
    def get_messages(self):
        # Get personnal messages (DM)
        params = {
            'limit': '20',
        }
        messages = self.conn.get('https://home.classdojo.com/api/parent/'+self.user_id+'/message-thread/page',params=params).json()
        
        return messages

    def get_amount_last_items_feed(self, days=None):
        if days is None:
            days = self.days
        
        # Count how many items are younger than 'days' days in your feed
        feed = self.get_feed()
        today_datetime = datetime.date.today()
        
        amount_last_items_feed = sum(1 for item in feed['_items'] if (today_datetime-datetime.datetime.strptime(item['time'][:16], "%Y-%m-%dT%H:%M").date()).days <= days )
        
        return amount_last_items_feed

    def get_amount_last_messages(self, days=None):
        if days is None:
            days = self.days
        
        # Count how many messages are younger than 'days' days in your personnal messages
        messages = self.get_messages()
        today_datetime = datetime.date.today()
        
        amount_last_messages = sum(1 for item in messages['_items'] if (today_datetime-datetime.datetime.strptime(item['lastUpdated'][:16], "%Y-%m-%dT%H:%M").date()).days <= days )
        
        return amount_last_messages
    
    def send_email(self):
        
        msg = EmailMessage()
        msg.set_content(self.get_content_email())
            
        msg['Subject'] = self.smtp_subject
        msg['From'] = self.smtp_from
        msg['To'] = self.smtp_to
        
        s = smtplib.SMTP_SSL(f'{self.smtp_url}:{self.smtp_port}')
        s.login(self.smtp_user, self.smtp_password)
        s.send_message(msg)
        print(f'Mail sent on {datetime.date.today()}')
        s.quit()
        
    def get_content_email(self, amount_last_items_feed=None, amount_last_messages=None):
        if amount_last_items_feed is None:
            amount_last_items_feed = self.amount_last_items_feed
        if amount_last_messages is None:
            amount_last_messages = self.amount_last_messages

        content_email = self.smtp_text.replace('%amount_last_items_feed%', str(amount_last_items_feed)).replace('%amount_last_messages%',str(amount_last_messages))
        
        return content_email
        

if __name__ == "__main__":
    scrap = ClassDojoScraper()
    scrap.connect()
    feed = scrap.get_feed()

    scrap.amount_last_items_feed = scrap.get_amount_last_items_feed()
    scrap.amount_last_messages = scrap.get_amount_last_messages()
    if scrap.amount_last_items_feed != 0 or scrap.amount_last_messages != 0:
        scrap.send_email()
    else:
        print('No new items in your feed or new messages')
