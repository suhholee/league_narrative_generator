import argparse
import modal

# Modal Configuration
image = (
    modal.Image.from_registry("nvcr.io/nvidia/pytorch:24.02-py3")  # Uses CUDA 12 and PyTorch 2.2
    .pip_install(
        "transformers==4.40.1", 
        "sentencepiece",            
        "accelerate",            
    )
)

# Modal App (will appear in the Modal dashboard)
app = modal.App("gpt2-xl-generator")

# Configuration for the GPT-2 XL model from Hugging Face Hub
GPT2_MODEL_ID = "gpt2-xl"

@app.function(
    image=image,        
    gpu="H100",          
    timeout=300          
)
def generate_text(prompt: str):
    """
    Generates text using the GPT-2 XL model on a Modal remote worker.

    Args:
        prompt (str): The initial text prompt to generate from.

    Returns:
        str: The generated text, including the original prompt.
    """
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Running on device: {device}")

    # Load the tokenizer. padding_side="left" for generation 
    tokenizer = AutoTokenizer.from_pretrained(GPT2_MODEL_ID, padding_side="left")
    # Set the padding token to be the same as the end-of-sequence token
    tokenizer.pad_token = tokenizer.eos_token

    # Load the GPT-2 XL model from Hugging Face's model hub and move it to the determined device (GPU/CPU)
    print(f"Loading model {GPT2_MODEL_ID}...")
    model = AutoModelForCausalLM.from_pretrained(GPT2_MODEL_ID).to(device)
    model.eval()
    print("Model loaded successfully.")

    # Encode the input prompt into token IDs and move it to the correct device
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)

    print("Generating text...")

    output = model.generate(
        input_ids,
        max_length=200,      # Maximum length of the generated sequence (prompt + new text)
        do_sample=True,      # Enable sampling for more diverse outputs
        top_k=50,            # Sample from the top 50 most probable words
        top_p=0.95,          # Sample from the smallest set of words whose cumulative probability exceeds 0.95
        temperature=0.9,     # Control the randomness of predictions (higher = more random)
        eos_token_id=tokenizer.eos_token_id, # Stop generation when the end-of-sequence token is generated
    )
    print("Text generation complete.")

    # Decode the generated token IDs back into human-readable text
    return tokenizer.decode(output[0], skip_special_tokens=True)

# Main execution block for running the script
if __name__ == "__main__":
    # Argument parser for command-line inputs
    parser = argparse.ArgumentParser(description="Generate text using GPT-2 XL on Modal.")
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="The initial text prompt to start text generation."
    )
    args = parser.parse_args()

    # Initiates the Modal app run
    with app.run():
        print(f"Initiating remote text generation (Modal) with prompt: '{args.prompt}'")
        story = generate_text.remote(args.prompt)
        print("\n--- Generated Story ---")
        print(story)
        print("-----------------------\n")