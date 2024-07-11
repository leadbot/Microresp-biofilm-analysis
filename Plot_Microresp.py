# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 12:20:25 2024

@author: dl923 / leadbot
"""

#%% Microresp CO2 % plots

import pandas as pd
import numpy as np
import xlrd 
import seaborn

result_folder = "Microresp_results"
layout_file_path = os.path.join(result_folder, 'Layout.csv')  # Update with your local file path
#normalise values by reading times
hour_list={0:6,
           1:6,
           2:3,
           3:6,
           4:'',
           5:'',
           6:4,
           7:6,
           8:6
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

# Identify all pairs of T0 and T1 files
file_pairs = []
for filename in os.listdir(result_folder):
    if "t0" in filename:
        t1_filename = filename.replace("t0", "t1")
        if t1_filename in os.listdir(result_folder):
            file_pairs.append((os.path.join(result_folder, filename), os.path.join(result_folder, t1_filename)))

# Process each pair of files and collect the results
all_stats = []

for t0_file, t1_file in file_pairs:
    stats = calculate_group_statistics(layout_file_path, t0_file, t1_file, hour_list)
    day = t0_file.split('_')[-2]  # Extract day from filename
    for group in stats[0]:
        mean=stats[0][group][0]
        std=stats[0][group][1]
        all_stats.append({
            "Group": group,
            "Day": day,
            "Mean": mean,
            "Std": std
        })

# Create a DataFrame from the collected statistics
stats_df = pd.DataFrame(all_stats)

# Plot the data using Seaborn
plt.figure(figsize=(12, 6))
sns.lineplot(data=stats_df, x="Day", y="Mean", hue="Group", marker="o", err_style="bars", ci="sd")
plt.title("Microresp Results")
plt.xlabel("Day")
plt.ylabel("CO2 Concentration (%)")
plt.legend(title="Group")
plt.show()