# Import necessary libraries
import streamlit as st
import pandas as pd
import plotly.express as px
import re

# Set Streamlit page config
st.set_page_config(page_title="Startups Dashboard", page_icon="📊", layout="wide")

st.title("Startups Dashboard")
st.write("Welcome to the dashboard displaying data on startups!")

# Load the pre-cleaned datasets
founders_data = pd.read_csv("data/Cleaned_Founders_Data.csv")
startup_data = pd.read_csv("data/Cleaned_Startup_Data.csv")
deal_data = pd.read_csv("data/Cleaned_Deal_Data.csv")  # Load Deal Data

# Merge founders and startup data
merged_data = founders_data.merge(startup_data, left_on="Startup", right_on="Name", how="left")

# Merge startup data with deal data
startup_data = pd.merge(
    startup_data,
    deal_data[['Name', 'Cohort']],
    on='Name',
    how='left'
)

# Ensure "Year" column exists
if "Year" not in startup_data.columns:
    startup_data["Year"] = None

# Aggregate data to count startups per faculty, path, and status
faculty_path_status_distribution = merged_data.groupby(["Faculty", "Path", "Status"]).size().reset_index(name="Count")


startup_data_original = pd.read_csv('data/Cleaned_Startup_Data.csv')

# Define industry categories for classification
industry_categories = {
    "Technology": ["AI", "ML", "Blockchain", "Cybersecurity", "SaaS", "IOT", "Tech"],
    "Health": ["Health", "Healthcare", "Biotech", "Medtech", "Pharma"],
    "Education": ["Edtech", "Education", "Learning"],
    "Finance": ["Fintech", "Finance", "Banking", "Investment"],
    "Agriculture": ["Agritech", "Agriculture", "Farming"],
    "Retail": ["Retail", "Ecommerce", "Marketplace", "Shopping"],
    "Environment": ["Green", "Energy", "Sustainability", "CleanTech"],
    "Entertainment": ["Entertainment", "Media", "Gaming", "Music"],
    "Mobility": ["Automotive", "Mobility", "Transport", "Logistics"],
    "Other": ["Other", "General", "Miscellaneous"]
}

# Function to classify industries
def classify_industry(industry, categories):
    for category, keywords in categories.items():
        if any(keyword.lower() in industry.lower() for keyword in keywords):
            return category
    return "Uncategorized"

# Transform startup data
startup_data = startup_data_original.copy()
startup_data["Industry"] = startup_data["Industry"].fillna("").str.strip()
startup_data["Industry_Category"] = startup_data["Industry"].str.split(",")
startup_data = startup_data.explode("Industry_Category")
startup_data["Industry_Category"] = startup_data["Industry_Category"].str.strip()
startup_data["Classified_Category"] = startup_data["Industry_Category"].apply(
    lambda x: classify_industry(x, industry_categories)
)

# Merge with deal data
merged_data = pd.merge(
    startup_data, 
    deal_data[['Name', 'Cohort']], 
    on='Name', 
    how='left'
)

# Clean and transform the Cohort column
merged_data["Cohort_Copy"] = merged_data["Cohort"].copy()
start_year = 2019

def clean_cohort(value):
    if pd.isna(value) or value in ["Cactus Academy", "Checks"]:
        return None
    if value == "Current":
        return 12
    match = re.search(r'\d+', str(value))
    return int(match.group()) if match else None

merged_data["Cohort_Copy"] = merged_data["Cohort_Copy"].apply(clean_cohort)

# Add Year column
merged_data["Year"] = merged_data["Cohort_Copy"].apply(
    lambda x: start_year + ((x - 1) // 2) if pd.notna(x) else None
)
merged_data["Year"] = merged_data["Year"].astype("Int64")

# Filter out invalid Year rows
cleaned_data = merged_data[merged_data["Year"].notna()].reset_index(drop=True)

# ---------------------------------------------------------------------
# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a Visualization:",
    ["Bar Chart", "Pie Chart", "Trends & Cohort Analysis", "Applications & Industry Trends", "Startup Status Flow", "Graph 3", "Graph 4"]
)

# ---------------------------------------------------------------------
# Page Rendering Based on Selection

if page == "Bar Chart":
    st.title("Bar Chart: Faculty Distribution")

    # Status Filter (Positioned Below the Title)
    st.markdown("### Select Status Filter:")
    if "Status" in faculty_path_status_distribution.columns:
        status_options = ["All"] + sorted(faculty_path_status_distribution["Status"].dropna().unique().tolist())
        selected_status = st.selectbox("", status_options, key="status_filter_bar_chart", label_visibility="collapsed")

        # Filter data based on selection
        filtered_data = faculty_path_status_distribution.copy()
        if selected_status != "All":
            filtered_data = filtered_data[filtered_data["Status"] == selected_status]
    else:
        st.warning("'Status' column not found in the dataset. Filtering disabled.")
        filtered_data = faculty_path_status_distribution.copy()

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

