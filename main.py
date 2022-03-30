import streamlit as st
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import ColumnDictionary

# https://www.nfl.com/stats/player-stats/category/passing/2021/REG/all/passingyards/desc
# https://www.nfl.com/stats/player-stats/category/rushing/2021/REG/all/rushingyards/desc
# https://www.nfl.com/stats/player-stats/category/receiving/2019/REG/all/receivingreceptions/desc


@st.cache(show_spinner=False)
def load_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36'
    }
    page = requests.get(url, headers=headers)
    html = pd.read_html(page.text, header=0)
    df = html[0]

    while True:
        soup = BeautifulSoup(page.content, features="lxml")
        pag = soup.find_all(class_='nfl-o-table-pagination__buttons')
        if len(pag) == 0:
            break
        else:
            a = pag[0].a
            url = 'https://www.nfl.com' + a['href']
            page = requests.get(url, headers=headers)
            html = pd.read_html(page.text, header=0)
            df = pd.concat([df, html[0]])

    return df


def make_url(p, y):
    if p == "passing":
        last_blank = "passingyards"
    elif p == "rushing":
        last_blank = "rushingyards"
    elif p == "receiving":
        last_blank = "receivingreceptions"
    else:
        last_blank = ""

    url = f'https://www.nfl.com/stats/player-stats/category/{p}/{y}/REG/all/{last_blank}/desc'
    return url


# MAIN
st.title('NFL Offensive Football Player Stats')
st.sidebar.subheader("Input Options:")
pos = st.sidebar.selectbox('Select Position', ["passing", "rushing", "receiving"])
year = st.sidebar.selectbox('Select Year', [*range(2021, 1969, -1)])

u = make_url(pos, year)

with st.spinner(f"Loading data for {pos}, {year}"):
    data = load_data(u)

st.sidebar.subheader("Filter Options:")
if st.sidebar.checkbox("Filter columns"):
    columns = st.sidebar.multiselect("Columns to include", list(data.columns), default=list(data.columns))
    if len(columns) != 0:
        data = data[columns]

if st.sidebar.checkbox("Filter by percentile"):
    stat_options = ['None'] + list(data.columns)
    if 'Player' in stat_options:
        stat_options.remove('Player')

    stat = st.sidebar.selectbox("Statistic For Percentile", stat_options)
    perc = st.sidebar.slider("Choose Percentile", min_value=10, max_value=100, step=5)
    area = st.sidebar.selectbox(f"Players ____ the {perc}th percentile in {stat}", ['Above', 'Below'])
    if stat != 'None':
        if area == 'Above':
            data = data.loc[data[stat] > np.percentile(data[stat], perc)]
        else:
            data = data.loc[data[stat] < np.percentile(data[stat], perc)]

if st.checkbox("Show Column Dictionary"):
    if pos == 'passing':
        c_dict = ColumnDictionary.c_dict_pass
    elif pos == 'receiving':
        c_dict = ColumnDictionary.c_dict_receiving
    else:
        c_dict = ColumnDictionary.c_dict_rush

    d = pd.DataFrame({'Column Name': c_dict.keys(), 'Description': c_dict.values()})
    st.write(d)

if st.checkbox("Show Data", value=True):
    st.subheader(f"{str.upper(pos)}, {year}")
    st.text(f"Data is {data.shape[0]} x {data.shape[1]}")
    st.write(data)

if st.checkbox("Show Aggregated Data"):
    c = list(data.columns)
    if 'Player' in c:
        c.remove('Player')
    agg_data = data[c].agg(func=['mean', 'std', 'var', 'sem', 'min', 'max']).round(2)
    st.write(agg_data)

if st.checkbox("Show Histogram"):
    col_options = list(data.columns)
    if 'Player' in col_options:
        col_options.remove('Player')
    column = st.selectbox("Select Statistic For Histogram", col_options)
    mv = 40 if data[column].max() > 40 else data[column].max()
    n_bins = st.slider("Number of bins", min_value=5, max_value=int(mv))
    bins = list(range(0, data[column].max(), int(data[column].max() / n_bins)))
    plt.figure(figsize=(8, 4))
    plt.hist(data[column], bins=bins)
    # Change x-ticks based on n_bins so that they do not overlap
    if n_bins >= 30:
        plt.xticks(bins[::4])
    elif n_bins >= 15:
        plt.xticks(bins[::2])
    else:
        plt.xticks(bins)

    plt.ylabel(column)
    plt.xlabel('Num Players')
    st.pyplot(plt)

if st.checkbox("Show Box Plot"):
    col_options = list(data.columns)
    if 'Player' in col_options:
        col_options.remove('Player')
    column = st.selectbox("Select Statistic For Box Plot", col_options)
    plt.figure(figsize=(4, 6))
    plt.boxplot(data[column], labels=[f'{column} among players'])
    plt.ylabel(column)
    st.pyplot(plt)

if st.checkbox("Show Heat Map"):
    corr = data.corr()
    mask = np.zeros_like(corr)
    # Upper Triangle
    mask[np.triu_indices_from(mask)] = 1
    with sns.axes_style("white"):
        f_heat, ax_heat = plt.subplots(figsize=(7, 5))
        ax_heat = sns.heatmap(corr, mask=mask, vmax=1, square=True)
        st.pyplot(f_heat)

