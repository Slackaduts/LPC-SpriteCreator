This is intended as a standalone program for randomly generating LPC spritesheets.


Adjusting generation settings:
    Paths in the GUI describe the folder structure of the spritesheets folder, so paths like /hair/bob must point to an actual folder within /spritesheets.

    For the variant black/whitelists, these are dictionaries using the name of a json file in /sheet_definitions as keys.
    The values are a list of the desired variants to force or blacklist.

    Keep in mind when messing with either of these settings that crashes may occur, as the LPC spritesheet resources/database aren't perfect, and neither is my JSON file describing folder correlations.

How to generate sprites:
    Once the settings are how you'd like, you can generate without saving them by clicking the "Preview" button.
    To save the current preview, click the "Save" button.

    To generate many sprites, enter how many you wish to generate into the "Amount:" field and click "Generate".

    The "Prefix:" field gives the filename a prefix when it is saved, useful for animation/sprite systems like QSprite.

Everything else is fairly self explanatory, this tool isn't perfect and I probably won't do more than resource updates to it.
I hope this saves you as much time on your game project as it will for mine. Cheers.