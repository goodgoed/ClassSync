import csv
import os
import logging
from dotenv import dotenv_values

from user import User
from class_record import Class_Record
from class_checker import Class_Checker

if __name__ == '__main__':
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.txt')
    logging.basicConfig(filename=log_file, encoding='utf-8', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    credentials = dotenv_values(env_file)
    
    user_classes = dict()
    logging.info("START RUNNING")
    csv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'classes.csv')
    with open(csv_file, newline='') as csvfile:
        for _class in csv.DictReader(csvfile, delimiter=','):
            new_class = Class_Record(_class['section_number'], _class['course_subject'], _class['course_number'])
            user_id = _class['user']
            if user_id in user_classes:
                user_classes[user_id].append(new_class)
            else:
                user_classes[user_id] = [new_class]

    users = []
    for id,classes in user_classes.items():
        user = User(id, credentials[f'USER_{id}'], classes)
        users.append(user)

    class_checker = Class_Checker(credentials)
    class_checker.login()

    messages = []
    for user in users:
        message = ""
        for _class in user.classes:
            class_checker.find(_class)
            message += f"{str(_class)}\n"
        messages.append({"id":user.po_id, "content":message})

    for message in messages:
        class_checker.notify(message['id'], message['content'])