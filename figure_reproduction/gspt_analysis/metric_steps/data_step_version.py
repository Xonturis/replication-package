import duckdb
import numpy as np

conn = duckdb.connect('../dataset.db', read_only = True)

listen_process_aggrQ_for_testQ_for_metricQ_template = None
all_tests_template = None

with open('./dbqueries/listen_process_aggr?_for_test?_for_metric?.sql') as file:
    listen_process_aggrQ_for_testQ_for_metricQ_template = file.read()

with open('./dbqueries/all_tests.sql') as file:
    all_tests_template = file.read()

def insert_res(results, test, step_name, aggr):
    mode = test["mode"]
    
    if mode not in results:
        results[mode] = {}

    if step_name not in results[mode]:
        results[mode][step_name] = []
    
    results[mode][step_name].append(aggr)

def main():
    results = {}
    tests = conn.sql(all_tests_template).df()

    for i, test in tests.iterrows():
        test_id = test["id"]
        measures = conn.sql(listen_process_aggrQ_for_testQ_for_metricQ_template.format(aggr="SUM", test=test_id, metric="AH_PL")).df()
        for i, step in measures.iterrows():
            aggr = step["aggr"]
            step_name = step["name"]
            insert_res(results, test, step_name, aggr)
    
    print(results)

if __name__ == "__main__":
    main()