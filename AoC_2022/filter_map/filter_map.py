#!/usr/bin/env python3


import sys
import math
import random
import json
import datetime
import matplotlib.pyplot as P


DARK = True

# Color constants
if DARK: 
    RED  = "#404040"
    GREY = "#008080"
    BLUE = "#404040"
    TEXT = "#ffffff"
    TEXT_GREY = "#dfdfdf"
    BACKGROUND = "#000810"

else:
    RED  = "#bf0000"
    GREY = "#bfbfbf"
    BLUE = "#40bfbf"
    TEXT = "#000000"
    TEXT_GREY = "#606060"
    BACKGROUND = "#ffffff"


# Default options
OPTS = {
    "day_min": 1, # First day of the event
    "days_total": 25, # Last day of the event
    "days_passed": 25, # How many days have passed?
    "figure_size": (26,13), # Size of figure measured in bananas
    "display_names": True, # Whether to display names
    "figure_title_override": None, # Overrides the figure title
    "display_percentage": True, # Whether to display filtering stats on top
    "order_mode": "id1000", # How to order the users
    "time_limit": math.inf, # Sets a time limit for the puzzles 
            # (in seconds, command line arg in hours)
}

DELTA = 0.15 # X-offset of filter lines



def main():
    input_filenames = getOptions()
    members, event = readData(input_filenames)
    filtered_by_day = getMemberProgress(members, event)
    orderMembers(members)

    plotInit(event)
    plotLines(members)
    plotEndPoints(members)
    plotStats(members, filtered_by_day)

    # P.show()
    P.savefig("tgf.png", bbox_inches="tight", dpi=100)
    

def getOptions():
    """
    Overwrites the OPTS table with whatever options are set by sys.argv.
    Also returns a list of input filenames.
    """
    input_filenames = ["a.json"]
    # Override options from args
    for a in sys.argv[1:]:
        if a.startswith("-d"):
            OPTS["days_passed"] = int(a[2:])
        elif a.startswith("-t"):
            OPTS["days_total"] = int(a[2:])
        elif a.startswith("-s"):
            w,h = a[2:].split('x')
            OPTS["figure_size"] = (float(w), float(h))
        elif a.startswith("-o"):
            m = a[2:]
            if m == "i":
                OPTS["order_mode"] = "id"
            elif m == "g":
                OPTS["order_mode"] = "global"
            elif m == "l":
                OPTS["order_mode"] = "local"
            elif m == "p":
                OPTS["order_mode"] = "progress"
            elif m == "s":
                OPTS["order_mode"] = "stars"
            elif m == "m":
                OPTS["order_mode"] = "magic"
            else:
                raise Exception("Unknown order mode")
        elif a == "-n":
            OPTS["display_names"] = False
        elif a == "-p":
            OPTS["display_percentage"] = False
        elif a.startswith("-i"):
            OPTS["day_min"] = int(a[2:])
        elif a.startswith("-l"):
            # Entered in hours
            OPTS["time_limit"] = float(a[2:]) * 3600
        elif a.startswith("-T"):
            OPTS["figure_title_override"] = a[2:]
        else:
            # Filename, can be multiple
            input_filenames.append(a)
    return input_filenames




def readData(input_filenames):
    """
    Reads data from the input files.
    """
    print("Reading data")
    members = {}

    for filename in input_filenames:
        with open(filename) as f:
            data = json.loads(f.read())
        members.update(data["members"])

    filtered_members = {}
    for member, item in members.items():
        if item["stars"] != 0:
            filtered_members[member] = item
        
    event = data["event"]

    return filtered_members, event



