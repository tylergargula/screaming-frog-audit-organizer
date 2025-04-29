import streamlit as st
import os
import pandas as pd
import plotly.express as px
import re
import tempfile
from src.data import clean_data, label_data
from src.utils import generate_embeddings, export_streamlit_data
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


st.set_page_config(page_title="Screaming Frog Tech Audit Prioritizer", layout="wide")


def show_intro_content():
    """Display introduction and explanation of the app"""
    st.markdown("""
    # Screaming Frog Tech Audit Prioritizer 🐸⚡️

    Create a prioritized list of issues from Screaming Frog's tech audit based on level of impact. This tool uses a custom prioritization algorithm to label issues based on factors like:
    * **Organic Traffic:** The traffic of affected pages
    * **Issue Type:** Warning, Opportunity, Issue
    * **Issue Priority:** Low, Medium, High
    * **Issue Scale:** The volume of each issue
    """)


def analyze_internal_links(all_inlinks_df, gsc_df):
    """Process internal links data and return analyzed dataframe"""
    # Process status groups
    gsc_df = gsc_df[gsc_df['Clicks'] > 0]

    all_inlinks_df['status_group'] = all_inlinks_df['Status Code'].apply(lambda x: str(x)[0])
    all_inlinks_df['status_group'] = all_inlinks_df['status_group'].astype(int)
    all_inlinks_df['status_group'] = all_inlinks_df['status_group'].apply(label_status)

    return all_inlinks_df


def label_status(status):
    """Label status codes into groups"""
    if status == 0:
        return 'Cancelled: 0'
    if status == 2:
        return 'Successful'
    elif status == 3:
        return 'Redirect'
    elif status == 4:
        return 'Client Error'
    elif status == 5:
        return 'Server Error'
    else:
        return 'other'


def plot_status_distribution(all_inlinks):
    """Create pie chart of status code distribution"""
    fig = px.pie(
        all_inlinks,
        names='status_group',
        title='Distribution of Internal Links by Status Code Group',
        color='status_group',
        width=700,
        height=500
    )

    fig.update_traces(
        textinfo='percent+label',
        textfont_size=14,
        marker=dict(line=dict(color='#000000', width=1))
    )
    return fig


def analyze_status_groups(all_inlinks, gsc_data):
    """Analyze each status group and return figures and summaries"""
    # Validate required columns
    required_columns = {
        'all_inlinks': ['Status Code', 'Destination', 'status_group'],
        'gsc_data': ['Address', 'Clicks']
    }

    for col in required_columns['all_inlinks']:
        if col not in all_inlinks.columns:
            raise ValueError(f"Missing required column '{col}' in all_inlinks data")

    for col in required_columns['gsc_data']:
        if col not in gsc_data.columns:
            raise ValueError(f"Missing required column '{col}' in GSC data")

    """Analyze each status group and return figures and summaries"""
    plotly_color = px.colors.qualitative.Plotly
    color_map = {
        'Cancelled: 0': plotly_color[9],
        'Successful': plotly_color[2],
        'Redirect': plotly_color[0],
        'Client Error': plotly_color[1],
        'Server Error': plotly_color[4]
    }

    recommendations = {
        'Cancelled: 0': 'Review the page to ensure that the URL is correct and the page is not blocked by robots.txt.',
        'Redirect': 'Update the internal redirect to the new, target/final URL.',
        'Client Error': 'Update the broken link to be a valid, canonical, 200 status URL.',
        'Server Error': 'Review the server logs to identify the cause of the server error and resolve the issue.'
    }

    results = []
    unique_non_200 = [x for x in all_inlinks['status_group'].unique() if x != 'Successful']

    for status in unique_non_200:
        status_data = all_inlinks[all_inlinks['status_group'] == status]
        inlinks_merge = pd.merge(
            status_data,
            gsc_data,
            left_on='Destination',
            right_on='Address',
            how='left',
            suffixes=('_inlinks', '_gsc')
        )

        inlinks_merge['Clicks'] = inlinks_merge['Clicks'].fillna(0)
        inlinks_unique = inlinks_merge.drop_duplicates(subset='Destination')
        inlinks_unique_traffic = inlinks_unique[inlinks_unique['Clicks'] > 0]

        # Create histogram
        fig = px.histogram(
            inlinks_unique.sort_values('Status Code_inlinks'),
            x='Status Code_inlinks',
            title=f'Distribution of Unique Internal Links by Status ({status})',
            color='status_group',
            width=900,
            height=500,
            color_discrete_map=color_map
        )

        fig.update_layout(
            xaxis_title='Status Code',
            yaxis_title='Count of Inlinks',
            legend_title_text='Status',
            xaxis=dict(
                type='category',
                tickmode='array',
                tickvals=status_data['Status Code'].unique()
            )
        )

        results.append({
            'status': status,
            'data': inlinks_merge,
            'unique_data': inlinks_unique,
            'with_traffic': len(inlinks_unique_traffic),
            'without_traffic': len(inlinks_unique) - len(inlinks_unique_traffic),
            'recommendation': recommendations[status],
            'figure': fig
        })

    return results


