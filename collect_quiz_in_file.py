import os
import json
from environs import env


def collect_quiz_in_file(filefolder: str) -> None:
    files_in_filefolder = os.listdir(filefolder)
    collected_quiz = dict()
    for file in files_in_filefolder:
        with open(f'{filefolder}/{file}', 'r', encoding='KOI8-R') as file:
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
    with open('quiz_data.json', 'w', encoding='utf-8') as file:
        json.dump(collected_quiz, file, ensure_ascii=False, indent=4)


def main():
    env.read_env()
    filefolder = env.str('FILEFOLDER_NAME')
    collect_quiz_in_file(filefolder)


if __name__ == '__main__':
    main()