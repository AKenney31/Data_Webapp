import streamlit as st
import pandas as pd
import numpy as np
import enum
from bs4 import BeautifulSoup
import requests
import matplotlib.pyplot as plt
import seaborn as sns

# https://www.nfl.com/stats/player-stats/category/passing/2021/REG/all/passingyards/desc
# https://www.nfl.com/stats/player-stats/category/rushing/2021/REG/all/rushingyards/desc
# https://www.nfl.com/stats/player-stats/category/receiving/2019/REG/all/receivingreceptions/desc


class POSITIONS(enum.Enum):
    qb = "passing"
    running = "rushing"
    receiver = "receiving"


@st.cache(show_spinner=False)
def load_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36'
    }
    page = requests.get(url, headers=headers)
    html = pd.read_html(page.text, header=0)
    df = html[0]

    while True:
        soup = BeautifulSoup(page.content)
        pag = soup.find_all(class_='nfl-o-table-pagination__buttons')
        if len(pag) == 0:
            break
        else:
            a = pag[0].a
            url = 'https://www.nfl.com' + a['href']
            page = requests.get(url, headers=headers)
            html = pd.read_html(page.text, header=0)
            df = df.append(html[0])

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
st.sidebar.subheader("Input Options")
pos = st.sidebar.selectbox('Select Position', ["passing", "rushing", "receiving"])
year = st.sidebar.selectbox('Select Year', [*range(2021, 1969, -1)])

u = make_url(pos, year)

with st.spinner(f"Loading data for {pos}, {year}"):
    data = load_data(u)

st.sidebar.subheader("Filter Options")
columns = st.sidebar.multiselect("Columns to include", list(data.columns), default=list(data.columns))
if 'All' not in columns and len(columns) != 0:
    data = data[columns]

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

if st.checkbox("Show Data", value=True):
    st.subheader(f"{str.upper(pos)}, {year}")
    st.text(f"Data is {data.shape[0]} x {data.shape[1]}")
    st.write(data)

if st.checkbox("Show Heat Map"):
    corr = data.corr()
    mask = np.zeros_like(corr)
    # Upper Triangle
    mask[np.triu_indices_from(mask)] = 1
    with sns.axes_style("white"):
        f, ax = plt.subplots(figsize=(7, 5))
        ax = sns.heatmap(corr, mask=mask, vmax=1, square=True)
        st.pyplot(f)
