# %%
import sys, os
# Add the parent directory to the sys.path
sys.path.append(os.path.dirname(os.getcwd()))
sys.path.append(os.getcwd())

import datetime as dt
import pandas as pd
from mailjet_rest import Client

from dotenv import load_dotenv
load_dotenv()

# from IPython.display import HTML

# %%
def send_email_using_mailjet(html, distro, subject='Testing email', attachments=None):
    """
    Send email using the MailJet service.

    Args:
        html (str): html email body.
        distro (str): email distribution list name.
        subject (str): email subject

    Returns: None
    """
    # Send the message via mailjet
    api_key = os.environ['MAILJET_API_KEY']
    api_secret = os.environ['MAILJET_SECRET_KEY']
    mailjet = Client(auth=(api_key, api_secret))
    recipients = get_email_distro_list(distro_name=distro)
    # recipients = ['jones.wan@shell.com']
    data = {
        'FromEmail': "systradingmonitor@shell.com",
        'FromName': 'Systematic Trading & Fundamentals Monitor',
        'Subject': subject,
        'Text-part': '',
        'Html-part': html,
        'Recipients': [{'Email': a} for a in recipients],
        "InlinedAttachments": attachments
    }
    
    result = mailjet.send.create(data=data)
    

# %%
def get_email_distro_list(distro_name):
    """
    This function is used to retrieve email distribution lists.

    Args:
        distro_name (str): name of the email distribution list to retrieve.

    Returns: distribution_list value

    """

    if distro_name.lower() == 'live':
        d_list = os.environ['MAILLIST_LIVE'].split(';')
    elif distro_name.lower() == 'test':
        d_list = os.environ['MAILLIST_TEST'].split(';')
    else:
        d_list = os.environ['MAILLIST_DEV'].split(';')

    return d_list

# %%
def read_forcast(output_dir, forecast_date):
    """
    Read the forecast from local output folder
    """
    
    if isinstance(forecast_date, dt.datetime):
        forecast_date = forecast_date.date()

    df = pd.read_csv(f'{output_dir}/forecast_{forecast_date}.csv', index_col=0)
    df.index = pd.to_datetime(df.index)
    
    return df

# %%
def send_email_alert(subject='Testing email', distro='dev',
input_1=None, description_1=None,
input_2=None, description_2=None,
input_3=None, description_3=None):    

    if (input_1 is None) and (input_2 is None) and (input_3 is None):
        print("Input is not provided")
    else:
        html = ""
        if input_1 is not None:
            if isinstance(input_1, str):
                html += input_1                
            else:
                html += f"""<br><p style="font-family:Arial, sans-serif;font-size:14px;font-weight:bold">{description_1}</p><br>"""                
                if isinstance(input_1, pd.DataFrame):
                    html += input_1.to_html()

        if input_2 is not None:
            if isinstance(input_2, str):
                html += input_2                
            else:
                html += f"""<br><p style="font-family:Arial, sans-serif;font-size:14px;font-weight:bold">{description_2}</p><br>"""                
                if isinstance(input_2, pd.DataFrame):
                    html += input_2.to_html()

        if input_3 is not None:
            if isinstance(input_3, str):
                html += input_3                
            else:
                html += f"""<br><p style="font-family:Arial, sans-serif;font-size:14px;font-weight:bold">{description_3}</p><br>"""                
                if isinstance(input_3, pd.DataFrame):
                    html += input_3.to_html()

    send_email_using_mailjet(html, distro, subject=subject)
    print("Sending email alert completed ...")

# %%
if __name__ == '__main__':

    print(get_email_distro_list('live'))
    print(get_email_distro_list('test'))
    print(get_email_distro_list('dev'))

    # Testing email
    send_date = dt.date.today()

    html = """<br><p style="font-family:Arial, sans-serif;font-size:14px;font-weight:bold">This is a testing email
                                </p><br>"""
    send_email_using_mailjet(html, 'dev', subject='Testing email sent on %(send_date)s' % {'send_date':send_date})
    print("Sending testing email completed ...")

    df_1 = pd.DataFrame({'col1': range(1,11), 'col2': range(11,21)})
    send_email_alert(subject='Testing email sent on %(send_date)s' % {'send_date':send_date}, distro='dev',
    input_1=df_1, description_1='Sample table 1')
    
    df_2 = pd.DataFrame({'col1': range(1,11), 'col2': range(11,21), 'col3': range(21,31)})
    send_email_alert(subject='Testing email sent on %(send_date)s' % {'send_date':send_date}, distro='dev',
    input_1=df_1, description_1='Sample table 1',
    input_2=df_2, description_2='Sample table 2')

    send_email_alert(subject='Testing email sent on %(send_date)s' % {'send_date':send_date}, distro='dev',
    input_1='Sample text',
    input_2=df_2, description_2='Sample table')
    