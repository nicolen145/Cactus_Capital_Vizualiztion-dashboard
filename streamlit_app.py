# Import necessary libraries
import streamlit as st
import pandas as pd
import plotly.express as px

# Set the page configuration
st.set_page_config(
    page_title="Startup Faculty Distribution",
    page_icon=":bar_chart:",
)

# ---------------------------------------------------------------------
# Load datasets

@st.cache_data
def load_data():
    """Load and merge the founders and startup data."""
    
    # Adjust these paths based on where your CSVs are stored in Codespaces
    founders_data = pd.read_csv("data/Cleaned_Founders_Data.csv")
    startup_data = pd.read_csv("data/Cleaned_Startup_Data.csv")
    
    # Merge founders and startup data to associate faculties with acceleration programs and status
    merged_data = founders_data.merge(startup_data, left_on="Startup", right_on="Name", how="left")

    return merged_data

merged_data = load_data()

# Aggregate data to count startups per faculty, acceleration program, and status
faculty_path_status_distribution = merged_data.groupby(["Path", "Status", "Faculty"]).size().reset_index(name="Count")

# ---------------------------------------------------------------------
# Draw the interactive page

st.title(":bar_chart: Startup Faculty Distribution")

st.markdown("""
This dashboard visualizes the **distribution of startups** across **different faculties**, **acceleration programs**, and **status levels**.
""")

# Dropdown for acceleration program with "All" option
path_options = ["All"] + sorted(faculty_path_status_distribution["Path"].dropna().unique().tolist())
selected_path = st.selectbox("Select an Acceleration Program", path_options)

# Dropdown for status with "All" option
status_options = ["All"] + sorted(faculty_path_status_distribution["Status"].dropna().unique().tolist())
selected_status = st.selectbox("Select a Status", status_options)

# Filter data based on selection
filtered_data = faculty_path_status_distribution.copy()
if selected_path != "All":
    filtered_data = filtered_data[filtered_data["Path"] == selected_path]
if selected_status != "All":
    filtered_data = filtered_data[filtered_data["Status"] == selected_status]

# Create an interactive bar chart
fig = px.bar(
    filtered_data,
    x="Faculty",
    y="Count",
    color="Path",  # Color by acceleration program for better visualization
    barmode="group",
    title=f"Faculty Distribution for {selected_path if selected_path != 'All' else 'All Paths'} - {selected_status if selected_status != 'All' else 'All Statuses'}",
    labels={"Faculty": "Faculty", "Count": "Number of Startups", "Path": "Acceleration Program"},
    height=600
)

# Show the plot
st.plotly_chart(fig)
