# league_narrative_generator


🛠️ Pipeline Overview

Download Models

1.1download_gpt2.py: fetches GPT-2 XL weights & tokenizer into models/gpt2-xl/.

1.2download_sbert.py: fetches SBERT all-MiniLM-L6-v2 into models/sbert_all-MiniLM-L6-v2/.

Convert to Parquet

2.to_parquet.ipynb: reads lol_champions_data.csv, enforces dtypes, and writes lol_champions_data.parquet for faster I/O.

GPT-2 XL Embedding

3.gpt2-xl_embedding.ipynb: loads the Parquet, concatenates key text fields, and mean-pools GPT-2 XL hidden states to produce a (N, 1600) array saved as gpt2_embeddings.npy.

SBERT Embedding

4.sbert_embedding.ipynb: uses the SentenceTransformer to embed texts into a (N, 384) array saved as sbert_embeddings.npy.

Graph & Metadata Embeddings

5.graph_meta_embeddings.ipynb: builds a related_champions graph, runs Node2Vec (128-d), and one-hot- or learned-encodes region, role, and race, saving results in graph_embeddings.npy and meta_embeddings.npy / meta_learned_embeddings.npy.

Raw Embedding Concatenation

6.raw_embedding_concat.ipynb: loads all per-type embeddings and concatenates them into a single matrix saved as combined_raw_embeddings.npy.

Projection Embedding

7.projection_embedding.ipynb: trains an autoencoder (or projection MLP) on the raw concatenated vectors, producing a compact (N, 768) array saved as combined_projected_embeddings.npy.

🤔 Why this Embedding Design?

We employ multiple embedding types to capture different aspects of champion information:

GPT-2 XL embeddings capture narrative and stylistic nuances from the full text, ensuring the rich lore and tone influence similarity.

SBERT embeddings excel at semantic similarity, helping group champions by conceptual or thematic likeness.

Graph embeddings (via Node2Vec) encode explicit lore relationships between champions, reflecting how they are connected in the lore network.

Metadata embeddings (one-hot or learned for region, role, race) bring in structured categorical signals that text alone may not fully encode.

Raw Concatenation vs. Learned Projection

Raw concatenation simply stitches all embedding vectors together into one high-dimensional representation (~2K dims). This preserves all signals and serves as a strong baseline for retrieval. However, it can be heavy for indexing and storage.

Learned projection uses an autoencoder (or small MLP) to compress the raw concatenated vectors into a compact space (e.g. 768 dims). This approach:

Reduces memory footprint and speeds up nearest neighbor search.

Learns to prioritize the most salient combined features through reconstruction loss or task-specific fine-tuning.

Offers a balance between compactness and representational power.

By comparing both raw and projected embeddings in downstream retrieval and generation tasks, we can choose the vector space that best balances performance, speed, and storage constraints.