elif page == "Pie Chart":
    st.title("Pie Chart: Faculty Proportions")

    # Pie Chart Visualization
    fig_pie = px.pie(
        faculty_path_status_distribution,
        names="Faculty",
        values="Count",
        title="Pie Chart of Faculty Distribution",
        hole=0.4,
        color="Faculty"
    )
    st.plotly_chart(fig_pie)

elif page == "Trends & Cohort Analysis":
    st.title("Trends & Cohort Analysis")

    # Move Filters to the Upper Side of the Chart
    col1, col2 = st.columns([1, 1])

    with col1:
        # **Filter by Faculty**
        if "Faculty" in merged_data.columns:
            faculty_list = ["All"] + sorted(merged_data["Faculty"].dropna().unique())
            selected_faculty = st.selectbox("Select Faculty", faculty_list, key="faculty_filter")

    with col2:
        # **Filter by Startup Type (Industry)**
        if "Industry" in merged_data.columns:
            industry_list = ["All"] + sorted(merged_data["Industry"].dropna().unique())
            selected_industry = st.selectbox("Select Startup Type", industry_list, key="industry_filter")

    # Apply Filters
    filtered_data = merged_data.copy()

    if selected_faculty != "All":
        filtered_data = filtered_data[filtered_data["Faculty"] == selected_faculty]

    if selected_industry != "All":
        filtered_data = filtered_data[
            filtered_data["Industry"].str.upper().str.contains(selected_industry, na=False, case=False)
        ]

    # Creating two columns for side-by-side visualization
    col1, col2 = st.columns(2)

    # Graph 1: Run Chart for Startups by Year
    with col1:
        st.subheader("Startups by Year (Click to Filter Cohorts)")

        if "Year" in filtered_data.columns:
            yearly_counts = filtered_data["Year"].value_counts().reset_index()
            yearly_counts.columns = ["Year", "Startup Count"]
            yearly_counts = yearly_counts.sort_values("Year")

            fig1 = px.line(
                yearly_counts,
                x="Year",
                y="Startup Count",
                markers=True,
                title="Trends in Number of Startups Over the Years (Run Chart)",
                labels={"Year": "Year", "Startup Count": "Number of Startups"},
            )
            st.plotly_chart(fig1)

            # Add a selection box for clicking a year
            selected_year = st.selectbox("Click on a year to filter the cohort chart:", yearly_counts["Year"])

    # Graph 2: Cohort (Semester) Distribution (Filtered by Selected Year)
    with col2:
        st.subheader(f"Startups by Cohort (Year: {selected_year})")

        if "Cohort_Copy" in filtered_data.columns:
            cohort_counts = filtered_data[filtered_data["Year"] == selected_year]["Cohort_Copy"].value_counts().reset_index()
            cohort_counts.columns = ["Cohort", "Startup Count"]
            cohort_counts = cohort_counts.sort_values("Cohort")

            fig2 = px.bar(
                cohort_counts,
                x="Cohort",
                y="Startup Count",
                title=f"Distribution of Startups by Cohort (Year: {selected_year})",
                labels={"Cohort": "Cohort (Semester)", "Startup Count": "Number of Startups"},
                text_auto=True
            )
            st.plotly_chart(fig2)

elif page == "Applications & Industry Trends":
    st.title("Applications & Industry Trends")

    # Ensure valid data exists before rendering
    if "Year" in startup_data.columns and "Classified_Category" in startup_data.columns:
        
        # Visualization 1: Applications Over the Years
        st.subheader("Number of Applications per Year")
        applications_per_year = startup_data["Year"].value_counts().sort_index()

        if not applications_per_year.empty:
            fig3 = px.bar(
                x=applications_per_year.index,
                y=applications_per_year.values,
                labels={"x": "Year", "y": "Number of Applications"},
                title="Number of Applications per Year",
                text=applications_per_year.values
            )
            fig3.update_traces(textposition="outside")
            st.plotly_chart(fig3)

        # Visualization 2: Industry Categories Over the Years
        st.subheader("Industry Categories Over the Years")
        industry_yearly_counts = (
            startup_data.groupby(["Year", "Classified_Category"])
            .size()
            .reset_index(name="Count")
        )

        if not industry_yearly_counts.empty:
            fig4 = px.bar(
                industry_yearly_counts,
                x="Year",
                y="Count",
                color="Classified_Category",
                title="Distribution of Industry Categories Over the Years",
                labels={"Year": "Year", "Count": "Number of Startups"},
                text="Count"
            )
            st.plotly_chart(fig4)
    else:
        st.warning("No valid data found for Applications or Industry Trends.")
