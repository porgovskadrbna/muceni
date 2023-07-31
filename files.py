from aiofiles import os


def list_by_grade_and_subject(
    grades: list[int],
    subjects: list[str],
) -> dict[int, dict[str, list[str]]]:
    files = {}

    # For each grade
    for grade in grades:
        # List the files in the grade directory
        for file in os.scandir(f"files/{grade}"):
            # If the subject is in the list of filtered subjects
            if file.name.split("_")[0] in subjects:
                # Add the file to the list of files for the subject
                files[grade].append(file.name)

    return files
