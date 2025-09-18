import duckdb
import os
import yaml
import csv
import logging
from dateutil import parser
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_database(db_path):
    """Ensure tables exist and predefined environments are inserted."""
    conn = duckdb.connect(db_path)
    # Predefined environments (platform::os::version::device::batt_volt::batt_capa)

    predefined_envs = [
        "mobile::android::8::Samsung - Galaxy S7::3.85::3000.0",              ## To be tested
        "mobile::android::10::Samsung - Galaxy S9::3.85::3000.0",
        "mobile::android::10::Samsung - Galaxy S9::3.85::3000.0",             ## To be tested
        "mobile::android::10::Samsung - Galaxy S9::3.85::3000.0",
        "mobile::android::13::Samsung - Galaxy S22::3.88::3700.0",            ## To be tested
        "mobile::android::13::Samsung - Galaxy Tab S7 FE::3.86::10090.0",
        "mobile::android::12::Samsung - Galaxy S10::3.85::3400.0",
        "mobile::android::12::Samsung - Galaxy S10::3.85::3400.0",
        "mobile::android::14::Samsung - Galaxy S22::3.88::3700.0",            ## To be tested
    ]
    # Insert if not exists
    for env in predefined_envs:
        platform, os_, version, device, bv, bc = env.split("::")
        conn.execute(f"""
            INSERT INTO GSPT_Environment (device, OS, platform, version, battery_voltage, battery_capacity)
            SELECT '{device}', '{os_}', '{platform}', {version}, {bv}, {bc}
            WHERE NOT EXISTS (
                SELECT 1 FROM GSPT_Environment 
                WHERE device = '{device}' AND OS = '{os_}' 
                AND platform = '{platform}' AND version = {version}
            )
        """)
    logging.info("Inserted predefined environments.")
    return conn

def process_test_folder(conn, folder_path):
    """Process one test folder (config.yml + CSV files)."""
    config_file_path = os.path.join(folder_path, 'config.yml')
    with open(config_file_path) as f:
        config = yaml.safe_load(f)

    if config.get("db_test_id") != None:
        logging.info(f"Folder {folder_path} skipped, database id present in config file.")
        return
    
    # Insert G5K_Node (e.g., "paradoxe-7" → cluster "paradoxe")
    node_name = config['node']
    cluster = node_name.split('-')[0]
    conn.execute(f"""
        INSERT OR IGNORE INTO G5K_Node (cluster, name)
        VALUES (?, ?)
    """, [cluster, node_name])
    
    # Get node_id
    node_id = conn.execute(f"""
        SELECT id FROM G5K_Node WHERE name = ?
    """, [node_name]).fetchone()[0]
    
    # Insert GSPT_Test (match environment)
    env = config['environment']
    env_id = conn.execute(f"""
        SELECT id FROM GSPT_Environment
        WHERE device = ? AND OS = ? AND platform = ? AND version = ?
    """, [env['device'], env['os'], env['platform'], env['version']]).fetchone()[0]
    
    test_time = config['time']
    conn.execute(f"""
        INSERT INTO GSPT_Test (env_id, node_id, time, network, mode)
        VALUES (?, ?, ?, ?, ?)
    """, [env_id, node_id, test_time, config['network'], config['mode']])
    test_id = conn.execute("SELECT currval('seq_GSPT_Test_id')").fetchone()[0]
    config["db_test_id"] = test_id

    with open(config_file_path, "w") as conf:
        yaml.dump(config, conf, default_flow_style=False)

    logging.info(f"Inserted test {test_id} for node {node_name}.")
    
    # Process CSV files (steps)
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            step_name = filename.rpartition('_')[0]  # e.g., "step1_1234.csv" → "step1"
            # Insert step if not exists
            conn.execute(f"""
                INSERT OR IGNORE INTO GSPT_Step (name)
                VALUES (?)
            """, [step_name])
            step_id = conn.execute(f"""
                SELECT id FROM GSPT_Step WHERE name = ?
            """, [step_name]).fetchone()[0]
            
            # Parse CSV and insert measures
            with open(os.path.join(folder_path, filename)) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    timestamp = parser.parse(row['timestamp'])
                    rel_time = (timestamp - config['time']).total_seconds()  # Time since test start
                    conn.execute(f"""
                        INSERT INTO GSPT_Measure (
                            test_id, step_id, rel_time, AH_PL, C_ID, C_PL, 
                            D_ID, D_IN_ID, D_OUT_ID, M_ID, M_PL, O_DPacket_ID
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        test_id, step_id, rel_time,
                        row['AH_PL'] or None,
                        row['C_ID'] or None, 
                        row['C_PL'] or None, 
                        row['D_ID'] or None, 
                        row['D_IN_ID'] or None, 
                        row['D_OUT_ID'] or None, 
                        row['M_ID'] or None, 
                        row['M_PL'] or None, 
                        row['O_DPacket_ID'] or None,
                    ])
            logging.info(f"Inserted measures for step {step_name} in test {test_id}.")

def process(results_dir, db_path):
    conn = setup_database(db_path)
    conn.begin()
    try:
        for folder in os.listdir(results_dir):
            if folder in ["old", "staging"]: continue
            folder_path = os.path.join(results_dir, folder)
            if os.path.isdir(folder_path):
                logging.info(f"Processing folder: {folder}")
                process_test_folder(conn, folder_path)

        conn.commit()
    except Exception as e:
        logging.error("Couldn't finish ETL process")
        logging.error(e)
        traceback.print_exc()
        conn.rollback()

    conn.close()


process("../RESULTS_GSPT", "dataset.db")