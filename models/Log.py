import pandas as pd
from datetime import datetime
from typing import Optional
import json
import os
from firebase_admin import credentials, db, initialize_app


class Batch:
    _batch_id_counter = 1  # Static counter for generating unique batch IDs
    def __init__(
        self,
        mushroom_type: Optional[str] = None,
        iteration_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        room_number: Optional[int] = None,
        substrate: Optional[float] = None
    ):
        self.batch_id = Batch._batch_id_counter
        Batch._batch_id_counter += 1
        self.mushroom_type = mushroom_type
        self.iteration_id = iteration_id
        self.start_date = start_date
        self.room_number = room_number
        self.substrate = substrate

    def __repr__(self):
        return (
            f"Batch(batch_id={self.batch_id}, mushroom_type='{self.mushroom_type}', "
            f"iteration_id={self.iteration_id}, start_date={self.start_date}, "
            f"room_number={self.room_number}, substrate={self.substrate})"
        )

class Log:
    _log_id_counter = 1  # Static counter for generating unique log IDs

    def __init__(
        self,
        batch_id: int,
        days_after_plant: Optional[int] = None,
        date: Optional[datetime] = None,
        hour: Optional[str] = None,
        air_temp: Optional[float] = None,
        substrate_temp: Optional[float] = None,
        rh_humidity: Optional[float] = None,
        co2: Optional[float] = None,
        day_hours: Optional[int] = None,
        harvest: Optional[float] = None,
        if_bagged: Optional[bool] = None
    ):
        self.log_id = Log._log_id_counter
        Log._log_id_counter += 1  # Increment the counter

        self.batch_id = batch_id
        self.days_after_plant = days_after_plant
        self.date = date
        self.hour = hour
        self.air_temp = air_temp
        self.substrate_temp = substrate_temp
        self.rh_humidity = rh_humidity
        self.co2 = co2
        self.day_hours = day_hours
        self.harvest = harvest
        self.if_bagged = if_bagged

    def __repr__(self):
        return (
            f"Log(log_id={self.log_id}, batch_id={self.batch_id}, days_after_plant={self.days_after_plant}, "
            f"date={self.date}, hour='{self.hour}', air_temp={self.air_temp}, substrate_temp={self.substrate_temp}, "
            f"rh_humidity={self.rh_humidity}, co2={self.co2}, day_hours={self.day_hours}, "
            f"harvest='{self.harvest}', if_bagged={self.if_bagged})"
        )




def create_objects_from_df(iteration_table, log_table):
    """
    Reads an Excel file with two sheets to create lists of Batch and Log objects.

    :param file_path: Path to the Excel file.
    :return: Tuple containing a list of Batch objects and a list of Log objects.
    """


    # Create lists to store Batch and Log objects
    batches = []
    logs = []

    # Map Mahzor_id to Batch ID
    mahzor_to_batch_id = {}

    # Process iteration_table to create Batch objects
    for _, row in iteration_table.iterrows():
        # Keep the date as is if it's already in datetime format
        start_date = row.get("Start_date")
        if not pd.isna(start_date) and not isinstance(start_date, datetime):
            start_date = datetime.strptime(start_date, "%d/%m/%Y")

        batch = Batch(
            mushroom_type=row.get("mushroom_type"),
            iteration_id=row.get("Iteration_ID"),
            start_date=start_date,
            room_number=row.get("Room_number"),
            substrate=row.get("Substrate")
        )
        batches.append(batch)
        mahzor_to_batch_id[row.get("MAHZOR_ID")] = batch.batch_id  # Map Mahzor_id to generated Batch ID

    # Process log_table to create Log objects
    for _, row in log_table.iterrows():
        # Match the batch_id using the Mahzor_id from the log
        mahzor_id = row.get("Mahzor_id")
        batch_id = mahzor_to_batch_id.get(mahzor_id)

        # Keep the date as is if it's already in datetime format
        log_date = row.get("Date")
        if not pd.isna(log_date) and not isinstance(log_date, datetime):
            log_date = datetime.strptime(log_date, "%d/%m/%Y")

        log = Log(
            batch_id=batch_id,
            days_after_plant=row.get("Days_after_plant"),
            date=log_date,
            hour=row.get("Hour"),
            air_temp=row.get("AIR_temp"),
            substrate_temp=row.get("Substrate_temp"),
            rh_humidity=row.get("RH_Humadity"),
            co2=row.get("CO2"),
            day_hours=row.get("day_hours"),
            harvest=row.get("Katif"),
            if_bagged=bool(row.get("if_bagged"))
        )
        logs.append(log)

    return batches, logs


def convert_to_datetime(value):
    """ Converts timestamp (milliseconds) or date string to datetime object """
    if isinstance(value, int):  # Check if it's a timestamp
        return datetime.utcfromtimestamp(value / 1000)  # Convert from ms to seconds
    elif isinstance(value, str):  # Check if it's a date string
        try:
            return datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            return None  # Handle invalid date formats
    return None  # Handle None values

def run_example():
    ref_batches = db.reference("Batches")
    batches_data = ref_batches.get()

    ref_logs = db.reference("Logs")
    logs_data = ref_logs.get()

    # Check if the data is a string and convert it
    if isinstance(batches_data, str):
        try:
            batches_data = json.loads(batches_data)  # Convert JSON string to Python object
        except json.JSONDecodeError:
            batches_data = []  # Fallback to empty list

    if isinstance(logs_data, str):
        try:
            logs_data = json.loads(logs_data)
        except json.JSONDecodeError:
            logs_data = []

    # Ensure the data is in list format
    if isinstance(batches_data, dict):
        batches_data = list(batches_data.values())

    if isinstance(logs_data, dict):
        logs_data = list(logs_data.values())

    df_batches = pd.DataFrame(batches_data)
    df_logs = pd.DataFrame(logs_data)

    df_batches["Start_date"] = df_batches["Start_date"].apply(convert_to_datetime)
    df_logs["Date"] = df_logs["Date"].apply(convert_to_datetime)

    # Convert DataFrames to objects
    batch_list, log_list = create_objects_from_df(df_batches, df_logs)

    return batch_list, log_list