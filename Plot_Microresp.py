# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 12:20:25 2024

@author: dl923 / leadbot
"""

#%% Microresp CO2 % plots

import pandas as pd
import numpy as np
import xlrd 
import seaborn as sns
import sys
import os
import matplotlib.pyplot as plt

result_folder = "Microresp_results"
layoutfile='Layout_R3.csv'

#normalise values by reading times
hour_list={0:2,
           1:6,
           2:6,
           5:7
               }


def process_files(t0_file, t1_file):
    """
    Processes the Excel files to compute differences and reverses the order of values in each row.

    Parameters:
    t0_file (str): Path to the time point 0 Excel file.
    t1_file (str): Path to the time point 1 Excel file.

    Returns:
    pd.DataFrame: The DataFrame with computed differences and reversed row values.
    """
    # Read the Excel files starting from the correct cell (B11 corresponds to row index 10 and column index 1)
    t0_data = pd.read_excel(t0_file, skiprows=10, usecols=range(1, 1+12), header=None)
    t1_data = pd.read_excel(t1_file, skiprows=10, usecols=range(1, 1+12), header=None)   
    # Reverse the values in each row
    reversed_t0_data = t0_data.apply(lambda row: row[::-1], axis=1)
    reversed_t1_data = t1_data.apply(lambda row: row[::-1], axis=1)
    
    return reversed_t0_data, reversed_t1_data

def calculate_group_statistics(layout_file, t0file, t1file, hour_list):
    """
    Calculates the mean and standard deviation for each group defined by the layout.

    Parameters:
    reversed_df (pd.DataFrame): The DataFrame with reversed row values.
    layout_file (str): Path to the layout CSV file.

    Returns:
    dict: A dictionary with group names as keys and a tuple (mean, std) as values.
    """
    # Load the layout file
    layout_df = pd.read_csv(layout_file, header=None)
    
    #read data from results files
    t0_data, t1_data = process_files(t0file, t1file)
    
    # Calculate the mean of the "Blank" values
    blank_mask = layout_df == "Blank"
    blank_t0_values = t0_data[blank_mask].values.flatten()
    # Filter out NaNs from the blank values
    blank_t0_values = blank_t0_values[~np.isnan(blank_t0_values)]
    # Calculate mean from blank t0 values
    mean_blank_t0 = np.mean(blank_t0_values)
    
    # Calculate the results by subtracting T0 from T1
    normalised_results = (t1_data.values[0:24] / t0_data.values[0:24]) * mean_blank_t0

    ### Microresp curve values ###
    A=-0.2265
    B=-1.606
    D=-6.771
    pct_co2_df=(A+B)/ (1+D * normalised_results)
    
    # Normalise results AFTER Co2 calculation as reading timepoints are different
    day=t0file.split('_')[-2] 
    hour=hour_list[int(day)]
    time_normalised_pct_co2_df=(pct_co2_df / hour)
    
    # Create a DataFrame from the results
    results_df = pd.DataFrame(time_normalised_pct_co2_df)
    
    # Get unique groups from the layout
    unique_groups = layout_df.values.flatten()
    unique_groups = [group for group in unique_groups if group != "Blank"]
    unique_groups = sorted(set(unique_groups))
    print(unique_groups)
    # Initialize a dictionary to store statistics for each group
    group_statistics = {}
    
    # Calculate mean and standard deviation for each group
    for group in unique_groups:
        mask = layout_df == group
        group_values = results_df[mask].values.flatten()
        group_values = group_values[~np.isnan(group_values)]  # Filter out NaNs
        mean = np.mean(group_values)
        std = np.std(group_values)
        group_statistics[group] = (mean, std)
    
    return group_statistics, layout_df


while True:
     try:
          layout_file_path = os.path.join(result_folder, layoutfile)  # Update with your local file path
     except Exception as e:
               exc_type, exc_obj, exc_tb = sys.exc_info()
               fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
               print('\nError:', e)         
               exit_error_countdown()
               print("####Error reading layout csv file###")
     break
# Identify all pairs of T0 and T1 files
file_pairs = []
for filename in os.listdir(result_folder):
    if "t0" in filename and "R3" in filename:
        t1_filename = filename.replace("t0", "t1")
        if t1_filename in os.listdir(result_folder):
            file_pairs.append((os.path.join(result_folder, filename), os.path.join(result_folder, t1_filename)))

# Process each pair of files and collect the results
all_stats = []

for t0_file, t1_file in file_pairs:
    stats, layout = calculate_group_statistics(layout_file_path, t0_file, t1_file, hour_list)
    day = t0_file.split('_')[-2]  # Extract day from filename
    for group in stats:
        mean=stats[group][0]
        std=stats[group][1]
        all_stats.append({
            "Group": group,
            "Day": day,
            "Mean": mean,
            "Std": std
        })
    final_day=day

# Create a DataFrame from the collected statistics
stats_df = pd.DataFrame(all_stats)

# Ensure the 'Day' column is treated as integers for correct numerical sorting
stats_df['Day'] = stats_df['Day'].astype(int)

# Sort the DataFrame by the 'Day' column to ensure correct ordering
stats_df = stats_df.sort_values(by='Day')

# Use the HLS palette
palette = sns.color_palette("hls", len(stats_df["Group"].unique()))

# Define a list of unique markers
markers = ['o', 's', '^', 'D', 'P', '*', 'X', 'H', 'v', '<', '>', '8']

# Create a color and marker dictionary to map groups to colors and markers
color_dict = {group: color for group, color in zip(stats_df["Group"].unique(), palette)}
marker_dict = {group: marker for group, marker in zip(stats_df["Group"].unique(), markers)}

# Plot the data using Seaborn and Matplotlib
fig=plt.figure(figsize=(12, 6))

for group in stats_df["Group"].unique():
    group_data = stats_df[stats_df["Group"] == group]
    color = color_dict[group]
    marker = marker_dict[group]
    plt.errorbar(group_data["Day"], group_data["Mean"], yerr=group_data["Std"], label=group, marker=marker, linestyle='--', markersize=8, color=color, capsize=5)
    plt.fill_between(group_data["Day"], group_data["Mean"] - group_data["Std"], group_data["Mean"] + group_data["Std"], alpha=0.2, color=color)

plt.title("Microresp Results")
plt.xlabel("Day")
plt.ylabel("CO2 Concentration (Δ%.h)")
plt.legend(title="Group")
plt.grid(True)
plt.tight_layout()
plt.show()
fig.savefig("Miscroresp_results_day_"+str(final_day)+".png", dpi=600, bbox_inches='tight')
