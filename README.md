# who-is-emailing-me

After I saw [this](https://news.ycombinator.com/item?id=18925818) post on hacker news I decided it would be interesing to see who has my email (or rather who has been emailing me).

## Requirements and Setup

A gmail account.

Follow step 1 from google's [quickstart page](https://developers.google.com/gmail/api/quickstart/python) to get your api credentials file.

Install the required python packages:

```sh
pip install -r requirements.txt
```

## Running the Script

```
python whomail.py
```

<!-- ## Script Options

```
python whomail.py  --help
Usage: whomail.py [OPTIONS]

Options:
  --email_dir TEXT       Directory to store email data. Default is ./email_data
  --email_print BOOLEAN  Select whether to print email data as they're being saved. Default is False.
  --help                 Show this message and exit.
``` -->
