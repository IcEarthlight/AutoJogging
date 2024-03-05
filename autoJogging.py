import time
import json
import math
import ctypes
import random
import configparser

import requests
from http import client

client.HTTPConnection._http_vsn = 11
client.HTTPConnection._http_vsn_str = "HTTP/1.1"

# prevent the computer from sleeping or hibernating when running
SetThreadExecutionState = ctypes.windll.kernel32.SetThreadExecutionState

ES_CONTINUOUS = 0x80000000
ES_DISPLAY_REQUIRED = 0x00000002
SetThreadExecutionState(ES_CONTINUOUS | ES_DISPLAY_REQUIRED)

class Location():
    """ This class represents an specific location by given latitude and longtitude.

        # Attributes
        - lat: A float represents the latitude of the location.
        - lng: A float represents the longtitude of the location.

        # Methods
        - randomShift(offset): Randomly shift the location with the given offset.
    """
    def __init__(self, lat, lng):
        self.lat = float(lat) if isinstance(lat, str) else lat
        self.lng = float(lng) if isinstance(lng, str) else lng
    
    def randomShift(self, offset:float=1e-4):
        """ This method randomly shift the location with the given offset. Probability evenly
            distributed in a circle, whose radius is decided by the parameter `offset`. Return
            a shifted Location object.
        """
        a = random.random() * 2*math.pi
        r = max(random.random(), random.random()) * offset
        return Location(self.lat + r*math.cos(a), self.lng + r*math.sin(a) * 8/11)
    
    @staticmethod
    def distance(loc1, loc2, axis=None) -> float:
        """ This method calculate the actural distance (meter) between two locations. If the
            argment "axis" == "lat", return the latitudinal distance (meter), similarly to the
            situation when "axis" == "lng".
        """
        if axis == "lat":
            return abs((loc1.lat - loc2.lat) * 87622.79444444444)
        if axis == "lng":
            return abs((loc1.lng - loc2.lng) * 111194.925)
        x = (loc1.lat - loc2.lat) * 87622.79444444444
        y = (loc1.lng - loc2.lng) * 111194.925
        return math.sqrt(x**2 + y**2)
    
    def __add__(self, other):
        return Location(self.lat + other.lat, self.lng + other.lng)