def export_internal_links(results, temp_dir):
    """Export internal links analysis to Excel"""
    excel_path = os.path.join(temp_dir, 'internal_links_summary.xlsx')

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for result in results:
            status = result['status']
            worksheet_name_all = f'internal_{re.sub(r"[^\w]", "_", status)}'
            worksheet_name_unique = f'unique_internal_{re.sub(r"[^\w]", "_", status)}'

            result['data'].to_excel(writer, sheet_name=worksheet_name_all, index=False)
            result['unique_data'].to_excel(writer, sheet_name=worksheet_name_unique, index=False)

    with open(excel_path, 'rb') as f:
        return f.read()

def save_uploaded_files(uploaded_files, temp_dir):
    """Save uploaded files to temporary directory and return their paths"""
    paths = []
    for file in uploaded_files:
        if file is not None:
            file_path = os.path.join(temp_dir, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getvalue())
            paths.append(file_path)
    return paths


def plot_impact_distribution(issues_group):
    """Create impact score distribution plot"""
    fig = px.histogram(
        issues_group,
        x='Impact_Score',
        color='Impact_Score_Quadrant',
        title='Distribution of Impact Scores by Cluster'
    )
    fig.update_layout(
        xaxis_title='Impact Score',
        yaxis_title='Count of Issues',
        legend_title_text='Impact Level Cluster'
    )
    return fig


def plot_top_percentiles(df, perc_n):
    """Plot both top and bottom percentile groups of impact scores"""
    threshold = df['Impact_Score'].quantile(perc_n)

    # Split data into top and bottom groups
    top_issues = df[df['Impact_Score'] >= threshold].sort_values('Impact_Score', ascending=True)
    bottom_issues = df[df['Impact_Score'] < threshold].sort_values('Impact_Score', ascending=True)

    # Create figure for top issues
    fig_top = px.bar(
        top_issues,
        x='Impact_Score',
        y='Issue Name',
        title=f'Top {int((1 - perc_n) * 100)}% Issues by Impact Score',
        orientation='h',
        color_discrete_sequence=['#1f77b4']  # Blue for high impact issues
    )

    # Create figure for bottom issues
    fig_bottom = px.bar(
        bottom_issues,
        x='Impact_Score',
        y='Issue Name',
        title=f'Bottom {int(perc_n * 100)}% Issues by Impact Score',
        orientation='h',
        color_discrete_sequence=['#ff7f0e']  # Orange for low impact issues
    )

    fig_top.update_yaxes(tickfont=dict(size=16))
    fig_bottom.update_yaxes(tickfont=dict(size=16))

    fig_top.update_xaxes(tickfont=dict(size=16))
    fig_bottom.update_xaxes(tickfont=dict(size=16))

    return fig_top, fig_bottom


def perform_clustering(issues_group, n_clusters=10):
    """Perform clustering analysis and return figures"""
    try:
        issues_list = issues_group['Issue Name'].tolist()
        
        # Generate embeddings - this now has a fallback to TF-IDF if transformer fails
        with st.status("Generating embeddings for clustering..."):
            issues_embeddings = generate_embeddings(issues_list)
        
        # Perform KMeans clustering
        with st.status("Performing clustering analysis..."):
            kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init='auto').fit(issues_embeddings)
            kmeans_labels = kmeans.labels_

            # Perform PCA
            pca_model = PCA(n_components=2)
            pca_model.fit(issues_embeddings)
            new_values = pca_model.transform(issues_embeddings)

            # Create cluster plot
            cluster_df = pd.DataFrame({
                'PCA1': new_values[:, 0],
                'PCA2': new_values[:, 1],
                'Cluster': kmeans_labels,
                'Issue': issues_group['Issue Name']
            })

            cluster_fig = px.scatter(
                cluster_df,
                x='PCA1',
                y='PCA2',
                color='Cluster',
                hover_data=['Issue'],
                title='Issue Clusters Visualization'
            )

            cluster_fig.update_traces(marker=dict(size=20))
            
        return cluster_fig
        
    except Exception as e:
        st.error(f"Error during clustering analysis: {str(e)}")
        st.info("Clustering requires either an internet connection to download models or sufficient data for the fallback method.")
        return None


