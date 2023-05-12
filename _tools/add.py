#!/usr/bin/env python3

from os import listdir, makedirs, rename, linesep
from os.path import isdir, exists, split, normpath, join, splitext
from urllib.parse import quote
from json import dump, load
import sys
import re
import subprocess

CPPCON_YEAR = 2018

def shell_call(cmd):
    process = subprocess.Popen(cmd, shell=True)
    process.wait()
    if process.returncode:
        print(f"'{cmd}' failed.")
        print("Exit code:", process.returncode)

        exit(process.returncode)


def add_index(readme, category):
    readme.write(f"\n## {category}\n\n")
    generate_index(readme, category)


def make_readme(readme):
    with open('_tools/readme_header.md', mode='r', encoding="utf8") as \
            readme_header:
        readme.writelines(readme_header.readlines())

    readme.write("# Index of Materials\n")
    CATEGORIES = [
        "Keynotes",
        "Presentations",
        "Lightning Talks and Lunch Sessions",
        "Posters"
    ]
    for category in CATEGORIES:
        add_index(readme, category)


def generate_entry(readme, path):
    def md_path(path):
        return quote(normpath(path).replace('\\', '/'))

    presentation_regex = re.compile((f"__cppcon_{str(CPPCON_YEAR)}" + "\\.[^.]*$"))
    pdf_regex = re.compile("\\.pdf$", flags=re.I)
    readme_md_regex = re.compile("README\\.md$")

    readme_md_file = ""
    presentation_file = ""
    all_presentation_files = []
    all_other_files = []
    author = ""

    dir_contents = listdir(path)

    for name in dir_contents:
        if name == '.presentation':
            continue
        elif presentation_regex.search(name):
            # Pick the first file we found, but prefer a PDF file if there
            # is one
            if (not presentation_file) or pdf_regex.search(name):
                presentation_file = name
                # author = get_author_from_filename(name)

            all_presentation_files.append(name)
        elif readme_md_regex.search(name):
            readme_md_file = name
        else:
            all_other_files.append(name)

    if all_presentation_files:
        presentation_path = join(path, presentation_file)
    else:
        presentation_path = path
        # author = get_author_from_readme_md(join(path, readme_md_file))

    with open(join(path, '.presentation'), mode="r", encoding="utf8") as f:
        presentation_info = load(f)

    session_name = presentation_info["Title"]
    author = presentation_info["Author"]
    readme.write(" - [{}]({}) by {}".format(session_name,
                                     md_path(presentation_path),
                                     author))

    if len(all_presentation_files) > 1:
        exts = [(splitext(f)[1].lower(), md_path(join(path, f))) for f in
                all_presentation_files]
        for e in exts:
            readme.write(" \\[[{}]({})\\]".format(e[0], e[1]))

    if readme_md_file:
        readme.write(" \\[[README]({})\\]".format(
            md_path(join(path, readme_md_file))))

    if all_other_files:
        readme.write(" \\[[more materials]({})\\]".format(md_path(path)))

    readme.write('\n')


def generate_index(readme, path):
    if not exists(path):
        print("Skipping", path, "since it doesn't exist yet")
        return

    dir_contents = listdir(path)
    dir_contents.sort(key=lambda s: s.lower())

    for name in dir_contents:
        try:
            # empty directories or other such issues get skipped over
            generate_entry(readme, join(path, name))
        except:
            pass


def add_presentation(path):
    session = ""
    SESSION_MAP = {
        'p': 'Presentations',
        'k': 'Keynotes',
        'l': 'Lightning Talks and Lunch Sessions',
        'o': 'Posters',
    }
    while not session or session not in SESSION_MAP.keys():
        session = input("[P]resentation, [K]eynote, " +
                        "[L]ighting/Lunch, P[o]ster? ").lower()
    folder = SESSION_MAP[session]

    filename = split(path)[-1]
    ext = splitext(filename)[-1]
    title = ""
    author = ""

    if ext == '.md':
        readme_header_regex = re.compile(r"\*\*(.*)\*\* by \*\*(.*)\*\*")

        with open(filename, mode='r', encoding="utf8") as readme:
            heading = readme.readline()
            if match := readme_header_regex.match(heading):
                title = match[1]
                author = match[2]
    else:
        title_author_regex = re.compile(
            f"(.*) - (.*) - CppCon {str(CPPCON_YEAR)}" + r"\.[^.]*$"
        )

        if title_author_match := title_author_regex.search(filename):
            title = title_author_match[1]
            author = title_author_match[2]

        print("\nExtension is", ext)

    if not title or not author:
        title = input("Title: ")
        author = input("Author: ")

    ok = ''
    while ok != 'y':
        if ok != 'n':
            print("\n\nTitle:", title)
            print("Author:", author)
            ok = input('OK? [y/n]: ').lower()

        if ok == 'n':
            title = input("Title: ")
            author = input("Author: ")
            ok = ''

    file_title = title.lower().replace(' - ', ' ').replace(
        ' ', '_').replace("c++", "cpp")
    file_title = ''.join([c for c in file_title if c.isalnum() or c in ' _'])
    file_title = ' '.join(file_title.lower().split())

    file_author = author.lower().replace(' ', '_')
    file_author = ''.join([c for c in file_author if c.isalnum() or c == '_'])

    if filename != 'README.md':
        new_filename = f"{file_title}__{file_author}__cppcon_{CPPCON_YEAR}{ext}"
        ok = ''
        while ok != 'y':
            print("\n\nFilename:", new_filename)
            ok = input("OK? [y/n]: ").lower()

            if ok == 'n':
                new_filename = input("Filename: ")
                new_name, new_ext = splitext(new_filename)

                title_author_regex = re.compile(
                    f"(.*)__(.*)__cppcon_{str(CPPCON_YEAR)}" + r"\.[^.]*$"
                )

                title_author_match = title_author_regex.search(new_filename)
                if not title_author_match:
                    print("Cannot parse title and author from new filename")
                elif not all((c.isalnum() or c == '_') for c in new_name):
                    print(f"Filename contains non-alphanumeric characters. ({new_filename})")
                elif new_ext != ext:
                    print("New file extension does not match original file" +
                        "extension")
                else:
                    file_title = title_author_match[1]
                    ok = ''
    else:
        new_filename = filename
        contents = None
        with open(filename, mode='r', encoding="utf8") as readme:
            contents = readme.readlines()
        contents[0] = f'**{title}** by **{author}**'
        with open(filename, mode='w', encoding="utf8") as readme:
            readme.writelines(contents)

    new_folder = join(folder, file_title)
    new_path = join(new_folder, new_filename)
    makedirs(new_folder, exist_ok=True)
    rename(path, new_path)

    with open(
            join(new_folder, '.presentation'), mode='w', encoding="utf8") as f:
        dump({'Title': title, 'Author': author}, f)

    shell_call(f'git add "{new_folder}"')

    return title, author


if __name__ == '__main__':
    if not (exists('_tools') and isdir('_tools')):
        print(f"Run this from the CppCon{CPPCON_YEAR} root.")
        exit(1)

    TITLE = None
    AUTHOR = None
    if len(sys.argv) == 2 and sys.argv[1]:
        TITLE, AUTHOR = add_presentation(sys.argv[1])

    with open('README.md', mode='w', encoding="utf8") as readme:
        make_readme(readme)

    shell_call('git add README.md')
    if TITLE and AUTHOR:
        shell_call(f'git commit -v -m "Add {TITLE} by {AUTHOR}" -e')
    else:
        shell_call('git commit -v -m "Updating index" -e')
