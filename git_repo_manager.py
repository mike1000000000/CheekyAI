import git
from git import Repo
import os
from dotenv import load_dotenv
import re
import logging

class GitRepoManager:
    def __init__(self):
        load_dotenv()
        self.mainbranch = os.getenv("MAINBRANCH")
        self.path = os.getenv("DEVPATH")
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(level=log_level)

        try:
            self.repo = Repo(self.path)
        except Exception as e:
          raise Exception(f"Failed to initialize repository at '{self.path}'") from e


    def get_current_branch(self):
        try:
            return self.repo.active_branch.name
        except git.GitCommandError as e:
            logging.error(f"Git command failed: {e}")
            return None

    def get_commit_list(self, base_branch, source_branch):
        # Get a list of commits between the base branch and the source branch.
        try:
            if base_branch == source_branch:
                return [self.repo.head.commit]
            commit_range = f"{base_branch}..{source_branch}"
            return list(self.repo.iter_commits(commit_range))
        except git.GitCommandError as e:
            logging.error(f"Error getting commit list: {e}")
            return []


    def get_commits(self):
        base_branch = self.mainbranch
        current_branch = self.get_current_branch()
        if current_branch:
            return self.get_commit_list(base_branch, current_branch)
        return []
    
    def get_changes(self, commit):
        try:
            current = self.repo.commit(commit)
            parent = self.get_parent(current)
            if parent:
                return self.repo.git.diff(parent.hexsha, current.hexsha)
            return ''
        except git.GitCommandError as e:
            logging.error(f"Error getting changes: {e}")
            return ''
    
    def get_commit(self,commit_hexsha):
        try:
            return self.repo.commit(commit_hexsha)
        except git.GitCommandError as e:
            logging.error(f"Error getting commit: {e}")
            return None
    
    def get_parent(self, current_commit):
        try:
            if current_commit.parents:
                parent_commit = current_commit.parents[0]
                logging.info(f"\nPrevious Commit: {parent_commit.hexsha}")
                logging.info(f"Previous Commit Message: {parent_commit.message}")
                return parent_commit
            return None
        except git.GitCommandError as e:
            logging.error(f"Error getting parent commit: {e}")
            return None

    @staticmethod
    def parse_diff_files(diff_content):
        file_diffs = {}
        current_file = None

        for line in diff_content.splitlines():
            # Check for a new file header in the diff
            match = re.match(r'diff --git a/(.*) b/(.*)', line)
            if match:
                current_file = match.group(2)
                file_diffs[current_file] = ''

            # Add the line to the current file's diff
            if current_file:
                file_diffs[current_file] += line + '\n'

        return file_diffs 

    @staticmethod
    def extract_filenames(diff_content):
        # This function parse the diff content and extracts each filename and whether it was added, removed, updated, or unchanged.
        new_filenames = set()
        unchanged_filenames = set()
        renamed_filenames = set()
        removed_filenames = set()

        oldfile = ''

        for line in diff_content.splitlines():
            if line.startswith('--- a/'):
                oldfile = line[6:].strip()
                continue
            
            if line.startswith('--- /dev/null'):
                oldfile = ''
                continue

            if line.startswith('+++ b/'):
                currentfile = line[6:].strip()

                if oldfile == '':
                    new_filenames.add(currentfile)
                elif oldfile == currentfile:
                    unchanged_filenames.add(currentfile)
                else:
                    renamed_filenames.add((oldfile, currentfile))
                continue

            if line.startswith('+++ /dev/null'): 
                removed_filenames.add(oldfile)

        all_filenames = new_filenames | unchanged_filenames | set(item[1] for item in renamed_filenames)

        all_changes = [
            {'added': filename} for filename in new_filenames
        ] + [
            {'renamed': {'old': oldfile, 'new': currentfile}} for oldfile, currentfile in renamed_filenames
        ] + [
            {'removed': filename} for filename in removed_filenames
        ]
        return all_filenames, all_changes


    def get_raw_file_content(self, commit_sha, file_path):
        # Retrieve the raw files from the git stash - Note this doesn't work on deleted files.
        try:
            commit = self.repo.commit(commit_sha)
            return commit.tree[file_path].data_stream.read().decode('utf-8')
        except git.GitError as e:
            logging.error(f"Git error occurred: {e}")
            return None


    # Run this script directly to get the current branch, commit, and message. 
    def run(self):
        if self.repo is None:
            logging.error("Repository not initialized.")
            return
        current_branch = self.get_current_branch()
        if current_branch:
            commit_list = self.get_commit_list(self.mainbranch, current_branch)
            for commit in commit_list:
                print(f"Branch: {current_branch}\nCommit: {commit.hexsha}\nMessage: {commit.message}")


if __name__ == "__main__":
    git_manager = GitRepoManager()
    git_manager.run()