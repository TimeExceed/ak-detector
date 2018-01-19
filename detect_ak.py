#!/usr/bin/python3
import os
import os.path as op
import subprocess as sp
import re
import sys
import hashlib

AK_PAT = re.compile(b'\\b[0-9a-zA-Z]{16,30}\\b')
NUMERIC_PAT = re.compile(b'\\b\\d+\\b')
ALL_ALPHABET_PAT = re.compile(b'\\b[a-zA-Z]+\\b')
WHITE_LIST = set([b'leftSmallThan100G'])

def get_remote_branches():
    stdout = sp.check_output(['git', 'branch', '--all'])
    branches = [x.strip() for x in str(stdout, 'utf-8').split('\n') if x and '->' not in x and 'HEAD' not in x]
    branches = [x if not x.startswith('*') else x[1:].strip() for x in branches]

    stdout = sp.check_output(['git', 'tag'])
    tags = [x.strip() for x in str(stdout, 'utf-8').split('\n') if x]

    return branches + tags

def get_commit_log(branch):
    sp.check_call(['git', 'checkout', '--detach', branch], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    stdout = sp.check_output(['git', 'log', '--full-history', '--date-order', '--reverse', '--pretty=format:%H'])
    commits = [x.strip() for x in str(stdout, 'utf-8').split('\n') if x]
    return commits

def check_commit(commit, checked_files):
    sp.check_call(['git', 'checkout', '--detach', commit], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    for rt, dirs, files in os.walk('.'):
        if '.git' in dirs:
            dirs.remove('.git')
        for f in files:
            fn = op.normpath(op.join(rt, f))
            with open(fn, 'rb') as fp:
                content = fp.read()
            digest = hashlib.sha1(content).digest()
            if digest in checked_files:
                continue
            m = AK_PAT.search(content)
            if m:
                text = m.group(0)
                if text not in WHITE_LIST and not NUMERIC_PAT.match(text) and not ALL_ALPHABET_PAT.match(text):
                    print(text, file=sys.stderr)
                    return fn
            checked_files.add(digest)

if __name__ == '__main__':
    branches = get_remote_branches()
    checked_commits = set()
    checked_files = set()
    for branch in branches:
        print('checking branch/tag', branch)
        commits = get_commit_log(branch)
        for commit in commits:
            if commit in checked_commits:
                continue
            print('checking commit', commit)
            failed_file = check_commit(commit, checked_files)
            if failed_file:
                print('ERROR', failed_file, 'in commit', commit, 'of branch', branch, 'may contain access-key ID/Secret', file=sys.stderr)
                sys.exit(1)
            checked_commits.add(commit)

