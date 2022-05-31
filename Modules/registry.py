"""
This code is responsible for keeping a registry of available modules.
"""

mods = []


def register(mod):
    mods.append(mod)
