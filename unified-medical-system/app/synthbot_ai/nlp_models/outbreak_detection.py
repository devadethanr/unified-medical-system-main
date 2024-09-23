import requests
import os
from dotenv import load_dotenv
import folium
from collections import defaultdict
from flask import redirect, url_for, render_template
import random

# Load environment variables
load_dotenv()

def roberta_QA(question):
    # Read context from file
    file_path = "unified-medical-system/app/synthbot_ai/nlp_models/outbreak_detection_covid.txt"
    try:
        with open(file_path, "r") as file:
            context = file.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None

    # Hugging Face API configuration
    api_key = "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"
    api_url = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"
    
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"inputs": {"question": question, "context": context}}

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        answer = response.json().get('answer')
        return answer
    except requests.RequestException as e:
        print(f"Error making request: {e}")
        return None

def extract_locations(context):
    locations = defaultdict(lambda: defaultdict(int))
    for line in context.split('\n'):
        if "Last known location:" in line:
            location = line.split("Last known location:")[-1].strip()
            disease = "COVID-19" if "COVID-19" in line else "Other"
            locations[location][disease] += 1
    return locations


import folium
from folium import plugins
from folium.plugins import HeatMap

def create_map(locations):
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="CartoDB positron")
    
    folium.TileLayer('CartoDB positron', name="Light Map", control=False).add_to(m)
    
    # Add title to the map
    title_html = '''
             <h3 align="center" style="font-size:20px"><b>Disease Outbreak Map in India</b></h3>
             '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add back button to the map
    back_button_html = '''
    <a href="/admin" class="btn btn-primary absolute top-4 left-4 z-10">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Back to Admin
    </a>
    '''
    m.get_root().html.add_child(folium.Element(back_button_html))
    
    covid_data = []
    other_diseases = []
    
    for location, disease_counts in locations.items():
        coords = get_coordinates(location)
        if coords != [0, 0]:  # Only add valid coordinates
            covid_count = disease_counts.get('COVID-19', 0)
            other_count = sum(count for disease, count in disease_counts.items() if disease != 'COVID-19')
            
            if covid_count > 0:
                covid_data.extend([coords + [covid_count]] * covid_count)
                
                # Add small data points for each COVID-19 case
                for _ in range(covid_count):
                    # Generate random coordinates within 5 mile radius
                    lat_offset = random.uniform(-0.07, 0.07)  # Approximately 5 miles in latitude
                    lon_offset = random.uniform(-0.07, 0.07)  # Approximately 5 miles in longitude
                    patient_coords = [coords[0] + lat_offset, coords[1] + lon_offset]
                    
                    folium.CircleMarker(
                        location=patient_coords,
                        radius=3,
                        color='red',
                        fill=True,
                        fillColor='red',
                        fillOpacity=0.7,
                        popup='COVID-19 case'
                    ).add_to(m)
            
            if other_count > 0:
                other_diseases.append((coords, other_count))

    # Add COVID-19 heatmap layer (blood red)
    heat_map = HeatMap(covid_data, 
            radius=20,
            blur=15, 
            max_zoom=1,
            gradient={0.4: 'pink', 0.65: 'red', 1: 'darkred'}
    )
    heat_map.add_to(m)

    # Add dashed circles for other diseases
    for coords, count in other_diseases:
        folium.Circle(
            location=coords,
            radius=5000,  # 5 km radius
            color='green',
            fill=False,
            dash_array='5, 5',
            weight=2,
            popup=f'Other diseases: {count} cases'
        ).add_to(m)
    
    # Add a legend
    legend_html = '''
         <div style="position: fixed; 
                     bottom: 50px; left: 50px; width: 250px; height: 140px; 
                     border:2px solid grey; z-index:9999; font-size:14px;
                     background-color: white; padding: 10px;
                     ">&nbsp; <b>Legend</b> <br>
                      &nbsp; Outbreak Cases: <i class="fa fa-map-marker fa-2x" style="color:red"></i> Heat Map<br>
                      &nbsp; Individual Outbreak Cases: <i class="fa fa-circle fa-1x" style="color:red"></i> Red Dots<br>
                      &nbsp; Other Diseases: <i class="fa fa-circle-o fa-2x" style="color:green"></i> Green Circles<br>
                      &nbsp; (Circle radius: 5 km)
         </div>
         '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    m.save("unified-medical-system/app/templates/admin/outbreak_map.html")


import requests

def get_coordinates(location):
    api_key = "AIzaSyCwrIvSVrnX091MAxkWIDLQ-K3gc1Z4VLY"  # Use the API key from the register.html file
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": location,
        "key": api_key
    }
    
    response = requests.get(base_url, params=params)
    data = response.json()
    
    if data["status"] == "OK":
        result = data["results"][0]
        lat = result["geometry"]["location"]["lat"]
        lng = result["geometry"]["location"]["lng"]
        return [lat, lng]
    else:
        print(f"Error: Unable to geocode {location}")
        return [0, 0]  # Default to [0, 0] if geocoding fails

def analyze_outbreak():
    file_path = "unified-medical-system/app/synthbot_ai/nlp_models/outbreak_detection_covid.txt"
    try:
        with open(file_path, "r") as file:
            context = file.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return

    locations = extract_locations(context)
    create_map(locations)
    
    question = "Is there covid?"
    answer = roberta_QA(question)
    
    if answer:
        print(f"Question: {question}")
        print(f"Answer: {answer}")
        
        if "positive" in answer.lower() or "yes" in answer.lower():
            simplified_answer = "Yes"
            print(f"Simplified Answer: {simplified_answer}")
            print("Warning: Potential outbreak detected. Further investigation required.")
            print("A map of outbreak locations has been generated as 'outbreak_map.html'")
        else:
            simplified_answer = "No"
            print(f"Simplified Answer: {simplified_answer}")
            print("No immediate outbreak detected. Continue monitoring.")
    else:
        print("Unable to analyze outbreak situation.")
    
    return render_template('admin/outbreak_map.html')
