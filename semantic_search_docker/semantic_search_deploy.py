# Build paths relative to this script.
from pathlib import Path

# Use NumPy to load embeddings and calculate distances.
import numpy as np

# Use pandas to load the posts that correspond to the embeddings.
import pandas as pd

# Load the saved Sentence Transformers model.
from sentence_transformers import SentenceTransformer

# load spellchecker
from spellchecker import SpellChecker

# gradio will help wrap the mvp into an "app"
import gradio as gr

def search_posts(query: str) -> str:
    """Search the posts and return the top results as text.

    Args:
        query: User search query.

    Returns:
        Formatted search results.
    """
    # Locate the folders beside this Python file.
    base_dir = Path(__file__).resolve().parent

    # Locate the saved embeddings and posts.
    data_dir = base_dir / "search_data"

    # Load the post embeddings without allowing pickled data.
    post_embeddings = np.load(
        data_dir / "post_embeddings.npy",
        allow_pickle=False,
    )

    # Load the posts while preserving post IDs as strings.
    posts = pd.read_csv(
        data_dir / "posts.csv",
        dtype={"post_id": str},
        keep_default_na=False,
    )

    # Check that each embedding has a corresponding post row.
    if len(posts) != len(post_embeddings):
        raise ValueError(
            "The number of posts and embeddings does not match."
        )

    # Check that there are posts available to search.
    if len(posts) == 0:
        raise ValueError("There are no posts to search.")

    # Locate the saved model beside this Python file.
    model_path = base_dir / "models" / "all-MiniLM-L6-v2"

    # Check for a file expected in the saved Sentence Transformers model.
    if not (model_path / "modules.json").is_file():
        raise FileNotFoundError(
            f"Saved model not found at {model_path}"
        )

    # Load the model from disk without downloading it.
    embedding_model = SentenceTransformer(
        str(model_path),
        local_files_only=True,
    )

    # Create a spell checker instance.
    spell = SpellChecker()

    # Split the query into individual words.
    query_words = query.split()

    # Correct spelling mistakes in each word.
    corrected_words = [
        spell.correction(word) or word
        for word in query_words
    ]

    # Rebuild the corrected query.
    query = " ".join(corrected_words)

    # Convert the query into an embedding vector.
    query_embedding = embedding_model.encode(
        query,
        convert_to_numpy=True,
    )

    # Ensure the stored embeddings are a NumPy array.
    post_embeddings = np.asarray(post_embeddings)

    # Check that embedding dimensions match.
    if (
        post_embeddings.ndim != 2
        or post_embeddings.shape[1] != query_embedding.size
    ):
        raise ValueError(
            "Post embeddings and query embedding "
            "have incompatible shapes."
        )

    # Calculate vector lengths.
    query_norm = np.linalg.norm(query_embedding)
    post_norms = np.linalg.norm(post_embeddings, axis=1)

    # Ensure no embedding has zero length.
    if query_norm == 0 or np.any(post_norms == 0):
        raise ValueError(
            "Cosine distance requires non-zero embeddings."
        )

    # Calculate cosine similarity.
    similarities = (
        post_embeddings @ query_embedding
    ) / (post_norms * query_norm)

    # Convert similarity to distance.
    distances = 1.0 - similarities

    # Select the five closest posts.
    top_indices = np.argsort(
        distances,
        kind="stable",
    )[:5]

    # Collect formatted results.
    results = [f'Query: "{query}"', ""]

    # Build output text.
    for rank, index in enumerate(top_indices, start=1):
        post = posts.iloc[index]

        results.append(f"{rank}. post_id: {post['post_id']}")
        results.append(
            f"   distance: {float(distances[index]):.4f}"
        )
        results.append(
            f"   text_content: {post['text_content']}"
        )
        results.append(
            f"   hashtags: {post['hashtags']}"
        )
        results.append(
            f"   topic_category: {post['topic_category']}"
        )
        results.append("")

    # Return the formatted search results.
    return "\n".join(results)



