import json

import pandas as pd


def main():

    with open('./email_data.json', 'r') as f:
        email_data = json.load(f)

    # print(email_data)
    df = pd.DataFrame(email_data['emails'])
    # print(df.describe())
    print(df.head())

if __name__ == '__main__':
    main()