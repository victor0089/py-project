import sqlite3

# Connect to the database
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Define the ALTER TABLE statements to add each new column
alter_queries = [
    "ALTER TABLE invoices ADD COLUMN discount REAL;",
    "ALTER TABLE invoices ADD COLUMN total REAL;",
    "ALTER TABLE invoices ADD COLUMN notes TEXT;",
    "ALTER TABLE invoices ADD FOREIGN KEY (customer_id) REFERENCES customers(id);",
    "ALTER TABLE invoices ADD FOREIGN KEY (product_id) REFERENCES products(id);"
]

# Execute each ALTER TABLE statement
for query in alter_queries:
    c.execute(query)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Columns added to the table successfully.")
