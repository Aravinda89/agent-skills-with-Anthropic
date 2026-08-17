import pandas as pd
import sqlite3

# Create SQLite database
# Read the CSV file
df = pd.read_csv('campaign_performance_4weeks.csv')

# Connect to SQLite database (creates it if it doesn't exist)
conn = sqlite3.connect('mydatabase.db')

# Import CSV data into a table
df.to_sql('tablename', conn, if_exists='replace', index=False)

# Close the connection
conn.close()


# vertify
conn = sqlite3.connect('mydatabase.db')
cursor = conn.cursor()

# Check the data
cursor.execute('SELECT * FROM tablename LIMIT 5')
print(cursor.fetchall())

conn.close()