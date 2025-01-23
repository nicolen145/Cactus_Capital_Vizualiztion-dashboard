# Import necessary libraries
import streamlit as st
import pandas as pd
import plotly.express as px
import re
import os
import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output
import time

# Set Streamlit page config
st.set_page_config(page_title="Cactus Capital Startups Dashboard", page_icon="🌵", layout="wide")
st.title("🌵 Cactus Capital fund for Startups 🌵")
# Dashboard description
st.markdown(
    """
    This dashboard analyzes investment trends at Cactus Capital, a student-run VC fund at Ben-Gurion University (BGU).  
    Our goal is to identify the key factors that increase a startup's chances of securing investment.  
    """
)

# Load the pre-cleaned datasets
founders_data = pd.read_csv("data/Cleaned_Founders_Data.csv")
startup_data = pd.read_csv("data/Cleaned_Startup_Data.csv")
deal_data = pd.read_csv("data/Cleaned_Deal_Data.csv") 



status_categories = {
    "Applied": ["Application", "Submitted"],
    "Selection Process": ["Introduced", "First Meeting", "Second Follow-Up", "Live Pitch Event", "Follow-Up Meeting"],
    "Considered but Not Invested": ["IC But Not Invested"],
    "Invested": ["Invested", "Funding Secured"],
    "Rejected": ["Denied", "Not Selected", "Opted Out"],
    "Other": ["Other", "Unknown", "Pending"]
}

# Define industry categories for classification
industry_categories = {
    "Technology": ["AI", "ML", "Blockchain", "Cybersecurity", "SaaS", "IOT", "Tech"],
    "Health": ["Health", "Healthcare", "Biotech", "Medtech", "Pharma"],
    "Education": ["Edtech", "Education", "Learning"],
    "Finance": ["Fintech", "Finance", "Banking", "Investment"],
    "Agriculture": ["Agritech", "Agriculture", "Farming"],
    "Retail": ["Retail", "Ecommerce", "Marketplace", "Shopping"],
    "Energy": ["Green", "Energy", "Sustainability", "CleanTech"],
    "Entertainment": ["Entertainment", "Media", "Gaming", "Music"],
    "Mobility": ["Automotive", "Mobility", "Transport", "Logistics"],
    "Manufacturing": ["Manufacturing", "Industrial", "Production", "Supply Chain"],
    "Food": ["FoodTech", "Beverage", "Restaurants", "Hospitality"],
    "Security": ["Defense", "Aerospace", "MilitaryTech", "Cybersecurity", "Privacy"],
    "Government": ["GovTech", "Public Sector", "Smart Cities"],
    "HR": ["HRTech", "Recruitment", "Hiring", "Talent Management"],
}


# Function to classify industries
def classify_industry(industry, categories):
    for category, keywords in categories.items():
        if any(keyword.lower() in industry.lower() for keyword in keywords):
            return category
    return "Other"

# Function to classify status
def classify_status(status, categories):
    for category, keywords in categories.items():
        if any(keyword.lower() in status.lower() for keyword in keywords):
            return category
    return "Other"

# Function to classify faculty
def classify_faculty(faculty):
    faculties = ['Business and Management','Cognitive science','Engineering','Health Sciences','Humanities and Social Sciences','Natural Sciences','Cyber Industry']
    if faculty in faculties:
        return faculty
    return "Not BGU"

founders_data["Faculty"] = founders_data["Faculty"].apply(lambda x: classify_faculty(x))

# Transform startup data
startup_data["Industry"] = startup_data["Industry"].fillna("").str.strip()
startup_data["Industry_Category"] = startup_data["Industry"].str.split(",")
startup_data = startup_data.explode("Industry_Category")
startup_data["Industry_Category"] = startup_data["Industry_Category"].str.strip()
startup_data["Industry_Category"] = startup_data["Industry_Category"].apply(
    lambda x: classify_industry(x, industry_categories)
)
startup_data["Status"] = startup_data["Status"].apply(
    lambda x: classify_industry(x, status_categories)
)



# Merge founders and startup data
merged_data = founders_data.merge(startup_data, left_on="Startup", right_on="Name", how="left")
# Aggregate data to count startups per faculty, path, and status
faculty_path_status_distribution = merged_data.groupby(["Faculty", "Path", "Status"]).size().reset_index(name="Count")
# Merge startup data with deal data
startup_data = pd.merge(
    startup_data,
    deal_data[['Name', 'Cohort','Year']],
    on='Name',
    how='left'
)
startup_data["Year"] = startup_data["Year"].astype("Int64")
# Merge datasets
merged_data_1 = pd.merge(founders_data, startup_data, left_on='Startup', right_on='Name', how='inner')
merged_data_1 = pd.merge(merged_data_1, deal_data, left_on='Startup', right_on='Name', how='left')

