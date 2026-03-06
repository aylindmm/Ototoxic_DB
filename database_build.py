import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

import sys
sys.path.insert(0, f'/home/aylin/Scripts/Literature_Mining/Packages/ototoxic_database/')
from pubmed_search import EntrezSearcher
from GPT_search import GPTextract
from pubchem_search import PubChemSearcher

# Define variables
_ = load_dotenv(find_dotenv()) # read local .env file

entrez = EntrezSearcher(email = os.environ['MAIL'], 
                        api_key = os.environ['ENTREZ_API_KEY'])

gpt = GPTextract(api_key = os.environ['OPENAI_API_KEY'], 
                 model = "gpt-4.1-nano-2025-04-14") # specify GPT model

# Output files
timestamp = datetime.now().strftime("%d_%m_%Y_%H.%M")
out_dir = "/home/aylin/ototoxic/new_database/"
print(f"Output will be saved to: {out_dir}")

# --------------------------- PUBMED SEARCH ---------------------------
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

 # Search PubMed for articles
articles = entrez.fetch_pubmed_articles(query) #test with small number of articles first
articles.to_csv(f"{out_dir}ototoxic_articles_{timestamp}.tsv", sep="\t", index=False)

# --------------------------- GPT EXTRACTION ---------------------------

prompt = """You are an expert pharmacologist specializing in otolaryngology. 
Your task is to extract drug information from the following research article.

Definitions:
- Ototoxic Agent: A drug or molecule that causes damage to the inner ear (cochleotoxicity or vestibulotoxicity), hearing loss or dizziness.
- Otoprotective Agent: A compound that prevents or mitigates such damage.

Instructions:
1. Identify all drugs, molecules, or experimental compounds mentioned.
2. Determine their role: "Ototoxic" or "Otoprotective".
3. Beware of Co-treatments: If an otoprotective agent is being tested *against* or in combination with a specific ototoxin, distinguish between the primary toxin (e.g., Cisplatin) and the protective candidate (e.g., N-acetylcysteine)."""

 # Parse the results with GPT
print("Starting GPT extraction with {}.".format(gpt.model))

results = gpt.fetch_gpt_data(df = articles,
                              prompt = prompt, 
                              variables = pd.read_csv(f"/home/aylin/Scripts/Literature_Mining/Packages/ototoxic_database/variables.txt", sep="\t")) 


results.to_csv(f"{out_dir}gpt_extracted_ototoxic_data_{timestamp}.tsv", sep="\t", index=False)
print("GPT extraction complete.")

results = pd.read_csv(f"/home/aylin/ototoxic/new_database/gpt_extracted_ototoxic_data_09_01_2026_00.14.tsv", sep="\t")   
articles = pd.read_csv(f"/home/aylin/ototoxic/new_database/ototoxic_articles_09_01_2026_00.14.tsv", sep="\t")
# --------------------------- PUBCHEM SEARCH ---------------------------
 # Convert drug lists to pubchem IDs and fetch compound info

pubchem_results = PubChemSearcher().fetch_compound_info(df = results, 
                                                        columns= ["ototoxic_drugs", "otoprotective_drugs"])
print("PubChem data retrieval complete.")

# Merge the results with the original articles
final_df = articles.merge(results.merge(pubchem_results, on="PMID", how="inner"), on="PMID", how="inner")

# Save final database
final_df.to_csv(f"{out_dir}ototoxic_compound_database_{timestamp}.tsv", sep="\t", index=False) 

print("Database build complete.")

