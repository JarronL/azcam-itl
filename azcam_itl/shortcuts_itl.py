"""
*shortcuts* contains keyboard shortcuts for ITL systems.
"""


import azcam


def ws():
    """Shortcut to toggle webserver status logging to console."""

    old = azcam.db.tools["webserver"].logstatus
    new = not old
    azcam.db.tools["webserver"].logstatus = new
    print("webserver logststatus is now %s" % ("ON" if new else "OFF"))

    return


# add to shortcuts
azcam.db.shortcuts.update({"ws": ws})
