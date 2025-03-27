# Smart Waste Management System

## Description
This project is a Flask-based backend for a smart waste management system. It collects sensor data from IoT-enabled bins, optimizes waste collection routes, and provides an API for real-time monitoring and decision-making.

## Features
- Collects real-time fill level data from IoT sensors (ESP32-based).
- Stores bin locations, fill levels, and truck details in an Oracle database.
- Uses OpenRouteService API to calculate optimized waste collection routes.
- Provides a RESTful API for integrating with a React frontend and AR interface.

## Installation
### Prerequisites
- Python 3.x
- Flask
- Oracle Database
- OpenRouteService API Key

### Steps
1. Clone the repository:
   ```sh
   git clone <repo_url>
   cd <repo_name>
   ```
2. Create a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set up environment variables for database connection and API keys.
5. Run the application:
   ```sh
   python app.py
   ```

## API Endpoints
- `GET /bins` - Fetches all dustbins with current fill levels.
- `POST /update-bin` - Updates bin status from sensor input.
- `GET /routes` - Returns optimized truck collection routes.

## Database Schema
### `DUSTBIN_INFO`
| Column      | Type    | Description |
|------------|--------|-------------|
| bin_id     | INT    | Unique bin identifier |
| location   | STRING | Bin coordinates |
| fill_level | FLOAT  | Current fill percentage |
| waste_type | STRING | Type of waste (organic, plastic, etc.) |

### `TRUCK_INFO`
| Column  | Type    | Description |
|--------|--------|-------------|
| truck_id | INT    | Unique truck identifier |
| capacity | FLOAT  | Maximum waste capacity |
| status  | STRING | Available/On Route |

## Contributing
1. Fork the repository.
2. Create a new branch (`feature-branch`).
3. Commit your changes.
4. Push to the branch.
5. Open a pull request.

## License
This project is licensed under the MIT License.

