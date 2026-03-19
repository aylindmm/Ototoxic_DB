This repository contains the source code and data processing workflows used to generate the dataset of otoactive small molecules reported in:

> **Mapping the Otoactive Landscape: An LLM-Aided Extraction of Compounds and Their Targets**  DOI: [Link to Article]

The core code for the dataset generation is contained in [database_build.py](https://github.com/aylindmm/Ototoxic_DB/blob/main/database_build.py). Here is an step by step explanation.

### How to Use the Pipeline

Load requiered packages and declare variables.

For this pipeline to work you need a valid OpenAI API key and an email. This shold be stored in a local .env file.


```python
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

import sys
from pubmed_search import EntrezSearcher
from GPT_search import GPTextract
from pubchem_search import PubChemSearcher

# Define variables
_ = load_dotenv(find_dotenv()) # read local .env file

entrez = EntrezSearcher(email = os.environ['MAIL'], 
                        api_key = os.environ['ENTREZ_API_KEY'])

gpt = GPTextract(api_key = os.environ['OPENAI_API_KEY'], 
                 model = "gpt-4.1-nano-2025-04-14") # specify GPT model

```

Define output files 

```python
# Include a timestamp 
timestamp = datetime.now().strftime("%d_%m_%Y_%H.%M") 
out_dir = "/out_dir/" # specify output directory
```
Now, you shold define the search terms for PubMed article search. The query is a string with each search term separated by a coma.

```python
query = [
    "Ototoxicity",
    "Drug-induced hearing loss",
    "Vestibulotoxicity",
    "Cochleotoxicity",
    "Drug-induced tinnitus",
    "Drug-induced vertigo",
    "Drug-induced dizziness",
    "Inner ear toxicity",
    "Ototoxic side effects",
    "Drug-induced cochlear damage",
    "Drug-induced vestibular dysfunction",
    "Hearing loss AND side effect",
    "Tinnitus AND side effect",  
    "Vertigo AND side effect",
    "Dizziness AND side effect",
    "sensorineural hearing loss AND side effect"
]
```

Search PubMed for articles. This retrieves a data frame with the search results metadata.

```python
articles = entrez.fetch_pubmed_articles(query) #test with small number of articles first
articles.to_csv(f"{out_dir}ototoxic_articles_{timestamp}.tsv", sep="\t", index=False)
```

Now, we define the prompt for data extraction with the GPT model. The more specific you are with the instructions, the better

```python3 
prompt = """You are an expert pharmacologist specializing in otolaryngology. 
Your task is to extract drug information from the following research article.

Definitions:
- Ototoxic Agent: A drug or molecule that causes damage to the inner ear (cochleotoxicity or vestibulotoxicity), hearing loss or dizziness.
- Otoprotective Agent: A compound that prevents or mitigates such damage.

Instructions:
1. Identify all drugs, molecules, or experimental compounds mentioned.
2. Determine their role: "Ototoxic" or "Otoprotective".
3. Beware of Co-treatments: If an otoprotective agent is being tested *against* or in combination with a specific ototoxin, distinguish between the primary toxin (e.g., Cisplatin) and the protective candidate (e.g., N-acetylcysteine)."""
```

To maintain a structured and predictable output, the pipeline needs a configuration file to determine exactly what data points to extract. These variables must be defined in a **plain text table (`.txt`)** using the following three-column format:

| Column | Description |
| :--- | :--- |
| **Name** | The unique identifier for the variable (e.g., `compound_name`). |
| **Description** | A brief explanation of the variable's content to guide the LLM. |
| **Type** | Data format constraint: either `"List"` or `"String"`. |

The file used for the otoactive compound mining is in the [variables.txt](https://github.com/aylindmm/Ototoxic_DB/blob/main/variables.txt) file.

```python
results = gpt.fetch_gpt_data(df = articles,
                              prompt = prompt, 
                              variables = pd.read_csv(f"Ototoxic_DB/variables.txt", sep="\t")) 


results.to_csv(f"{out_dir}gpt_extracted_ototoxic_data_{timestamp}.tsv", sep="\t", index=False)
```

Finally, to homogenize compound nomenclature and retrieve the PubChem Compound ID, we execute the PubChemSearcher module.

```python
pubchem_results = PubChemSearcher().fetch_compound_info(df = results,  
columns= ["ototoxic_drugs", "otoprotective_drugs"])


# Merge the results with the original articles
final_df = articles.merge(results.merge(pubchem_results, on="PMID", how="inner"), on="PMID", how="inner")

# Save final database
final_df.to_csv(f"{out_dir}ototoxic_compound_database_{timestamp}.tsv", sep="\t", index=False) 


```
