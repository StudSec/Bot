"""
This is a simple test module used to test the main functionality.
"""
# Custom imports
from . import registry

# External imports
import lorem


class TestModule:
    def __init__(self, client):
        self.commands = {
            "hello": self.hello,
            "error": self.error,
            "overflow": self.overflow
        }
        self.name = ["Test Module"]
        self.category = ["Utils"]
        self.client = client
        self.type = "Runtime"

    async def process_message(self, message):
        if message.content.split(" ")[0][1:] in self.commands.keys():
            return self.commands[message.content.split(" ")[0][1:]](message)

    # This function tests the basic message sending functionality.
    @staticmethod
    def hello(msg):
        return "Hello World."

    # This function tests the error handling capabilities of our bot.
    @staticmethod
    def error(msg):
        return 1 / 0

    # This function tests the max message size handling capabilities of our bot.
    @staticmethod
    def overflow(msg):
        return "```\n" + lorem.text()*3 + "```"


registry.register(TestModule)
