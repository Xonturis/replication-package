import duckdb
import os
import yaml
import csv
from datetime import datetime
from dateutil import parser
import logging
import traceback
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_g5k_wattmeter(conn, csvfile, test_start_time, test_id):
    reader = csv.DictReader(csvfile)
    for row in reader:
        csv_timestamp = datetime.fromisoformat(row['timestamp']).replace(tzinfo=None)
        rel_time = (csv_timestamp - test_start_time).total_seconds()  # Time since test start
        value = float(row['value'])
        conn.execute("""
            INSERT INTO G5K_Power_Measure (test_id, rel_time, power)
            VALUES (?, ?, ?)
        """, [test_id, rel_time, value])

def process_g5k_throughput(conn, csvfile, test_start_time, test_id):
    reader = csv.DictReader(csvfile)
    for row in reader:
        if "POST" != row["Type"]: continue
        csv_timestamp = datetime.fromtimestamp(int(row['Timestamp'])).replace(tzinfo=None)
        rel_time = (csv_timestamp - test_start_time).total_seconds()  # Time since test start
        thrp = float(row['Requests/s'])
        med_rt = int(row['50%'])
        nn_rt = int(row['99%'])
        conn.execute("""
            INSERT INTO G5K_Throughput_Measure (test_id, rel_time, throughput, med_response_time, nnth_response_time)
            VALUES (?, ?, ?, ?, ?)
        """, [test_id, rel_time, thrp, med_rt, nn_rt])

def process_g5k_folder(conn, folder_path):
    """Process one G5K test folder (config.yml + CSV files)."""
    test_start_time = parser.parse(os.path.basename(folder_path)).replace(tzinfo=None)
    config_file_path = os.path.join(folder_path, 'config.yml')

    with open(config_file_path) as f:
        config = yaml.safe_load(f)

    if config.get("db_test_id") != None:
        logging.info(f"Folder {folder_path} skipped, database id present in config file.")
        return
    
    # Insert G5K_Node (e.g., "paradoxe-19" → cluster "paradoxe")
    node_name = config['node']
    cluster = node_name.split('-')[0]
    conn.execute(f"""
        INSERT OR IGNORE INTO G5K_Node (cluster, name)
        VALUES (?, ?)
    """, [cluster, node_name])
    node_id = conn.execute("SELECT id FROM G5K_Node WHERE name = ?", [node_name]).fetchone()[0]
    
    # Insert G5K_Test (handle optional args)
    args = config.get('args', {})
    conn.execute(f"""
        INSERT INTO G5K_Test (
            node_id, mode, time, run_time, spawn_rate, users, cstate
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        node_id,
        config["mode"],
        test_start_time,
        _parse_duration(args['run-time']),
        args['spawn-rate'],
        args['users'],
        config['cstate']
    ])
    test_id = conn.execute("SELECT currval('seq_G5K_Test_id')").fetchone()[0]
    config["db_test_id"] = test_id

    logging.info(f"Inserted G5K test {test_id} for node {node_name}.")
    
    throughput_path = 'locust/locust_stats_history.csv'
    csv_path = os.path.join(folder_path, throughput_path)
    if os.path.exists(csv_path):
        with open(csv_path) as csvfile:
            process_g5k_throughput(conn, csvfile, test_start_time, test_id)
        logging.info(f"Inserted {throughput_path} data for test {test_id}.")

    power_path = 'wattmetre.csv'
    csv_path = os.path.join(folder_path, power_path)
    if os.path.exists(csv_path):
        with open(csv_path) as csvfile:
            process_g5k_wattmeter(conn, csvfile, test_start_time, test_id)
        logging.info(f"Inserted {power_path} data for test {test_id}.")

    
    with open(config_file_path, "w") as conf:
        yaml.dump(config, conf, default_flow_style=False)

def _parse_duration(duration_str):
    """Convert "60s" -> 60 (int). Handles None."""
    if not duration_str:
        return None
    return pd.Timedelta(duration_str).total_seconds()

def setup_database(db_path):
    """Ensure tables exist and predefined environments are inserted."""
    conn = duckdb.connect(db_path)
    return conn

def process(results_g5k_dir, db_path):
    conn = setup_database(db_path)
    conn.begin()
    try:
        # Process G5K folders
        for folder in os.listdir(results_g5k_dir):
            folder_path = os.path.join(results_g5k_dir, folder)
            if os.path.isdir(folder_path):
                logging.info(f"Processing G5K folder: {folder}")
                process_g5k_folder(conn, folder_path)

        conn.commit()
    except Exception as e:
        logging.error("Couldn't finish ETL process")
        logging.error(e)
        traceback.print_exc()
        conn.rollback()
    
    conn.close()

process("../RESULTS_G5K", "dataset.db")