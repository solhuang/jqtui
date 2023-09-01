import json
import logging
from typing import Any

import pyjq
import pyperclip
import typer
from pyjq import ScriptRuntimeError
from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Footer, Input, Static
from typing_extensions import Annotated

typer_app = typer.Typer(no_args_is_help=True, add_completion=False)

logging.basicConfig(
    filename='/tmp/jqtui.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
)
logger = logging.getLogger('__name__')


class Result(Static):
    """Display results"""


class ResultHeader(Static):
    """Display header"""


class Message(Static):
    """Display messages"""

    def on_mount(self):
        self.update('Please enter a jq expression above')


class Notification(Static):
    def on_mount(self) -> None:
        self.set_timer(2, self.remove)

    def on_click(self) -> None:
        self.remove()


class JQTUI(App):
    CSS_PATH = 'jqtui.css'
    BINDINGS = [
        Binding(key="ctrl+c", action="quit", description="Quit", priority=True),
        Binding(
            key="ctrl+r ",
            action="toggle_errors",
            description="Show/Hide Errors",
            priority=True,
        ),
        Binding(
            key="ctrl+o",
            action="copy_output",
            description="Copy output",
            priority=True,
        ),
        Binding(
            key="ctrl+y",
            action="copy_query",
            description="Copy query",
            priority=True,
        ),
    ]

    def __init__(self, data: dict):
        """
        data: the json that was loaded from file or from stdin
        """
        self.data = data
        self.jq_expression = ''
        super().__init__()

    def action_toggle_errors(self):
        if self.query_one('#message').has_class('hide'):
            self.query_one('#message').remove_class('hide')
        else:
            self.query_one('#message').add_class('hide')

    def action_copy_output(self):
        """
        Copy output to the clipboard
        """
        pyperclip.copy(self.formatted_result)
        message = "Successfully copied the output to the clipboard"
        self.screen.mount(Notification(message))

    def action_copy_query(self):
        """
        Copy jq expression to the clipboard
        """
        pyperclip.copy(self.jq_expression)
        message = "Successfully copied the jq query to the clipboard"
        self.screen.mount(Notification(message))

    def compose(self) -> ComposeResult:
        yield Input(id="input", placeholder="Type in a jq query")
        yield Message(id="message", classes="hide")

        with VerticalScroll(id="results-container"):
            yield ResultHeader(id="results-header")
            yield Result(id="results")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        self.formatted_result = self.format_result([self.data])
        syntax = self.get_syntax(self.formatted_result)
        self.query_one("#results").update(syntax)
        self.query_one("#results-header").update('Displaying original file contents')

    async def on_input_changed(self, message: Input.Changed) -> None:
        """A coroutine to handle a text changed message."""
        if message.value:
            self.run_jq(message.value)
        else:
            self.query_one("#results-header").update('Displaying original contents')
            self.formatted_result = self.format_result([self.data])
            syntax = self.get_syntax(self.formatted_result)
            self.query_one("#results").update(syntax)
            self.query_one('#input').remove_class('red_border')

    def run_jq(self, value):
        try:
            filtered_data = pyjq.all(value, self.data)
            if not any(filtered_data):
                raise ValueError('The query did not produce any results')

            self.jq_expression = value
            self.formatted_result = self.format_result(filtered_data)
            syntax = self.get_syntax(self.formatted_result)

            self.query_one("#results-header").update(
                f"Displaying results for: '{value}'"
            )
            self.query_one("#results").update(syntax)
            self.query_one('#input').remove_class('red_border')
            self.query_one("#message").update(
                'Congrats! There are no errors with the jq query'
            )
        except (ValueError, ScriptRuntimeError) as e:
            self.query_one('#input').add_class('red_border')
            self.query_one("#message").update(f"ERROR: {e}")

    def format_result(self, items: list[Any]) -> str:
        """
        Given a list of dictionaries, convert it to a jq output

        Each item in the list is json serializable
        """
        lines = []
        for item in items:
            lines.append(json.dumps(item, indent=4))
        result = '\n'.join(lines)
        return result

    def get_syntax(self, value) -> Syntax:
        """
        Returns a syntax object
        """
        syntax = Syntax(value, 'json', theme='material', line_numbers=False, padding=1)

        return syntax


def cli(filename: Annotated[str, typer.Argument(help='Name of the JSON file')]):
    with open(filename) as f:
        data = json.loads(f.read())
    app = JQTUI(data=data)
    app.run()


def main():
    # TODO: fix piping
    # if not sys.stdin.isatty():
    #     data = json.loads(sys.stdin.read())
    #     app = JQTUI(data=data)
    #     app.run()

    typer.run(cli)


if __name__ == '__main__':
    main()
