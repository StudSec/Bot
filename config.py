import os
config = dict(
    bot=dict(
        token=os.environ["DISCORD_TOKEN"],
        prefix="!"
    )
)

# Cleanup sensitive information
del os.environ["DISCORD_TOKEN"]
