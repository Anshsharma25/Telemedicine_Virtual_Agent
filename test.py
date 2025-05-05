import requests
import googlemaps # type: ignore

# Replace with your Google API Key
GOOGLE_API_KEY = "AIzaSyCVQNuIoyvSAMJL24Pu6ZI7r3zK2DKAZNo"

# Initialize the Google Maps clientS
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

# Function to get latitude and longitude from an address
def get_coordinates(address):
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
        print(f"Coordinates for {address}: Latitude = {lat}, Longitude = {lng}")
        return lat, lng
    else:
        print("Address not found.")
        return None, None

# Function to find nearby hospitals
def find_nearby_hospitals(lat, lng, radius=5000):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=hospital&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data.get("status") == "OK":
        hospitals = data.get("results", [])
        for i, hospital in enumerate(hospitals[:5]):  # Get top 5 hospitals
            name = hospital.get("name")
            address = hospital.get("vicinity")
            rating = hospital.get("rating", "N/A")
            print(f"{i + 1}. {name} | Rating: {rating} | Address: {address}")
    else:
        print("No hospitals found nearby.")

# Example: Provide an address and get nearby hospitals
address = "Sector 132, Noida, Uttar Pradesh, India"
lat, lng = get_coordinates(address)

if lat and lng:
    find_nearby_hospitals(lat, lng)
