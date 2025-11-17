import os
from pathlib import PurePath


def collect_quiz_in_file(filefolder: str) -> None:
    files_in_filefolder = os.listdir(filefolder)
    collected_quiz = dict()
    for file in files_in_filefolder:
        with open(PurePath(filefolder, file), 'r', encoding='KOI8-R') as file:
            questions = file.read()
            result = str(questions).split("\n\n\n")
        for s in result:
            if 'Вопрос' in s:
                question = ''
                answer = ''
                for d in s.split("\n\n"):
                    if 'Вопрос' in d:
                        question = d.split(':')[1]
                    if 'Ответ' in d:
                        answer = d.split(':')[1]
                    collected_quiz[question] = answer
    return collected_quiz