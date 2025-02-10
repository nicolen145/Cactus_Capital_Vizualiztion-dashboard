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
    "Technology": ["AI", "ML", "Blockchain", "Cybersecurity", "SaaS", "IOT", "Tech","Mobile","Space","Engineering","Online Services","Sensors","AR/VR","Renewal","Web App","Time Management","Waste Management","ECO Engineering","Industry", "Time managment"],
    "Health": ["Health", "Healthcare", "Biotech", "Medtech", "Pharma"],
    "Education": ["Edtech", "Education", "Learning","Student","Ebooks","Non Profit","Private Teachers","Currently Student","Study Geography and Economics"],
    "Finance": ["Fintech", "Finance", "Banking", "Investment","Financial","Financial Security","Content Creators Economy","Business","Content creators economy"],
    "Agriculture": ["Agritech", "Agriculture", "Farming","Recycling"],
    "Retail": ["Retail", "Ecommerce", "Marketplace", "Shopping", "Real Estate","Job Market","Construction"],
    "Energy": ["Green", "Energy", "Sustainability", "CleanTech","Environmental"],
    "Entertainment": ["Entertainment", "Media", "Gaming", "Music","Dating","Tourism Platforms","Matchmaking & Dating","Dating App","Tourism","Sports App","Social","Events","Beauty","News and Magazine/Productivity"],
    "Mobility": ["Automotive", "Mobility", "Transport", "Logistics","Parkings"],
    "Manufacturing": ["Manufacturing", "Industrial", "Production", "Supply Chain"],
    "Food": ["FoodTech", "Beverage", "Restaurants", "Hospitality","מסעדה","Cook"],
    "Security": ["Defense", "Aerospace", "MilitaryTech", "Cybersecurity", "Privacy","Safety clothing","Security","Cyber","Women’s Safety","Earthquake Resistance","Safety","Earthquakes resistance"],
    "Government": ["GovTech", "Public Sector", "Smart Cities","Government","Services","Legal"],
    "HR": ["HRTech", "Recruitment", "Hiring", "Talent Management"],
}


# Function to classify industries
def classify_industry(industry, categories):
    for category, keywords in categories.items():
        if any(keyword.lower() in industry.lower() for keyword in keywords):
            return category

# Function to classify status
def classify_status(status, categories):
    for category, keywords in categories.items():
        if any(keyword.lower() in status.lower() for keyword in keywords):
            return category
    return "Other"

# Function to classify faculty
def classify_faculty(faculty):
    faculties = ['Business and Management','Cognitive Science','Engineering','Health Sciences','Humanities and Social Sciences','Natural Sciences','Cyber Industry']
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
    "Select Page:",
    ["🏠 Home", "📊 Faculty Distribution", "📈 Industry Trends Over the Years", "👥 Gender Analysis in Startup Investment"]
)

# Home Page
if page == "🏠 Home":
    st.title("🌵 Cactus Capital Fund for Startups 🌵")

    st.markdown(
        """
        Welcome to the **Cactus Capital Investment Dashboard**, an interactive tool designed to analyze investment trends at 
        **Cactus Capital**, the student-run VC fund at Ben-Gurion University (BGU).  
        Our goal is to uncover the key factors that contribute to a startup’s success in securing funding.  

        ---
        
        ### 📌 Dashboard Sections:
        - **📊 Faculty Distribution:** Understanding which faculties at BGU contribute the most to startup creation.  
        - **📈 Industry Trends Over the Years:** Tracking startup growth and industry investment patterns.  
        - **👥 Gender Analysis in Startup Investment:** Exploring the impact of gender on funding success.  

        ---
        
        🔍 **Use this dashboard to gain insights into startup investments and understand what drives success in the VC world!**  
        """
    )
# ---------------------------------------------------------------------
# Page Rendering Based on Selection

if page == "📊 Faculty Distribution":
    st.title("Faculty Distribution")

    # Create two columns: One for the description (left), one for the filter (right)
    col1, col2 = st.columns([3, 2])  # Adjust column width as needed

    with col1:
        # Short explanatory paragraph on the left
        st.markdown("##### **The chart displays the number of startups per faculty, categorized by acceleration program.**")
        st.markdown("##### **The filter allows users to select a startup status (All, Invested, Rejected, or Selection Process) to analyze trends across faculties.**")

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

