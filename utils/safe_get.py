# Define a function to safely access dictionary keys
def safe_get(dictionary, key, default=None):
    return dictionary.get(key, default)