def main() -> None:
    """Load the search data and model, then search for a typed query.

    Args:
        None.

    Returns:
        None. Prints up to five ranked posts to the command line.
    """
    # Locate the folders beside this Python file.
    base_dir = Path(__file__).resolve().parent

    # Locate the saved embeddings and posts.
    data_dir = base_dir / "search_data"

    # Load the post embeddings without allowing pickled data.
    post_embeddings = np.load(
        data_dir / "post_embeddings.npy",
        allow_pickle=False,
    )

    # Load the posts while preserving post IDs as strings.
    posts = pd.read_csv(
        data_dir / "posts.csv",
        dtype={"post_id": str},
        keep_default_na=False,
    )

    # Check that each embedding has a corresponding post row.
    if len(posts) != len(post_embeddings):
        # Stop rather than display a post with the wrong embedding.
        raise ValueError("The number of posts and embeddings does not match.")

    # Check that there are posts available to search.
    if len(posts) == 0:
        # Stop because there can be no search results.
        raise ValueError("There are no posts to search.")

    # Locate the saved model beside this Python file.
    model_path = base_dir / "models" / "all-MiniLM-L6-v2"

    # Check for a file expected in the saved Sentence Transformers model.
    if not (model_path / "modules.json").is_file():
        # Explain which model folder could not be found.
        raise FileNotFoundError(f"Saved model not found at {model_path}")

    # Load the model from disk without downloading it.
    embedding_model = SentenceTransformer(
        str(model_path),
        local_files_only=True,
    )

    # Create a spell checker instance for query correction.
    spell = SpellChecker()

    # Ask for a query when the script runs in the command line.
    query = input("Enter a search query: ").strip()

    if not query:
         # Explain what the user needs to enter.
         raise ValueError("The query must contain text.")

    # Split the query into individual words for spell correction.
    query_words = query.split()

    # Correct each word using the spell checker.
    corrected_words = [
        spell.correction(word) or word
        for word in query_words]

    # Rebuild the query from the corrected words.
    query = " ".join(corrected_words)
    

    # Embed the query using the same saved model used for the posts.
    query_embedding = np.asarray(embedding_model.encode(query))

    # Ensure the stored embeddings are a NumPy array.
    post_embeddings = np.asarray(post_embeddings)

    # Check that stored embeddings have the query embedding's dimensions.
    if post_embeddings.ndim != 2 or post_embeddings.shape[1] != query_embedding.size:
        # Stop if the vectors cannot be compared.
        raise ValueError(
            "Post embeddings and query embedding have incompatible shapes."
        )

    # Calculate the length of the query embedding.
    query_norm = np.linalg.norm(query_embedding)

    # Calculate the length of each post embedding.
    post_norms = np.linalg.norm(post_embeddings, axis=1)

    # Check for zero-length vectors before calculating cosine distance.
    if query_norm == 0 or np.any(post_norms == 0):
        # Stop because cosine distance is undefined for these vectors.
        raise ValueError("Cosine distance requires non-zero embeddings.")

    # Calculate cosine similarity between the query and every post.
    similarities = (
        post_embeddings @ query_embedding
    ) / (post_norms * query_norm)

    # Convert similarity to distance, where smaller means closer.
    distances = 1.0 - similarities

    # Find up to five posts in ascending distance order.
    top_indices = np.argsort(distances, kind="stable")[:5]

    # Print the query above its results.
    print(f'\nQuery: "{query}"\n')

    # Visit each selected post in ranked order.
    for rank, index in enumerate(top_indices, start=1):
        # Retrieve the post at the same position as its embedding.
        post = posts.iloc[index]

        # Print the post's rank and ID.
        print(f"{rank}. post_id: {post['post_id']}")

        # Print its cosine distance.
        print(f"   distance: {float(distances[index]):.4f}")

        # Print the post text.
        print(f"   text_content: {post['text_content']}")

        # Print its hashtags.
        print(f"   hashtags: {post['hashtags']}")

        # Print its topic and leave a blank line before the next result.
        print(f"   topic_category: {post['topic_category']}\n")


# Run main only when this file is executed directly.
if __name__ == "__main__":
    app = gr.Interface(
        fn=search_posts,
        inputs=gr.Textbox(label="Search"),
        outputs=gr.Textbox(label="Results"),
        title="Semantic Search",
    )

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
    )