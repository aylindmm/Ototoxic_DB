This repository contains the source code and data processing workflows used to generate the dataset of otoactive small molecules reported in:

> **Mapping the Otoactive Landscape: An LLM-Aided Extraction of Compounds and Their Targets**  DOI: [Link to Article]

The core code for the dataset generation is contained in: [database_build.py](https://github.com/aylindmm/Ototoxic_DB/blob/main/database_build.py).

### How to Use the Pipeline

1.  Load requiered packages and declare variables.

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