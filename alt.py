import sqlite3

def check_and_update_products_table():
    # Connect to the database
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Check if the table exists
    c.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='products' ''')
    table_exists = c.fetchone()[0]

    if table_exists:
        # Check if the required columns exist
        c.execute('''PRAGMA table_info(products)''')
        existing_columns = [row[1] for row in c.fetchall()]
        required_columns = ['id', 'name', 'category', 'barcode', 'description', 'vendor', 'manufacturer', 'price', 'discount', 'tax', 'image_url']

        # Add any missing columns
        for column in required_columns:
            if column not in existing_columns:
                c.execute(f"ALTER TABLE products ADD COLUMN {column} TEXT")

        # Commit the changes
        conn.commit()
        print("Table 'products' updated successfully.")
    else:
        print("Table 'products' does not exist.")

    # Close the connection
    conn.close()

# Call the function to check and update the 'products' table
check_and_update_products_table()