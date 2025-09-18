import duckdb
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.transforms as transforms

power_throughput_for_testQ_template = None
highest_throughput_for_latencyQ_for_testQ_template = None

with open('./dbqueries/power_throughput_for_test?.sql') as file:
    power_throughput_for_testQ_template = file.read()

with open('./dbqueries/highest_throughput_for_latency?_for_test?.sql') as file:
    highest_throughput_for_latencyQ_for_testQ_template = file.read()

def throughput_power_converter(conn, test_id):
    thr_pwr = conn.sql(power_throughput_for_testQ_template.format(test=test_id)).df()
    thr = thr_pwr["throughput"]
    pwr = thr_pwr["power"]

    return np.poly1d(np.polyfit(thr, pwr, 3))

def get_throughput_for_sla(conn, test_id, sla=1000):
    res = conn.sql(highest_throughput_for_latencyQ_for_testQ_template.format(latency=sla, test=test_id)).df()
    return res.iloc[0]["throughput"]

def get_power_draw_estimator(conn, sla, test_id):
    f_pwrthr = throughput_power_converter(conn, test_id)
    thrp_sla = get_throughput_for_sla(conn, test_id, sla)

    def f(thrp):
        res = []
        for x in thrp:
            res.append(f_pwrthr(thrp_sla) * math.floor((x/thrp_sla)) + f_pwrthr(x%thrp_sla))
        return res
    
    return f

def get_energy_per_req_estimator(conn, sla, test_id):
    f_pwrthr = throughput_power_converter(conn, test_id)
    thrp_sla = get_throughput_for_sla(conn, test_id, sla)

    def f(thrp):
        res = []
        for x in thrp:
            res.append(((f_pwrthr(thrp_sla) * math.floor((x/thrp_sla)) + f_pwrthr(x%thrp_sla))/x)/3.6)
        return res

    return f


def plot_power_draw_and_epr(conn, sla, test_id):
    power_model = get_power_draw_estimator(conn, sla, test_id)
    epr_model = get_energy_per_req_estimator(conn, sla, test_id)
    myline = np.linspace(1, 1000, 100)

    fig, ax1 = plt.subplots(figsize=(5, 5))

    # Instantiate a second axes that shares the same x-axis
    ax2 = ax1.twinx() 

    ax1.set_xlabel('Throughput (req/s)')
    ax1.set_ylabel("Power (W)")
    ax2.set_ylabel("Energy (mWh)")
    power_data = power_model(myline)
    epr_data = epr_model(myline)
    min_epr = 1.22 # np.min(epr_data)
    max_power = np.max(power_data)

    ax1.grid(True, linestyle='--', color='tab:orange', alpha=0.2)

    ax2.semilogy(myline, epr_data, color=cm.tab20c(16), label="SaaS Energy per Request", alpha=.7)

    # y_ticks = np.append(ax2.get_yticks(), 4)
    # y_ticks = np.append(y_ticks, 6)
    # ax2.set_yticks(y_ticks)

    ax1.axhline(y=max_power, color="tab:orange", ls='--', alpha=.7)
    trans = transforms.blended_transform_factory(ax1.get_yticklabels()[0].get_transform(), ax1.transData)
    ax1.text(0,max_power, "{:.0f}".format(max_power), color="tab:orange", transform=trans, 
        ha="right", va="center")

    ax2.axhline(y=min_epr, color=cm.tab20c(16), ls='--', alpha=.4)
    trans = transforms.blended_transform_factory(ax2.get_yticklabels()[0].get_transform(), ax2.transData)
    ax2.text(1,min_epr, "{:.2f}".format(min_epr), color=cm.tab20c(16), transform=trans, 
        ha="left", va="center")
    
    # ax2.text(1,4, "4", color="grey", transform=trans, ha="left", va="center")
    # ax2.text(1,6, "6", color="grey", transform=trans, ha="left", va="center")

    ax1.plot(myline, power_data, color='tab:orange', label="SaaS Servers Power Draw")
    plt.tight_layout(pad=0)
    ax1.set_ylim(ymin=0)
    ax2.set_ylim(ymin=min(epr_data)-.2)

    ax1.yaxis.label.set_color('tab:orange')
    ax1.spines["right"].set_visible(False)
    ax1.spines['left'].set_color("tab:orange")
    ax1.tick_params(axis='y', colors='tab:orange', which='both')

    ax2.yaxis.label.set_color(cm.tab20c(16))
    ax2.spines["right"].set_edgecolor(cm.tab20c(16))
    ax2.spines["left"].set_visible(False)
    ax2.tick_params(axis='y', colors=cm.tab20c(16), which='both')

    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)

    fig.legend(loc=(.2,.85), prop={'size': 12})

    # plt.show() 
    plt.savefig('./impact_load_plot.pdf')


def main():
    conn = duckdb.connect('../dataset.db', read_only = True)

    plot_power_draw_and_epr(conn, 1000, 1)
    
    conn.close()


if __name__ == "__main__":
    main()