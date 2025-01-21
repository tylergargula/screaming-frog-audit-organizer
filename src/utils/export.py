import os
import pandas as pd
import plotly_express as px
import streamlit as st

def export_data(issues_group, issues_df, export_path, issues_path):
    """
    Export issues data to Excel with multiple sheets.

    Parameters
    ----------
    issues_group : pandas.DataFrame
        DataFrame containing issues data
    issues_df : pandas.DataFrame
        DataFrame containing issues data
    export_path : str
        Path to export directory
    issues_path : str
        Path to issues directory

    Returns
    -------
    str
        Print message with path to the exported Excel file

    """
    # ensure export directory exists
    os.makedirs(export_path, exist_ok=True)

    excel_path = os.path.join(export_path, 'issues_with_traffic_pages.xlsx')

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        priorities = ['High', 'Medium', 'Low', 'Backlog']
        plotly_colors = px.colors.qualitative.Plotly
        color_mapping = {priority: plotly_colors[i % len(plotly_colors)] for i, priority in enumerate(priorities)}


        for priority in priorities:
            # Create priority summary worksheet
            issues_fig = issues_group[issues_group['Impact_Score_Quadrant'] == priority]
            # issues_fig = issues_fig[issues_fig['pct_rank_clicks'] > perc_n]
            issues_sorted = issues_fig.sort_values('Impact_Score', ascending=False)

            # Save priority summary
            worksheet_name = f'{priority}_Priority'
            issues_sorted.to_excel(writer, sheet_name=worksheet_name, index=False)

            # Create and display plots
            fig_impact = px.bar(issues_sorted,
                           x='Issue Name',
                           y='Address',
                           title=f'{priority} Priority Issues by Count of URLs - sorted by Impact Score',
                            color='Impact_Score_Quadrant',
                                color_discrete_map=color_mapping,)

            fig_impact.update_layout(
                yaxis_title="Volume of URLs",
                xaxis_title="Issues",
            )
            fig_impact.show()

            # Process individual issues
            for issue_name in issues_fig['issue'].unique():
                # Filter and sort data
                issue_data = issues_df[issues_df['issue'] == issue_name]
                issue_data = issue_data.sort_values('Clicks_gsc', ascending=False)

                # find relevant csv from issue_data using issue name
                issue_csv_path = os.path.join(issues_path, f"{issue_name}.csv")
                if os.path.exists(issue_csv_path):
                    issue_csv_df = pd.read_csv(issue_csv_path)
                    issue_data = issue_data.merge(issue_csv_df, how='left', on='Address', suffixes=('', '_crawl'))
                else:
                    pass

                # Create valid worksheet name
                issue_worksheet_name = f"{priority}_{issue_name}"[:31]

                # Write to worksheet
                issue_data.to_excel(writer, sheet_name=issue_worksheet_name, index=False)

    return print(f'Data exported to {excel_path}')


def export_streamlit_data(issues_group, issues_df, temp_dir, perc_n):
    """
    Export issues data to Excel based on selected impact score threshold.

    Parameters
    ----------
    issues_group : pandas.DataFrame
        DataFrame containing aggregated issues data
    issues_df : pandas.DataFrame
        DataFrame containing detailed issues data
    temp_dir : str
        Temporary directory path
    perc_n : float
        Percentile threshold for filtering issues
    """
    try:
        # Calculate threshold based on percentile
        threshold = issues_group['Impact_Score'].quantile(perc_n)

        # Filter issues_group based on threshold
        filtered_issues_group = issues_group[issues_group['Impact_Score'] >= threshold].copy()

        # Create export file path in temp directory
        excel_path = os.path.join(temp_dir, 'issues_analysis_results.xlsx')

        # Export data to Excel
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Export metadata sheet with analysis parameters
            metadata = pd.DataFrame({
                'Parameter': ['Percentile Threshold', 'Impact Score Threshold', 'Number of Issues'],
                'Value': [f"{perc_n:.2%}", f"{threshold:.2f}", len(filtered_issues_group)]
            })
            metadata.to_excel(writer, sheet_name='Analysis_Parameters', index=False)

            # Export filtered summary sheet with all issues
            filtered_issues_group.to_excel(writer, sheet_name='All_Issues_Summary', index=False)

            # Export sheets by priority
            priorities = ['High', 'Medium', 'Low', 'Backlog']
            for priority in priorities:
                priority_issues = filtered_issues_group[
                    filtered_issues_group['Impact_Score_Quadrant'] == priority
                    ].sort_values('Impact_Score', ascending=False)

                if not priority_issues.empty:
                    # Create priority summary sheet
                    sheet_name = f'{priority}_Priority'
                    priority_issues.to_excel(writer, sheet_name=sheet_name, index=False)

                    # Create individual issue sheets
                    for issue_name in priority_issues['issue'].unique():
                        # Filter issues_df to only include URLs for filtered issues
                        issue_data = issues_df[issues_df['issue'] == issue_name]
                        issue_data = issue_data.sort_values('Clicks_gsc', ascending=False)

                        # Create valid worksheet name (Excel has 31 character limit)
                        issue_worksheet_name = f"{priority}_{issue_name}"[:31]
                        issue_data.to_excel(writer, sheet_name=issue_worksheet_name, index=False)

        # Read the exported file
        with open(excel_path, 'rb') as f:
            excel_data = f.read()

        return excel_data, len(filtered_issues_group)

    except Exception as e:
        st.error(f"Error during export: {str(e)}")
        return None, 0