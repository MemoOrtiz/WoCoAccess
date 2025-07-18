import pyodbc  # Library to connect to and interact with SQL databases
import RPi.GPIO as GPIO  # Library to control GPIO pins on the Raspberry Pi
import time  # Library for time-related functions
from datetime import datetime  # Library for handling dates and times
import threading  # Library for creating and managing threads
import queue  # Library for managing a thread-safe queue
import schedule  # Library for scheduling tasks

# Database configuration
Database = ""  # Name of the database
Username = ""    # Username for database access
Password = ""     # Password for the database

# Connection string to connect to the database using ODBC
connection_string = f'DSN={{FreeDSN}};DATABASE={Database};UID={Username};PWD={Password}'

# Set up GPIO mode to BCM (Broadcom SOC channel)
GPIO.setmode(GPIO.BCM)

# List of GPIO pins connected to the sensors
sensor_pins = [27, 22, 14]  # GPIO pins for Sensor 1, 2, and 3
sensor_names = ["Sensor1", "Sensor2", "Sensor3"]  # Names of the sensors
values = ['A','B','C']  # Value to log when motion is detected
tables = ["", "", ""]  # Database tables for each sensor

# Configure each GPIO pin as an input with a pull-up resistor
for pin in sensor_pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Establish a connection to the database and create a cursor for executing SQL queries
connection = pyodbc.connect(connection_string)
cursor = connection.cursor()
print("Connected successfully")  # Confirm successful database connection

# Queue to manage tasks for inserting data into the database
insertion_queue = queue.Queue()

def insert_data_worker():
    """
    Worker thread function to insert data into the database from the queue.
    Runs continuously in the background.
    """
    while True:
        # Retrieve a task from the queue
        table_name, sensor_index, value, sensor_name = insertion_queue.get()
        if table_name is None:  # Exit signal if None is encountered
            break
        # Get the current timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        try:
            # Log insertion details and execute SQL query
            print(f"Inserting into table: [DBNAME].[-].[{table_name}]")
            query = f"INSERT INTO [DBNAME].[-].[{table_name}] VALUES (?, ?)"
            cursor.execute(query, current_time, value)
            connection.commit()  # Commit the transaction to the database
            print(f"{sensor_name} - productionDate:", current_time, "result:", value)
        except pyodbc.Error as e:
            print(f"Error inserting data: {e}")
        # Indicate that the task has been completed
        insertion_queue.task_done()

# Start a background thread to handle database insertions
worker_thread = threading.Thread(target=insert_data_worker)
worker_thread.start()

def insert_at_scheduled_times(sensor_index):
    """
    Schedule insertion of 'R' into the database at specific times.
    Puts the task into the queue.
    """
    insertion_queue.put((tables[sensor_index], sensor_index, 'R', sensor_names[sensor_index]))

# Schedule tasks to insert 'R' values at specific times
schedule_times = ["06:30", "11:30", "13:30", "16:30", "21:30", "02:00", "04:30"]
for time_str in schedule_times:
    for i in range(len(sensor_pins)):
        # Schedule insertion for each sensor at the specified times
        schedule.every().day.at(time_str).do(insert_at_scheduled_times, sensor_index=i)

def run_schedule():
    """
    Continuously run scheduled tasks.
    """
    while True:
        schedule.run_pending()  # Run any tasks that are due
        time.sleep(1)  # Wait for 1 second before checking again

# Start a background thread to handle scheduled tasks
schedule_thread = threading.Thread(target=run_schedule)
schedule_thread.daemon = True  # Daemon thread will exit when the main program exits
schedule_thread.start()

def motion_detected(channel):
    """
    Callback function triggered when motion is detected by a sensor.
    """
    sensor_index = sensor_pins.index(channel)  # Identify which sensor triggered the callback
    actual_state = GPIO.input(sensor_pins[sensor_index])  # Read the sensor state

    print(f"{sensor_names[sensor_index]} state: {actual_state}")  # Print sensor state

    if actual_state == 1:  # If motion is detected
        print(f"Object detected at {sensor_names[sensor_index]}")
        # Add a task to the queue to insert data into the database
        insertion_queue.put((tables[sensor_index], sensor_index, values[sensor_index], sensor_names[sensor_index]))
    elif actual_state == 0:  # If motion is no longer detected
        print(f"Object removed from {sensor_names[sensor_index]}")

# Set up interrupts to detect motion on each GPIO pin and call the motion_detected function
for pin in sensor_pins:
    GPIO.add_event_detect(pin, GPIO.BOTH, callback=motion_detected, bouncetime=200)  # Detect both rising and falling edges with a debounce of 200ms

try:
    while True:
        time.sleep(0.1)  # Keep the main program running
except KeyboardInterrupt:
    pass  # Exit on keyboard interrupt
finally:
    # Stop the worker thread and close the database connection
    insertion_queue.put((None, None, None, None))  # Signal the worker thread to exit
    worker_thread.join()  # Wait for the worker thread to finish

    if 'connection' in locals():
        connection.close()  # Close the database connection
        print("Database connection closed.")