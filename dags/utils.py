
import pymupdf
import pymupdf4llm
import os
import json
from openai import OpenAI

def pdf_to_markdown(pdf_path: str) -> str:
    """
    Convert a PDF file to Markdown format.
    """
    print(f"Opening PDF: {pdf_path}")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = pymupdf.open(pdf_path)

    try:
        #Converting PDF to Markdown
        md_text = pymupdf4llm.to_markdown(doc)

        return md_text

    finally:
        doc.close()

def summarize_paper(model_name: str, api_base_url: str, markdown_content: str) -> dict:
    """
    Summarize a research paper using an LLM and return
    the result as a structured JSON object.

    Args:
        markdown_content (str): Markdown content extracted from the PDF.

    Returns:
        dict: Structured research paper summary.
    """

    # Define the expected JSON structure
    output_structure = {
        "title": "Paper title",
        "summary": "A concise summary of the research paper",
        "keywords": [
            "keyword 1",
            "keyword 2",
            "keyword 3"
        ],
        "category": "Research paper category"
    }

    # Define the system message
    system_prompt = """
    You are an academic research assistant specialized in analyzing and summarizing scientific research papers in the field of **Computer Science**.

    Analyze the 
    provided research paper and extract the following information:

    1. **title**: The title of the research paper.
    2. **summary**: A concise but informative summary explaining the research objective, methodology, main findings, and conclusions.
    3. **keywords**: A list of 5 to 10 relevant keywords describing the paper's main topics, techniques, and concepts.
    4. **category**: The single main research category that best describes the paper.

    ### Research Categories

    You MUST classify every paper into exactly ONE of the following predefined categories:

    - `artificial_intelligence`: Artificial intelligence, machine learning, deep learning, neural networks, reinforcement learning, natural language processing, computer vision, and related AI techniques.
    - `software_engineering`: Software development, software testing, programming languages, software architecture, software maintenance, developer tools, and software design.
    - `computer_systems`: Operating systems, distributed systems, cloud computing, computer architecture, computer networks, databases, and infrastructure.
    - `data_management`: Data mining, information retrieval, big data, data processing, knowledge representation, and data management technologies.
    - `cybersecurity`: Information security, cryptography, privacy, authentication, vulnerability analysis, and secure computing.
    - `human_computer_interaction`: Human-computer interaction, user interfaces, usability, accessibility, interaction design, and user experience.
    - `theoretical_computer_science`: Algorithms, computational complexity, formal methods, logic, graph theory, and theoretical foundations of computing.

    ### Classification Rules

    - Assign exactly ONE category to each paper.
    - Select the category that best represents the paper's primary research contribution, not simply a secondary topic or technique it uses.
    - Consider the research objective, methodology, and main contributions when deciding on the category.
    - If a paper spans multiple categories, choose the one most central to its contribution.
    - Do not create new categories, rename categories, or return multiple categories.
    - Always use one of the exact category identifiers listed above.

    ### General Instructions

    - Only use information explicitly supported by the paper.
    - Do not invent information or make unsupported assumptions.
    - Be concise, precise, and objective.
    - Ensure keywords are relevant and avoid unnecessary duplication.
    - Return ONLY valid JSON.
    - Do not include Markdown formatting or code blocks.

    ### Expected JSON Output

    {
    "title": "Paper title",
    "summary": "Concise summary of the paper...",
    "keywords": [
        "keyword 1",
        "keyword 2",
        "keyword 3",
        "keyword 4",
        "keyword 5"
    ],
    "category": "artificial_intelligence"
    }
    """ 
    
    # Create the user message
    user_prompt = f"""
    Analyze the following research paper and return
    the results using this JSON structure:

    {json.dumps(output_structure, indent=4)}

    RESEARCH PAPER:

    {markdown_content}
    """
    client = OpenAI(
    api_key="your-api-key",
    base_url=api_base_url
    )

    # Call the LLM, parse and validate its JSON answer. If that fails, retry once.
    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )

        # Extract the response
        response = completion.choices[0].message.content

        try:
            return validate_metadata(parse_llm_json(response))
        except ValueError as e:
            print(f"Attempt {attempt}/{max_attempts}: invalid LLM output ({e})")
            last_error = e

    raise ValueError(
        f"The LLM did not return valid metadata JSON after {max_attempts} attempts: {response}"
    ) from last_error


def parse_llm_json(response: str) -> dict:
    """
    Parse the LLM response with json.loads(), tolerating a surrounding ```json code fence.
    Raises ValueError if the response is not a JSON object.
    """
    if not isinstance(response, str):
        raise ValueError("empty response")

    text = response.strip()
    if text.startswith("```"):
        # Drop the opening fence line (``` or ```json) and the closing fence
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"not valid JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("JSON is not an object")
    return data


def validate_metadata(data: dict) -> dict:
    """
    Check that the required fields exist and have the expected basic types.
    Raises ValueError otherwise.
    """
    for field in ("title", "summary", "category"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError(f"'{field}' must be a non-empty string")

    keywords = data.get("keywords")
    if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
        raise ValueError("'keywords' must be a list of strings")

    return {
        "title": data["title"].strip(),
        "summary": data["summary"].strip(),
        "keywords": [k.strip() for k in keywords if k.strip()],
        "category": data["category"].strip(),
    }
