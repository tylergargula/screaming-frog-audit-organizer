import numpy as np
import os
import logging
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

def generate_embeddings(issues_list):
    """
    Generate embeddings for a list of issues using a pre-trained model.
    Falls back to TF-IDF if the transformer model is unavailable.

    Parameters
    ----------
    issues_list : list
        List of issues to generate embeddings for

    Returns
    -------
    numpy.ndarray
        Array of embeddings for the input issues
    """
    try:
        # Try to use the transformer model first
        print("Attempting to load the transformer model...")
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        issues_embeddings = [model.encode(issue) for issue in issues_list]
        issues_embeddings = np.array(issues_embeddings)
        print("Successfully generated transformer embeddings.")
        return issues_embeddings
    except Exception as e:
        print(f"Error loading transformer model: {str(e)}")
        print("Falling back to TF-IDF vectorization...")
        
        # Fallback to TF-IDF
        vectorizer = TfidfVectorizer(max_features=384)  # Match embedding dimensions
        tfidf_matrix = vectorizer.fit_transform(issues_list)
        
        # Convert sparse matrix to dense array
        tfidf_embeddings = tfidf_matrix.toarray()
        
        # If dimensions don't match the expected size, pad with zeros
        if tfidf_embeddings.shape[1] < 384:
            padding = np.zeros((tfidf_embeddings.shape[0], 384 - tfidf_embeddings.shape[1]))
            tfidf_embeddings = np.hstack((tfidf_embeddings, padding))
        
        print(f"Generated TF-IDF embeddings with shape: {tfidf_embeddings.shape}")
        return tfidf_embeddings