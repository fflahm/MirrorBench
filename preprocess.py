import json

repos = {"body": json.load(open("tasks/body_repo.json", 'r')),
         "hand": json.load(open("tasks/hand_repo.json", 'r')),
         "mark": json.load(open("tasks/mark_repo.json", 'r'))}

def preprocess(task_dict):
    for key in task_dict:
        if isinstance(task_dict[key], dict) and "name" in task_dict[key]:
            item = repos[key][task_dict[key]["name"]]
            task_dict[key] |= item

def construct(id_dict):
    task_dict = {}
    for key in id_dict:
        task_dict[key] = repos[key][id_dict[key]]
    return task_dict