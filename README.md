# General Conference Recommender

This project builds a recommendation system for General Conference talks. The first goal is to create a "You may also like" feature that identifies talks similar to a selected talk.

The project begins with a small corpus of talks, cleans and stores their text, and then compares talks using text similarity methods such as TF-IDF and cosine similarity. Later versions may include semantic embeddings, scripture-reference extraction, topic modeling, and a web interface.


## Project Structure

- `data/raw/`: original downloaded or collected talk data
- `data/processed/`: cleaned talk data
- `notebooks/`: exploratory notebooks
- `src/`: reusable Python functions