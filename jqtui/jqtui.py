import json
from typing import Any

import pyjq
import typer
from pyjq import ScriptRuntimeError
from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Footer, Input, Static
from typing_extensions import Annotated

typer_app = typer.Typer(no_args_is_help=True, add_completion=False)


class Result(Static):
    """Display a json."""


class ResultHeader(Static):
    """Display a json."""


class Message(Static):
    """Display messages"""

    def on_mount(self):
        self.update('Please enter a jq expression above')


class JQTUI(App):
    CSS_PATH = 'jqtui.css'
    BINDINGS = [
        Binding(key="ctrl+c", action="quit", description="Quit", priority=True),
        Binding(
            key="ctrl+t",
            action="toggle_errors",
            description="Show/Hide Errors",
            priority=True,
        ),
    ]

    def __init__(self, filename):
        self.filename = filename
        super().__init__()

        with open(filename) as f:
            self.data = json.loads(f.read())

    def action_toggle_errors(self):
        if self.query_one('#message').has_class('hide'):
            self.query_one('#message').remove_class('hide')
        else:
            self.query_one('#message').add_class('hide')

    def compose(self) -> ComposeResult:
        yield Input(id="input", placeholder="Type in a jq command")
        yield Message(id="message", classes="hide")

        with VerticalScroll(id="results-container"):
            yield ResultHeader(id="results-header")
            yield Result(id="results")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        # Give the input focus, so we can start typing straight away
        # self.query_one(Input).focus()
        syntax = self.get_syntax([self.data])
        self.query_one("#results").update(syntax)
        self.query_one("#results-header").update('Displaying original file contents')

    async def on_input_changed(self, message: Input.Changed) -> None:
        """A coroutine to handle a text changed message."""
        if message.value:
            self.run_jq(message.value)
        else:
            self.query_one("#results-header").update('Displaying original contents')
            syntax = self.get_syntax([self.data])
            self.query_one("#results").update(syntax)
            self.query_one('#input').remove_class('red_border')

    def run_jq(self, value):
        try:
            filtered_data = pyjq.all(value, self.data)
            if not any(filtered_data):
                raise ValueError('The query did not produce any results')
            syntax = self.get_syntax(items=filtered_data)

            self.query_one("#results-header").update(
                f"Displaying results for: '{value}'"
            )
            self.query_one("#results").update(syntax)
            self.query_one('#input').remove_class('red_border')
            self.query_one("#message").update(
                'Congrats! There are no errors with the jq syntax'
            )
        except (ValueError, ScriptRuntimeError) as e:
            self.query_one('#input').add_class('red_border')
            self.query_one("#message").update(f"ERROR: {e}")

    def get_syntax(self, items: list[Any]):
        """
        Given a list of dictionaries, convert it to a Syntax object

        Each item in the list is json serializable
        """
        lines = []

        for item in items:
            lines.append(json.dumps(item, indent=4))

        result = '\n'.join(lines)
        syntax = Syntax(result, 'json', theme='material', line_numbers=False, padding=1)

        return syntax


def cli(filename: Annotated[str, typer.Argument(help='Name of the JSON file')]):
    app = JQTUI(filename=filename)
    app.run()


def main():
    typer.run(cli)


if __name__ == '__main__':
    main()
