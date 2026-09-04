import requests
try:
    import ollama as ollama_sdk
except ImportError:
    ollama_sdk = None
from openai import OpenAI

SYSTEM_PROMPT = """You are a Senior Robotic Process Automation (RPA) and Intelligent Automation (IA) Architect.
Your task is to take the extracted process text, screenshots text, and process notes provided, and synthesize them into structured automation documentation.

You must generate exactly the 6 sections defined below. Mark each section clearly using a line starting with '[SECTION: <Section Name>]' so that the application can parse them. Keep the text clean, detailed, and professional.

Sections to generate:

[SECTION: Process Summary]
Provide a detailed high-level summary of the process, its objectives, scope, frequency, and estimated business value.

[SECTION: Step-by-step workflow]
Detail the logical step-by-step sequence of events. Include what actions are taken, inputs entered, and conditional steps. Format it as a clear numbered list.

[SECTION: Risks & Exceptions]
Identify potential business and system exceptions (e.g., system downtime, invalid input formats, data discrepancies) and outline how the automation should handle them.

[SECTION: Automation Opportunities]
Analyze the process and suggest automation recommendations. Highlight which parts are highly structured (best for RPA) and which parts might require human-in-the-loop or cognitive capabilities (AI/OCR).

[SECTION: Test Cases]
Outline functional test cases for validating the automation, including happy path scenarios and edge/exception handling cases.

[SECTION: PDD Draft]
Draft a formal Process Definition Document (PDD) outline combining metadata, inputs, outputs, rules, and environment requirements.
"""