# ---------------------------------------------------------------------
# Page Rendering Based on Selection

if page == "Status Quantities Sankey":
    st.title("Status Quantities (Sankey Diagram)")

    # Ensure "Status" column exists
    if "Status" in startup_data.columns:
        # Count the number of startups in each status
        status_counts = startup_data["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        # Create nodes (status labels)
        all_labels = status_counts["Status"].tolist()
        node_indices = {label: i for i, label in enumerate(all_labels)}

        # Create links (self-referencing to show quantities)
        sources = [node_indices[status] for status in status_counts["Status"]]
        targets = [node_indices[status] for status in status_counts["Status"]]  # Self-links
        values = status_counts["Count"].tolist()

        # Create Sankey Diagram
        fig_sankey = go.Figure(go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_labels
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values
            )
        ))

        fig_sankey.update_layout(title_text="Startup Status Quantities", font_size=12)
        st.plotly_chart(fig_sankey)

    else:
        st.warning("⚠️ The dataset does not contain a 'Status' column. Unable to generate the Sankey Diagram.")


elif page == "Graph 3":
    st.title("Interactive Dashboard: Applications Over the Years")

    if "Year" in cleaned_data.columns and "Classified_Category" in cleaned_data.columns:
        # Count applications per year
        applications_per_year = cleaned_data["Year"].value_counts().sort_index()

        fig = px.bar(
        x=applications_per_year.index,
        y=applications_per_year.values,
        labels={"x": "Year", "y": "Number of Applications"},
        title="Number of Applications per Year",
        text=applications_per_year.values
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    # Select a year for category breakdown
    selected_year = st.selectbox(
        "Select a year to view category breakdown:",
        options=applications_per_year.index.tolist(),
        help="Select a year to view its category breakdown"
    )

    if selected_year:
        category_data = cleaned_data[cleaned_data["Year"] == selected_year]
        category_counts = category_data["Classified_Category"].value_counts().sort_index()

        breakdown_fig = px.bar(
            x=category_counts.index,
            y=category_counts.values,
            labels={"x": "Category", "y": "Number of Applications"},
            title=f"Category Breakdown for {selected_year}",
            text=category_counts.values,
            color=category_counts.index,
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        breakdown_fig.update_traces(textposition="outside")
        st.plotly_chart(breakdown_fig)

elif page == "Graph 4":
    st.title("Dashboard: Industry Categories Over the Years")

    if "Year" in cleaned_data.columns and "Classified_Category" in cleaned_data.columns:
        # Group data by Year and Classified_Category
        industry_yearly_counts = (
            cleaned_data.groupby(["Year", "Classified_Category"])
            .size()
            .reset_index(name="Count")
        )

        # Get unique categories and define colors
        unique_categories = sorted(industry_yearly_counts["Classified_Category"].unique())
        accessible_colors = px.colors.qualitative.Set1
        category_colors = {
            category: accessible_colors[i % len(accessible_colors)]
            for i, category in enumerate(unique_categories)
        }

        # Create the bar chart for all categories
        fig2 = px.bar(
            industry_yearly_counts,
            x="Year",
            y="Count",
            color="Classified_Category",
            title="Distribution of Industry Categories Over the Years",
            labels={"Year": "Year", "Count": "Number of Startups"},
            text="Count",
            color_discrete_map=category_colors
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Add "All Categories" to the category selection dropdown
        all_categories_option = ["All Categories"] + unique_categories

        # Multiselect with "All Categories" functionality
        selected_categories = st.multiselect(
            "Select categories to compare their yearly trends:",
            options=all_categories_option,
            default=["All Categories"],  # Default to all categories
        )

        # Handle "All Categories" selection
        if "All Categories" in selected_categories:
            selected_categories = unique_categories  # Use all categories if "All Categories" is selected

        if selected_categories:
            # Filter data for the selected categories
            category_data = industry_yearly_counts[
                industry_yearly_counts["Classified_Category"].isin(selected_categories)
            ]

            # Create a line chart for the selected categories
            line_fig = px.line(
                category_data,
                x="Year",
                y="Count",
                color="Classified_Category",
                title="Yearly Trends for Selected Categories",
                labels={"Year": "Year", "Count": "Number of Startups", "Classified_Category": "Category"},
                color_discrete_map=category_colors
            )
            st.plotly_chart(line_fig)