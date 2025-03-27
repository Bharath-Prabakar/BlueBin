from flask import Flask, render_template, request, redirect, url_for, session, flash,jsonify
import cx_Oracle
from flask_cors import CORS
from openrouteservice import Client
from math import radians, sin, cos, sqrt, atan2
from requests.exceptions import RequestException
from math import radians, sin, cos, sqrt, atan2


app = Flask(__name__) 
CORS(app)
secret_key = 'your_random_string_here_1234567890!@#$%^&*' # Required for session management
app.secret_key = secret_key

# Oracle database connection string
orcl_connect_str = 'system/orcl7bharath@localhost:1521/XE'
connection = cx_Oracle.connect(orcl_connect_str)
cursor = connection.cursor()

# Route for login page
@app.route('/', methods=['GET', 'POST'])
def login():
    
    return render_template('login.html')

#-----------------------------------------------------------------------------------------
#       STATUS PAGE
#------------------------------------------------------------------------------------------




@app.route('/status', methods=['GET', 'POST'])
def status():
    if request.method == 'POST':
        try:
            connection = cx_Oracle.connect(orcl_connect_str)
            cursor = connection.cursor()

            # Fetch location name and fill levels from DUSTBIN_INFO table
            query = """
            SELECT LOCATION_NAME, LAST_FILL_LEVEL
            FROM DUSTBIN_INFO
            ORDER BY LOCATION_NAME
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            # Debug: Print fetched data
            print("Fetched Data:", rows)

            # Convert rows to a list of dictionaries
            fill_levels = [{'LOCATION_NAME': row[0], 'LAST_FILL_LEVEL': row[1]} for row in rows]

            cursor.close()
            connection.close()

            return render_template('status.html', fill_levels=fill_levels)
        except Exception as e:
            # Debug: Print error
            print("Error:", str(e))
            return render_template('status.html', error=str(e))
    return render_template('status.html')

# Define the is_valid_coordinate function
def is_valid_coordinate(lat, lon):
    """Check if latitude and longitude are within valid ranges for Chennai."""
    return 12.9 <= lat <= 13.2 and 80.1 <= lon <= 80.3

from math import radians, sin, cos, sqrt, atan2

# Function to calculate the distance between two coordinates using the Haversine formula
def calculate_distance(loc1, loc2):
    
    R = 6371000.0  # Radius of the Earth in meters

    # Convert latitude and longitude from degrees to radians
    lat1 = radians(loc1[1])
    lon1 = radians(loc1[0])
    lat2 = radians(loc2[1])
    lon2 = radians(loc2[0])

    # Difference in coordinates
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Calculate the distance
    distance = R * c
    return distance

from polyline import decode as polyline_decode  # Ensure you have the polyline library installed

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        start_lat = float(request.form.get('latitude'))
        start_lon = float(request.form.get('longitude'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid latitude or longitude values.'})

    # Validate coordinates
    if not is_valid_coordinate(start_lat, start_lon):
        return jsonify({'error': 'Invalid coordinates for Chennai.'})

    # Fetch bins with fill level > 75%
    try:
        connection = cx_Oracle.connect(orcl_connect_str)
        cursor = connection.cursor()
        cursor.execute("SELECT LOCATION_NAME, LATITUDE, LONGITUDE, LAST_FILL_LEVEL FROM DUSTBIN_INFO WHERE LAST_FILL_LEVEL > 75")
        bins = cursor.fetchall()
        print("Fetched bins from database:", bins)  # Debug: Print fetched data
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Failed to fetch data from the database.'})
    finally:
        cursor.close()
        connection.close()

    # Convert bins to a list of dictionaries
    bins_data = [
        {"name": row[0], "location": [float(row[2]), float(row[1])], "fill_level": row[3]}
        for row in bins
    ]

    if not bins_data:
        return jsonify({'error': 'No valid bins with fill level above 75% found.'})

    # Sort bins by distance from the starting location
    start = [start_lon, start_lat]  # ORS expects [longitude, latitude]
    bins_data.sort(key=lambda x: calculate_distance(start, x['location']))

    # Define coordinates for the route
    coordinates = [start] + [bin['location'] for bin in bins_data]
    print("Coordinates sent to ORS API:", coordinates)  # Debug: Print coordinates

    # Use OpenRouteService API to calculate the route
    ors_api_key = "5b3ce3597851110001cf6248cea24e90714e4a8c9e6b653486f0e396"  # Replace with your ORS API key
    client = Client(key=ors_api_key)

    try:
        directions = client.directions(
            coordinates=coordinates,
            profile='driving-car',
            format='geojson'
        )
        print("ORS API Response:", directions)  # Debug: Print ORS API response
    except Exception as e:
        print(f"Error calculating route: {e}")
        return jsonify({'error': 'Failed to calculate route. Please check the coordinates.'})

    # Fix: Check if 'features' exist instead of 'routes'
    if 'features' not in directions or not directions['features']:
        print("No routes found in ORS API response:", directions)
        return jsonify({'error': 'No route found for the given coordinates.'})

    # Extract the first route
    route = directions['features'][0]

    # Debug: Check if 'geometry' and 'properties' keys exist
    if 'geometry' not in route or 'properties' not in route:
        print("Invalid route structure in ORS API response:", directions)
        return jsonify({'error': 'Invalid route structure in ORS API response.'})

    # Extract the geometry and summary
    route_geometry = route['geometry']['coordinates']  # No need to decode polyline
    total_distance = route['properties']['segments'][0]['distance']  # Distance in meters
    total_duration = route['properties']['segments'][0]['duration']  # Duration in seconds

    # Prepare the order of locations
    starting_location_name = request.form.get('locationName') or f"Start: ({start_lat}, {start_lon})"
    order_of_locations = [starting_location_name] + [bin['name'] for bin in bins_data]

    # Prepare the response data
    response_data = {
        'route_geometry': route_geometry,  # Route coordinates for Leaflet
        'order_of_locations': order_of_locations,
        'total_distance': f"{total_distance:.2f} meters",
        'total_duration': f"{total_duration / 60:.2f} minutes",
        'dustbin_locations': bins_data  # Dustbin locations for Leaflet markers
    }

    return jsonify(response_data)



#-----------------------------------------------------------------------------------------
#       LOCATION PAGE
#------------------------------------------------------------------------------------------
@app.route('/location')
def location():
    try:
        # Fetch dustbin locations from the database
        cursor.execute("SELECT BIN_ID, LOCATION_NAME, LATITUDE, LONGITUDE FROM DUSTBIN_INFO")
        dustbin_locations = cursor.fetchall()

        # Convert the data into a list of dictionaries
        locations = [
            {"BIN_ID": row[0], "name": row[1], "latitude": row[2], "longitude": row[3]}
            for row in dustbin_locations
        ]

        return render_template('location.html', locations=locations)
    except Exception as e:
        print(f"Database error: {e}")
        return render_template('location.html', error="Failed to fetch dustbin locations.")

#-----------------------------------------------------------------------------------------
#       SCHEMA PAGE
#------------------------------------------------------------------------------------------


@app.route('/add-dustbin', methods=['POST'])
def add_dustbin():
    try:
        data = request.get_json()
        bin_id = data['binId']
        location_name = data['locationName']
        latitude = data['latitude']
        longitude = data['longitude']
        waste_type = data['wasteType']

        # Insert into DUSTBIN_INFO table
        cursor.execute("""
            INSERT INTO DUSTBIN_INFO (BIN_ID, LOCATION_NAME, LATITUDE, LONGITUDE, WASTE_TYPE)
            VALUES (:1, :2, :3, :4, :5)
        """, (bin_id, location_name, latitude, longitude, waste_type))
        connection.commit()

        return jsonify({"success": True, "message": "Dustbin added successfully."})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/delete-dustbin', methods=['POST'])
def delete_dustbin():
    try:
        data = request.get_json()
        bin_id = data['binId']
        location_name = data['locationName']

        # Delete from DUSTBIN_INFO table
        cursor.execute("""
            DELETE FROM DUSTBIN_INFO
            WHERE BIN_ID = :1 AND LOCATION_NAME = :2
        """, (bin_id, location_name))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "No such dustbin exists."})

        return jsonify({"success": True, "message": "Dustbin deleted successfully."})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "message": str(e)})




# Route for schema
@app.route('/schema')
def schema():
    try:
        # Fetch data from DUSTBIN_INFO
        cursor.execute("SELECT BIN_ID, LOCATION_NAME, LATITUDE, LONGITUDE, LAST_FILL_LEVEL, WASTE_TYPE, LAST_UPDATED FROM DUSTBIN_INFO")
        dustbin_data = cursor.fetchall()

        # Fetch data from COLLECTION_ROUTE
        cursor.execute("SELECT ROUTE_ID, TRUCK_ID, SELECTED_BINS, TOTAL_DISTANCE, ROUTE_PATH, ROUTE_DATE FROM COLLECTION_ROUTE")
        route_data = cursor.fetchall()

        # Fetch data from SENSOR_LOGS
        cursor.execute("SELECT LOG_ID, BIN_ID, FILL_LEVEL, TIMESTAMP FROM SENSOR_LOGS")
        sensor_data = cursor.fetchall()

        # Convert data into lists of dictionaries for easier rendering in the template
        dustbin_info = [
            {"BIN_ID": row[0], "LOCATION_NAME": row[1], "LATITUDE": row[2], "LONGITUDE": row[3],
             "LAST_FILL_LEVEL": row[4], "WASTE_TYPE": row[5], "LAST_UPDATED": row[6]}
            for row in dustbin_data
        ]

        collection_route = [
            {"ROUTE_ID": row[0], "TRUCK_ID": row[1], "SELECTED_BINS": row[2],
             "TOTAL_DISTANCE": row[3], "ROUTE_PATH": row[4], "ROUTE_DATE": row[5]}
            for row in route_data
        ]

        sensor_logs = [
            {"LOG_ID": row[0], "BIN_ID": row[1], "FILL_LEVEL": row[2], "TIMESTAMP": row[3]}
            for row in sensor_data
        ]

        return render_template('schema.html', dustbin_info=dustbin_info, collection_route=collection_route, sensor_logs=sensor_logs)
    except Exception as e:
        print(f"Database error: {e}")
        return render_template('schema.html', error="Failed to fetch data from the database.")


if __name__ == '__main__':
    app.run(debug=True)
    