domain = "https://run.e**st.edu.cn"
initLocation = Location(30.833179, 121.505558).randomShift(1e-3)
headers = {
    "Host": "run.e**st.edu.cn",
    "Content-Type": "application/json",
    "Lan": "CH",
    "Accept": "*/*",
    "User-Agent": "chunTianChuangFu/1.1.9 (iPhone; iOS 16.3.1; Scale/3.00)",
    "Accpet-Language": "en-US;q=1, zh-Hans-US;q=0.9, zh-Hant-TW;q=0.8, ja-US;q=0.7",
    "Accpet-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

def postHeader(d: dict) -> dict:
    """ I noticed that when requests are posted to the host, compared to the 'get' situation,
        there is one more item "Content-Length" in the header, which represents the byte number
        of the posted json. This function add the item "Content-Length" to the original header,
        and the value of it is calculated by the given dict.

        # Args
        - d: The given dict to calculate the content length in the header.

        # Return
        - The processed dict with the added "Content-Length" item.
    """
    h = headers
    h["Content-Length"] = str(dumps(d)[1])
    return h

def dumps(d: dict | list | tuple) -> tuple[str, int]:
    """ In the strings returned by the build-in function `json.dumps`, there are always spaces
        after the commas and colons, but the ones posted by `requests.post` don't have any
        unecessary spaces. This function convert a dict/list/tuple into a json-style string
        without any unessencial spaces, so as to calculate the byte number correctly.

        # Args
        - d: A dict/list/tuple that is going to converted to the string in json style.

        # Returns
        - A json string represents the original data of `d`.
        - An integer represents the byte number of the string.
    """
    if isinstance(d, list):
        s = '['
        for value in d:
            if isinstance(value, str):
                s += "\"%s\"" % value
            elif isinstance(value, (int, float)):
                s += str(value)
            elif isinstance(value, dict | list | tuple):
                s += dumps(value)[0]
            else:
                raise TypeError("%s is not supported." % str(type(value)))
            s += ','
        if s[-1] == ',':
            s = s[:-1]
        s += ']'
        return s, len(s.encode("utf-8"))
    
    s = '{'
    for key, value in d.items():
        if isinstance(key, str):
            s += "\"%s\"" % key
        elif isinstance(key, (int, float)):
            s += str(key)
        else:
            raise TypeError("%s is not supported." % str(type(key)))
        s += ':'
        
        if isinstance(value, str):
            s += "\"%s\"" % value
        elif isinstance(value, (int, float)):
            s += str(value)
        elif isinstance(value, dict | list | tuple):
            s += dumps(value)[0]
        else:
            raise TypeError("%s is not supported." % str(type(value)))
        s += ','
    if s[-1] == ',':
        s = s[:-1]
    s += '}'
    return s, len(s.encode("utf-8"))

def autoRequest(method: str, url: str, *args, **kwargs) -> requests.Response:
    """ This function can automatically execute the get/post request 3 times if the response
        has any exceptions. If the exception remains constant after 3 times of trying, the
        function would raise an exception.

        # Args
        - method: A string specifying the get or post command. This string can only be "get" or
          "post".
        - *args, **kwargs: These parameters will be the argments of functions `requests.get()`
          or `requests.post()`.
        
        # Return
        - The response of the request if the response has no exceptions.

        # Raises
        - ConnectionError: The exception is raised when all three attempts to request are failed.
    """
    print("Request: %s %s" % (method, url))
    method = {"get": requests.get, "post": requests.post}[method]

    i = 0
    while i < 3:
        try:
            res = method(url, *args, **kwargs)
            if res.status_code == 200:
                print("Request successfully with response:", res)
                return res
            print("Request failed with response:", res)
        
        except Exception as e:
            print("Request failed with exception:", type(e), e)
        
        i += 1
        time.sleep(1.5 + 2*i)
    
    try:
        print(res.content)
    except:
        pass
    raise ConnectionError("Connection failed after tried 3 times.")

def formatTimestamp(ts: float) -> str:
    """ This function formatize the given timestamp according to the format of time posted to
        the server.
    """
    ts = time.localtime(ts)
    return "%d-%d-%d %d:%d:%d" % (ts.tm_year, ts.tm_mon, ts.tm_mday,
                                  ts.tm_hour, ts.tm_min, ts.tm_sec)

def wait(t, clear: bool = False):
    """ Wait for t seconds with visual progress bar on the console. """
    st = time.time() # start time
    st_ = time.localtime(st)
    et_ = time.localtime(st + t)
    timeSpan = "%d:%d -> %d:%d" % (st_.tm_hour, st_.tm_min, et_.tm_hour, et_.tm_min)
    progressBarLen = 64

    while time.time() < st + t:
        progress = (time.time() - st) / t
        progressInt = int(progress * progressBarLen)

        bar = " " * progressBarLen
        pct = str(int(progress*100)) + "%"
        bar = bar[:int((len(bar) - len(pct))/2)] + pct + bar[int((len(bar) + len(pct))/2):]
        bar = "\033[1;30;47m" + bar[:progressInt] + "\033[0m" + bar[progressInt:]

        s = "%s |%s| %d / %d" % (timeSpan, bar, int(time.time() - st), int(t))
        print("\r" + s, end="")
        time.sleep(0.1)

    bar = "\033[1;30;47m" + int(progressBarLen/2 - 2)*" " + "100%" \
        + int(progressBarLen/2 + 2)*" " + "\033[0m"
    s = "%s |%s| %d / %d" % (timeSpan, bar, int(time.time() - st), int(t))
    print("\r" + s, end = "\r" if clear else "\n")

def generateRoute(loc1: Location, loc2: Location) -> list:
    """ This function generate a route between two locations, and the step between two points
        is simillar to the route recorded in the app.
    """
    route = [loc1]
    randStep = lambda: 1e-4 * random.random() + 5e-5
    tolerance = 25
    direction = "NULL" # lat+ lat- lng+ lng-
    while not (Location.distance(route[-1], loc2, "lat") < tolerance
           and Location.distance(route[-1], loc2, "lng") < tolerance):
        
        if direction[-1] != "_":
            if Location.distance(route[-1], loc2, "lat") < tolerance:
                direction = "lng+_" if route[-1].lng < loc2.lng else "lng-_"
            elif Location.distance(route[-1], loc2, "lng") < tolerance:
                direction = "lat+_" if route[-1].lat < loc2.lat else "lat-_"

            elif route[-1].lat < loc2.lat and route[-1].lng < loc2.lng:
                if direction in ("lat+", "lng+"):
                    direction = direction if random.random() < 0.75 else \
                        {"lat+": "lng+", "lng+": "lat+"}[direction]
                else:
                    direction = "lat+" if random.random() < 0.5 else "lng+"

            elif route[-1].lat < loc2.lat and route[-1].lng >= loc2.lng:
                if direction in ("lat+", "lng-"):
                    direction = direction if random.random() < 0.75 else \
                        {"lat+": "lng-", "lng-": "lat+"}[direction]
                else:
                    direction = "lat+" if random.random() < 0.5 else "lng-"

            elif route[-1].lat >= loc2.lat and route[-1].lng < loc2.lng:
                if direction in ("lat-", "lng+"):
                    direction = direction if random.random() < 0.75 else \
                        {"lat-": "lng+", "lng+": "lat-"}[direction]
                else:
                    direction = "lat-" if random.random() < 0.5 else "lng+"

            elif route[-1].lat >= loc2.lat and route[-1].lng >= loc2.lng:
                if direction in ("lat-", "lng-"):
                    direction = direction if random.random() < 0.75 else \
                        {"lat-": "lng-", "lng-": "lat-"}[direction]
                else:
                    direction = "lat-" if random.random() < 0.5 else "lng-"

        if direction[:4] == "lat+":
            route.append(route[-1] + Location(randStep(), 0))
        elif direction[:4] == "lat-":
            route.append(route[-1] + Location(-randStep(), 0))
        elif direction[:4] == "lng+":
            route.append(route[-1] + Location(0, randStep() * 1.27))
        elif direction[:4] == "lng-":
            route.append(route[-1] + Location(0, -randStep() * 1.27))
        
        if len(route) > 1:
            route[-2] = route[-2].randomShift()

    route.append(loc2.randomShift())
    return [r.randomShift() for r in route]

def formatizeRoute(r: list[Location]) -> list[dict]:
    """ This function formatize the route list to the dict (json) to post. """
    l = []
    for loc in r:
        l.append({
            "lat": loc.lat,
            "lng": loc.lng,
            "name": "East China University of Science and Technology Fengxian Campus"
        })
    return l

# get student id
conf = configparser.ConfigParser()
conf.read("Config.ini")
if conf["UserInfo"]["studentID"].isdigit():
    student_id = int(conf["UserInfo"]["studentID"])
else:
    userLoginDict = {
        "iphone": conf["UserInfo"]["phoneNumber"],
        "password": conf["UserInfo"]["password"]
    }
    userLogin_res = autoRequest("post", domain + "/api/userLogin/", json=userLoginDict,
                                headers=postHeader(userLoginDict))
    userLoginData = userLogin_res.json()["data"]

    if "id" in userLoginData:
        student_id = int(userLogin_res.json()["data"]["id"])
    else:
        raise Exception("LoginError: " + str(userLogin_res.json()))
    del userLoginDict, userLogin_res, userLoginData

print("Student ID:", student_id)

del conf

# ======== prepare ========
# This section contains the requests posted when entering the "running assessment" interface on
# the app.
print("\n======== prepare ========\n")

userInfo_res = autoRequest("get", domain + "/api/getUserInfo/?id=%d" % student_id,
                           headers=headers)
userInfo = userInfo_res.json()

randrunInfo_res = autoRequest("get",
    domain + "/tapi/activity/randrunInfo?lat=%f&lng=%f&student_id=%d" % (initLocation.lat,
                                                                         initLocation.lng,
                                                                         student_id),
    headers=headers)
randrunInfo = randrunInfo_res.json()

print("Pass points: %s, %s, %s" % (
    randrunInfo["data"][0]["point_name"],
    randrunInfo["data"][1]["point_name"],
    randrunInfo["data"][2]["point_name"]
))

del userInfo_res, randrunInfo_res

# ======== begin ========
# This section contains the requests posted when pressing the "start running" button on the app.
print("\n======== begin ========\n")

createLineDict = {
    "student_id": str(student_id),
    "pass_point": randrunInfo["data"]
}
createLine_res = autoRequest("post", domain + "/api/createLine/", json=createLineDict,
                             headers=postHeader(createLineDict))

record_id = createLine_res.json()["data"]["record_id"]
print("Record ID: %d" % record_id)

# autoRequest("get", domain + "/api/getUserInfo/?id=%d" % student_id, headers=headers)

del createLineDict, createLine_res

# ======== running ========
# This section calculates the route between start point and each given path points, and then
# wait until it is the time to upload the running route.
print("\n======== running ========\n")

startTime = time.time()
print("Start time: " + formatTimestamp(startTime))

route = generateRoute(
    Location(randrunInfo["lat"], randrunInfo["lng"]),
    Location(randrunInfo["data"][0]["lat"], randrunInfo["data"][0]["lng"]))
route.extend(generateRoute(
    Location(randrunInfo["data"][0]["lat"], randrunInfo["data"][0]["lng"]),
    Location(randrunInfo["data"][1]["lat"], randrunInfo["data"][1]["lng"])))
route.extend(generateRoute(
    Location(randrunInfo["data"][1]["lat"], randrunInfo["data"][1]["lng"]),
    Location(randrunInfo["data"][2]["lat"], randrunInfo["data"][2]["lng"])))
route.extend(generateRoute(
    Location(randrunInfo["data"][2]["lat"], randrunInfo["data"][2]["lng"]),
    Location(randrunInfo["lat"], randrunInfo["lng"])))

mileage = 0
for i in range(len(route) - 1):
    mileage += Location.distance(route[i], route[i+1])
print("Mileage: %f" % mileage)

while mileage < 2250:
    loc = route[-1].randomShift()
    mileage += Location.distance(route[-1], loc)
    route.append(loc)
    print("\r     --> %f" % mileage, end="")
print()

runningTime = mileage / random.triangular(1.44, 3, 2.22)
stepNum = runningTime * random.triangular(2.5, 3.5, 3)
print("Running time: %f" % runningTime)
print("Step num: %f" % stepNum)

wait(startTime + runningTime - time.time())

# ======== upload ========
# This section contains the requests posted when pressing the "stop running" button on the app.
print("\n======== upload ========\n")

endTime = time.time()
updateRecordDict = {
    "id": str(student_id),
    "student_id": str(student_id),
    "running_time": int(runningTime),
    "record_id": str(record_id),
    "mileage": int(mileage),
    "pass_point": 3,
    "start_time": formatTimestamp(startTime),
    "step_count": stepNum,
    "end_time": formatTimestamp(endTime),
    "lat": route[-1].lat,
    "lng": route[-1].lng,
    "pace": int(runningTime / mileage)
}
updateRecord_res = autoRequest("post", domain + "/api/updateRecord/", json=updateRecordDict,
                               headers=postHeader(updateRecordDict))

pathPointDict = {
    "path_image": "https:\/\/i.e**st.edu.cn\/_upload\/tpl\/00\/06\/6\/template6\/images\/_wp_imgs\/red-logo.png",
    "record_id": str(record_id),
    "path_point": formatizeRoute(route)
}
updatePathPoint_res = autoRequest("post", domain + "/api/uploadPathPoint", json=pathPointDict,
                                  headers=postHeader(pathPointDict))

# time.sleep(1.5)
# autoRequest("get", domain + "/api/getUserInfo/?id=%d" % student_id, headers=headers)

time.sleep(1.5)
headers["Connection"] = "close"
recordInfo_res = autoRequest("get", domain + "/api/recordInfo/?id=%d" % record_id, headers=headers)
recordInfo = recordInfo_res.json()

print("Record info:")
print(json.dumps(recordInfo, indent=2))
