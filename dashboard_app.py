import pandas as pd
import numpy as np
import streamlit as st
# from streamlit.components.v1 import html
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



# def login_page():
#     st.title("Login")
#     username = st.text_input("Username")
#     password = st.text_input("Password", type="password")
#     if st.button("Login"):
#         user_role = check_credentials(username, password)
#         if user_role:
#             st.success(f"Logged in as {user_role}")
#         return user_role
#         else:
#             st.error("Invalid credentials")
#         return None


# def check_credentials(username, password):
#     if username in users and users[username]['password'] == password:
#         return users[username]['role']
#     return None

def categorize_age(age):
    if age <= 6:
        return "0-6"
    elif age <= 12:
        return "7-12"
    elif age <= 18:
        return "13-18"
    elif age <= 24:
        return "19-24"
    else:
        return "25+"
    
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


def bar_chart_age_sex(filtered_df):
    yes_grouped = filtered_df[filtered_df['curr_ll'] == 'yes'].groupby(['age_group', 'sex']).size().reset_index(name='curr_ll')

    all_age_groups = pd.DataFrame({
        'age_group': ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]
    })

    pivot_table = yes_grouped.pivot_table(index='age_group', columns='sex', values='curr_ll', fill_value=0).reset_index()

    pivot_table.columns.name = None
    pivot_table.reset_index(drop=True, inplace=True)

    merged_grouped_data = all_age_groups.merge(pivot_table, on='age_group', how='left').fillna(0)

    value_vars = [col for col in ['Male', 'Female'] if col in merged_grouped_data.columns]
    melted_grouped_data = pd.melt(merged_grouped_data, id_vars=['age_group'], value_vars=value_vars, var_name='sex', value_name='curr_ll')

    bar_chart = alt.Chart(melted_grouped_data).mark_bar().encode(
        x=alt.X('age_group:O', sort=["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]),
        y=alt.Y('curr_ll:Q'),
        color='sex:N',
        tooltip=['age_group', 'sex', 'curr_ll']
    )

    st.write("<h3 align='center'>TX_Curr by Age and Sex</h3>", unsafe_allow_html=True)
    st.altair_chart(bar_chart, use_container_width=True)


def bar_chart_age_sex1(filtered_df):
    #print("Original filtered_df:\n", filtered_df.head())
    yes_grouped = filtered_df[filtered_df['curr_ll'] == 'yes'].groupby(['age_group', 'sex']).size().reset_index(name='curr_ll')
    #print("yes_grouped:\n", yes_grouped.head())

    all_age_groups = pd.DataFrame({
        'age_group': ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]
    })

    pivot_table = yes_grouped.pivot_table(index='age_group', columns='sex', values='curr_ll', fill_value=0).reset_index()

    pivot_table.columns.name = None
    pivot_table.reset_index(drop=True, inplace=True)

    merged_grouped_data = all_age_groups.merge(pivot_table, on='age_group', how='left').fillna(0)

    value_vars = [col for col in ['Male', 'Female'] if col in merged_grouped_data.columns]
    melted_grouped_data = pd.melt(merged_grouped_data, id_vars=['age_group'], value_vars=value_vars, var_name='sex', value_name='curr_ll')

    age_group_order = ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]

    melted_grouped_data['age_group'] = pd.Categorical(melted_grouped_data['age_group'], categories=age_group_order, ordered=True)
    melted_grouped_data = melted_grouped_data.sort_values(['age_group', 'sex'])

    melted_grouped_data['direction'] = melted_grouped_data['sex'].apply(lambda x: -1 if x == 'Male' else 1)
    melted_grouped_data['curr_ll'] = melted_grouped_data['curr_ll'] * melted_grouped_data['direction']

    bar_chart = alt.Chart(melted_grouped_data).mark_bar().encode(
        y=alt.Y('age_group:O', axis=alt.Axis(title='Age Group'), sort=age_group_order),
        x=alt.X('curr_ll:Q', axis=alt.Axis(title='TX_Curr')),
        color='sex:N',
        tooltip=['age_group', 'sex', alt.Tooltip('curr_ll:Q', format=',.0f')]
    ).properties(
        height=600  # Set the desired height of the chart
    )

    st.write("<h3 align='center'>TX_Curr by Age and Sex</h3>", unsafe_allow_html=True)
    st.altair_chart(bar_chart, use_container_width=True)

