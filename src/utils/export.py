import os
import pandas as pd
import plotly_express as px

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