def parse_llm_response(response_text):
    """
    Parses the LLM output by looking for [SECTION: <Name>] tags.
    """
    sections = {
        'Process Summary': '',
        'Step-by-step workflow': '',
        'Risks & Exceptions': '',
        'Automation Opportunities': '',
        'Test Cases': '',
        'PDD Draft': ''
    }
    
    current_section = None
    lines = response_text.split('\n')
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[SECTION:'):
            sec_name = stripped.replace('[SECTION:', '').replace(']', '').strip()
            matched_key = None
            for key in sections.keys():
                if key.lower() in sec_name.lower():
                    matched_key = key
                    break
            current_section = matched_key
        else:
            if current_section:
                sections[current_section] += line + '\n'
                
    for key in sections.keys():
        sections[key] = sections[key].strip()
        
    has_content = any(len(val) > 0 for val in sections.values())
    if not has_content:
        sections['Process Summary'] = response_text
        sections['PDD Draft'] = "Raw LLM Output generated. Use the raw text above."
        
    return sections


def call_openai(api_key, model_name, user_content, base_url=None):
    """
    Calls the OpenAI Chat Completion API, or any OpenAI-compatible endpoint
    (e.g. Google Gemini via AI Studio, Groq) by supplying a custom base_url.
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content


def call_ollama_sdk(model_name, user_content, base_url="http://localhost:11434"):
    """
    Calls local Ollama using the official ollama Python SDK.
    Supports custom host via base_url.
    """
    if ollama_sdk is None:
        raise ImportError("Ollama Python library is not installed. Please run 'pip install ollama' or restore dependencies.")
    client = ollama_sdk.Client(host=base_url)
    response = client.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        options={"temperature": 0.2}
    )
    return response.message.content


def call_ollama_stream(model_name, user_content, base_url="http://localhost:11434"):
    """
    Calls local Ollama using the official SDK with streaming enabled.
    Returns a generator of text chunks for real-time display.
    """
    if ollama_sdk is None:
        raise ImportError("Ollama Python library is not installed. Please run 'pip install ollama' or restore dependencies.")
    client = ollama_sdk.Client(host=base_url)
    stream = client.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        options={"temperature": 0.2},
        stream=True
    )
    for chunk in stream:
        yield chunk.message.content


def call_ollama(base_url, model_name, user_content):
    """
    Fallback: calls a local Ollama server's chat endpoint via raw requests.
    Used when the SDK is unavailable.
    """
    url = f"{base_url}/api/chat"
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "options": {
            "temperature": 0.2
        },
        "stream": False
    }
    response = requests.post(url, json=payload, timeout=180)
    response.raise_for_status()
    data = response.json()
    return data['message']['content']


def get_ollama_models(base_url="http://localhost:11434"):
    """
    Returns a list of locally available Ollama model names.
    Returns an empty list on connection failure.
    """
    if ollama_sdk is None:
        return []
    try:
        client = ollama_sdk.Client(host=base_url)
        models_response = client.list()
        return [m.model for m in models_response.models]
    except Exception:
        return []


def check_ollama_health(base_url="http://localhost:11434"):
    """
    Checks whether the Ollama server is reachable.
    Returns (is_online: bool, message: str).
    """
    try:
        resp = requests.get(base_url, timeout=3)
        if resp.status_code == 200:
            return True, "Ollama server is online"
        return False, f"Unexpected status: {resp.status_code}"
    except requests.ConnectionError:
        return False, "Cannot connect to Ollama server"
    except requests.Timeout:
        return False, "Connection timed out"
    except Exception as e:
        return False, str(e)


def pull_ollama_model(model_name, base_url="http://localhost:11434"):
    """
    Pulls a model from the Ollama registry.
    Returns a generator of status strings for real-time progress display.
    """
    if ollama_sdk is None:
        yield "Error: Ollama library is not installed."
        return
    client = ollama_sdk.Client(host=base_url)
    for progress in client.pull(model_name, stream=True):
        status = progress.status or ""
        completed = progress.completed or 0
        total = progress.total or 0
        if total > 0:
            pct = int((completed / total) * 100)
            yield f"{status} ({pct}%)"
        else:
            yield status


def call_azure_ai_foundry(api_key, endpoint, model_name, user_content, api_version="2024-05-01-preview"):
    """
    Calls Azure AI Foundry (either via AzureOpenAI client or standard OpenAI client pointing to serverless endpoint).
    """
    endpoint = endpoint.strip() if endpoint else ""
    
    if "openai.azure.com" in endpoint.lower() or "services.ai.azure.com" in endpoint.lower():
        from openai import AzureOpenAI
        base_endpoint = endpoint
        if "/openai/deployments" in endpoint.lower():
            idx = endpoint.lower().find("/openai/deployments")
            base_endpoint = endpoint[:idx]
            
        client = AzureOpenAI(
            azure_endpoint=base_endpoint,
            api_key=api_key,
            api_version=api_version
        )
    else:
        from openai import OpenAI
        base_url = endpoint
        if not base_url.endswith("/v1") and not base_url.endswith("/v1/"):
            base_url = base_url.rstrip("/") + "/v1"
            
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content


def generate_documentation_from_text(provider, model_name, api_key, base_url, full_text, api_version="2024-05-01-preview"):
    """
    Orchestrates the generation process using the selected LLM provider.
    Supports OpenAI, Google Gemini (via AI Studio), Groq, Azure AI Foundry, and Ollama (Local).
    """
    if provider == "OpenAI":
        if not api_key:
            raise ValueError("OpenAI API Key is required but not provided.")
        # base_url is passed through to support OpenAI-compatible providers (Gemini, Groq)
        raw_output = call_openai(api_key, model_name, full_text, base_url=base_url or None)
    elif provider == "Azure AI Foundry":
        if not api_key:
            raise ValueError("Azure AI Foundry API Key is required but not provided.")
        if not base_url:
            raise ValueError("Azure AI Foundry Endpoint URL is required but not provided.")
        raw_output = call_azure_ai_foundry(api_key, base_url, model_name, full_text, api_version)
    elif provider == "Ollama (Local)":
        if not base_url:
            raise ValueError("Ollama Base URL is required but not provided.")
        actual_model = model_name if model_name else "llama3.2"
        try:
            raw_output = call_ollama_sdk(actual_model, full_text, base_url)
        except Exception:
            # Fallback to raw requests if SDK call fails
            raw_output = call_ollama(base_url, actual_model, full_text)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    return parse_llm_response(raw_output)
