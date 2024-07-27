import re
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

# Set matplotlib backend so figures don't pop up
mpl.use('agg')

'''Analyze free flight trap assay results'''

# Link for google sheets containing data
gsheet_link_txt = 'trap_gsheet_link.txt'

# Directory for figures
savedir = 'figures'


def convert_google_sheet_url(url):
    # Regular expression to match and capture the necessary part of the URL
    # https://skills.ai/blog/import-google-sheets-to-pandas/

    pattern = r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?'

    # Replace function to construct the new URL for CSV export
    # If gid is present in the URL, it includes it in the export URL, otherwise, it's omitted
    replacement = lambda m: f'https://docs.google.com/spreadsheets/d/{m.group(1)}/export?' + (
        f'gid={m.group(3)}&' if m.group(3) else '') + 'format=csv'

    # Replace using regex
    new_url = re.sub(pattern, replacement, url)

    return new_url


## Main
# Read trap data
gsheet_file = open(gsheet_link_txt, 'r')
gsheet_link = gsheet_file.readline()
gsheet_file.close()
df = pd.read_csv(convert_google_sheet_url(gsheet_link))

# Select relevant data
trap_df = df.loc[df['Exclude'] == False, :]
trap_df = trap_df.loc[:, ('Trap Start Time',
                          'Stage',
                          'Odor Position',
                          'Odor',
                          'Control',
                          '# Flies',
                          'Odor # Flies',
                          'Control # Flies',
                          'Odor Trap %',
                          'Control Trap %')].dropna(how='any').reset_index(drop=True)

# Reshape for plotting
odor_df = trap_df.copy()
odor_df['Trap'] = ['odor' for row in trap_df.index.values]
odor_df.rename(columns={'Odor Trap %': 'Trap %'}, inplace=True)
odor_df = odor_df.loc[:, ('Trap Start Time',
                          'Stage',
                          'Odor Position',
                          'Odor',
                          'Trap',
                          'Trap %')]

control_df = trap_df.copy()
control_df['Trap'] = ['solvent' for row in trap_df.index.values]
control_df.rename(columns={'Control Trap %': 'Trap %'}, inplace=True)
control_df = control_df.loc[:, ('Trap Start Time',
                             'Stage',
                             'Odor Position',
                             'Odor',
                             'Trap',
                             'Trap %')]

trap_df_bar = pd.concat([odor_df, control_df])

g = sns.catplot(
    data=trap_df_bar,
    kind='bar',
    x='Odor',
    y='Trap %',
    hue='Trap',
    #palette="dark",
    alpha=.6,
    height=6,
    aspect=1.6)
g.set_xticklabels(size=12, rotation=15)
g.set_ylabels(size=16)
g.set_yticklabels(size=15)
g._legend.remove()
g.despine(left=True)
plt.legend(loc='upper right')

plt.tight_layout()
fig = plt.gcf()
fig.savefig(f'{savedir}/funneltrap_bar.PNG', format='png')
