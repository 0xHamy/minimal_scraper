from anthropic import Anthropic
import json


def claude_classify(
    api_key: str,
    model_name: str,
    post_content: str,
    max_tokens: int = 100,
    temperature: float = 0.1
) -> dict:
    """
    Classify a post using Claude (e.g., Sonnet) to determine if it discusses selling initial access,
    unrelated items, or warnings/complaints.

    Args:
        api_key (str): Anthropic API key.
        model_name (str): Claude model name (e.g., 'claude-3-5-sonnet-20241022').
        post_content (str): Post text to classify.
        max_tokens (int, optional): Max output tokens. Defaults to 100.
        temperature (float, optional): Sampling temperature. Defaults to 0.1.

    Returns:
        dict: JSON with classification, scores, and error (if any).
    """
    client = Anthropic(api_key=api_key)
    prompt_template = """
    Does this post discuss selling initial access to a company (e.g., RDP, VPN, admin access), selling unrelated items (e.g., accounts, tools), or warnings/complaints? Classify it as:
- Positive: Selling initial access.
- Neutral: Selling unrelated items.
- Negative: Warnings, general posts or complaints.

The content must be specifically about selling access to a company or business whose name is mentioned in the post. 

Return **only** a JSON object with:
- `classification`: "Positive", "Neutral", or "Negative".
- `scores`: Probabilities for `positive`, `neutral`, `negative` (summing to 1).

Wrap the JSON in ```json
{
  ...
}
``` to ensure proper formatting. Do not include any reasoning or extra text.

Post:
```markdown
{{POST}}
``` 

Do not include any other text or explanations.
Make sure to return the JSON object in the specified format.
"""
    prompt = prompt_template.replace("{{POST}}", post_content)

    try:
        message = client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        content = message.content[0].text
        # Extract JSON between ```json and ```
        start = content.index("```json\n") + 7
        end = content.index("\n```", start)
        result = json.loads(content[start:end])
        return result
    except Exception as e:
        return {"error": f"Failed to classify post: {str(e)}", "classification": None, "scores": None}


# Example usage 
if __name__ == "__main__":
    API_KEY = "" 
    MODEL_NAME = "claude-3-7-sonnet-20250219"

    sample_post = """Selling access to Horizon Logistics\nRevenue: $1.2B\nAccess: RDP with DA\nPrice: 0.8 BTC\nDM for details"""

    result = claude_classify(
        api_key=API_KEY,
        model_name=MODEL_NAME,
        post_content=sample_post,
        max_tokens=100,
        temperature=0.1
    )
    print("API response:")
    print(json.dumps(result, indent=4))

