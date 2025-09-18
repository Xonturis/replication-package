import duckdb

listen_process_aggrQ_for_testQ_for_metricQ_template = None
listen_NF_process_aggrQ_for_testQ_for_metricQ_template = None
listen_process_times_for_testQ_template = None
all_tests_template = None
idle_ah_for_testQ_template = None

with open('../dbqueries/listen_process_aggr?_for_test?_for_metric?.sql') as file:
    listen_process_aggrQ_for_testQ_for_metricQ_template = file.read()

with open('../dbqueries/listen_NF_process_aggr?_for_test?_for_metric?.sql') as file:
    listen_NF_process_aggrQ_for_testQ_for_metricQ_template = file.read()

with open('../dbqueries/listen_process_times_for_test?.sql') as file:
    listen_process_times_for_testQ_template = file.read()

with open('../dbqueries/all_tests.sql') as file:
    all_tests_template = file.read()

with open('../dbqueries/environment_for_test?.sql') as file:
    environment_for_testQ_template = file.read()

with open('../dbqueries/idle_ah_for_test?.sql') as file:
    idle_ah_for_testQ_template = file.read()

def insert_res(results, test, step_name, phone, aggr):
    mode = test["mode"]
    
    if phone not in results:
        results[phone] = {}
    
    if mode not in results[phone]:
        results[phone][mode] = {}

    if step_name not in results[phone][mode]:
        results[phone][mode][step_name] = []
    
    results[phone][mode][step_name].append(aggr)

def get_result(conn):
    results = {}
    tests = conn.sql(all_tests_template).df()

    for i, test in tests.iterrows():
        test_id = test["id"]
        measures = conn.sql(listen_NF_process_aggrQ_for_testQ_for_metricQ_template.format(aggr="SUM", test=test_id, metric="AH_PL")).df()
        idle_ah = conn.sql(idle_ah_for_testQ_template.format(test=test_id)).df().iloc[0]
        env = conn.sql(environment_for_testQ_template.format(test=test_id)).df()
        phone = env.iloc[0]
        phone_name = phone["device"]
        battery_voltage = phone["battery_voltage"]
        energy_idle = (idle_ah["AH_PL"]/1000000) * battery_voltage / idle_ah["duration"]
        for i, step in measures.iterrows():
            step_name = step["name"]

            aggr = step["aggr"]
            energy = (aggr/1000000) * battery_voltage
            duration = step["end"]-step["start"]
            energy_noidle = energy - (energy_idle*duration)
            insert_res(results, test, step_name, phone_name, {
                'aggr': aggr, 
                'l_energy_mwh': energy, 
                'l_energy_mwh_noidle': energy_noidle, 
                'l_duration': duration, 
                'energy_idle': energy_idle
                }
            )
            
    return results

def main():
    conn = duckdb.connect('../../dataset.db', read_only = True)

    for phone, r in get_result(conn).items():
        for result in r["saas"]["secondListen"]:
            # Dev total energy for listen step
            energy_free_total = result["l_energy_mwh"]
            # Energy idle
            energy_idle = result["energy_idle"]
            # Idle time spent in scenario with a throughput of 1
            scenario_idle = 266
            # Response time with loaded server
            lat_sla = 1000 - scenario_idle # 1s - scenario_idle because this value is embedded in the SaaS measurements

            print(f'{phone} {(lat_sla/1000) * energy_idle}')
            print()

    conn.close()


if __name__ == "__main__":
    main()