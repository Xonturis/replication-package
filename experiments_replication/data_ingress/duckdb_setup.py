import duckdb

conn = duckdb.connect('./dataset.db')

conn.sql("""
CREATE SEQUENCE seq_G5K_Node_id START 1;
CREATE TABLE IF NOT EXISTS G5K_Node (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_G5K_Node_id'),
    cluster TEXT NOT NULL,
    name TEXT UNIQUE NOT NULL
);

CREATE SEQUENCE seq_G5K_Test_id START 1;
CREATE TABLE IF NOT EXISTS G5K_Test (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_G5K_Test_id'),
    node_id INTEGER NOT NULL,
    mode TEXT NOT NULL,
    time TIMESTAMP NOT NULL,
    run_time INTEGER NOT NULL,
    spawn_rate FLOAT NOT NULL,
    users INTEGER NOT NULL,
    cstate BOOL NOT NULL,
    FOREIGN KEY (node_id) REFERENCES G5K_Node(id)
);

CREATE SEQUENCE seq_G5K_Throughput_Measure_id START 1;
CREATE TABLE IF NOT EXISTS G5K_Throughput_Measure (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_G5K_Throughput_Measure_id'),
    test_id INTEGER NOT NULL,
    rel_time FLOAT NOT NULL,
    throughput FLOAT NOT NULL,
    med_response_time INTEGER NOT NULL,
    nnth_response_time INTEGER NOT NULL,
    FOREIGN KEY (test_id) REFERENCES G5K_Test(id)
);

CREATE SEQUENCE seq_G5K_Power_Measure_id START 1;
CREATE TABLE IF NOT EXISTS G5K_Power_Measure (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_G5K_Power_Measure_id'),  
    test_id INTEGER NOT NULL,
    rel_time FLOAT NOT NULL,
    power FLOAT NOT NULL, 
    FOREIGN KEY (test_id) REFERENCES G5K_Test(id)
);

CREATE SEQUENCE seq_GSPT_Environment_id START 1;
CREATE TABLE IF NOT EXISTS GSPT_Environment (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_GSPT_Environment_id'),
    device TEXT NOT NULL,
    OS TEXT NOT NULL,
    platform TEXT NOT NULL,
    battery_voltage FLOAT,
    battery_capacity FLOAT,
    version INTEGER NOT NULL
);

CREATE SEQUENCE seq_GSPT_Test_id START 1;
CREATE TABLE IF NOT EXISTS GSPT_Test (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_GSPT_Test_id'),
    env_id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    time TIMESTAMP NOT NULL,
    network TEXT NOT NULL,
    mode TEXT NOT NULL,
    FOREIGN KEY (env_id) REFERENCES GSPT_Environment(id),
    FOREIGN KEY (node_id) REFERENCES G5K_Node(id)
);

CREATE SEQUENCE seq_GSPT_Step_id START 1;
CREATE TABLE IF NOT EXISTS GSPT_Step (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_GSPT_Step_id'),
    name TEXT UNIQUE NOT NULL
);

CREATE SEQUENCE seq_GSPT_Measure_id START 1;
CREATE TABLE IF NOT EXISTS GSPT_Measure (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_GSPT_Measure_id'),
    test_id INTEGER NOT NULL,
    step_id INTEGER NOT NULL,
    rel_time FLOAT NOT NULL,
    AH_PL FLOAT,
    C_ID FLOAT,
    C_PL FLOAT,
    D_ID INTEGER,
    D_IN_ID INTEGER,
    D_OUT_ID INTEGER,
    M_ID INTEGER,
    M_PL INTEGER,
    O_DPacket_ID INTEGER,
    FOREIGN KEY (test_id) REFERENCES GSPT_Test(id),
    FOREIGN KEY (step_id) REFERENCES GSPT_Step(id)
);
""")