def bar_chart_tx_age(filtered_df):
    filtered_df['tx_age_group'] = filtered_df['tx_age'].apply(categorize_age)
    yes_data = filtered_df[filtered_df['curr_ll'] == 'yes']
    yes_grouped = yes_data.groupby('tx_age_group')['curr_ll'].count().reset_index()

    all_tx_age_groups = pd.DataFrame({
        'tx_age_group': ["0-6", "7-12", "13-18", "19-24", "25+"]
    })

    merged_yes_grouped = all_tx_age_groups.merge(yes_grouped, on='tx_age_group', how='left').fillna(0)

    bar_chart = alt.Chart(merged_yes_grouped).mark_bar().encode(
        x=alt.X('tx_age_group:O', axis=alt.Axis(title='Treatment Age (Months)'), sort=["0-6", "7-12", "13-18", "19-24", "25+"]),
        y=alt.Y('curr_ll:Q', axis=alt.Axis(title='TX_Curr')),
        tooltip=['tx_age_group', 'curr_ll']
    )

    st.write("<h3 align='center'>TX_Curr by Tx_age</h3>", unsafe_allow_html=True)
    st.altair_chart(bar_chart, use_container_width=True)

def scatter_plot_tx_age(filtered_df):
    scatter_plot = alt.Chart(filtered_df).mark_circle(size=60).encode(
        x='tx_age',
        y='curr_ll',
        tooltip=['tx_age', 'curr_ll']
    ).interactive()

    st.write("<h3 align='center'>Scatter plot of tx_age vs Tx_Curr</h3>", unsafe_allow_html=True)
    st.altair_chart(scatter_plot, use_container_width=True)

def display_facility_table(facility_df):
    
    st.write("<h3 align='center'>Facility Table</h3>", unsafe_allow_html=True)
    st.dataframe(facility_df)


def page_1(filtered_df):
    # Your visualizations for page 1
    bar_chart_age_sex(filtered_df)
    bar_chart_age_sex1(filtered_df)
    #bar_chart_age_sex2(filtered_df)

def page_2(filtered_df):
    # Your visualizations for page 2
    bar_chart_tx_age(filtered_df)

def page_3(filtered_df):
    # Your visualizations for page 3
    scatter_plot_tx_age(filtered_df)

def page_4(filtered_df):
    # Your visualizations for page 3
    display_facility_table(filtered_df)

# Add more functions for additional pages as needed




