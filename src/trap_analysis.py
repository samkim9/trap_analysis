import re
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import scipy.stats as st

# Set matplotlib backend so figures don't pop up
mpl.use('agg')

'''Analyze free flight trap assay results'''

# Link for google sheets containing data
gsheet_link_txt = 'trap_gsheet_link.txt'

# Directory for figures
savedir = 'figures'

# Odor order
odor_order = [
    '2-butanone @ -2, water',
    #'2-butanone @ -2, pfo',
    #'Isoamyl Acetate @ -3, water',
    'Banana filtrate',
    'Banana filtrate @ -1, water',
    'Pear filtrate',
    'Pear filtrate @ -1, water',
    'PearB filtrate',
    'PearB filtrate @ -1, water',
    'Basil filtrate',
    'Basil filtrate @ -1, water'
]

# Abbreviated labels for odors
odor_abb = {
    '2-butanone @ -2, water': '2-but @ -2, water',
    '2-butanone @ -2, pfo': '2-but @ -2, pfo',
    'Isoamyl Acetate @ -3, water': 'IaA @ -3, water',
    'Banana filtrate': 'Ban @ 0',
    'Banana filtrate @ -1, water': 'Ban @ -1, water',
    'Pear filtrate': 'Pear @ 0',
    'Pear filtrate @ -1, water': 'Pear @ -1, water',
    'PearB filtrate': 'PearB @ 0',
    'PearB filtrate @ -1, water': 'PearB @ -1, water',
    'Basil filtrate': 'Basil @ 0',
    'Basil filtrate @ -1, water': 'Basil @ -1'
}

# P-value significance threshold
p_sig = 0.05

# Palette for plot
palette = {'odor': 'tab:orange',
           'solvent': 'tab:blue'}

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

# Sort by desired order of odors
# Create a column to store sort order
odor_sort_col = trap_df['Odor'].copy()
odor_sort_col.rename('odor_sort_col', inplace=True)

for i, odor in enumerate(odor_order):

    # Assign order to sort
    odor_sort_col[odor_sort_col == odor] = i

# Add the sorting column to the main dataframe
trap_df = pd.concat([trap_df, odor_sort_col], axis=1)

# Sort based on the sorting column
trap_df = trap_df.sort_values('odor_sort_col')

# Remove the sorting column
trap_df = trap_df.drop('odor_sort_col', axis=1)



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

# Get N per odor
trap_df_bar_n = trap_df_bar.loc[trap_df_bar['Trap'] == 'odor']
odor_n = {}
for odor in odor_order:
    odor_n[odor] = trap_df_bar_n['Odor'].loc[trap_df_bar_n['Odor'] == odor].count()

# Abbreviated odor labels
xtick_labels = [f'{odor_abb[odor]}\nn={odor_n[odor]}' for odor in list(odor_n.keys())]

# Plot barplot
# https://stackoverflow.com/questions/69315871/how-to-overlay-data-points-on-a-barplot-with-a-categorical-axis
ax = sns.barplot(
    data=trap_df_bar,
    x='Odor',
    y='Trap %',
    hue='Trap',
    palette=palette,
    capsize=0.1,
    errwidth=1.5,
    alpha=0.4)

sns.stripplot(
    data=trap_df_bar,
    x='Odor',
    y='Trap %',
    hue='Trap',
    palette=palette,
    dodge=True,
    alpha=0.9,
    ax=ax
)

ax.set_xticklabels(xtick_labels, size=12, rotation=45)
ax.set_ylabel('% Flies trapped\n(Mean + 95% CI)', size=16)
ax.set_xlabel('')
ax.set_yticklabels(ax.get_yticklabels(), size=15)
ax.set_ylim(0, 100)
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles[0:2], labels[0:2])
plt.tight_layout()
fig = plt.gcf()
fig.set_size_inches(12, 4)


# Statistical tests
# Kruskal-Wallis for each group against the solvent control
trap_ks = {}
trap_df_stats = trap_df_bar[['Odor', 'Trap', 'Trap %']].set_index('Odor')

for odor, odf in trap_df_stats.groupby('Odor'):
    odor_group = odf.loc[odf['Trap']=='odor', 'Trap %']
    solvent_group = odf.loc[odf['Trap']=='solvent', 'Trap %']
    trap_ks[odor] = st.kruskal(odor_group, solvent_group)

# Mark significance and p-value for each odor-solvent pair
#https://stackoverflow.com/questions/57203871/put-significance-asterisks-in-the-horizontal-middle-of-each-bar-in-a-barplot
for patch, odor in zip(ax.patches, odor_order):
    p_val = round(trap_ks[odor][1], 3)
    p_text = f'p={p_val}'
    color = 'black'

    if p_val < p_sig:
        p_text = '*\n' + p_text
        color = 'magenta'

    text_x = patch.get_x() + patch.get_width()
    text_y = patch.get_height()*1.1
    if text_y < 50:
        text_y = 50

    ax.text(text_x,
            text_y,
            p_text,
            fontsize=8,
            fontweight='bold',
            color=color)


fig.savefig(f'{savedir}/funneltrap_bar.PNG', format='png')
