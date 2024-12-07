import pickle

with open('./data/spots_merged.pkl', 'rb') as f:
    data = pickle.load(f)

print(data)