def main():
    # Title
    # Add the title with the center align attribute
    st.write("<h1 align='center'>Analytics Dashboard</h1>", unsafe_allow_html=True)


    # Load DataEntry data
        # Load DataEntry data
    data_entry_query = text("SELECT * FROM data_entry")  # Replace 'data_entry' with the correct table name
    data_entry_result = session.execute(data_entry_query)
    data_entry_df = pd.DataFrame(data_entry_result.fetchall(), columns=data_entry_result.keys())

    # Load Facility data
    facility_query = text("SELECT * FROM facility")  # Replace 'facility' with the correct table name
    facility_result = session.execute(facility_query)
    facility_df = pd.DataFrame(facility_result.fetchall(), columns=facility_result.keys())

    # Merge the facility table with the data_entry table on facility_name
    merged_df = data_entry_df.merge(facility_df, on='facility_name', how='left')
    merged_df['age_group'] = merged_df['age'].apply(age_group) 

    
    # Create a sidebar expander for filters
    with st.expander("Filters", expanded=True):
        # Create columns for filters
        col1, col2, col3, col4, col5 = st.columns(5)

        # State filter
        with col1:
            selected_state = st.multiselect("Select State", options=['All'] + list(facility_df['state'].unique()), default=['All'])

        # LGA filter
        with col2:
            selected_lga = st.multiselect("Select LGA", options=['All'] + list(facility_df['lga'].unique()), default=['All'])

        # Facility name filter
        with col3:
            selected_facility = st.multiselect("Select Facility", options=['All'] + list(data_entry_df['facility_name'].unique()), default=['All'])

        # Sex filter
        with col4:
            selected_sex = st.multiselect("Select Sex", options=['All'] + list(data_entry_df['sex'].unique()), default=['All'])

        # Age group filter
        with col5:
            all_age_groups = ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]
            selected_age_group = st.multiselect("Select Age Group", options=['All'] + all_age_groups, default=['All'])


    
    filtered_df = merged_df.copy()
    filtered_df['curr_ll'] = filtered_df['curr_ll'].str.lower().str.strip()

    # Filter the data based on the selected filters
    if 'All' not in selected_state:
        filtered_df = filtered_df[filtered_df['state'].isin(selected_state)]

    if 'All' not in selected_lga:
        filtered_df = filtered_df[filtered_df['lga'].isin(selected_lga)]

    if 'All' not in selected_facility:
        filtered_df = filtered_df[filtered_df['facility_name'].isin(selected_facility)]

    if 'All' not in selected_sex:
        filtered_df = filtered_df[filtered_df['sex'].isin(selected_sex)]
    if 'All' not in selected_age_group:
        filtered_df = filtered_df[filtered_df['age_group'].isin(selected_age_group)]

    # Call the visualization functions with the filtered dataframe
    # bar_chart_age_sex(filtered_df)
    # bar_chart_tx_age(filtered_df)
    # scatter_plot_tx_age(filtered_df)
    # display_facility_table(filtered_df)

    # Create a custom sidebar tab navigation using buttons and session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Page 1"

    if st.sidebar.button("Page 1"):
        st.session_state.current_page = "Page 1"
    if st.sidebar.button("Page 2"):
        st.session_state.current_page = "Page 2"
    if st.sidebar.button("Page 3"):
        st.session_state.current_page = "Page 3"
    if st.sidebar.button("Page 4"):
        st.session_state.current_page = "Page 4"
    # Add more buttons for additional pages as needed

    # Display the selected page
    if st.session_state.current_page == "Page 1":
        page_1(filtered_df)
    elif st.session_state.current_page == "Page 2":
        page_2(filtered_df)
    elif st.session_state.current_page == "Page 3":
        page_3(filtered_df)
    elif st.session_state.current_page == "Page 4":
        page_4(filtered_df)
    # Add more conditional statements for additional pages as needed

    # # Create a sidebar selectbox for page navigation
    # page = st.sidebar.selectbox("Choose a page", ["Page 1", "Page 2", "Page 3", "Page 4", "Page 5", "Page 6", "Page 7", "Page 8", "Page 9", "Page 10"])

    # # Display the selected page
    # if page == "Page 1":
    #     page_1(filtered_df)
    # elif page == "Page 2":
    #     page_2(filtered_df)
    # elif page == "Page 3":
    #     page_3(filtered_df)
    # elif page == "Page 4":
    #     page_4(filtered_df)
    # # elif page == "Page 5":
    # #     page_5(filtered_df)
    # # # Add more conditional statements for additional pages as needed
    # # elif page == "Page 6":
    # #     # ...
    # # elif page == "Page 7":
    # #     # ...
    # # elif page == "Page 8":
    # #     # ...
    # # elif page == "Page 9":
    # #     # ...
    # # elif page == "Page 10":
    #     # ...

if __name__ == "__main__":
    main()
