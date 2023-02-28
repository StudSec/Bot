"""
Role master, used to allow users to opt-in to roles.
"""
# Custom imports
from . import registry


class RoleMaster:
    def __init__(self, client):
        self.commands = {}
        self.name = ["Role Master"]
        self.category = ["Social"]
        self.client = client
        self.type = "Runtime"

    async def process_message(self, message):
        pass


registry.register(RoleMaster)
