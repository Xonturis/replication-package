import duckdb
import matplotlib.pyplot as plt
from matplotlib import cm


cumulative_metricQ_for_testQ_template = None
test_id_modeQ_template = None
step_start_rel_time_for_testQ_template = None

with open('../dbqueries/test_id_mode?.sql') as file:
    test_id_modeQ_template = file.read()

with open('../dbqueries/cumulative_metric?_for_test?.sql') as file:
    cumulative_metricQ_for_testQ_template = file.read()

with open("../dbqueries/step_start_rel_time_for_test?.sql", "r") as file:
    step_start_rel_time_for_testQ_template = file.read()

def plot_step_starts(conn, test_id, ax=None):
    req=step_start_rel_time_for_testQ_template.format(test=test_id)
    df=conn.sql(req).df()

    if ax == None:
        ax=plt.gca()

    for i, row in df.iterrows():
        if "BEFORE" in row["name"] or "AFTER" in row["name"]: continue
        ax.axvline(x=row["relative_rel_time"], color='k', linestyle='-', zorder=0)
        y_top = ax.get_ylim()[1]  # Get max y-axis value
        ax.text(
            row["relative_rel_time"] + 0.15,
            y_top,  # Use actual data coordinate
            row["name"],
            rotation=90,
            va='top',
            zorder=3,
            alpha=0.7
        )

def create_composite_plot(bar_data_dict, line_data_dict, 
                         bar_colors_dict, line_colors, info_line_stops,
                         figsize=(16, 12), bar_width=0.6,
                         category_names=None):
    
    if category_names is None:
        category_names = list(bar_data_dict.keys())
    
    # Create figure with 2x2 grid
    fig = plt.figure(figsize=figsize)
    
    # Create grid specification
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 10], height_ratios=[1, 1])
    
    

    # Create axes
    ax_bar1 = fig.add_subplot(gs[0, 0])  # Top left - bar plot for category 1
    ax_bar2 = fig.add_subplot(gs[1, 0])  # Bottom left - bar plot for category 2
    ax_line1 = fig.add_subplot(gs[0, 1])  # Top right - line plot for category 1
    ax_line2 = fig.add_subplot(gs[1, 1])  # Bottom right - line plot for category 2
    
    # Share xy-axis for plots
    ax_line1.sharex(ax_line2)
    ax_line1.sharey(ax_line2)
    ax_bar2.sharey(ax_line2)
    ax_bar1.sharey(ax_line1)
    
    # Prepare bar data
    bar_labels = ['A', 'B', 'C']  # Default labels, you can customize this
    
    # Plot stacked bar plots
    for i, category in enumerate(category_names):
        if category in bar_data_dict:
            bar_values = bar_data_dict[category]
            bar_colors = bar_colors_dict[category]
            
            # Create bottom positions for stacking
            bottom = 0
            ax = ax_bar1 if i == 0 else ax_bar2
            
            for j, val in enumerate(bar_values):
                val -= bottom
                b=ax.bar(0, val, bottom=bottom, 
                        color=bar_colors[j % len(bar_colors)], 
                        width=bar_width)
                bottom += val
                ax.bar_label(b, label_type='center', labels=[bar_labels[j]])
            
            
            
            # Customize bar plots
            # ax.set_xticks(range(n_bars))
            # ax.set_xticklabels(bar_labels)
            ax.tick_params(
                axis='x',
                which='both',
                bottom=False,
                top=False,
                labelbottom=False)
            # ax.set_title(f'{category} - Events')
            # ax.set_ylabel('Data Consumption (MB)')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Remove top and right spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
    
    # Plot line plots
    for i, category in enumerate(category_names):
        if category in line_data_dict:
            df = line_data_dict[category]
            ax = ax_line1 if i == 0 else ax_line2
            
            ax.plot(df["relative_rel_time"], df["cumul"], 
                   color=line_colors[i % len(line_colors)], 
                   linewidth=2.5, label=category, zorder=2)
            
            bar_values = bar_data_dict[category]
            bar_colors = bar_colors_dict[category]
            line_stops = info_line_stops[category]
            for j, val in enumerate(bar_values):
                ax.hlines(y=val, xmin=-10, xmax=line_stops[j], colors=bar_colors[j],zorder=1, linestyles='dashed', linewidths=.85)
                
            # Customize line plots
            # ax.set_title(f'{category} - Evolution')
            # ax.set_ylabel('Cumulated ')
            ax.grid(True, alpha=0.3)
            
            # Remove top and right spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.legend(loc='lower right')# , prop={'size': 12}
            ax.set_xlim(xmin=-10)
    
    # Set x-label for bottom line plot only
    ax_line2.set_xlabel('Time (s)')
    
    ax_line1.tick_params(
                axis='y',
                which='both',
                left=True,
                labelleft=False)
    ax_line2.tick_params(
                axis='y',
                which='both',
                left=True,
                labelleft=False)
    ax_line1.tick_params(
                axis='x',
                which='both',
                bottom=True,
                labelbottom=False)
    

    fig.supylabel("Data Transfer (MB)")

    plt.tight_layout(pad=0, rect=(0.025,0,1,1))
    return fig, (ax_bar1, ax_bar2, ax_line1, ax_line2)

def main():
    conn = duckdb.connect('../../dataset.db', read_only = True)

    saas_test_id = 4
    lofi_test_id = 7

    saas_df = conn.sql(cumulative_metricQ_for_testQ_template.format(metric="D_ID", test=saas_test_id)).df()
    lofi_df = conn.sql(cumulative_metricQ_for_testQ_template.format(metric="D_ID", test=lofi_test_id)).df()

    saas_df["cumul"] = saas_df["cumul"] / 1_000_000
    lofi_df["cumul"] = lofi_df["cumul"] / 1_000_000

    saas_df = saas_df[saas_df["relative_rel_time"].between(0,110)]
    lofi_df = lofi_df[lofi_df["relative_rel_time"].between(0,110)]

    events_x = [87, 90]

    bar_data = {
        'SaaS (Test 4)': [saas_df[saas_df['relative_rel_time']<events_x[0]].iloc[-1]["cumul"],
                          saas_df[saas_df['relative_rel_time']<events_x[1]].iloc[-1]["cumul"],
                          saas_df.iloc[-1]["cumul"]],
        'LP (Test 7)': [lofi_df[lofi_df['relative_rel_time']<events_x[0]].iloc[-1]["cumul"],
                          lofi_df[lofi_df['relative_rel_time']<events_x[1]].iloc[-1]["cumul"],
                          lofi_df.iloc[-1]["cumul"]]
    }

    bar_colors = {
        'SaaS (Test 4)': [cm.tab20c(5), cm.tab20c(6), cm.tab20c(7)],
        'LP (Test 7)': [cm.tab20c(9), cm.tab20c(10), cm.tab20c(11)]
    }

    line_data = {
        'SaaS (Test 4)': saas_df,
        'LP (Test 7)': lofi_df
    }

    info_line_stops = {
        'SaaS (Test 4)': [75,90,110],
        'LP (Test 7)': [75,90,90]
    }

    fig, axes = create_composite_plot(
        bar_data_dict=bar_data,
        line_data_dict=line_data,
        bar_colors_dict=bar_colors,
        info_line_stops=info_line_stops,
        line_colors=['tab:orange', 'tab:green'],
        figsize=(4,3),
        category_names=['SaaS (Test 4)', 'LP (Test 7)']
    )

    # If you want to plot lines for step start
    # plot_step_starts(conn, 7, axes[3])
    
    # plt.show()
    plt.savefig("data_cumul.pdf")
    conn.close()

if __name__ == "__main__":
    main()