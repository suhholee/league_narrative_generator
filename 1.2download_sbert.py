#!/usr/bin/env python3
import os
import shutil
from sentence_transformers import SentenceTransformer

# Configuration
SBERT_ID    = "all-MiniLM-L6-v2"
SBERT_LOCAL = "models/sbert_all-MiniLM-L6-v2"

def reset_dir(path):
    if os.path.exists(path):
        print(f"Removing existing directory: {path}/")
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)

if __name__ == "__main__":
    reset_dir(SBERT_LOCAL)

    print(f"Downloading SBERT model for {SBERT_ID} (CPU-only) …")
    # Force SBERT onto CPU
    sbert = SentenceTransformer(SBERT_ID, device="cpu")
    sbert.save(str(SBERT_LOCAL))
    print(f"✅ SBERT model saved to {SBERT_LOCAL}/\n")

    print("SBERT download complete.")