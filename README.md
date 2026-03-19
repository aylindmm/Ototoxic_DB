This repository contains the source code and data processing workflows used to generate the dataset of otoactive small molecules reported in:

> **Mapping the Otoactive Landscape: An LLM-Aided Extraction of Compounds and Their Targets**  DOI: [Link to Article]

The core code for the dataset generation is contained in: [database_build.py](https://github.com/aylindmm/Ototoxic_DB/blob/main/database_build.py).

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