def plotInit(event):
    """
    Set some main figure stuff.
    """

    # Set figure title
    if OPTS["figure_title_override"] is not None:
        figure_title = OPTS["figure_title_override"]
    else:
        figure_title = f"THE GREAT FILTER {event}"

    # Set figure size
    P.figure(figsize=OPTS["figure_size"])
    # Set colors
    if DARK:
        P.style.use("dark_background")
    ax = P.axes()
    ax.set_facecolor(BACKGROUND)
    # Limits
    P.xlim([-1, OPTS["days_total"]+2])
    P.ylim([-0.05, 1.065])
    P.title(figure_title, fontdict={'fontsize': 36})
    # Label 1-25
    P.xticks(range(1, OPTS["days_total"]+1))
    P.tick_params(axis="x", bottom=True, top=True, labelbottom=True, labeltop=True)

    # Hide y-axis labels
    ax = P.gca()
    ax.axes.yaxis.set_visible(False)

    # Draw filter lines
    for day in range(1, OPTS["day_min"]):
        P.axvline(day - DELTA, color=GREY)
        P.axvline(day + DELTA, color=GREY)
    for day in range(OPTS["day_min"], OPTS["days_passed"] + 1):
        P.axvline(day - DELTA, color=RED)
        P.axvline(day + DELTA, color=RED)
    for day in range(OPTS["days_passed"] + 1, OPTS["days_total"] + 1):
        P.axvline(day - DELTA, color=GREY)
        P.axvline(day + DELTA, color=GREY)



def getMemberProgress(members, event):
    """
    Get progress info for every member.
    Sets the "progress", "progress_exact" and "filtered" fields.
    Returns a filtered_by_day dict. 
    """
    # Start time of first puzzle (2020-12-01 05:00 UTC)
    # TODO probably different for different timezones
    # This is only really relevant if a time limit is set.
    event_start_time = datetime.datetime(int(event), 12, 1, 6).timestamp()

    # Init filtered_by_day structure
    filtered_by_day = {}
    for i in range(1, OPTS["days_total"] + 1):
        filtered_by_day[i] = 0

    # Get filtered_by values for each member
    print("Determining progress")
    for member in members.values():
        completion_data = member["completion_day_level"]

        # A member is filtered the first day without star
        # or if time_limit is enabled, the first star not gotten within 
        # this time limit
        filtered = False
        progress = OPTS["days_total"] + 2
        progress_exact = progress

        def randDelta(delta):
            return random.random() * delta * 2 - delta

        for day in range(OPTS["day_min"], OPTS["days_total"] + 1):
            day_str = str(day)
            time1, time2 = None, None
            start_time = event_start_time + (86400 * (day - 1))

            if day_str in completion_data:
                day_data = completion_data[day_str]
                if "1" in day_data:
                    time1 = int(day_data["1"]["get_star_ts"])
                if "2" in day_data:
                    time2 = int(day_data["2"]["get_star_ts"])

            pass1 = (time1 is not None and 
                    time1 - start_time <= OPTS["time_limit"])
            pass2 = (time2 is not None and 
                    time2 - start_time <= OPTS["time_limit"])

            if not pass1:
                # Filtered by part 1
                filtered_by_day[day] += 1
                if day <= OPTS["days_passed"]:
                    filtered = True
                    progress = day - DELTA
                    progress_exact = progress
                else:
                    progress = day - 0.5 + randDelta(0.15)
                    progress_exact = day - 0.5
                break

            if not pass2:
                # Filtered by part 2
                filtered_by_day[day] += 1
                if day <= OPTS["days_passed"]:
                    filtered = True
                    progress = day + DELTA
                    progress_exact = progress
                else:
                    progress = day + randDelta(0.05)
                    progress_exact = day
                break
            
        member["progress"] = progress
        member["progress_exact"] = progress_exact
        member["filtered"] = filtered

    return filtered_by_day



