import pickle
from pprint import pprint

# read python dict back from the file
pkl_file = open('subject_image_mapping.pkl', 'rb')
mydict2 = pickle.load(pkl_file)
pkl_file.close()

# create a txt file with the mapping
with open('subject_image_mapping.txt', 'w') as f:
    pprint(mydict2, stream=f)
