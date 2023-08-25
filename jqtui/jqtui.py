import pyjq
import _pyjq
import json
import sys
from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Input, Markdown, Static

from textual.widget import Widget
from textual.app import App, ComposeResult, RenderResult
from rich.syntax import Syntax
from rich.json import JSON
from pyjq import ScriptRuntimeError
from typing import Any

with open('example.json') as f:
    data = json.loads(f.read())


class Result(Static):
    """Display a json."""


class ResultHeader(Static):
    """Display a json."""


class JQTUI(App):
    CSS_PATH = 'jqtui.css'

    def compose(self) -> ComposeResult:
        yield Input(id="input", placeholder="Type in a jq command")
        yield Static(id="message")
        with VerticalScroll(id="results-container"):
            yield ResultHeader(id="results-header")
            yield Result(id="results")
            yield Markdown(id="md")

    def on_mount(self) -> None:
        """Called when app starts."""
        # Give the input focus, so we can start typing straight away
        self.query_one(Input).focus()
        syntax = self.get_syntax([data])
        self.query_one("#results").update(syntax)
        self.query_one("#results-header").update("Displaying the original JSON")

    async def on_input_changed(self, message: Input.Changed) -> None:
        """A coroutine to handle a text changed message."""
        if message.value:
            self.run_jq(message.value)
        else:
            self.query_one("#results-header").update('Displaying the original JSON')
            syntax = self.get_syntax([data])
            self.query_one("#results").update(syntax)
            self.query_one('#input').remove_class('red_border')

    def run_jq(self, value):
        result = ''
        try:
            filtered_data = pyjq.all(value, data)
            if not any(filtered_data):
                raise ValueError('The results produced all Nones')
            syntax = self.get_syntax(items=filtered_data)

            self.query_one("#results-header").update(
                f'Displaying results for: "{value}"'
            )
            self.query_one("#results").update(syntax)
            self.query_one("#message").update("")
            self.query_one('#input').remove_class('red_border')
        except (ValueError, ScriptRuntimeError) as e:
            self.query_one('#input').add_class('red_border')
            self.query_one("#message").update(f"Not a valid jq query: {value}: {e}")

    def get_syntax(self, items: list[Any]):
        """
        Given a list of dictionaries, convert it to a Syntax object

        Each item in the list is json serializable
        """
        lines = []

        for item in items:
            lines.append(json.dumps(item, indent=4))

        result = '\n'.join(lines)
        syntax = Syntax(result, "json", theme="material", line_numbers=False, padding=1)

        return syntax

def main():
    app = JQTUI()
    app.run()

if __name__ == '__main__':
    main()
