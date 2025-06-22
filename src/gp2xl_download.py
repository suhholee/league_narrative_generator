from dotenv import load_dotenv
import os
import shutil
from transformers import AutoTokenizer, AutoModelForCausalLM

load_dotenv()

GPT2_ID = "openai-community/gpt2-xl"
GPT2_LOCAL = "../models/gpt2-xl"

def reset_dir(path):
    """
    Resets a directory:
    - If the directory exists, it removes it and all its contents.
    - Then, it creates a new, empty directory at the specified path.
    - If the directory doesn't exist initially, it just creates it.
    """
    if os.path.exists(path):
        print(f"Removing existing directory: {path}/")
        shutil.rmtree(path) 
    os.makedirs(path, exist_ok=True)

if __name__ == "__main__":
    # Prepare the local directory for saving the model and tokenizer
    reset_dir(GPT2_LOCAL)

    # --- Download and save the GPT-2 XL tokenizer ---
    print(f"Downloading GPT-2 XL tokenizer for {GPT2_ID} …")
    # AutoTokenizer.from_pretrained(GPT2_ID) downloads the tokenizer configuration and vocabulary
    tokenizer = AutoTokenizer.from_pretrained(GPT2_ID)
    tokenizer.save_pretrained(GPT2_LOCAL)
    print(f"✅ GPT-2 XL tokenizer saved to {GPT2_LOCAL}/\n")

    # --- Download and save the GPT-2 XL model ---
    print(f"Downloading GPT-2 XL model for {GPT2_ID} …")
    # AutoModelForCausalLM.from_pretrained(GPT2_ID) downloads the actual model weights
    model = AutoModelForCausalLM.from_pretrained(GPT2_ID)
    model.save_pretrained(GPT2_LOCAL)
    print(f"✅ GPT-2 XL model saved to {GPT2_LOCAL}/\n")

    print("GPT-2 XL download complete.")