# Ensure "Year" column exists
if "Year" not in startup_data.columns:
    startup_data["Year"] = None


# Filter out invalid Year rows
cleaned_data = startup_data[merged_data["Year"].notna()].reset_index(drop=True)

# ---------------------------------------------------------------------
# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a Visualization:",
    ["Faculty Distribution","Industry Trends Over the Years","Gender Analysis in Startup Investment"]
)

# ---------------------------------------------------------------------
# Page Rendering Based on Selection

if page == "Faculty Distribution":
    st.title("Faculty Distribution")

    # Create two columns: One for the description (left), one for the filter (right)
    col1, col2 = st.columns([3, 2])  # Adjust column width as needed

    with col1:
        # Short explanatory paragraph on the left
        st.markdown("**The chart displays the number of startups per faculty, categorized by acceleration program.**")
        st.markdown("**The filter allows users to select a startup status (All, Invested, Rejected, or Selection Process) to analyze trends across faculties.**")

    with col2:
        # Status Filter on the right
        st.markdown("### Select Status Filter:")
        if "Status" in faculty_path_status_distribution.columns:
            # Keep only these specific status options
            allowed_statuses = ["All", "Invested", "Rejected", "Selection Process"]
            status_options = ["All"] + sorted(set(faculty_path_status_distribution["Status"].dropna()) & set(allowed_statuses))
            
            selected_status = st.selectbox("", status_options, key="status_filter_bar_chart", label_visibility="collapsed")

            # Filter data based on selection
            filtered_data = faculty_path_status_distribution.copy()
            if selected_status != "All":
                filtered_data = filtered_data[filtered_data["Status"] == selected_status]
        else:
            st.warning("'Status' column not found in the dataset. Filtering disabled.")
            filtered_data = faculty_path_status_distribution.copy()

    # Sort faculties alphabetically
    filtered_data = filtered_data.sort_values(by="Faculty")

    # Bar Chart Visualization
    fig_bar = px.bar(
        filtered_data,
        x="Faculty",
        y="Count",
        color="Path",
        barmode="group",
        title="Faculty Distribution",
        labels={"Faculty": "Faculty", "Count": "Number of Startups", "Path": "Acceleration Program"},
        height=500
    )

    st.plotly_chart(fig_bar)


# ---------------------------------------------------------------------
# Page Rendering Based on Selection

elif page == "Industry Trends Over the Years":
    st.title("Industry Trends Over the Years")

    if "Year" in cleaned_data.columns and "Industry_Category" in cleaned_data.columns:
        # Ensure Year is an integer and remove NaN values
        cleaned_data = cleaned_data.dropna(subset=["Year"])  
        cleaned_data["Year"] = cleaned_data["Year"].astype(int)  # Convert to integer

        # Group data by Year for overall trend (without breaking into industries)
        yearly_overall_counts = cleaned_data.groupby("Year").size().reset_index(name="Total Startups")

        # Group data by Year and Industry Category for category-specific trends
        industry_yearly_counts = (
            cleaned_data.groupby(["Year", "Industry_Category"])
            .size()
            .reset_index(name="Count")
        )

        # **12 Distinct Colorblind-Friendly Colors (CUD color palette)**
        color_palette = [
            "#332288", "#117733", "#44AA99", "#F0E442", "#88CCEE", "#DDCC77",
            "#CC6677", "#AA4499", "#882255", "#000000", "#0571B0", "#CA0020"
        ]  

        # Assign each industry category a unique color
        unique_categories = sorted(industry_yearly_counts["Industry_Category"].unique())
        category_colors = {category: color_palette[i % len(color_palette)] for i, category in enumerate(unique_categories)}

        # Layout: Explanation above, two columns for charts
        st.markdown("### Industry Trends Analysis")
        st.markdown(
            "**The first chart provides an overall picture of startup growth over the years, "
            "while the second chart allows users to compare specific industry categories.**"
        )

        # Create two columns
        col1, col2 = st.columns(2)

        with col1:
            # **Fixing the Bar Chart (Categorical X-axis)**
            fig_overall = px.bar(
                yearly_overall_counts,
                x=yearly_overall_counts["Year"].astype(str),  # Convert to string for categorical x-axis
                y="Total Startups",
                title="Overall Startup Growth Over the Years",
                labels={"x": "Year", "Total Startups": "Number of Startups"},
                text_auto=True,
                color_discrete_sequence=["#1f77b4"]  # Single blue color for clarity
            )
            st.plotly_chart(fig_overall, use_container_width=True)

        with col2:
            # Add "All Categories" option to the category selection dropdown
            all_categories_option = ["All Categories"] + unique_categories

            # Multiselect for category-specific trends
            selected_categories = st.multiselect(
                "Select categories to compare yearly trends:",
                options=all_categories_option,
                default=["All Categories"],
            )

            # Handle "All Categories" selection
            if "All Categories" in selected_categories:
                selected_categories = unique_categories  # Show all if "All Categories" is selected

            if selected_categories:
                # Filter data for the selected categories
                category_data = industry_yearly_counts[
                    industry_yearly_counts["Industry_Category"].isin(selected_categories)
                ]

                # **Fixing the Trends Line Chart (Continuous X-axis)**
                fig_category = px.line(
                    category_data,
                    x="Year",  # Use integer year values
                    y="Count",
                    color="Industry_Category",
                    title="Yearly Trends for Selected Categories",
                    labels={"Year": "Year", "Count": "Number of Startups", "Industry_Category": "Category"},
                    color_discrete_map=category_colors
                )

                # **Ensure X-axis only shows whole years**
                fig_category.update_xaxes(
                    tickmode="array",
                    tickvals=sorted(industry_yearly_counts["Year"].unique()),  # Force integer years
                    ticktext=[str(year) for year in sorted(industry_yearly_counts["Year"].unique())]  # Display as string
                )

                st.plotly_chart(fig_category, use_container_width=True)


