import pandas as pd


df = pd.read_csv('strangerthings.fandom.com_pages_full_hard_part002.csv', delimiter=',', quotechar='|', index_col='revision_id')
print(df[df['revision_id']=='179'])
