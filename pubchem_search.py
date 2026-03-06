import ast
import time
import pandas as pd
import pubchempy as pcp
from tqdm import tqdm

class PubChemSearcher:
    def __init__(self, delay=0.2): # Delay to prevent SSL handshake kicks
        self.delay = delay

    def fetch_compound_info(self, df, columns):
        compound_data = []
        
        for index, row in tqdm(df.iterrows(), total=len(df), desc="Processing compounds"):
            for column in columns:
                raw_value = row[column]

                # --- STEP 1: FIX THE DATA TYPE ---
                # This ensures we aren't iterating over letters in a string
                if isinstance(raw_value, str):
                    if raw_value.startswith('['):
                        try:
                            compounds = ast.literal_eval(raw_value)
                        except:
                            compounds = [raw_value]
                    else:
                        compounds = [raw_value]
                elif isinstance(raw_value, list):
                    compounds = raw_value
                else:
                    continue

                # --- STEP 2: SEARCH COMPOUNDS ---
                for compound in compounds:
                    # Clean the string and skip noise
                    compound = str(compound).strip()
                    if not compound or compound in ["[", "]", ""]:
                        continue

                    results = None
                    success = False
                    retries = 3
                    
                    while retries > 0 and not success:
                        try:
                            time.sleep(self.delay)
                            results = pcp.get_cids(compound, 'name', listkey_count=1, list_return='flat')
                            success = True 
                        except Exception as e:
                            retries -= 1
                            print(f"\nConnection error for {compound}, retrying... ({retries} left)")
                            time.sleep(2) # Wait longer on network failure

                    if success and results:
                        try:
                            # Fetch details for the first CID found
                            c = pcp.Compound.from_cid(results[0])
                            info = c.to_dict(properties=['canonical_smiles', 'iupac_name', 'inchikey', 'synonyms', 'cid'])
                            
                            # Safely handle synonyms
                            syns = info.get('synonyms', [])
                            primary_name = syns[0] if syns else info.get('iupac_name', compound)

                            compound_data.append({
                                "PMID": row.get('PMID'),
                                "PubChem_CID": info.get('cid'),
                                "iupac_name": info.get('iupac_name'),
                                "inchi_key": info.get('inchikey'),
                                "name": primary_name,
                                "synonyms": syns,
                                "smiles": info.get('canonical_smiles'),
                                "variable": column
                            })
                        except Exception as e:
                            print(f"\nError parsing {compound}: {e}")

        return pd.DataFrame(compound_data)