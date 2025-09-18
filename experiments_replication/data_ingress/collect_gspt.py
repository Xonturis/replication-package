import pandas as pd
import requests
import csv
import os
from datetime import datetime, timedelta
import yaml
import os
import datetime as dt
import glob

def transform_metrics_csv(input_file, output_file=None):
    """
    Transform a long-format metrics CSV into a wide-format DataFrame with metrics as columns.
    Also converts Unix timestamps in milliseconds to standard Python datetime format.
    
    Args:
        input_file (str): Path to the input CSV file
        output_file (str, optional): If provided, save the result to this file. Defaults to None.
    
    Returns:
        pd.DataFrame: Transformed DataFrame with timestamp as index and metrics as columns
    """
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Convert Unix timestamp (milliseconds) to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['timestamp'] = df['timestamp'] + timedelta(hours=2)
    
    # Pivot the table to get metrics as columns
    df_pivoted = df.pivot(index='timestamp', columns='metric', values='value')
    
    # Reset index to make timestamp a column again if needed
    df_pivoted = df_pivoted.reset_index()
    
    # Save to file if output_path is provided
    if output_file:
        df_pivoted.to_csv(output_file, index=False)
    
    return df_pivoted

# Constants
BASE_URL = "https://core-saas-prod.greenspector.com"
AUDIT_ID = "5099"

def load_bearer_token(token_path="token.txt"):
    """Read bearer token from a text file."""
    with open(token_path, "r") as f:
        return f.read().strip()  # Remove any trailing whitespace/newline

def fetch_json(endpoint):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {load_bearer_token()}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()

def get_gspt_results(test_time, results_folder):
    # Step 1: Get testCaseResults
    test_case_results = fetch_json(f"/api/audits/{AUDIT_ID}/meter")["testCaseResults"]

    for test_case in test_case_results:
        test_id = test_case["TestId"]
        
        # Step 2: Fetch test details
        test_details = fetch_json(f"/api/audits/{AUDIT_ID}/meter/test/{test_id}")
        
        # Step 3: Get TestScenarios[-2] and check updatedAt
        test_scenarios = test_details["TestScenarios"]
        updated_at = None
        measure = None
        for ts in test_scenarios:
            if "dumpsys" in ts["Device"]["name"]: continue

            ts_measure = ts["Measures"][-1]
            ts_upd_at = datetime.strptime(ts_measure["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
            if updated_at == None or ts_upd_at > updated_at: # Get latest measures
                updated_at = ts_upd_at
                measure = ts_measure
        
        if updated_at > test_time:
            test_name = test_details["Test"]["name"]
            measure_id = measure["id"]
            
            # Step 5: Fetch raw measures and save as CSV
            raw_measures = fetch_json(f"/api/measures/{measure_id}/rawMeasures")
            
            if not raw_measures:
                print(f"No raw measures for measure ID {measure_id}")
                continue
            
            # Generate safe filename (replace invalid chars if needed)
            safe_name = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in test_name)
            csv_filename = f"{safe_name}_{measure_id}.csv"
            csv_path = os.path.join(results_folder, csv_filename)
            
            with open(csv_path, mode='w', newline='') as csv_file:
                #Here:
                writer = csv.DictWriter(csv_file, fieldnames=["timestamp", "metric", "value"])
                writer.writeheader()
                writer.writerows(raw_measures)
            
            print(f"Saved {csv_path}")

def main():
    print("Starting collect of GSPT data")
    results_folder = "../RESULTS_GSPT"
    staging_folder = f"{results_folder}/staging"
    staging_config = f"{staging_folder}/config.yml"
    loaded_config = None
    with open(staging_config) as fh:
        loaded_config = yaml.safe_load(fh)

    if loaded_config is None:
        print("Couldn't load config")
        exit(1)

    time_of_exp = loaded_config["time"]
    adjusted_toe = time_of_exp - dt.timedelta(hours=2)

    result_folder = f"{results_folder}/{time_of_exp}"

    os.makedirs(result_folder, exist_ok=True)

    get_gspt_results(adjusted_toe, staging_folder)

    os.rename(staging_config, f'{result_folder}/config.yml')
    # Process each CSV in staging_folder
    for csv_file in glob.glob(f"{staging_folder}/*.csv"):
        filename = os.path.basename(csv_file)
        output_path = f"{result_folder}/{filename}"
        
        # Skip processing if output already exists
        if os.path.exists(output_path):
            continue
        
        # Process the file (assuming transform_metrics_csv is defined elsewhere)
        transform_metrics_csv(csv_file, output_path)
        print(f"Processed: {filename} → {output_path}")
        os.remove(csv_file)

if __name__ == "__main__":
    main()

