import streamlit as st
import requests as rq
import bs4
import pandas as pd
from io import StringIO
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide")
st.title("Global GDP by Country and Region")

# Fetch the Wikipedia page
url = "https://en.wikipedia.org/w/index.php?title=List_of_countries_by_GDP_(nominal)&oldid=1187446467"
page = rq.get(url, headers={"User-Agent": "Chrome"})
bs4page = bs4.BeautifulSoup(page.text, "html.parser")

# Find all tables
tables = bs4page.find_all("table")

# Find the GDP table using its caption
gdp_table = None
for table in tables:
    caption = table.find("caption")
    if caption is not None and "GDP (USD million) by country" in caption.get_text():
        gdp_table = table
        break

if gdp_table is None:
    st.error("GDP table not found.")
else:
    # Convert the BeautifulSoup table to a pandas DataFrame
    gdp = pd.read_html(StringIO(str(gdp_table)))[0]

    # Clean table
    gdp.columns = [
        "country", "region", "imf_gdp", "imf_year", "world_bank_gdp", "world_bank_year", "un_gdp", "un_year"
    ]

    # Clean text fields
    gdp["country"] = gdp["country"].astype(str).str.strip()
    gdp["region"] = gdp["region"].astype(str).str.strip()

    # Identify all columns ending in "_gdp" and convert columns to numeric values
    gdp_columns = [col for col in gdp.columns if col.endswith("_gdp")]

    for col in gdp_columns:
        gdp[col] = (
            gdp[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("-NA", "", regex=False)
            .str.replace("—", "", regex=False)
            .str.strip()
        )
        gdp[col] = pd.to_numeric(gdp[col], errors="coerce")

    # Dropdown menu of selection of data source
    source = st.selectbox(
        "Choose GDP Data Source:",
        ("IMF", "World Bank", "UN")
    )

    # Filter out world total
    gdp_region = gdp[gdp["country"] != "World"].copy()

    # Map selection to column name and year column
    if source == "IMF":
        gdp_col = "imf_gdp"
        title = "IMF GDP (nominal) by Region"
    elif source == "World Bank":
        gdp_col = "world_bank_gdp"
        title = "World Bank GDP (nominal) by Region"
    else:  # UN
        gdp_col = "un_gdp"
        title = "UN GDP (nominal) by Region"

    # Remove rows with missing GDP values for selected source
    gdp_region = gdp_region.dropna(subset=[gdp_col])

    # Create stacked bar plot
    fig = px.bar(
        gdp_region,
        x="region",
        y=gdp_col,
        color="country",
        hover_name="country",
        hover_data={
            "region": False,
            gdp_col: ":,.0f",
        },
        title=title
    )

    fig.update_layout(
        barmode="stack",
        showlegend=False,
        xaxis_title="Region",
        yaxis_title="Million USD ($)"
    )

    fig.update_traces(
    hovertemplate="<b>%{fullData.name}</b><br>GDP: $%{y:,.0f}M<extra></extra>",
    showlegend = False
)


    # Display plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)
