import plotly_express as px

def plot_top_percentiles(issues_group, perc_n):
    """
    Plot top issues by percentile of clicks and URLs.

    Parameters
    ----------
    issues_group : pandas.DataFrame
        DataFrame containing issues data
    perc_n : float
        Percentile value to filter issues by

    Returns
    -------
    Plot of top issues by percentile
    """
    issues_pct_n_clicks = issues_group[issues_group['pct_rank_clicks'] > perc_n]
    issues_pct_n_clicks = issues_pct_n_clicks[issues_pct_n_clicks['Clicks_gsc'] > perc_n]

    issues_pct_n_urls = issues_group[issues_group['pct_rank_urls'] > perc_n]
    issues_pct_n_urls = issues_pct_n_urls[issues_pct_n_urls['Address'] > perc_n]

    category_orders = {'Impact_Score_Quadrant': ['High', 'Medium', 'Low', 'Backlog']}

    fig_clicks = px.bar(issues_pct_n_clicks.sort_values('Clicks_gsc', ascending=False),
                   x='Issue Name',
                   y='Clicks_gsc',
                   color='Impact_Score_Quadrant',
                   title=f'Top Issues by {perc_n * 100}th percentile of Clicks',
                   category_orders=category_orders,
                    height=600,
                    width=1000
                   )
    fig_clicks.update_layout(
        yaxis_title="Clicks",
    )
    fig_clicks.show()

    fig_url_count = px.bar(issues_pct_n_urls.sort_values('Address', ascending=False),
                   x='Issue Name',
                   y='Address',
                   color='Impact_Score_Quadrant',
                   title=f'Top Issues by by {perc_n * 100}th percentile Count of URLs',
                   category_orders=category_orders,
                    height = 600,
                    width = 1000
                   )
    fig_url_count.update_layout(
        yaxis_title="Count",
    )
    fig_url_count.show()
