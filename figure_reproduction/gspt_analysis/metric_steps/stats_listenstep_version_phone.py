import duckdb
import numpy as np

import matplotlib.pyplot as plt
from typing import Dict, List, Optional
import numpy as np

def plot_phone_metrics_scatter(
    data: Dict[str, Dict],
    metric: str = 'l_energy_mwh',
    show_listen_events: Optional[List[str]] = None,
    figsize: tuple = (4, 6),
    point_size: int = 100,
    jitter: bool = True,
    title: bool = False,
    metric_name: str = "metric name",
    show: bool = False
) -> None:
    """
    Creates a scatter plot of phone metrics with lofi (blue) and saas (red) points.
    
    Args:
        data: The dictionary containing phone metrics data
        metric: The metric to plot (default 'l_energy_mwh')
        show_listen_events: Specific listen events to include (None shows all)
        figsize: Size of the figure
        point_size: Size of the scatter points
        jitter: If True, adds slight horizontal jitter to avoid point overlap
    """
    plt.figure(figsize=figsize)
    
    phones_idx = {
        "Samsung - Galaxy S7":0,
        "Samsung - Galaxy S9":1,
        "Samsung - Galaxy Tab S7 FE":2,
        "Samsung - Galaxy S22":3
    }
    
    # Prepare data for plotting
    phones = list(data.keys())
    lofi_values = []
    saas_values = []
    idle_values = []
    phone_labels = []  # To keep track of which phone each point belongs to
    
    for phone_idx, (phone_name, phone_data) in enumerate(data.items()):
        # Process lofi data
        if 'lofi' in phone_data:
            for listen_event, measurements in phone_data['lofi'].items():
                if show_listen_events and listen_event not in show_listen_events:
                    continue
                for measurement in measurements:
                    lofi_values.append(measurement[metric])
                    idle_values.append(measurement["l_energy_mwh_of_idle"])
                    phone_labels.append((phones_idx[phone_name], 'lofi'))
                    phone_labels.append((phones_idx[phone_name], 'lofi_idle'))
        
        # Process saas data
        if 'saas' in phone_data:
            for listen_event, measurements in phone_data['saas'].items():
                if show_listen_events and listen_event not in show_listen_events:
                    continue
                for measurement in measurements:
                    saas_values.append(measurement[metric])
                    idle_values.append(measurement["l_energy_mwh_of_idle"])
                    phone_labels.append((phones_idx[phone_name], 'saas'))
                    phone_labels.append((phones_idx[phone_name], 'saas_idle'))
    
    # Prepare x-axis positions (potentially with jitter)
    x_lofi = []
    x_saas = []
    x_idle = []
    
    for i, (phone_idx, genre) in enumerate(phone_labels):
        pos = phone_idx
        if jitter:
            # Add small random offset to prevent overlap
            pos += np.random.uniform(-0.2, 0.2)
        
        if genre == 'lofi':
            pos += .1
            x_lofi.append(pos)
        elif genre == 'saas':
            pos -= .1
            x_saas.append(pos)
        elif 'lofi' in genre:
            pos += .1
            x_idle.append(pos)
        elif 'saas' in genre:
            pos -= .1
            x_idle.append(pos)
    
    # Plot the points
    # plt.scatter(x_lofi, lofi_values, s=point_size, color='tab:green', alpha=0.7, label='LoFi')
    # plt.scatter(x_saas, saas_values, s=point_size, color='tab:orange', alpha=0.7, label='SaaS')
    # plt.scatter(x_idle, idle_values, s=60, color='tab:red', alpha=0.7, label='Idle', marker='s')

    plt.scatter(lofi_values, x_lofi, s=point_size, color='tab:green', alpha=0.7, label='LP')
    plt.scatter(saas_values, x_saas, s=point_size, color='tab:orange', alpha=0.7, label='SaaS')
    plt.scatter(idle_values, x_idle, s=60, color='tab:red', alpha=0.7, label='Idle', marker='s')
    
    # Customize the plot
    # plt.xlabel('Phone Model')
    # plt.ylabel(metric_name)
    plt.ylabel('Phone Model')
    plt.xlabel(metric_name)
    if title:
        plt.title(f'{metric} comparison across phone models')
    
    # Set x-ticks at original phone positions
    phone_names = [
        name.split("Galaxy")[1]
        for name in phones_idx.keys()
    ]
    plt.yticks(range(len(phones)), phone_names, rotation=90, ha='right', va='center')
    
    # Add grid and legend
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.ylim(ymin=-.215)
    plt.tight_layout(pad=0)
    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)
    if show:
        plt.show()


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
            energy_ofidle = energy_idle*duration
            insert_res(results, test, step_name, phone_name, {
                'aggr': aggr, 
                'l_energy_mwh': energy, 
                'l_energy_mwh_noidle': energy_noidle, 
                'l_duration': duration,
                'l_energy_mwh_of_idle': energy_ofidle
                }
            )
    
    return results

def main():
    conn = duckdb.connect('../../dataset.db', read_only = True)

    metrics = [
        ["l_duration", "Duration (s)"],
        ["l_energy_mwh", "Energy (mWh)"],
        ["l_energy_mwh_noidle", "Energy (mWh)"],
        ["l_energy_mwh_of_idle", "Energy (mWh)"]
    ]

    m=metrics[1]
    metric = m[0]
    metric_name = m[1]
    print("\n" + metric + "\n")

    plot_phone_metrics_scatter(get_result(conn), jitter=False, metric=metric, metric_name=metric_name, show=False, figsize=(4,3))
    plt.savefig(f'./{metric}_dataset.pdf')

    # generate_avg_table(get_result(conn), metric)
    print(generate_avg_table(get_result(conn), metric))

    conn.close()

def generate_avg_table(data, metric):
    """
    Generates a LaTeX table with device energy consumption averages for LoFi and SaaS listen steps.
    
    Args:
        data (dict): Input dictionary containing device energy consumption data
    
    Returns:
        str: LaTeX formatted table string
    """
    # Initialize table header
    latex_table = """\\begin{table}[h]
\\centering
\\caption{XXX(Average or median) XXX per Device}
\\label{tab:XXX}
\\begin{tabular}{l|c|c}
\\textbf{Device} & \\textbf{LoFi (XXX)} & \\textbf{SaaS (XXX)} \\
\\hline
"""
    
    # Process each device
    for device, device_data in data.items():
        # Calculate LoFi average
        lofi_listens = device_data.get('lofi', {})
        lofi_energies = [
            step[metric] 
            for listen in list(lofi_listens.values())
            for step in listen
        ]
        lofi_avg = f'{np.median(lofi_energies):.3f}' if lofi_energies else "No data..."
        # lofi_avg = f'{(sum(lofi_energies) / len(lofi_energies)):.3f}' if lofi_energies else "No data..."

        # Calculate SaaS average
        saas_listens = device_data.get('saas', {})
        saas_energies = [
            step[metric] 
            for listen in saas_listens.values() 
            for step in listen
        ]
        saas_avg = f'{np.median(saas_energies):.3f}' if saas_energies else "No data..."
        # saas_avg = f'{(sum(saas_energies) / len(saas_energies)):.3f}' if saas_energies else "No data..."
        

        print(device)
        print("lofi", lofi_energies)
        print("saas", saas_energies)
        print()

        # Add device row to table
        latex_table += f"{device} & {lofi_avg} & {saas_avg} \\\\ \n"
    
    # Close table
    latex_table += """\\end{tabular}
\\end{table}"""
    
    return latex_table


if __name__ == "__main__":
    main()