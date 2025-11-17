import os
from pathlib import PurePath


def collect_quiz_in_file(filefolder: str) -> None:
    files_in_filefolder = os.listdir(filefolder)
    collected_quiz = dict()
    for file in files_in_filefolder:
        with open(PurePath(filefolder, file), 'r', encoding='KOI8-R') as file:
            text = file.read()
            text_blocks = str(text).split("\n\n\n")
        for text_block in text_blocks:
            if 'Вопрос' in text_block:
                question = ''
                answer = ''
                for text in text_block.split("\n\n"):
                    if 'Вопрос' in text:
                        question = text.split(':')[1]
                    if 'Ответ' in text:
                        answer = text.split(':')[1]
                    collected_quiz[question] = answer
    return collected_quiz