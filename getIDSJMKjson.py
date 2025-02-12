import json
import requests
import re
from datetime import datetime, timedelta

# URL of bus stop name
# after busStopName fill name of bus stop. Find it for example on https://www.idsjmk.cz/connection-finder/search
url = "https://www.idsjmk.cz/api/departures/busstop-by-name?busStopName=Doubravice,%20n%C3%A1m."
bus_stop_id = 1967    # determines direction if bus stop has more, see from json, which direction interests you
keyword = "Boskovice"   # determines end stop, some connections may not go there

key="KEY"  # access key to zivy obraz



response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()  # Parse JSON response
    print(json.dumps(data, indent=4))  # Pretty print JSON
else:
    print(f"Failed to fetch data. Status code: {response.status_code}")



# Get current time
current_time = datetime.now()

output=""
icnt=0
result = []
for stop in data["stops"]:
    for sign in stop["signs"]:
        if sign["busStopSign"]["id"] == bus_stop_id:
            for departure in sign["departures"]:
                if keyword in departure["destinationStop"]:
                    time_str = departure["time"]
                    
                    # Check if time contains "NUMBERmin". In this case add current time, because zivyobraz is refreshing in 
                    # 5 min intervals and time of departure is better
                    match = re.match(r"(.*)(\d+)min", time_str)
                    if match:
                        added_minutes = int(match.group(2))
                        adjusted_time = current_time + timedelta(minutes=added_minutes)
                        time_str = match.group(1)+adjusted_time.strftime("%H:%M")
 

                    if not time_str[0].isdigit():
                        # there is "for disabled" icon in front of time, remove it because zivyobraz
                        time_str=time_str[1:]
                    result.append({"link": departure["link"], "time": time_str})
                    icnt=icnt+1
                    if icnt==1:
                        output=departure["link"]+" "+time_str
                    else:
                        output=output+"\n"+departure["link"]+" "+time_str
# Print the result
print(result)
print(output)

if (icnt>0):
    url="https://in.zivyobraz.eu/?import_key="+key+"&autobusy="+output
else:
    # not detected any connection (usual on weekends)
    url="https://in.zivyobraz.eu/?import_key="+key+"&autobusy=Nic nejede"

if (key == "KEY"):
    print("Set zivyobraz key to send values")
    print(output)
else:
    response = requests.get(url)
