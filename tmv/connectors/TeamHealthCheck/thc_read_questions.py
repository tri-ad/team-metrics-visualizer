from typing import List, Dict


def read_thc_questions(path: str) -> List[Dict]:
    questions = []

    with open(path) as f:
        for line in f:
            parts = line.split("\t")

            questions.append(
                {
                    "topic": parts[0].strip(),
                    "answer_green": parts[1].strip(),
                    "answer_red": parts[2].strip(),
                }
            )

    return questions
