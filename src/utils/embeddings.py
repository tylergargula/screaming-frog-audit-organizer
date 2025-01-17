import numpy as np
from sentence_transformers import SentenceTransformer

def generate_embeddings(issues_list):
    """
    Generate embeddings for a list of issues using a pre-trained model.

    Parameters
    ----------
    issues_list : list
        List of issues to generate embeddings for

    Returns
    -------
    numpy.ndarray
        Array of embeddings for the input issues
    """
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2') # update as needed
    issues_embeddings = [model.encode(issue) for issue in issues_list]
    issues_embeddings = np.array(issues_embeddings)
    return issues_embeddings