def orderMembers(members): 
    """
    Returns the members_ordered list, ordering members by whatever key we've chosen.
    Sets the "y" field of the members.
    """
    if OPTS["order_mode"] in ["id1000", "magic"]:
        order_func = lambda m : int(m["id"]) % 1000
    elif OPTS["order_mode"] == "id":
        order_func = lambda m : int(m["id"])
    elif OPTS["order_mode"] == "global":
        order_func = lambda m : m["global_score"]
    elif OPTS["order_mode"] == "local":
        order_func = lambda m : m["local_score"]
    elif OPTS["order_mode"] == "progress":
        order_func = lambda m : m["progress_exact"]
    elif OPTS["order_mode"] == "stars":
        order_func = lambda m : m["stars"]
    members_ordered = sorted(members.values(), key=order_func)
    for i, member in enumerate(members_ordered):
        member["y"] = (i+1)/len(members)

    # Recompute magic order numbers for the unfiltered, to prevent names from overlapping
    if OPTS["order_mode"] == "magic":
        ms = [m for m in members.values() if not m["filtered"]]
        ms = sorted(ms, key=lambda m : int(m["id"]) % 1000)
        if len(ms) != 0:
            dy = 1.0/len(ms)
            offset = random.random() % dy
            for i,m in enumerate(ms):
                m["y"] = offset + i * dy + random.uniform(-dy/4, dy/4)


def plotLines(members):
    """
    Draw wavy lines.
    Also adds the "end_pos" field to each member.
    """
    print("Plotting lines")
    for member in members.values():
        progress = member["progress"]
        filtered = member["filtered"]
        line_color = GREY
        if not filtered: 
            line_color = BLUE

        N = 100
        values_x = [i/N for i in range(-1*N, int(progress * N))]
        offset_x = random.random() * 100
        offset_y = member["y"]

        def f(x, ox, oy):
            return oy + 0.01 * math.sin(x + ox) 
        
        offset_y -= f(progress, offset_x, offset_y) - offset_y
        values_y = [f(x, offset_x, offset_y) for x in values_x]
        P.plot(values_x, values_y, '-', linewidth=1.0, color=line_color, alpha=0.7)
        member["end_pos"] = (progress, f(progress, offset_x, offset_y))



def plotEndPoints(members):
    """
    Draw end dot and labels.
    """
    print("Plotting dots/labels")
    for member in members.values():
        filtered = member["filtered"]
        x, y = member["end_pos"]
        #if filtered:
        #    P.plot([x], [y], 'or')

        if OPTS["display_names"]:
            name = member["name"]
            if name is None:
                name = member["id"]
            color = TEXT
            if filtered: 
                color = TEXT_GREY
            if filtered or x >= OPTS["days_total"]+1:
                align = "center"
                x -= 0.1
            else:
                align = "left"
                x += 0.1
            P.annotate(name, (x,y), horizontalalignment=align, color=color, size=8)


def plotStats(members, filtered_by_day):
    """
    Plot the stats on top of the graph.
    """
    # Compute number of unfiltered members per day
    remaining_by_day = {}
    remaining = len(members)
    remaining_by_day[0] = remaining
    for i in range(1, OPTS["days_total"] + 1):
        filtered = filtered_by_day[i]
        remaining = remaining - filtered
        remaining_by_day[i] = remaining

    # Draw user counts
    for i in range(1, OPTS["days_passed"] + 1):
        if remaining_by_day[i-1] == 0:
            continue
        pass_frac = remaining_by_day[i] / remaining_by_day[i-1]
        percent_filtered = 100 * (1.0-pass_frac)
        total_frac = remaining_by_day[i] / remaining_by_day[0]
        percent_total = 100 * total_frac
        print(f"day {i:2d}: {remaining_by_day[i-1] - remaining_by_day[i]:3}" +
            f"/{percent_filtered:5.1f}% filtered ({percent_total:2.0f}%" +
            " of total remaining)")
        if OPTS["display_percentage"] and pass_frac != 1.0:
            P.annotate(f"-{percent_filtered:.0f}%", (i,1.05), horizontalalignment="center", size=8)

    # Draw percentages
    if OPTS["display_percentage"]:
        for i in range(0, OPTS["days_passed"] + 1):
            P.annotate(f"{remaining_by_day[i]}", (i+0.5,1.04), horizontalalignment="center", size=8)




main()
