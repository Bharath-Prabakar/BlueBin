-- 1. Table for storing bin locations, fill levels, and waste type
CREATE TABLE DUSTBIN_INFO (
    BIN_ID            VARCHAR2(10) PRIMARY KEY,   -- Unique ID for each bin
    LOCATION_NAME     VARCHAR2(100),             -- Readable location name
    LATITUDE         NUMBER(10, 6),              -- Geolocation (latitude)
    LONGITUDE        NUMBER(10, 6),              -- Geolocation (longitude)
    LAST_FILL_LEVEL  NUMBER(5, 2),              -- Fill level in percentage (0-100%)
    WASTE_TYPE       VARCHAR2(20) CHECK (WASTE_TYPE IN ('BIODEGRADABLE', 'NON-BIODEGRADABLE')),  -- Type of waste
    LAST_UPDATED     TIMESTAMP DEFAULT SYSDATE  -- Timestamp of last update
);

-- 2. Table for storing the single truck's details
CREATE TABLE TRUCK_INFO (
    TRUCK_ID          VARCHAR2(10) PRIMARY KEY,  -- Unique truck ID
    DRIVER_NAME       VARCHAR2(100),            -- Driver assigned to the truck
    CURRENT_LAT       NUMBER(10, 6),            -- Current truck location (latitude)
    CURRENT_LON       NUMBER(10, 6),            -- Current truck location (longitude)
    STATUS           VARCHAR2(20) DEFAULT 'AVAILABLE'  -- Truck status (AVAILABLE, IN_TRANSIT)
);

-- 3. Table for storing the optimized route for the single truck
CREATE TABLE COLLECTION_ROUTE (
    ROUTE_ID         VARCHAR2(10) PRIMARY KEY,   -- Unique route ID (e.g., "RID_001")
    TRUCK_ID        VARCHAR2(10) REFERENCES TRUCK_INFO(TRUCK_ID), -- Single truck assigned
    SELECTED_BINS    VARCHAR2(500),             -- Bins to collect from (comma-separated BIN_IDs)
    TOTAL_DISTANCE   NUMBER(10, 2),             -- Total route distance (in meters)
    ROUTE_PATH       CLOB,                      -- JSON or Polyline string from ORS
    ROUTE_DATE       DATE DEFAULT SYSDATE       -- Date when route was calculated
);

-- 4. Table for storing sensor logs (optional)
CREATE TABLE SENSOR_LOGS (
    LOG_ID           NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    BIN_ID          VARCHAR2(10) REFERENCES DUSTBIN_INFO(BIN_ID), -- Foreign key to DUSTBIN_INFO
    FILL_LEVEL      NUMBER(5, 2),              -- Fill level at that time
    TIMESTAMP       TIMESTAMP DEFAULT SYSDATE  -- Time of data logging
);
