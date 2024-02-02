import os
import sys
import time
import argparse
from dotenv import load_dotenv
import threading
from queue import Queue
from rich.console import Console
from utility import Utility 
from commit_analysis import CodeSummarization, CommitMsgComparison
import git_repo_manager
from rich import box
from rich.progress import (
    BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TimeElapsedColumn, Table
)

class CommitProcessor:
    def __init__(self):
        try:
            load_dotenv()
            self.URI = os.getenv("URI", "")
            self.MODEL = os.getenv("MODEL", "gpt-3.5-turbo")
            self.console = Console()
            self.result_queue = Queue()
            self.MAX_RETRIES = 5
            self.VALID_RESPONSES = ["true", "false",True,False]
            self.done_flag = threading.Event()
            self.GitRepoManager = git_repo_manager.GitRepoManager()
            self.confidence_level = int(os.getenv("CONFIDENCE", "60"))
        except Exception as e:
            print(f"\n\nUnexpected error occurred: {e}")
            sys.exit(1)


    def thinking_animation(self, progress, text):
        task = progress.add_task(f"[cyan] {text}", total=None)
        while not self.done_flag.is_set():
            progress.update(task,advance=1)
            time.sleep(.5)
        
        # Update progress bar to completed state
        bar_column = next(column for column in progress.columns if isinstance(column, BarColumn))
        bar_column.style = "green"
        bar_column.pulse_style = "green"
        progress.refresh()


    def output_table(self, commit_message, suggested_commit_message):
        # Create a table
        table = Table(show_header=False, header_style="bold magenta", border_style="white", show_lines=True, box=box.HORIZONTALS, width=80)

        # Add rows to the table
        table.add_row("Original Commit Message:", style="white")
        table.add_row(commit_message, style="red")
        table.add_row("Ai Generated Commit Message",style="white")
        table.add_row(suggested_commit_message,style="cyan")

        # Print the table
        self.console.print(table)
        tip = "\n[white][bold]Tip:[/bold] Use [reverse]git commit --amend[/reverse] to update the commit message.[/white]\n"
        self.console.print(tip)

    def thinking_threaded(self, target, args, text):
        try:
            # Queue for communication of errors
            error_queue = Queue()
            def subprocess_function():
                try:
                    target(*args)
                except Exception as e:
                    error_queue.put(e)

            text_len = len(text)
            progress_columns = (
                SpinnerColumn(),
                "[progress.description]{task.description}",
                BarColumn(style="black", complete_style="green", finished_style="green", pulse_style="white", bar_width=(57-text_len)),
                TaskProgressColumn(),
                "Elapsed:",
                TimeElapsedColumn(),
            )

            with Progress(*progress_columns) as progress:
                # Start the subprocess in a separate thread
                subprocess_thread = threading.Thread(target=subprocess_function)
                subprocess_thread.start()

                if not self.silent:
                    thinking_thread = threading.Thread(target=self.thinking_animation, args=(progress,text))
                    thinking_thread.start()

                subprocess_thread.join()

                # Check for errors in the subprocess
                if not error_queue.empty():
                    error = error_queue.get()
                    print(f"Error occurred in thread: {error}")
                    raise error

                self.done_flag.set()
                if not self.silent: thinking_thread.join()


            return self.result_queue.get()
        
        except ValueError as e:
            raise e

    def code_summary(self, commit, codetext):
        try:
            code_summary_chain = CodeSummarization()
            code_summary_chain.simulate = self.simulate
            code_summary = code_summary_chain.get_code_summary(commit,codetext)
            self.result_queue.put(code_summary)
        except ValueError as e:
            raise e

    def compare_commit_messages(self, original_commit_msg, generated_commit_msg):
        if self.simulate:
            result = -1
        else:    
            result = CommitMsgComparison.compare_messages(original_commit_msg,generated_commit_msg)
        self.result_queue.put(result)

    def validate_commit_message(self, UseCommitMessage):
        return UseCommitMessage in self.VALID_RESPONSES

    def process_commit_data(self, commit, codetext):
        try:
            target_function = self.code_summary
            generated_commit_message = self.thinking_threaded(target_function, [commit.hexsha, codetext], "Generating summary...")
            if not generated_commit_message:
                raise ValueError("The generated commit message is empty.")
          
            if self.compare_commits_arg:
                original_commit_msg = commit.message

                target_function = self.compare_commit_messages
                commit_similarity_confidence = self.thinking_threaded(target_function, [original_commit_msg, generated_commit_message], "Comparing commit messages...")

                self.console.print(f"\n[green]Inference Confidence Level: [/green][white] {commit_similarity_confidence}%[/white]")                           
                if commit_similarity_confidence >= self.confidence_level:
                    self.console.print("\n[green]:green_circle: Commit Message Check Passed[/green]")
                    sys.exit(0)
                else:            
                    self.console.print("\n[red]:red_circle: Commit Message Check Failed[/red]\n")
                    self.output_table(original_commit_msg,generated_commit_message)
            else:
                small_banner_begin = "\n:black_large_square::brown_square::red_square::orange_square::yellow_square::green_square::blue_square::purple_square::white_large_square: "
                small_banner_end = " :white_large_square::purple_square::blue_square::green_square::yellow_square::orange_square::red_square::brown_square::black_large_square:\n"
                table_banner = (small_banner_begin + "Ai Generated Commit Message" + small_banner_end) 

                table = Table(title = None if self.silent else table_banner,  width=80, border_style="white", box=None, show_header=False)
                table.add_row(f"[white]{generated_commit_message}[/white]\n")
                self.console.print(table)
                sys.exit(0)

        except ValueError as e:
            self.console.print(f"\n\n[red]:police_car_light: An error occurred:[/red][white] {e}[/white]")

        except Exception as e:
            self.console.print(f"\n\n[red]:police_car_light: Unexpected error occurred:[/red][white] {e}[/white]")

        else:
            # If no break is on, exit gracefully
            if self.nobreak:
                sys.exit(0)

        # Default message and exit
        self.console.print(":stop_sign: Exiting with status code 1.")
        sys.exit(1)     

    def process_current_repo(self):
        commits = self.GitRepoManager.get_commits()
        for commit in commits:
            self.process_single_commit(commit)

    def process_single_commit(self, commit):
        if not self.silent:
            print(f"Current Commit: {commit.hexsha}\n")
        raw_diff = self.GitRepoManager.get_changes(commit)
        self.process_commit_data(commit, self.clean(raw_diff))

    def clean(self, raw_diff):
        return Utility.cleanTripleSlashes(
            Utility.cleanTripleQuotes(raw_diff)
        )

    def show_banner(self):
        if self.URI:
            style="bold white on blue"
            connecting_to=self.URI
        else:
            style="bold white"
            connecting_to="OpenAI"
        model_name = f"{self.MODEL}" or False


        description = "CheekyAI utilizes artificial intelligence to suggest and/or examine commit messages, ensuring that the provided commit message aligns with the content of the commit.\n\nUse -h for the help menu"
        banner = Table(
            title="\nCheekyAI :grinning_face:",
            box=box.HORIZONTALS,
            width=80,
            style=style,
            title_style="none",
        )

        # Nested Table to handle colspans
        table = Table(
            show_header=False,
            width=76,
            box=None,
            style="none",
            title_style="none",
            border_style="none",
            show_edge=False
        )
        table.add_column("Column 1", justify="right",width=20)
        table.add_column("Column 2", justify="left",width=50)
        table.add_row(f"Connecting to:", f"{connecting_to}")

        if model_name:
            table.add_row("Model:",f"{model_name}")

        # Outside table 
        banner.add_column(description)
        banner.add_row(table)
        self.console.print(banner)


    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="CheekyAI - Create / Validate commit messages.")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--compare",action="store_true", help="Compare the current commit message to the generated one.")
        group.add_argument("--silent",action="store_true", help="Do not show banners and output only the suggested message. Not compatible with --compare.")
        parser.add_argument("--commit", help="Specify a commit hash to process.")
        parser.add_argument("--nobreak",action="store_true", help="When used with compare, CheekyAi won't exit with an error code if the comparison fails.")
        # Used for testing
        parser.add_argument("--simulate",action="store_true", help=argparse.SUPPRESS)
        return parser.parse_args()

    compare_commits_arg = False

    def run(self):
        args = self.parse_arguments()
        self.silent = bool(args.silent)
        self.compare_commits_arg = bool(args.compare)
        self.nobreak = bool(args.nobreak)
        self.simulate = bool(args.simulate)

        if not self.silent: self.show_banner()      

        if args.commit:
            commit = self.GitRepoManager.get_commit(args.commit)
            self.process_single_commit(commit)    
        else:
            self.process_current_repo()


if __name__ == "__main__":
    processor = CommitProcessor()
    processor.run()
