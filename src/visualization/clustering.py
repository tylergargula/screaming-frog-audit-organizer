import matplotlib.pyplot as plt
import mplcursors
import numpy as np
from sklearn.cluster import KMeans


def plot_elbow(embeddings, max_clusters=15):
    """
    Create elbow plot to determine optimal number of clusters

    Parameters:
    -----------
    embeddings : array-like
        The embedded data to cluster
    max_clusters : int, optional (default=15)
        Maximum number of clusters to try

    Returns:
    --------
    None
        Displays the elbow plot
    """
    inertias = []
    K = range(1, max_clusters + 1)

    for k in K:
        kmeans = KMeans(n_clusters=k, random_state=0, n_init='auto')
        kmeans.fit(embeddings)
        inertias.append(kmeans.inertia_)

    # Create the elbow plot
    plt.figure(figsize=(8, 5))
    plt.plot(K, inertias, 'bx-')
    plt.xlabel('Number of Clusters (k)', fontsize=12)
    plt.ylabel('Distortion (Inertia)', fontsize=12)
    plt.title('Elbow Method For Optimal k', fontsize=14, pad=20)

    # Add grid for better readability
    plt.grid(True, linestyle='--', alpha=0.7)

    # Calculate the percentage decrease in inertia
    decreases = np.diff(inertias) / np.array(inertias)[:-1] * 100

    # Print the percentage decrease
    print("\nPercentage decrease in distortion:")
    for k, decrease in enumerate(decreases, start=1):
        print(f"From {k} to {k + 1} clusters: {abs(decrease):.1f}% decrease")

    plt.tight_layout()
    plt.show()

def clusters_2D(x_values, y_values, labels, kmeans_labels):
    """
    Create an interactive scatter plot of clusters with hoverable points

    Parameters:
    -----------
    x_values : array-like
        x coordinates from dimensionality reduction
    y_values : array-like
        y coordinates from dimensionality reduction
    labels : pandas.DataFrame
        DataFrame containing issue information
    kmeans_labels : array-like
        cluster labels from KMeans clustering
    """
    # Set up the plot with a white background for better visibility
    plt.figure(figsize=(15, 10))
    plt.set_cmap('viridis')

    # Create scatter plot with different colors for each cluster
    scatter = plt.scatter(x_values, y_values,
                          c=kmeans_labels,
                          s=50,  # Increased point size
                          alpha=0.7)

    # Add labels and title
    plt.xlabel('Dimension 1', fontsize=12)
    plt.ylabel('Dimension 2', fontsize=12)
    plt.title('SEO Issues Clusters', fontsize=14, pad=20)

    # Add colorbar
    plt.colorbar(scatter, label='Cluster')

    # Add interactive cursor with enhanced tooltip
    cursor = mplcursors.cursor(scatter, hover=True)

    @cursor.connect("add")
    def on_add(sel):
        point_idx = sel.target.index

        # Enhanced tooltip with more information
        tooltip_text = (
            f"Issue: {labels['Issue Name'].iloc[point_idx]}\n"
            f"Cluster: {kmeans_labels[point_idx]}\n"
            f"Impact Score: {labels['Impact_Score'].iloc[point_idx]:.1f}\n"
            f"Type: {labels['Issue Type'].iloc[point_idx]}\n"
            f"Priority: {labels['Issue Priority'].iloc[point_idx]}\n"
            f"Avg Clicks: {labels['Avg_Clicks_Per_URL'].iloc[point_idx]:,.0f}"
        )

        sel.annotation.set_text(tooltip_text)
        sel.annotation.get_bbox_patch().set(
            fc="white",
            alpha=0.8,
            edgecolor="darkgray"
        )

    # Add text labels for top impact scores
    top_n = 10  # Number of points to label
    top_indices = labels['Impact_Score'].nlargest(top_n).index

    for idx in top_indices:
        plt.annotate(
            labels['Issue Name'].iloc[idx][:30] + "...",  # Truncate long names
            (x_values[idx], y_values[idx]),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=8,
            alpha=0.8,
            bbox=dict(
                facecolor='white',
                edgecolor='none',
                alpha=0.7,
                pad=0.5
            )
        )

    plt.tight_layout()
    plt.show()

    # Print enhanced cluster statistics
    print("\nCluster Statistics:")
    for cluster in np.unique(kmeans_labels):
        cluster_mask = kmeans_labels == cluster
        cluster_issues = labels[cluster_mask]

        print(f"\nCluster {cluster+1}:")
        print(f"Number of issues: {len(cluster_issues)}")
        print(f"Average Impact Score: {cluster_issues['Impact_Score'].mean():.1f}")
        print("Top issues in this cluster:")
        for _, issue in cluster_issues.nlargest(3, 'Impact_Score').iterrows():
            print(f"- {issue['Issue Name']}")
            print(f"  Impact: {issue['Impact_Score']:.1f}")
            print(f"  Type: {issue['Issue Type']}")
            print(f"  Priority: {issue['Issue Priority']}")


