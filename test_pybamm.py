import pybamm

# Load the DFN model
model = pybamm.lithium_ion.DFN()

# Load the parameter values
parameter_values = pybamm.ParameterValues.create_from_bpx('converted_battery_parameters.json')

# Define the experiment: Charge from SOC=0.01, then discharge
experiment = pybamm.Experiment([
    ("Charge at C/5 until 4.2 V",
     "Hold at 4.2 V until 1 mA",
     "Rest for 1 hour",
     "Discharge at C/5 until 2.5 V")
])

# Create the simulation with the experiment
sim = pybamm.Simulation(model, experiment=experiment, parameter_values=parameter_values)


# Define initial concentration in negative and positive electrodes
parameter_values["Initial concentration in negative electrode [mol.m-3]"] = 0.0279 * parameter_values["Maximum concentration in negative electrode [mol.m-3]"]
parameter_values["Initial concentration in positive electrode [mol.m-3]"] = 0.9084 * parameter_values["Maximum concentration in positive electrode [mol.m-3]"]

# Solve the simulation
sim.solve()

# Plot the results
sim.plot()
