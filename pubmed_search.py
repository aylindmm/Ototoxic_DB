import time
import pandas as pd
from Bio import Entrez
from tqdm import tqdm
from dotenv import load_dotenv, find_dotenv

class EntrezSearcher:
    def __init__(self, email, api_key):
        self.email = email
        self.api_key = api_key

    def fetch_pubmed_articles(self, search_terms, retmax=10000, batch_size=200):
        articles = []

        Entrez.email = self.email
        Entrez.api_key = self.api_key

        for term in tqdm(search_terms, total=len(search_terms), desc="Searching PubMed"):
            try:
                handle = Entrez.esearch(db="pubmed", 
                                        term=term, 
                                        retmax=retmax, 
                                        sort="pub_date",
                                        datetype="pdat",
                                        mindate="1950/01/01",
                                        maxdate="2025/12/31",
                                        usehistory="y")
                record = Entrez.read(handle)
                handle.close()
                count = int(record["Count"])
                webenv = record["WebEnv"]
                query_key = record["QueryKey"]

            except Exception as e:
                print(f"Error fetching IDs for term '{term}': {e}")
                continue

            # Fetch in batches 
            for start in range(0, count, batch_size):
                
                attempt = 0
                max_retries = 3
                success = False
                
                while attempt < max_retries and not success:
                    try:
                        handle = Entrez.efetch(db="pubmed", 
                                               webenv=webenv, 
                                               query_key=query_key, 
                                               retstart=start, 
                                               retmax=batch_size, 
                                               retmode="xml")
                        records = Entrez.read(handle)
                        handle.close()
                        success = True # We got the data!
                    except Exception as e:
                        attempt += 1
                        print(f"\nBatch error (Attempt {attempt}/{max_retries}): {e}")
                        time.sleep(5) # Wait 5 seconds before trying again

                for article in records["PubmedArticle"]:
                    citation = article["MedlineCitation"]
                    article_data = citation["Article"]

                    pmid = citation.get("PMID", "NA")
                    title = article_data.get("ArticleTitle", "NA")

                    # Abstract may have multiple parts
                    abstract = " ".join(article_data.get("Abstract", {}).get("AbstractText", [])) if "Abstract" in article_data else "NA"

                    # Year can come from different fields
                    date = article_data.get("ArticleDate", [])
                    year = article_data['Journal']['JournalIssue']['PubDate'].get("Year", "NA")
                    
                    # Extract DOI (if present) if not continue
                    
                    doi = "NA"
                    for el in article_data.get("ELocationID", []):
                        if el.attributes.get("EIdType") == "doi":
                            doi = str(el)
                            break
                    
                    # Get Language filter (only English)
                    languages = article_data.get("Language", [])
                    if "eng" not in languages:
                        continue  # Skip non-English articles

                    pub_types = article_data.get("PublicationTypeList", [])
                    if pub_types:
                        pub = str(pub_types[0])   # "Journal Article"

                    articles.append({
                        "PMID": pmid,
                        "DOI": doi,
                        "Title": title,
                        "Abstract": abstract,
                        "Year": year,
                        "PublicationTypes": pub
                    })
            print(f"Found {count} records for search '{term}'")
        articles = pd.DataFrame(articles)

        print("Filtering articles...")

        articles = articles.drop_duplicates(subset=["PMID"]) # Remove duplicate PMIDs
        articles = articles[(articles["Abstract"] != "NA")   # Filter out articles without abstracts, titles, or DOIs
                    &(articles["Title"] != "NA") 
                    ]  
        
        valid_types = ["Journal Article",
                       "Comparative Study",
                       "Clinical Trial", 
                       "Randomized Controlled Trial",
                       "Clinical Trial, Phase I",
                       "Clinical Trial, Phase II",
                       "Clinical Trial, Phase III",
                       "Case Reports"]
        articles = articles[articles["PublicationTypes"].isin(valid_types)]

        article_types = articles["PublicationTypes"].value_counts()
        print("Article types distribution:")
        print(article_types)
        print(f"Total articles fetched: {len(articles)}")
        print("Pubmed search script executed in ", time.process_time(), "seconds")
        return articles

