# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 12:20:25 2024

@author: dl923 / leadbot
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import glob

# Function to process a single pair of T0 and T1 files
def process_files(t0_file, t1_file):
    # Read the Excel files starting from the correct cell (B11 corresponds to row index 10 and column index 1)
    t0_data = pd.read_excel(t0_file, skiprows=10, usecols=range(1, 1+12))
    t1_data = pd.read_excel(t1_file, skiprows=10, usecols=range(1, 1+12))

    # Calculate the results by subtracting T0 from T1
    results = t1_data.values - t0_data.values

    # Define the groups (flipping the column indices)
    groups = {
        '1% 25mg': [(0, 0), (0, 1), (0, 2)],   # wells A1, A2, A3 -> A12, A11, A10
        '5% 25mg': [(0, 3), (0, 4), (0, 5)],   # wells A4, A5, A6 -> A9, A8, A7
        '10% 25mg': [(0, 6), (0, 7), (0, 8)],  # wells A7, A8, A9 -> A6, A5, A4
        '10% Glu 25mg ctrl': [(0, 9), (0, 10), (0, 11)],  # wells A10, A11, A13 -> A3, A2, A1
        '0% Glu 25mg ctrl': [(1, 9), (1, 10), (1, 11)],  # wells B10, B11, B13 -> B3, B2, B1
        '10% ctrl 0mg': [(1, 6), (1, 7), (1, 8)]  # wells B5, B6, B7 -> B6, B5, B4
    }

    # Calculate mean and standard deviation for each group
    group_means = {}
    group_stds = {}

    for group, indices in groups.items():
        values = [results[r][c] for r, c in indices]
        group_means[group] = np.mean(values)
        group_stds[group] = np.std(values)

    return group_means, group_stds

# Initialize lists to hold all means and standard deviations
all_group_means = {}
all_group_stds = {}

# Initialize lists for overall mean and std
overall_means = []
overall_stds = []

result_folder = "Microresp_results"
# Process each pair of files
for day in range(10):  # Adjust the range based on the number of days/files you have
    t0_file = os.path.join(result_folder, f'Microresp_day_{day}_t0.xls')
    t1_file = os.path.join(result_folder, f'Microresp_day_{day}_t1.xls')
    try:
         group_means, group_stds = process_files(t0_file, t1_file)
     
         for group in group_means:
             if group not in all_group_means:
                 all_group_means[group] = []
                 all_group_stds[group] = []
             all_group_means[group].append(group_means[group])
             all_group_stds[group].append(group_stds[group])
    except:
        print("Not completed day", str(day), "yet. Breaking...")
        break

# Calculate overall means and standard deviations for plotting
for group in all_group_means:
    overall_means.append(np.mean(all_group_means[group]))
    overall_stds.append(np.mean(all_group_stds[group]))

# Plot the results
fig, ax = plt.subplots()
groups = list(all_group_means.keys())

ax.bar(groups, overall_means, yerr=overall_stds, capsize=5)
ax.set_ylabel('Result (T1 - T0)')
ax.set_title('Mean Result and Standard Deviation for Each Group')
plt.xticks(rotation=45)
plt.tight_layout()

plt.show()