# ---------------------------------------------------------------------
# Page Rendering Based on Selection
if page == "Gender Analysis in Startup Investment":
    # Title and description
    data = merged_data_1
    st.title('Gender Analysis in Startup Investment')

    # Filter only relevant paths
    relevant_paths = ['The LAUNCHER', 'The KICKSTARTER']
    data = data[data['Path_x'].isin(relevant_paths)]

    # Define consistent colors for gender categories
    gender_colors = {
        'Female': '#FF69B4',  # Pink
        'Male': '#1f77b4',    # Blue
        'Prefer not to disclose': '#9467bd'  # Purple
    }

    # Layout: Two columns for Pie Chart (left) and Bar Chart (right)
    st.header('Gender Distribution and Investment Progress')
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            "**This section provides an overview of gender representation among startup founders.** "
            "The pie chart shows the total number of founders from each gender, helping to visualize "
            "disparities in startup leadership."
        )

        # Overall Founders by Gender Pie Chart
        founders_by_gender = (
            data.groupby('Gender')['Num Of Founders']
            .sum()
            .reset_index()
        )
        founders_by_gender.columns = ['Gender', 'Count']

        fig1 = px.pie(
            founders_by_gender,
            names='Gender',
            values='Count',
            title='Total Founders by Gender',
            hole=0.3,
            color='Gender', 
            color_discrete_map=gender_colors  # Apply gender-specific colors
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Move path filter above the bar chart
        paths = ["All Paths"] + list(data["Path_x"].unique())  # Allow filtering by path
        selected_path = st.selectbox('Select Program Path:', paths, index=0)

        if selected_path != "All Paths":
            data = data[data["Path_x"] == selected_path]

        # Add explanation above the bar chart
        st.markdown(
            "**This bar chart shows how founders of different genders progress through the investment process.** "
            "Each bar represents the number of founders who reached each stage: 'Invested', 'Rejected', "
            "or are still in the 'Selection Process'."
        )

        key_statuses = ["Invested", "Rejected", "Selection Process"]
        status_gender_counts = (
            data[data['Status_x'].isin(key_statuses)]
            .groupby(['Status_x', 'Gender'])['Num Of Founders']
            .sum()
            .reset_index()
        )

        fig2 = px.bar(
            status_gender_counts, 
            x='Status_x', 
            y='Num Of Founders', 
            color='Gender', 
            title='Founders by Gender Across Investment Stages', 
            barmode='group',
            labels={"Status_x": "Application Status", "Num Of Founders": "Number of Founders"},
            color_discrete_map=gender_colors  # Ensure consistent colors
        )
        st.plotly_chart(fig2, use_container_width=True)



# ---------------------------------------------------------------------
