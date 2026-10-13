import streamlit as st
import pandas as pd
import requests as rq
import bs4
import plotly.express as px
from io import StringIO

st.title("GDP by Country and Region")

# Reading in the data from Wikipedia page
url = 'https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)'
page = rq.get(url, headers={"User-Agent": "MyProject/1.0 (nanssoma22@gmail.com)"})

# Reading into BS4
bs4page = bs4.BeautifulSoup(page.text, 'html.parser')
tables = bs4page.find_all('table', {'class': "wikitable"})

# Reading into pandas
wiki_tables = pd.read_html(StringIO(str(tables)))

countries = wiki_tables[0]
regions = wiki_tables[1]

# Rename columns
regions = regions.rename(columns={
    'Regional groupings': 'regions',
    'IMF (2026)[1]': 'imf',
    'World Bank (2024)[6]': 'wb',
    'United Nations (2023)[12]': 'un'
})

# Clean cells - remove brackets
regions['regions'] = regions['regions'].str.replace(r'\[.*?\]', '', regex=True)

# Let user select data source
source = st.selectbox("Select GDP Source:", ["IMF", "World Bank", "United Nations"])

# Map selection to column name
source_map = {
    "IMF": "imf",
    "World Bank": "wb",
    "United Nations": "un"
}

selected_column = source_map[source]

# Create bar chart
fig = px.bar(
    regions,
    x='regions',
    y=selected_column,
    title=f'GDP by Region ({source})',
    color='regions'
)

fig.update_layout(
    xaxis_title='Region',
    yaxis_title='Million USD ($)',
    width=800,
    height=500
)

# Display chart
st.plotly_chart(fig)
