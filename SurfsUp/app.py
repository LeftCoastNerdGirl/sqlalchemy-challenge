# Import the dependencies.
from flask import Flask, jsonify
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt 
import os

#################################################
# Database Setup
#################################################
# Get the absolute path to the current directory to fix access issue
basedir = os.path.abspath(os.path.dirname(__file__))

# Use the absolute path to construct the database file path
database_path = "sqlite:///" + os.path.join(basedir, "Resources", "hawaii.sqlite")

# Create engine
engine = create_engine(database_path)

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(bind=engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# List all the available routes.
@app.route("/")
def welcome():
    return(
        f"Available Routes: <br/>"
        f"/api/v1.0/precipitation <br/>"
        f"/api/v1.0/stations <br/>"
        f"/api/v1.0/tobs <br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )


# Convert the query results from your precipitation analysis to a dictionary using date as the key and prcp as the value.
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Query precipitation measurement from database
    prcp_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= '2016, 8, 23').order_by(Measurement.date).all()
    
    # Create dictionary to store response
    prcp = []
    for date, prcp_value in prcp_data:
        prcp_dict = {}
        prcp_dict['date'] = date
        prcp_dict['prcp'] = prcp_value
        prcp.append(prcp_dict)

    session.close()

    # Jsonify the dictionary
    return jsonify(prcp)


# Return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def stations():
    # Query database to get station data
    station_results = session.query(Station.station, Station.name).all()

    # Create dictionary to store the results
    stations_list = []
    for station in station_results:
        station_dict = {
            "station": station.station,
            "name": station.name
        }
        stations_list.append(station_dict)

    session.close()

    # Jsonify the dictionary
    return jsonify(stations_list)


# Query the dates and temperature observations of the most-active station for the previous year of data.
@app.route("/api/v1.0/tobs")
def most_active():
    # Find most recent date and calculate the year prior date
    find_latest_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    latest_date = dt.datetime.strptime(find_latest_date.date, '%Y-%m-%d').date()
    year_ago = latest_date - dt.timedelta(days = 365)

    # Find the most active station
    active_station_list = [Measurement.station, func.count(Measurement.station)]
    active_station = session.query(*active_station_list).group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first().station

    # Query database to find the tobs for the most active station for the prior year
    active_station_temp = session.query(Measurement.date, Measurement.tobs).filter(Measurement.date > year_ago).\
        filter(Measurement.station == active_station).all()

    session.close()

    # Create dictonary to store the results
    temp_list = []

    for date, temp in active_station_temp:
        temp_dict = {}
        temp_dict['Date'] = date
        temp_dict['Temperature'] = temp
        temp_list.append(temp_dict)

    # Jsonify the dictionary
    return jsonify(temp_list)


# For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date.
@app.route("/api/v1.0/<start>")
def temp_date_start(start):
    # Convert date to date objects
    start_date = dt.datetime.strptime(start, '%Y-%m-%d').date()

    # Query to find TMIN, TAVG, TMAX   
    temp_stats = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).all()
    
    # Round TAVG
    tavg_rounded = round(temp_stats[0][1],1)
    
    # Create dictionary to store the results
    temps_dict = {
        'TMIN': temp_stats[0][0],
        'TAVG': tavg_rounded,
        'TMAX': temp_stats[0][2]
    }

    session.close()

    # Jsonify the dictionary
    return jsonify(temps_dict)


# For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive.
@app.route("/api/v1.0/<start>/<end>")
def temp_date_range(start, end):
    # Convert dates to date objects
    start_date = dt.datetime.strptime(start, '%Y-%m-%d').date()
    end_date = dt.datetime.strptime(end, '%Y-%m-%d').date()

    # Query to find TMIN, TAVG, TMAX 
    temp_range_stats = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    
     # Round TAVG
    tavg_rounded = round(temp_range_stats[0][1],1)

    # Create dictionary to store the results
    range_dict = {
        'TMIN': temp_range_stats[0][0],
        'TAVG': tavg_rounded,
        'TMAX': temp_range_stats[0][2]
    }

    session.close()

    # Jsonify the dictionary
    return jsonify(range_dict)

if __name__ == '__main__':
    app.run(debug=True, port=5005)
