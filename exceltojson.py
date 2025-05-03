import pandas as pd
import json

# Read the Excel file
df = pd.read_excel('data_logs_extended.xlsx', sheet_name='Iteration_table')
df1 = pd.read_excel('data_logs_extended.xlsx', sheet_name='LOGS')

# Convert DataFrames to dictionaries
iteration_data = df.to_json(orient='records')
logs_data = df1.to_json(orient='records')

with open('iteration_data.json', 'w') as f:
    f.write(iteration_data)

with open('logs_data.json', 'w') as f:
    f.write(logs_data)
    



