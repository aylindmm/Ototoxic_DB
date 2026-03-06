
import openai
import requests
import pandas as pd
from tqdm import tqdm
import ast
import time
from langchain_openai.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser

class GPTextract:
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model
        openai.api_key = self.api_key

    def fetch_gpt_data(self, df, prompt, variables):
        # GPT model configuration
        llm_model = self.model

        # API endpoint and headers
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        # Prompt engineering: build ResponseSchemas from variables

        schemas = []

        for _, row in variables.iterrows():
            var_name = row['Name'].lower().replace(" ", "_").replace("-", "_")
            description = row['Description'].strip().replace('"', '\\"')
            type_ = row['Type'].strip().lower()

            # Add automatic phrasing based on Type
            if type_ == "list":
                description = ( description +
                    ". List them as a Python list string in the order they appear in the text "
                    "(e.g., '[drug1, drug2]'). If none, use '[]'."
                )
            elif type_ == "string":
                description = ( description +
                    " If not mentioned, use an empty string."
                )

            # append schema and use var_name as the schema name so parsed keys match var_name
            schemas.append(ResponseSchema(name=var_name, description=description))

        output_parser = StructuredOutputParser.from_response_schemas(schemas)
        format_instructions = output_parser.get_format_instructions()

        # Template for the prompt sent to GPT; includes placeholders for the main prompt, article title, abstract, and format instructions.
        review_template = """ {prompt}
        
        Article title: "{art_title}"
        Article abstract: "{art_abstract}"
        
        Do NOT include in your responses escape characters like \', \n, or \".

        {format_instructions}
        """
        
        # Request formatting
    
        results = []

        for index, row in tqdm(df.iterrows(), total=len(df), desc="Processing articles"):  # iterate over DataFrame rows with progress bar
            prompt_text = review_template.format(
                prompt=prompt,
                art_title=row.get("Title", ""),
                art_abstract=row.get("Abstract", ""),
                format_instructions=format_instructions
            )

            formatted_prompt = {
                "model": llm_model,
                "messages": [
                    {"role": "system", "content": "You are an expert pharmacologist with experience in drug side effects."},
                    {"role": "user", "content": prompt_text}
                ],
                "temperature": 0.0
            }

            try:
                response = requests.post(url, headers=headers, json=formatted_prompt, timeout=60)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Request error for PMID {row.get('PMID')}: {e}")
                # on network error, skip this article
                continue

            try:
                content = response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"Unexpected response format for PMID {row.get('PMID')}: {e}")
                continue

            try:
                parsed = output_parser.parse(content)
            except Exception as e:
                print(f"Parsing error for PMID {row.get('PMID')}: {e}\nRaw content:\n{content}")
                continue

            # Safely interpret the list-strings produced by the model. Use ast.literal_eval
            def _safe_list(s):
                if not s:
                    return []
                s = s.strip()
                if s == '[]':
                    return []
                try:
                    val = ast.literal_eval(s)
                    if isinstance(val, (list, tuple)):
                        return [str(x).strip() for x in val]
                except Exception:
                    # fallback: split on commas
                    return [x.strip() for x in s.strip('[]').split(',') if x.strip()]
                return []

            response_data = {"PMID": row.get("PMID")}
            for _, vrow in variables.iterrows():
                var_name = vrow['Name'].lower().replace(" ", "_").replace("-", "_")
                vtype = vrow['Type'].strip().lower()
                if vtype == "list":
                    try:
                        value = _safe_list(parsed.get(var_name, "[]"))
                    except Exception as e:
                        print(f"Error processing list variable '{var_name}' for PMID {row.get('PMID')}: {e}")
                        value = []
                else:
                    # default to empty string for non-list types
                    value = parsed.get(var_name, "")
                response_data[var_name] = value

            results.append(response_data)

        # build DataFrame once
        results = pd.DataFrame(results)
        print("GPT search script executed in ", time.process_time(), "seconds")
        return results
