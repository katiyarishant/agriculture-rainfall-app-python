import streamlit as st
import pandas as pd
import re


@st.cache_data
def load_data():
    crop_df = pd.read_csv("crop.csv")
    rain_df = pd.read_csv("rain.csv")
    merged_df = pd.read_csv("Merged_Agri_Rainfall_Data.csv")

    # Clean crop data
    crop_df.columns = crop_df.columns.str.strip()
    if "State_Name" in crop_df.columns:
        crop_df.rename(columns={"State_Name": "State"}, inplace=True)
    if "Crop_Year" in crop_df.columns:
        crop_df.rename(columns={"Crop_Year": "Year"}, inplace=True)


    crop_df["Year"] = crop_df["Year"].astype(str).str[:4].astype(int)


    rain_df.columns = rain_df.columns.str.strip()
    rain_df.rename(
        columns={
            "SUBDIVISION": "State",
            "YEAR": "Year",
            "ANNUAL": "Annual_Rainfall",
        },
        inplace=True,
    )


    merged_df.columns = merged_df.columns.str.strip()
    if "Annual" in merged_df.columns:
        merged_df.rename(columns={"Annual": "Annual_Rainfall"}, inplace=True)
    if "State_Name" in merged_df.columns:
        merged_df.rename(columns={"State_Name": "State"}, inplace=True)

    return crop_df, rain_df, merged_df


crop_df, rain_df, merged_df = load_data()


def understand_query(query):
    query = query.lower()
    dataset = None
    action = None
    filters = {}

    if "rain" in query or "imd" in query:
        dataset = "rainfall"
    elif "crop" in query or "production" in query or "yield" in query:
        dataset = "crop"
    elif "rainfall" in query and "crop" in query:
        dataset = "merged"

    if "compare" in query:
        action = "compare"
    elif "top" in query:
        action = "top"
    elif "trend" in query or "year" in query or "over time" in query:
        action = "trend"
    elif "average" in query or "mean" in query:
        action = "average"
    elif "max" in query or "highest" in query:
        action = "max"
    elif "min" in query or "lowest" in query:
        action = "min"
    else:
        action = "general"

    states = [
        "uttar pradesh", "madhya pradesh", "maharashtra", "tamil nadu",
        "karnataka", "bihar", "gujarat", "west bengal", "andhra pradesh",
        "rajasthan", "kerala", "punjab", "haryana", "odisha", "jharkhand"
    ]
    crops = ["rice", "wheat", "sugarcane", "maize", "cotton", "pulses", "millets"]

    for s in states:
        if s in query:
            filters["state"] = s.title()
    for c in crops:
        if c in query:
            filters["crop"] = c.title()

    year_match = re.findall(r"\b(19|20)\d{2}\b", query)
    if year_match:
        filters["years"] = [int(y) for y in year_match]

    return dataset, action, filters


def generate_answer(dataset, action, filters, crop_df, rain_df, merged_df):
    result = ""

    if dataset == "rainfall":
        df = rain_df.copy()
        source = "IMD 2017"
    elif dataset == "crop":
        df = crop_df.copy()
        source = "Agriculture Ministry 2022"
    else:
        df = merged_df.copy()
        source = "IMD + Agriculture Ministry"

    if "state" in filters and "State" in df.columns:
        df = df[df["State"].str.lower() == filters["state"].lower()]
    if "crop" in filters and "Crop" in df.columns:
        df = df[df["Crop"].str.lower() == filters["crop"].lower()]
    if "years" in filters and "Year" in df.columns:
        df = df[df["Year"].isin(filters["years"])]

    if df.empty:
        return f"No data found for this query (filters: {filters})."

    if action == "average":
        if dataset == "rainfall" and "Annual_Rainfall" in df.columns:
            avg_rain = round(df["Annual_Rainfall"].mean(), 2)
            result = f"Average rainfall in {filters.get('state', 'India')} = {avg_rain} mm (source: {source})"
        elif dataset == "crop" and "Production" in df.columns:
            avg_prod = round(df["Production"].mean(), 2)
            result = f"Average crop production in {filters.get('state', 'India')} = {avg_prod} tons (source: {source})"

    elif action == "max":
        if dataset == "rainfall" and "Annual_Rainfall" in df.columns:
            max_rain = df.loc[df["Annual_Rainfall"].idxmax()]
            result = f"Highest rainfall in {max_rain['State']} = {max_rain['Annual_Rainfall']} mm, Year = {int(max_rain['Year'])} (source: {source})"
        elif dataset == "crop" and "Production" in df.columns:
            max_prod = df.loc[df["Production"].idxmax()]
            year_str = str(max_prod["Year"])[:4]  # handle 2007-08 type
            result = f"Highest {max_prod['Crop']} production in {max_prod['State']} = {max_prod['Production']} tons, Year = {year_str} (source: {source})"

    elif action == "top" and dataset == "crop" and "Production" in df.columns:
        top_crops = (
            df.groupby("Crop")["Production"]
            .sum()
            .sort_values(ascending=False)
            .head(3)
            .index.tolist()
        )
        result = f"Top crops in {filters.get('state', 'India')} = {', '.join(top_crops)} (source: {source})"

    elif action == "trend" and dataset == "merged":
        trend = (
            df.groupby("Year")[["Annual_Rainfall", "Production"]]
            .mean()
            .reset_index()
        )
        st.line_chart(trend.set_index("Year"))
        result = f"Trend data ready for {filters.get('crop', 'selected crop')} in {filters.get('state', 'India')} (source: {source})"

    else:
        result = "Answer not available in dataset"

    return result


st.title("🌾 Indian Agriculture and Rainfall Q&A")
st.caption("Ask questions like 'Average rainfall in Maharashtra' or 'Top crops in Punjab'.")

st.sidebar.title("💡 Example Questions")
st.sidebar.write("""
- Average rainfall in Kerala  
- Highest rainfall in Tamil Nadu  
- Top crops in Madhya Pradesh  
- Trend of rainfall and crop production in Maharashtra  
- Average crop production in Punjab  
- Rainfall trend in Karnataka
""")

query = st.text_input("Type your question here:")

if st.button("Get Answer"):
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        dataset, action, filters = understand_query(query)
        answer = generate_answer(dataset, action, filters, crop_df, rain_df, merged_df)
        st.success(answer)