def main():
    show_intro_content()
    # File uploaders
    st.header("Upload Data Files")
    col1, col2 = st.columns(2)

    with col1:
        all_inlinks = st.file_uploader("Upload all_inlinks.csv", type=['csv'])
        with st.expander("💡 Need help exporting all_inlinks.csv?"):
            st.markdown("""
                1. With Screaming Frog Crawl Open
                2. Go to "Bulk Export" tab
                3. Click "Links" > "All Inlinks"
            """)
        issues_overview = st.file_uploader("Upload issues_overview_report.csv", type=['csv'])
        with st.expander("💡 Need help exporting issues_overview_report.csv?"):
            st.markdown("""
                1. With Screaming Frog Crawl Open
                2. Go to "Reports" tab
                3. Click "Issues Overview"
            """)
    with col2:
        search_console = st.file_uploader("Upload search_console_all.csv", type=['csv'])
        with st.expander("💡 Need help exporting search_console_all.csv?"):
            st.markdown("""
                1. Ensure GSC API is Enabled Across Entire Crawl
                2. Go to "Search Console" Crawl tab
                3. Click "📤 Export"
            """)
        issues_reports = st.file_uploader("Upload issues_reports (multiple files)", type=['csv'],
                                          accept_multiple_files=True)
        with st.expander("💡 Need help exporting issues_report?"):
            st.markdown("""
                1. With Screaming Frog Crawl Open
                2. Go to "Bulk Export" tab
                3. Navigate to "Issues"
                4. Click "All Issues", or select specific Issue Type
            """)

    if all([all_inlinks, issues_overview, search_console]) and issues_reports:
        # Create main tabs
        tab_issues, tab_internal_links = st.tabs(["📊 Technical Issues Analysis", "🔗 Internal Links Analysis"])

        with tab_issues:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create issues_reports directory
                issues_dir = os.path.join(temp_dir, 'issues_reports')
                os.makedirs(issues_dir)

                # Save uploaded files
                save_uploaded_files([all_inlinks, issues_overview, search_console], temp_dir)
                save_uploaded_files(issues_reports, issues_dir)

                try:
                    # Load and process data
                    issues_report = pd.read_csv(os.path.join(temp_dir, issues_overview.name))
                    gsc_df = pd.read_csv(os.path.join(temp_dir, search_console.name))

                    # Process issue files
                    issues = []
                    for issue in os.listdir(issues_dir):
                        # Skip macOS hidden metadata files
                        if issue.startswith('._'):
                         
                            print(f"Skipping macOS metadata file: {issue}")
                            continue
                            
                        try:
                            issue_path = os.path.join(issues_dir, issue)
                            # Try with explicit encoding or detect encoding
                            try:
                                issue_df = pd.read_csv(issue_path)
                            except UnicodeDecodeError:
                                print(f"Encoding issue detected with file: {issue}. Trying with Latin-1 encoding.")
                                issue_df = pd.read_csv(issue_path, encoding='latin-1')
                            
                            issue_name = issue.split('.')[0]
                            issue_df['issue'] = issue_name
                            issues.append(issue_df)
                        except Exception as e:
                            st.error(f"Error processing file {issue}: {str(e)}")
                            continue

                    if not issues:
                        st.error("No valid issue files could be processed.")
                        return
                        
                    issues_df = pd.concat(issues)
                    issues_df = issues_df.dropna(subset=['Address'])

                    # Clean and label data
                    issues_group, issues_df = clean_data(issues_df, gsc_df, issues_report)
                    issues_group = label_data(issues_group)

                    # Create visualizations
                    st.header("Analysis Results")

                    # Impact Distribution
                    st.subheader("Impact Score Distribution")
                    impact_fig = plot_impact_distribution(issues_group)
                    st.plotly_chart(impact_fig, use_container_width=True)

                    # Top Percentiles
                    st.subheader("Impact Score Analysis by Percentile")
                    perc_n = st.slider("Select percentile threshold", 0.0, 1.0, 0.75)
                    fig_top, fig_bottom = plot_top_percentiles(issues_group, perc_n)

                    # Display top issues chart
                    st.plotly_chart(fig_top, use_container_width=True)

                    # Display bottom issues chart
                    st.plotly_chart(fig_bottom, use_container_width=True)

                    # Clustering
                    st.subheader("Clustering Analysis")
                    n_clusters = st.slider("Select number of clusters", 2, 15, 10)
                    cluster_fig = perform_clustering(issues_group, n_clusters)
                    
                    if cluster_fig is not None:
                        st.plotly_chart(cluster_fig, use_container_width=True)
                    else:
                        st.warning("Clustering could not be performed. Please check your internet connection or try again later.")

                    # Export Section
                    st.subheader("Export Results")
                    threshold_value = issues_group['Impact_Score'].quantile(perc_n)
                    filtered_count = len(issues_group[issues_group['Impact_Score'] >= threshold_value])

                    st.info(
                        f"Current threshold will export {filtered_count} issues (top {(1 - perc_n):.1%} by Impact Score)")

                    if st.button("Generate Excel Export"):
                        with st.spinner("Generating Excel file..."):
                            excel_data, exported_count = export_streamlit_data(
                                issues_group,
                                issues_df,
                                temp_dir,
                                perc_n
                            )
                            if excel_data is not None:
                                st.download_button(
                                    label=f"📥 Download Prioritized Audit ({exported_count} issues)",
                                    data=excel_data,
                                    file_name=f"issues_analysis_results_{int((1 - perc_n) * 100)}percentile.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                                st.success(f"Excel file generated successfully with {exported_count} issues!")

                except Exception as e:
                    st.error(f"An error occurred during processing: {str(e)}")

        with tab_internal_links:
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    # Save files first
                    all_inlinks_path = os.path.join(temp_dir, all_inlinks.name)
                    search_console_path = os.path.join(temp_dir, search_console.name)

                    # Save the files
                    with open(all_inlinks_path, "wb") as f:
                        f.write(all_inlinks.getvalue())
                    with open(search_console_path, "wb") as f:
                        f.write(search_console.getvalue())

                    st.write("Debug: Attempting to read files")
                    try:
                        all_inlinks_df = pd.read_csv(all_inlinks_path)
                    except Exception as e:
                        st.error(f"Error reading all_inlinks.csv: {str(e)}")
                        return

                    processed_inlinks = analyze_internal_links(all_inlinks_df, gsc_df)

                    # Overall distribution
                    st.header("Internal Links Analysis")
                    st.subheader("Status Code Distribution")
                    status_dist_fig = plot_status_distribution(processed_inlinks)
                    st.plotly_chart(status_dist_fig, use_container_width=True)

                    # Detailed analysis by status
                    st.subheader("Detailed Status Analysis")
                    results = analyze_status_groups(processed_inlinks, pd.read_csv(search_console))

                    # Create tabs for each status group
                    status_tabs = st.tabs([result['status'] for result in results])

                    for tab, result in zip(status_tabs, results):
                        with tab:
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                st.plotly_chart(result['figure'], use_container_width=True)

                            with col2:
                                st.metric("URLs with Traffic", result['with_traffic'])
                                st.metric("URLs without Traffic", result['without_traffic'])
                                st.metric("Total Affected Traffic", int(result['data']['Clicks'].sum()))
                                st.info(f"**Recommendation:**\n\n{result['recommendation']}")
                                

                    # Export button for internal links analysis
                    st.subheader("Export Internal Links Analysis")
                    if st.button("Generate Internal Links Report"):
                        excel_data = export_internal_links(results, temp_dir)
                        st.download_button(
                            label="📥 Download Internal Links Report",
                            data=excel_data,
                            file_name="internal_links_analysis.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        st.success("Internal links report generated successfully!")

                except Exception as e:
                    st.error(f"An error occurred during internal links analysis: {str(e)}")


if __name__ == "__main__":

    main()



# FAQ Section
st.markdown("### Frequently Asked Questions")

faq_items = [
    ("How do I use this tool effectively?", """
    To get the best results:
    1. Export the data directly from Screaming Frog SEO Spider.
    2. Do not change the file names when uploading.
    3. Follow the tips above to make sure you're uploading the correct files.

    💡Tip: Remove any unnecessary data from the issues_reports folder. I recommend removing
    issues that are known to be low SEO impact such as Security issues. 
    """),
    ("Do I need a paid Screaming Frog license?", """
    You don't need a paid Screaming Frog license, but your insights from this tool may 
    be limited by the free version's crawl limits. 
    """),
    ("What if I don't have access to the GSC API or a GSC Property", """
    This tool is currently designed to only run off of the GSC data exported from Screaming Frog. 
    An open source notebook will be released in the future to allow for easier custom data uploads.
    """),
    ('How is "Impact Score" calculate?', """
    The impact score is calculated using a combination of metrics, such as traffic, issue type, 
    issue priority, and issue scale. The impact scores is a product of calculated weights, and should be
    reviewed for accuracy by an SEO.
    """)
]


for question, answer in faq_items:
    with st.expander(question):
        st.markdown(answer)


# Footer
st.markdown("""
    <div style='position: fixed; bottom: 0; width: 100%; text-align: center; padding: 1rem; background-color: white;'>
        <p style='color: #6B7280; font-size: 0.875rem; display: flex; align-items: center; justify-content: center; gap: 4px;'>
            Built by 
            <img src="https://avatars.githubusercontent.com/u/64625949" style='width: 20px; height: 20px; border-radius: 50%; object-fit: cover; margin: 0 2px;'/>
            <a href="https://tylergargula.dev" style='color: rgb(37, 99, 235); text-decoration: none;'>Tyler Gargula</a>
        </p>
    </div>
""", unsafe_allow_html=True)