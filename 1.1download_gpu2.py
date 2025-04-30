#!/usr/bin/env python3
import os
import shutil
from transformers import AutoTokenizer, AutoModelForCausalLM

# Configuration
GPT2_ID    = "openai-community/gpt2-xl"
GPT2_LOCAL = "models/gpt2-xl"

def reset_dir(path):
    if os.path.exists(path):
        print(f"Removing existing directory: {path}/")
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)

if __name__ == "__main__":
    reset_dir(GPT2_LOCAL)

    print(f"Downloading GPT-2 XL tokenizer for {GPT2_ID} …")
    tokenizer = AutoTokenizer.from_pretrained(GPT2_ID)
    tokenizer.save_pretrained(GPT2_LOCAL)
    print(f"✅ GPT-2 XL tokenizer saved to {GPT2_LOCAL}/\n")

    print(f"Downloading GPT-2 XL model for {GPT2_ID} …")
    model = AutoModelForCausalLM.from_pretrained(GPT2_ID)
    model.save_pretrained(GPT2_LOCAL)
    print(f"✅ GPT-2 XL model saved to {GPT2_LOCAL}/\n")

    print("GPT-2 XL download complete.")