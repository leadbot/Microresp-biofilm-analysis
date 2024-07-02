# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 12:20:25 2024

@author: dl923 / leadbot
"""

####updated script
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os

#%% CO2 absorbance only
# Function to process a single pair of T0 and T1 files
def process_files(t0_file, t1_file):
    # Read the Excel files starting from the correct cell (B11 corresponds to row index 10 and column index 1)
    t0_data = pd.read_excel(t0_file, skiprows=10, usecols=range(1, 1+12), header=None)
    t1_data = pd.read_excel(t1_file, skiprows=10, usecols=range(1, 1+12), header=None)
    print(t0_data, t1_data)
    # Calculate the results by subtracting T0 from T1
    results = -1 * (t1_data.values - t0_data.values) 
    print(str(t0_file))
    print(results)
    
    # Define the groups (flipping the column indices)
    groups = {
        '1% innoculum + 25mg biofilm': [(0, 11), (0, 10), (0, 9)],   # wells A1, A2, A3 -> A12, A11, A10
        '5% innoculum + 25mg': [(0, 8), (0, 7), (0, 6)],   # wells A4, A5, A6 -> A9, A8, A7
        '10% innoculum + 25mg': [(0, 3), (0, 4), (0, 5)],  # wells A7, A8, A9 -> A6, A5, A4
        '10% innoculum + 25mg Glu ctrl': [(0, 0), (0, 1), (0, 2)],  # wells A10, A11, A13 -> A3, A2, A1
        '0% innoculum + 25mg Glu ctrl': [(1, 0), (1, 1), (1, 2)],  # wells B10, B11, B13 -> B3, B2, B1
        '10% innoculum only': [(1, 3), (1, 4), (1, 5)]  # wells B5, B6, B7 -> B6, B5, B4
    }
    # Calculate mean and standard deviation for each group
    group_means = {}
    group_stds = {}

    for group, indices in groups.items():
        values = [results[r][c] for r, c in indices]
        group_means[group] = np.mean(values)
        group_stds[group] = np.std(values)

    return group_means, group_stds, t0_data, t1_data, t0_data.values, t1_data.values

# Initialize dictionaries to hold all means and standard deviations per day
all_group_means = {}
all_group_stds = {}

result_folder = "Microresp_results"

# Find all T0 files and process corresponding T1 files
t0_files = glob.glob(os.path.join(result_folder, 'Microresp_day_*_t0.xls'))

if not t0_files:
    print("No T0 files found in the result folder.")
else:
    for t0_file in t0_files:
        day = t0_file.split('_')[3]
        t1_file = os.path.join(result_folder, f'Microresp_day_{day}_t1.xls')
        if os.path.exists(t1_file):  # Check if corresponding T1 file exists
            try:
                group_means, group_stds, t0d, t1v, t0v, t1v = process_files(t0_file, t1_file)
                for group in group_means:
                    if group not in all_group_means:
                        all_group_means[group] = {}
                        all_group_stds[group] = {}
                    all_group_means[group][day] = group_means[group]
                    all_group_stds[group][day] = group_stds[group]
            except Exception as e:
                print(f"Error processing files for day {day}: {e}")
        else:
            print(f"T1 file for day {day} not found: {t1_file}")

if all_group_means:
    # Plot all groups on a single scatter plot
    plt.figure(figsize=(12, 8))
    plt.title('Mean Result and Standard Deviation for Each Group by Day')

    markers = ['o', 's', '^', 'D', 'P', '*']
    colors = ['b', 'g', 'r', 'c', 'm', 'y']

    for (group, means), marker, color in zip(all_group_means.items(), markers, colors):
        days = sorted(means.keys())
        mean_values = [means[day] for day in days]
        std_values = [all_group_stds[group][day] for day in days]
        
        plt.errorbar(days, mean_values, yerr=std_values, fmt=marker, label=group, capsize=5, color=color)

    plt.xlabel('Day')
    plt.ylabel('Cresol red absorbance change')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
else:
    print("No data processed. Please check the files and the result folder path.")

#%% CO2 mM concentration estimation
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os

# Constants for CO2 calculation
pKa = 6.1  # pKa for bicarbonate buffer system
calibration_slope = -1.0  # Example slope, convert absorbance change to pH change; negative for typical cresol red response
initial_pH = 7.0
initial_HCO3_concentration = 1.0  # in mM, example value

# Function to transform absorbance to CO2 concentration
def transform_absorbance_to_co2(A_T0, A_T1):
    # Calculate change in absorbance
    delta_A = A_T1 - A_T0
    
    # Convert change in absorbance to change in pH using the calibration curve
    delta_pH = delta_A * calibration_slope
    
    # Calculate final pH
    final_pH = initial_pH + delta_pH
    
    # Use Henderson-Hasselbalch equation to find initial and final CO2 concentration
    initial_CO2_concentration = initial_HCO3_concentration / (10**(initial_pH - pKa))
    final_CO2_concentration = initial_HCO3_concentration / (10**(final_pH - pKa))
    
    # Calculate change in CO2 concentration
    delta_CO2_concentration = final_CO2_concentration - initial_CO2_concentration
    
    return delta_CO2_concentration

# Function to process a single pair of T0 and T1 files
def process_files(t0_file, t1_file):
    # Read the Excel files starting from the correct cell (B11 corresponds to row index 10 and column index 1)
    t0_data = pd.read_excel(t0_file, skiprows=10, usecols=range(1, 1+12), header=None)
    t1_data = pd.read_excel(t1_file, skiprows=10, usecols=range(1, 1+12), header=None)
    
    # Calculate the results by subtracting T0 from T1 and transforming to CO2 concentration
    results = np.vectorize(transform_absorbance_to_co2)(t0_data.values[0:24], t1_data.values[0:24])
    
    # Define the groups (flipping the column indices)
    groups = {
        '1% 25mg': [(0, 11), (0, 10), (0, 9)],   # wells A1, A2, A3 -> A12, A11, A10
        '5% 25mg': [(0, 8), (0, 7), (0, 6)],     # wells A4, A5, A6 -> A9, A8, A7
        '10% 25mg': [(0, 3), (0, 4), (0, 5)],    # wells A7, A8, A9 -> A6, A5, A4
        '10% Glu 25mg ctrl': [(0, 0), (0, 1), (0, 2)],  # wells A10, A11, A13 -> A3, A2, A1
        '0% Glu 25mg ctrl': [(1, 0), (1, 1), (1, 2)],   # wells B10, B11, B13 -> B3, B2, B1
        '10% ctrl 0mg': [(1, 3), (1, 4), (1, 5)]        # wells B5, B6, B7 -> B6, B5, B4
    }
    
    # Calculate mean and standard deviation for each group
    group_means = {}
    group_stds = {}

    for group, indices in groups.items():
        values = [results[r][c] for r, c in indices]
        group_means[group] = np.mean(values)
        group_stds[group] = np.std(values)

    return group_means, group_stds

# Initialize dictionaries to hold all means and standard deviations per day
all_group_means = {}
all_group_stds = {}

result_folder = "Microresp_results"

# Find all T0 files and process corresponding T1 files
t0_files = glob.glob(os.path.join(result_folder, 'Microresp_day_*_t0.xls'))

if not t0_files:
    print("No T0 files found in the result folder.")
else:
    for t0_file in t0_files:
        day = t0_file.split('_')[3]
        t1_file = os.path.join(result_folder, f'Microresp_day_{day}_t1.xls')
        if os.path.exists(t1_file):  # Check if corresponding T1 file exists
            try:
                group_means, group_stds = process_files(t0_file, t1_file)
                for group in group_means:
                    if group not in all_group_means:
                        all_group_means[group] = {}
                        all_group_stds[group] = {}
                    all_group_means[group][day] = group_means[group]
                    all_group_stds[group][day] = group_stds[group]
            except Exception as e:
                print(f"Error processing files for day {day}: {e}")
        else:
            print(f"T1 file for day {day} not found: {t1_file}")

if all_group_means:
    # Plot all groups on a single scatter plot
    plt.figure(figsize=(12, 8))
    plt.title('Mean CO2 Concentration and Standard Deviation for Each Group by Day')

    markers = ['o', 's', '^', 'D', 'P', '*']
    colors = ['b', 'g', 'r', 'c', 'm', 'y']

    for (group, means), marker, color in zip(all_group_means.items(), markers, colors):
        days = sorted(means.keys())
        mean_values = [means[day] for day in days]
        std_values = [all_group_stds[group][day] for day in days]
        
        plt.errorbar(days, mean_values, yerr=std_values, fmt=marker, label=group, capsize=5, color=color)

    plt.xlabel('Day')
    plt.ylabel('CO2 Concentration (mM)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
else:
    print("No data processed. Please check the files and the result folder path.")
