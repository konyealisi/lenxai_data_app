import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import pydeck as pdk
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


# Set the default layout to wide mode
st.set_page_config(layout="wide")

# Database connection settings
db_user = os.environ.get('DB_USER_ndqadata')
db_password = os.environ.get('DB_PASSWORD_ndqadata')
db_host = os.environ.get('DB_HOST_ndqadata')
db_name = os.environ.get('DB_NAME_ndqadata') 

# Connect to the database
db_url = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

def categorize_age(age):
    if age <= 6:
        return "0 <= age <= 6"
    elif age <= 12:
        return "6 < age <= 12"
    elif age <= 18:
        return "12 < age <= 18"
    elif age <= 24:
        return "18 < age <= 24"
    else:
        return "age > 24"
    
def age_group(age):
    if age < 1:
        return "<1"
    elif 1 <= age <= 4:
        return "1-4"
    elif 5 <= age <= 9:
        return "5-9"
    elif 10 <= age <= 14:
        return "10-14"
    elif 15 <= age <= 19:
        return "15-19"
    elif 20 <= age <= 24:
        return "20-24"
    elif 25 <= age <= 29:
        return "25-29"
    elif 30 <= age <= 34:
        return "30-34"
    elif 35 <= age <= 39:
        return "35-39"
    elif 40 <= age <= 44:
        return "40-44"
    elif 45 <= age <= 49:
        return "45-49"
    elif 50 <= age <= 54:
        return "50-54"
    elif 55 <= age <= 59:
        return "55-59"
    elif 60 <= age <= 64:
        return "60-64"
    else:
        return "65+"


def main():
    # Title
    st.title("Analytics Dashboard")

    # Load DataEntry data
    data_entry_query = text("SELECT * FROM data_entry")  # Replace 'data_entry' with the correct table name
    data_entry_result = session.execute(data_entry_query)
    data_entry_df = pd.DataFrame(data_entry_result.fetchall(), columns=data_entry_result.keys())

    # Load Facility data
    facility_query = text("SELECT * FROM facility")  # Replace 'facility' with the correct table name
    facility_result = session.execute(facility_query)
    facility_df = pd.DataFrame(facility_result.fetchall(), columns=facility_result.keys())

    # Add your Streamlit visualizations and data processing here

    

    
    # Merge the facility table with the data_entry table on facility_name
    merged_df = data_entry_df.merge(facility_df, on='facility_name', how='left')

    # Create columns for filters
    col1, col2, col3 = st.columns(3)

    # State filter
    with col1:
        selected_state = st.selectbox("Select State", options=['All'] + list(merged_df['state'].unique()))
        if selected_state != 'All':
            merged_df = merged_df[merged_df['state'] == selected_state]

    # LGA filter
    with col2:
        selected_lga = st.selectbox("Select LGA", options=['All'] + list(merged_df['lga'].unique()))
        if selected_lga != 'All':
            merged_df = merged_df[merged_df['lga'] == selected_lga]

    # Facility name filter
    with col3:
        selected_facility = st.selectbox("Select Facility", options=['All'] + list(merged_df['facility_name'].unique()))
        if selected_facility != 'All':
            merged_df = merged_df[merged_df['facility_name'] == selected_facility]

    # Create age_group column
    merged_df['age_group'] = merged_df['age'].apply(age_group)

    # Group the data by 'age_group' and 'sex', and calculate the sum of 'curr_ll_yes'
    yes_grouped = merged_df[merged_df['curr_ll'] == 'yes'].groupby(['age_group', 'sex']).size().reset_index(name='curr_ll')

    # Create a DataFrame containing all age groups
    all_age_groups = pd.DataFrame({
        'age_group': ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]
    })

    # Create a pivot table with 'yes' counts for each age group and sex
    pivot_table = yes_grouped.pivot_table(index='age_group', columns='sex', values='curr_ll', fill_value=0).reset_index()

    # Reset the column names after pivoting
    pivot_table.columns.name = None
    pivot_table.reset_index(drop=True, inplace=True)

    # Merge all_age_groups with the pivot_table
    merged_grouped_data = all_age_groups.merge(pivot_table, on='age_group', how='left').fillna(0)

    # Melt the merged_grouped_data back into a long format
    value_vars = [col for col in ['Male', 'Female'] if col in merged_grouped_data.columns]
    melted_grouped_data = pd.melt(merged_grouped_data, id_vars=['age_group'], value_vars=value_vars, var_name='sex', value_name='curr_ll')


    # Bar chart of the count of 'yes' in curr_ll by age group and sex
    bar_chart = alt.Chart(melted_grouped_data).mark_bar().encode(
        x=alt.X('age_group:O', sort=["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]),
        y=alt.Y('curr_ll:Q'),
        color='sex:N',
        tooltip=['age_group', 'sex', 'curr_ll']
    )

    st.subheader("TX_Curr by Age and Sex")
    st.altair_chart(bar_chart, use_container_width=True)

    
    #Bar plot - Tx_Curr by Tx_age Group
    # Categorize tx_age into age groups
    data_entry_df['tx_age_group'] = data_entry_df['tx_age'].apply(categorize_age)

    # Filter rows with 'yes' in curr_ll
    yes_data = data_entry_df[data_entry_df['curr_ll'] == 'yes']

    # Group by age_group and calculate the average count of 'yes'
    yes_grouped = yes_data.groupby('tx_age_group')['curr_ll'].count().reset_index()

    # Create a DataFrame containing all age groups
    all_tx_age_groups = pd.DataFrame({
        'tx_age_group': ["0 <= age <= 6", "6 < age <= 12", "12 < age <= 18", "18 < age <= 24", "age > 24"]
    })

    # Merge with yes_grouped, filling missing counts with 0
    merged_yes_grouped = all_tx_age_groups.merge(yes_grouped, on='tx_age_group', how='left').fillna(0)

    # Bar chart of average count of 'yes' in curr_ll by age group
    bar_chart = alt.Chart(merged_yes_grouped).mark_bar().encode(
        x='tx_age_group:O',
        y='curr_ll:Q',
        tooltip=['tx_age_group', 'curr_ll']
    )


    st.subheader("TX_Curr by Tx_age")
    st.altair_chart(bar_chart, use_container_width=True)

   # Scatter plot of tx_age vs curr_ll
    scatter_plot = alt.Chart(data_entry_df).mark_circle(size=60).encode(
        x='tx_age',
        y='curr_ll',
        tooltip=['tx_age', 'curr_ll']
    ).interactive()

    st.subheader("Scatter plot of tx_age vs Tx_Curr")
    st.altair_chart(scatter_plot, use_container_width=True)

    st.subheader("Facility")
    st.dataframe(facility_df)
    
if __name__ == "__main__":
    main()