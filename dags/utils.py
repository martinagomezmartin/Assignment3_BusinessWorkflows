
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
        #print(f"PDF opened successfully. Pages: {len(doc)}")


        #print("Converting PDF to Markdown...")
        md_text = pymupdf4llm.to_markdown(doc)

        #print(f"Conversion completed! Characters: {len(md_text)}")

        return md_text

    finally:
        doc.close()




def summarize_paper(markdown_content: str) -> dict:
    """
    Summarize a research paper using an LLM and return
    the result as a structured JSON object.

    Args:
        markdown_content (str): Markdown content extracted from the PDF.

    Returns:
        dict: Structured research paper summary.
    """

    # 1. Define the expected JSON structure
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

    # 2. Define the system message
    system_prompt = """
    You are an academic research assistant specialized
    in analyzing and summarizing scientific research papers.

    Analyze the provided research paper and extract:

    1. title: The title of the research paper.
    2. summary: A concise but informative summary explaining
       the research objective, methodology, main findings
       and conclusions.
    3. keywords: A list of 5 to 10 relevant keywords.
    4. category: The main research category or field.

    Instructions:
    - Only use information explicitly supported by the paper.
    - Do not invent information.
    - Be concise and precise.
    - Return ONLY valid JSON.
    - Do not include Markdown formatting or code blocks.
    """

    # 3. Create the user message
    user_prompt = f"""
    Analyze the following research paper and return
    the results using this JSON structure:

    {json.dumps(output_structure, indent=4)}

    RESEARCH PAPER:

    {markdown_content}
    """

    # 4. Call the LLM
    completion = client.chat.completions.create(
        model=os.getenv("MODEL", "gemma-4-e2b-it-qat"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )

    # 5. Extract the response
    response = completion.choices[0].message.content

    # 6. Convert the response into a Python dictionary
    try:
        summary = json.loads(response)
    except (json.JSONDecodeError, TypeError) as e:
        raise ValueError(
            f"The LLM did not return valid JSON: {response}"
        ) from e

    return summary