elif page == "📈 Industry Trends Over the Years":
    st.title("Industry Trends Over the Years Analysis")

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

        # 12 Distinct Colorblind-Friendly Colors (CUD color palette)
        color_palette = [
            "#332288", "#117733", "#44AA99", "#F0E442", "#88CCEE", "#DDCC77",
            "#CC6677", "#AA4499", "#882255", "#000000", "#0571B0", "#CA0020"
        ]

        # Assign each industry category a unique color
        unique_categories = sorted(industry_yearly_counts["Industry_Category"].unique())
        category_colors = {category: color_palette[i % len(color_palette)] for i, category in enumerate(unique_categories)}

        st.markdown("##### This section provides insights into startup investment trends.\n"
            "##### The bar chart shows startup growth trends over the years,\n"
            "##### while the line chart compares industry categories to highlight market dynamics and opportunities,\n"
            "##### helping to identify key areas of innovation and investment potential.")




        col1, col2 = st.columns(2)

        with col1:
            # Overall Startup Growth Chart
            fig_overall = px.bar(
                yearly_overall_counts,
                x=yearly_overall_counts["Year"].astype(str),  # Convert to string for categorical x-axis
                y="Total Startups",
                title="Overall Startup Growth Over the Years",
                labels={"x": "Year", "Total Startups": "Number of Startups"},
                text_auto=True,
                color_discrete_sequence=["#1f77b4"]  # Single blue color for clarity
            )

            # Ensure X-axis only shows whole years
            fig_overall.update_xaxes(
                tickmode="array",
                tickvals=sorted(industry_yearly_counts["Year"].unique()),  # Force integer years
                ticktext=[str(year) for year in sorted(industry_yearly_counts["Year"].unique())]  # Display as string
            )
            fig_overall.update_layout(height=535)
            st.plotly_chart(fig_overall, use_container_width=True)

        with col2:
            # Add "All Categories" option to the category selection dropdown
            all_categories_option = ["All Categories"] + unique_categories

            # Multiselect for category-specific trends
            selected_categories = st.multiselect(
                "Select categories to compare yearly trends:",
                options=all_categories_option,
                default=["All Categories"]
            )

            # Handle "All Categories" selection
            if "All Categories" in selected_categories:
                selected_categories = unique_categories  # Show all if "All Categories" is selected

            if selected_categories:
                # Filter data for the selected categories
                category_data = industry_yearly_counts[
                    industry_yearly_counts["Industry_Category"].isin(selected_categories)
                ]

                # Category Specific Trends Chart
                fig_category = px.line(
                    category_data,
                    x="Year",  # Use integer year values
                    y="Count",
                    color="Industry_Category",
                    title="Yearly Trends for Selected Categories",
                    labels={"Year": "Year", "Count": "Number of Startups", "Industry_Category": "Category"},
                    color_discrete_map=category_colors
                )

                # Ensure X-axis only shows whole years
                fig_category.update_xaxes(
                    tickmode="array",
                    tickvals=sorted(industry_yearly_counts["Year"].unique()),  # Force integer years
                    ticktext=[str(year) for year in sorted(industry_yearly_counts["Year"].unique())]  # Display as string
                )
                
                st.plotly_chart(fig_category, use_container_width=True)


# ---------------------------------------------------------------------
# Page Rendering Based on Selection
if page == "👥 Gender Analysis in Startup Investment":
    # Title and description
    data = merged_data_1
    st.title('Gender Analysis in Startup Investment')
    st.markdown("##### **This section provides an overview of gender representation among startup founders.**\n"
            "##### The pie chart visualizes the total number of founders by gender, highlighting disparities in leadership.\n\n"
            "##### **The bar chart illustrates how founders progress through the investment process.**\n"
            "##### It shows the proportions of those invested, rejected, or still in selection.")



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

    col1, col2 = st.columns(2)

    with col1:
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
        fig1.update_layout(height=430)
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Move path filter above the bar chart
        paths = ["All Paths"] + list(data["Path_x"].unique())  # Allow filtering by path
        selected_path = st.selectbox('Select Program Path:', paths, index=0)

        if selected_path != "All Paths":
            data = data[data["Path_x"] == selected_path]

        

        key_statuses = ["Invested", "Rejected", "Selection Process"]
        filtered_data = data[data['Status_x'].isin(key_statuses)]
        status_gender_counts = (
            filtered_data.groupby(['Status_x', 'Gender'])['Num Of Founders']
            .sum()
            .reset_index()
        )

        

        # Bar chart showing investment stages by gender in percentage
        status_gender_counts = filtered_data.groupby(['Status_x', 'Gender']).size().reset_index(name='Count')
        total_by_gender = filtered_data.groupby('Gender').size().reset_index(name='Total')
        status_gender_counts = status_gender_counts.merge(total_by_gender, on='Gender')
        status_gender_counts['Percentage'] = (status_gender_counts['Count'] / status_gender_counts['Total']) * 100
        
        fig2 = px.bar(
            status_gender_counts,
            x='Status_x',
            y='Percentage',
            color='Gender',
            title='Percentage of Founders by Gender Across Investment Stages',
            labels={"Status_x": "Application Status", "Percentage": "Percentage of Founders"},
            color_discrete_map=gender_colors,
            barmode='group'
        )
        st.plotly_chart(fig2, use_container_width=True)



# ---------------------------------------------------------------------
