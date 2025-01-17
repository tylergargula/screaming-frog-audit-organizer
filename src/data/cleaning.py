def clean_data(issues_df, gsc_df, issues_report):

    """
    Clean and merge issues data with GSC data

    Parameters
    ----------
    issues_df : pandas.DataFrame
        DataFrame containing issues data
    gsc_df : pandas.DataFrame
        DataFrame containing GSC data
    issues_report : pandas.DataFrame
        DataFrame containing issues report data

    Returns
    -------
    issues_group : pandas.DataFrame
        DataFrame containing aggregated issues data
    """
    issues_df = issues_df.merge(gsc_df,
                                how='left',
                                left_on='Address',
                                right_on='Address',
                                suffixes=('_issues', '_gsc'),
                                indicator=True)[[
                                        'Address',
                                        'issue',
                                        'Clicks_gsc',
                                        'Impressions_gsc',
                                        'CTR_gsc',
                                        'Position_gsc']]

    issues_group = issues_df.groupby('issue').agg({
        'Clicks_gsc': 'sum',
        'Impressions_gsc': 'sum',
        'CTR_gsc': 'mean',
        'Position_gsc': 'mean',
        'Address': 'count',
    }).sort_values('Clicks_gsc', ascending=False)

    issues_report['issue_normalized'] = (issues_report['Issue Name']
                                         .str.lower()
                                         .str.replace(r'[^\w\s]', '', regex=True)  # Remove special characters
                                         .str.replace(r'\s+', '_', regex=True)  # Replace spaces with underscore
                                         )

    # merge issues_overview to issues_group
    issues_group = issues_group.reset_index()
    issues_group = issues_group.merge(issues_report,
                                      how='left',
                                      left_on='issue',
                                      right_on='issue_normalized',
                                      suffixes=('_sum', '_overview'))
    issues_group = issues_group[
        ['Issue Name', 'Clicks_gsc', 'Impressions_gsc', 'CTR_gsc', 'Position_gsc', 'Issue Type', 'Issue Priority',
         '% of Total', 'issue', 'Address']]

    issues_group = issues_group.dropna(subset='Issue Name')
    issues_group['pct_rank_clicks'] = issues_group['Clicks_gsc'].rank(pct=True)
    issues_group['pct_rank_urls'] = issues_group['Address'].rank(pct=True)
    return issues_group, issues_df

