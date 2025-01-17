import pandas as pd
import numpy as np

def calculate_impact_score(row, issues_group):
    """
    Calculate the impact score for a given row based on various factors.
    The impact score is a weighted sum of several factors, including click
    counts, URL scope, priority, and issue type.

    Parameters
    ----------
    row : pandas.Series
        A row from the DataFrame containing issue data.
    issues_group : pandas.DataFrame
        DataFrame containing all issues fo
        r context.

    Returns
    -------
    float
        The calculated impact score for the issue.
    """
    click_multiplier = 0

    if 'Security' in row['Issue Name']:
        click_multiplier += 0.001
    else:
        click_multiplier += 0.3

    # Click impact: normalized log of clicks to handle large numbers
    click_impact = np.log1p(row['Clicks_gsc']) / np.log1p(issues_group['Clicks_gsc'].max()) * click_multiplier

    # URL scope impact: combination of URL and click percentile ranks
    scope_impact = (row['pct_rank_urls'] * row['pct_rank_clicks']) * 0.25

    # Priority impact: normalized priority score
    priority_impact = (row['Priority_Score'] / 5) * 0.25

    # Issue Type impact: normalized type score
    type_impact = (row['Type_Score'] / 5) * 0.2

    # Combine all components and scale to 0-100
    impact_score = (click_impact + scope_impact + priority_impact + type_impact) * 100
    return impact_score

def label_data(issues_group):
    """
    Label data with impact scores and quadrants.

    Parameters
    ----------
    issues_group : pandas.DataFrame
        DataFrame containing grouped issues data

    Returns
    -------
    pandas.DataFrame
        DataFrame with added label columns for impact scores and quadrants
    """
    priority_map = {'Low': 1, 'Medium': 3, 'High': 5}
    issue_type_map = {'Warning': 1, 'Opportunity': 3, 'Issue': 5}
    impact_quadrant_map = {1: 'Backlog', 2: 'Low', 3: 'Medium', 4: 'High'}

    issues_group['Priority_Score'] = issues_group['Issue Priority'].map(priority_map)
    issues_group['Type_Score'] = issues_group['Issue Type'].map(issue_type_map)

    issues_group['Impact_Score'] = issues_group.apply(
        lambda row: calculate_impact_score(row, issues_group),
        axis=1
    )

    issues_group = issues_group.sort_values('Impact_Score', ascending=False)
    issues_group['pct_rank_impact'] = issues_group['Impact_Score'].rank(pct=True)

    # divide into 4 equal quadrants
    issues_group['Impact_Score_Quadrant'] = pd.qcut(issues_group['Impact_Score'], 4, labels=False)
    issues_group['Impact_Score_Quadrant'] = issues_group['Impact_Score_Quadrant'].astype(int) + 1
    issues_group['Impact_Score_Quadrant'] = issues_group['Impact_Score_Quadrant'].map(impact_quadrant_map)

    return issues_group