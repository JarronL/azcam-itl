"""
*shortcuts* contains keyboard shortcuts for ITL systems.
"""

import azcam


def ws():
    """Shortcut to toggle webserver status logging to console."""

    old = azcam.db.webserver.logstatus
    new = not old
    azcam.db.webserver.logstatus = new
    print("webserver logststatus is now %s" % ("ON" if new else "OFF"))

    return


# add to cli
azcam.db.cli.update({"ws": ws})
