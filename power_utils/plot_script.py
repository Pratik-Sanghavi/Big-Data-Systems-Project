import matplotlib.pyplot as plt

# Data for the baseline model
baseline = {
    "min": 0.495957,
    "25%": 0.693522,
    "50%": 0.834943,
    "75%": 1.195045,
    "max": 2.326239
}

# Data for the ADAPter model
adapter = {
    "min": 0.527821,
    "25%": 0.958327,
    "50%": 1.431101,
    "75%": 2.088507,
    "max": 3.642344
}

# Creating boxplot data
data_baseline = [baseline["min"], baseline["25%"], baseline["50%"], baseline["75%"], baseline["max"]]
data_adapter = [adapter["min"], adapter["25%"], adapter["50%"], adapter["75%"], adapter["max"]]

# Creating the plot
fig, ax = plt.subplots()
ax.boxplot([data_baseline, data_adapter], positions=[1, 2], widths=0.6)

# Adding labels and title
ax.set_xticklabels(['Baseline', 'ADAPter'])
ax.set_title('Latency Comparison')
ax.set_ylabel('Latency (seconds)')
plt.grid('on')
plt.hlines(2, xmin=0, xmax=2.5)
# Display the plot
plt.show()
