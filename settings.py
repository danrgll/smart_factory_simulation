import numpy as np
import random
MOVER_CAPACITY = 3
BASE_STATION_CAPACITY = 1
CAP_STATION_CAPACITY = 2
RING_STATION_CAPACITY = 2
STORAGE_CAPACITY = 24
REPAIRMEN_CAPACITY = 3
DESTINATION_CAPACITY = 1
# stations location
BASE_LOCATION = np.array([0, 5])
RING_LOCATION1 = np.array([5, 7])
RING_LOCATION2 = np.array([11, 4])
RING_LOCATION3 = np.array([15, 15])  #gibts nicht
CAP_LOCATION1 = np.array([6, 3])
CAP_LOCATION2 = np.array([13, 5])
CAP_LOCATION3 = np.array([20, 20])  #gibts nicht
DEL_LOCATION = np.array([0, 1])
# mover init location
MOVER_LOCATION1 = np.array([0, 0])
MOVER_LOCATION2 = np.array([1, 0])
MOVER_LOCATION3 = np.array([2, 0])
TIME_TO_PICK_UP = (2, 0.3)
# repairman init location
REPAIRMEN_LOCATION = np.array([0, 0])
REPAIR_TIME = (120, 20) #120
# Base Station
TIME_TO_CHANGE_PROC_TYPE_BS = (100 , 10) #ursprünglich 100
MEAN_TIME_TO_FAILURE_BS = 1/random.randint(600,1000)
PROC_TIME_BASE = [(10, 2)]
PROC_TYPE_INIT_BS = ["LILA", "GREY", "ROSA"]
# Ring Station
TIME_TO_CHANGE_PROC_TYPE_RS = (100, 10)
MEAN_TIME_TO_FAILURE_RS = 1/random.randint(600,1000)
PROC_TIME_RING = [(50, 10), (70, 10), (90, 10)]
PROC_TYPE_INIT_RS = ["LILA", "GREY", "ROSA"]
# Cap Station
PROC_TYPE_INIT_CS = ["LILA", "GREY"]
PROC_TIME_CAP = [(20, 5)]
TIME_TO_CHANGE_PROC_TYPE_CS = (100, 10)
MEAN_TIME_TO_FAILURE_CS = 1/random.randint(600,1000)
# Products
PRODUCT_CC3_1 = {"base": ["BLACK"], "ring": ["GREEN", "ORANGE", "YELLOW"], "cap": ["RED"], "points": 30}
PRODUCT_CC2_1 = {"base": ["BLACK"], "ring": ["GREEN", "ORANGE"], "cap": ["RED"], "points": 20}
PRODUCT_CC1_1 = {"base": ["BLACK"], "ring": ["GREEN"], "cap": ["RED"], "points": 10}
PRODUCT_CC0_1 = {"base": ["BLACK"], "cap": ["RED"], "points": 5}
PRODUCT_CC3_2 = {"base": ["RED"], "ring": ["BLUE", "RED", "BLACK"], "cap": ["GREEN"], "points": 30}
PRODUCT_CC2_2 = {"base": ["RED"], "ring": ["BLUE", "RED"], "cap": ["GREEN"], "points": 20}
PRODUCT_CC1_2 = {"base": ["RED"], "ring": ["BLUE"], "cap": ["GREEN"], "points": 10}
PRODUCT_CC0_2 = {"base": ["RED"], "cap": ["BLUE"], "points": 5}
PRODUCT_CC3_3 = {"base": ["BLACK"], "ring": ["GREEN", "BLUE", "GREEN"], "cap": ["BLUE"], "points": 30}
PRODUCT_CC2_3 = {"base": ["BLACK"], "ring": ["GREEN", "BLUE"], "cap": ["BLUE"], "points": 20}
PRODUCT_CC1_3 = {"base": ["BLACK"], "ring": ["GREEN"], "cap": ["RED"], "points": 10}
PRODUCT_CC0_3 = {"base": ["BLACK"], "cap": ["BLUE"], "points": 5}
MEAN_TIME_TO_FAILURE = 1/250
#del_station
PROC_TIME_DEL = (30, 10)





