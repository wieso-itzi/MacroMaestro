import json

# gets a list of input from the keyboard and mouse module and writes it to a file
def write_json_file(data, file):
    with open(file, 'w') as f:
        json.dump(data, f)

# reads inputs from file and returns a queue
def read_macro_file(file):
    macro_events = []
    f = open(file)
    saved_inputs = json.load(f)
    for input in saved_inputs:
        macro_events.append(input)
    f.close()
    return macro_events

def read_config_file(file):
    f = open(file)
    config = json.load(f)
    f.close()
    return config