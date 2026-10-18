import streamlit as st
import requests as rq
import bs4
import pandas as pd
from io import StringIO
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("Global GDP by Country and Region")

# Fetch the Wikipedia page containing GDP data
url = "https://en.wikipedia.org/w/index.php?title=List_of_countries_by_GDP_(nominal)&oldid=1187446467"
page = rq.get(url, headers={"User-Agent": "Chrome"})
bs4page = bs4.BeautifulSoup(page.text, "html.parser")

# Find all tables on the page
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

    # Clean table - rename columns to meaningful names
    gdp.columns = [
        "country", "region", "imf_gdp", "imf_year", 
        "world_bank_gdp", "world_bank_year", "un_gdp", "un_year"
    ]

    # Clean text fields by stripping whitespace
    gdp["country"] = gdp["country"].astype(str).str.strip()
    gdp["region"] = gdp["region"].astype(str).str.strip()

    # Identify all columns ending in "_gdp" and convert to numeric values
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

    # Sidebar for user selection of data source
    st.sidebar.header("Select Data Source")
    source = st.sidebar.radio(
        "Choose GDP Data Source:",
        ("IMF", "World Bank", "UN")
    )

    # Filter out world total row for regional analysis
    gdp_region = gdp[gdp["country"] != "World"].copy()

    # Map selection to column name and create plot
    if source == "IMF":
        gdp_region = gdp_region.dropna(subset=["imf_gdp"])
        gdp_col = "imf_gdp"
        title = "IMF GDP (nominal) by Region"
    elif source == "World Bank":
        gdp_region = gdp_region.dropna(subset=["world_bank_gdp"])
        gdp_col = "world_bank_gdp"
        title = "World Bank GDP (nominal) by Region"
    else:
        gdp_region = gdp_region.dropna(subset=["un_gdp"])
        gdp_col = "un_gdp"
        title = "UN GDP (nominal) by Region"

    # Create stacked bar plot for selected data source
    fig = go.Figure()

    # Add bars for each country, stacked within regions
    for country in gdp_region["country"].unique():
        country_data = gdp_region[gdp_region["country"] == country]
        fig.add_trace(go.Bar(
            x=country_data["region"],
            y=country_data[gdp_col],
            name=country,
            hovertemplate="<b>%{fullData.name}</b><br>Region: %{x}<br>GDP: $%{y:,.0f}M<extra></extra>"
        ))

    # Update layout for stacked bar plot
    fig.update_layout(
        barmode="stack",
        title=title,
        xaxis_title="Region",
        yaxis_title="Million USD ($)",
        hovermode="x unified",
        height=600,
        width=1200,
        showlegend=True
    )

    # Display plot
    st.plotly_chart(fig, use_container_width=True)

    # Display data table
    st.subheader("Data Table")
    display_columns = ["country", "region", gdp_col]
    st.dataframe(gdp[display_columns].dropna(subset=[gdp_col]))
