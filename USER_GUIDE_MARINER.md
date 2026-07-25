# Vessel Agent System - Captain & Crew User Guide

**Vessel:** F/V EILEEN
**Home Port:** Southeast Alaska
**Primary Fishery:** Power Trolling
**System Version:** 1.0 (Phase 0 - Data Capture)

---

## A Note from the Captain

You've spent years learning to read the water, understanding how tides, temperatures, and structure move fish through your fishing grounds. You know that spot off Cape Decision that fires when the flood hits 45 feet, and you know how the chum stack up differently in July versus September.

This system isn't here to replace any of that knowledge. It's here to capture it, build on it, and help you see patterns you might miss in the moment.

Think of this as another tool in your wheelhouse—like your Furuno sounder or your GPS plotter. You wouldn't head out without your depth sounder, and you wouldn't steam to the grounds without checking your charts. The vessel agent system is the same: it's another data source that helps you make better decisions on the water.

**What this system does:**
- Captures what your sounder sees, every ping, tied to exactly where you were
- Records how you were fishing (speed, depth, direction) when you found fish
- Learns from your successes over days, weeks, and seasons
- Helps you see patterns across your entire fishing history

**What this system doesn't do:**
- Tell you how to fish
- Replace your judgment on the water
- Make decisions for you

Your experience and intuition are still the most sophisticated system on this boat. The vessel agent is just there to back you up with data.

---

## Part 1: Getting Started - What This System Actually Is

### The Problem This Solves

You've been there: You're trolling along, watching the echogram, seeing marks come and go. Three hours later, you're wondering, "Where exactly were we when we saw that good school of chum? How deep was the gear? What was the tide doing?"

Or you come back to a spot that's been good in previous years, but you're trying to remember—was it August 15th or August 22nd last year when they stacked up here? Was the flood stronger or weaker?

This system captures all that, continuously, in the background, so you can focus on fishing instead of trying to remember details.

### How It Works: The Non-Technical Explanation

Your Furuno sounder sends out a ping, listens for the echo, and displays it on the screen. This system taps into that same data stream, but instead of just showing it on the screen, it:

1. **Records the ping** - Every depth reading from top to bottom
2. **Marks the location** - Ties it to your GPS position at that exact moment
3. **Saves the conditions** - Water temp, boat speed, heading, tide phase
4. **Stores it all** - Organized so you can pull it up later

Think of it like a deckhand who never sleeps, writing down everything that happens on the sounder and where you were when it happened.

### What Equipment It Talks To

**Primary Connections:**
- **Furuno Sounder** - Reads the echogram data directly
- **GPS** - Records position, speed, and heading
- **NMEA Network** - Pulls in water temp, depth, and other sensors

**Integration:**
- **TimeZero Professional** - Works alongside your existing chartplotter
- **Existing Sounder Display** - Your normal echogram doesn't change

---

## Part 2: Daily Operations - From Dock to Fishing Grounds

### Pre-Trip Checklist (5 Minutes)

Before you leave the dock:

**1. System Check**
```bash
# From the wheelhouse computer, open a command prompt and run:
python capture_daemon.py doctor
```

What you should see:
```
✓ Configuration valid
✓ Archive path: C:\data\vessel_agent\archive
✓ Log path: C:\data\vessel_agent\logs
✓ All validation checks passed
```

If you see red X's instead of green checkmarks, call your technical contact before heading out.

**2. Storage Check**
- Make sure you have at least 10 GB free space on the wheelhouse computer
- A full day of fishing creates about 2-3 GB of data

**3. Start the System**
```bash
python capture_daemon.py run
```

You should see:
```
Starting capture daemon...
Daemon started at 2026-07-25T04:30:00
Capturing... (Ctrl+C to stop)
```

That's it. The system is now running in the background, capturing everything.

### During the Trip - What You'll See

The system runs quietly in the background. You don't need to interact with it while fishing—it's just recording continuously.

**What's Being Captured:**
- Every ping from your sounder
- Your position, speed, and heading
- Water temperature and depth
- When you change course or speed
- When you deploy or haul back gear

**What You Need to Do:**
Nothing. Just fish like you normally would.

**Crew Communication**

When you're marking fish and want to make sure the system captures that moment for later analysis, you can say something like:

*"Good marks right here, 35 fathoms, flood tide coming on."*

The system doesn't record voice (yet), but when you review the data later, you'll be able to see exactly where you were and what the sounder showed when you made that comment. It's a way to mentally bookmark moments.

### Post-Tip Procedures (10 Minutes)

When you return to the dock:

**1. Stop the System**
```bash
python capture_daemon.py stop
```

You should see:
```
Stopping capture daemon...
Daemon stopped at 2026-07-25T18:00:00
Uptime: 49200.5 seconds (13.7 hours)
  Cycles: 734,821
  Packets processed: 734,821
  Storage flushes: 7,348
```

**2. Quick Health Check**
Look for these key numbers:
- **Uptime** - Should match your time on the water (within 10%)
- **Packets processed** - Should be in the hundreds of thousands for a full day
- **No error messages** - If you see errors, note them for troubleshooting

**3. Data Review**
The system automatically organizes data by day. You can review today's capture by checking:
```
C:\data\vessel_agent\archive\year=2026\month=07\day=25\
```

You don't need to do anything with this data yet—it's just good to know it's there.

---

## Part 3: Understanding Your Equipment Integration

### Working Alongside Your Furuno Sounder

Your Furuno DFF3-UHD (or similar) continues to work exactly as it always has. The vessel agent taps into the network data that's already flowing between your sounder and your display.

**What Changes:**
- Nothing. Your display, gain settings, range—all work exactly the same

**What's Added:**
- Every ping is now recorded with position and time
- You can go back and see what the sounder showed at any moment during any trip

### GPS Integration

The system pulls GPS data from your NMEA network—the same data your chartplotter uses. It does this through:

1. **Serial Connection** - Direct connection to your GPS output (COM port)
2. **Network Connection** - Reads NMEA sentences from your network

**What Gets Captured:**
- Position (latitude/longitude)
- Speed over ground
- Heading (true and magnetic)
- GPS fix quality (number of satellites, accuracy)

**Why This Matters:**

When you're reviewing data later, you'll be able to see exactly where you were when you saw particular marks. The system uses "dead reckoning" to fill in between GPS updates, so even though your GPS updates once per second, the system knows where you were for every single sounder ping (15 times per second).

### NMEA Network Sensors

If you have additional sensors on your NMEA network:

**Water Temperature:**
- Recorded continuously
- Helps explain fish distribution patterns
- Correlates with catch data over seasons

**Depth Sensors:**
- Bottom depth recorded continuously
- Helps identify productive structure
- Builds a database of good bottom types for your fisheries

**Heading/Compass:**
- Records course over ground and heading
- Helps understand troll direction vs. fish location
- Useful for pattern recognition

---

## Part 4: Troubleshooting at Sea

### Common Issues and Quick Fixes

**Problem: System won't start**

**Symptoms:**
- Error message when running `python capture_daemon.py run`

**Quick Check:**
1. Is the wheelhouse computer turned on?
2. Is the GPS working? (Check your chartplotter)
3. Is the sounder working? (Check your echogram display)

**Solution:**
- If GPS and sounder are working normally, try restarting the capture daemon:
```bash
python capture_daemon.py doctor  # Check for errors
python capture_daemon.py run     # Start again
```

**Problem: No data being captured**

**Symptoms:**
- System appears to run, but packet count isn't increasing
- No files created in archive directory

**Quick Check:**
1. Check network connection between sounder and wheelhouse computer
2. Verify GPS is outputting NMEA data
3. Check available disk space

**Solution:**
- Most common issue: Network cable loose or disconnected
- Check the ethernet connection from your Furuno network hub
- If that's secure, restart the system and watch for error messages

**Problem: System using too much computer resources**

**Symptoms:**
- Wheelhouse computer running slowly
- Chartplotter lagging

**Solution:**
- The system is designed to use minimal resources (<50% CPU, <4GB RAM)
- If it's using more, stop the system and restart:
```bash
python capture_daemon.py stop
python capture_daemon.py run
```
- If problem persists, note the CPU/memory usage for troubleshooting

### When to Call for Technical Support

Some issues require expert help. Contact technical support if:

1. **System crashes repeatedly** - Won't stay running for more than a few minutes
2. **Data corruption** - Error messages about corrupted files
3. **Hardware conflicts** - Chartplotter or sounder not working properly
4. **Disk space issues** - System filling up disk too quickly

**Information to Have Ready:**
- Exact error messages
- How long the system was running
- What you were doing when the problem occurred
- Whether GPS, sounder, and chartplotter were working normally

---

## Part 5: Reading Your Data - Making It Useful

### Daily Review - Learning from Today

At the end of a fishing day, you can review what the system captured. This is useful for:

**Pattern Recognition:**
- "We found fish at 35 fathoms on the flood—where else did we see marks at that depth?"
- "The water temp was 48°F when we started catching—did it change when the bite shut off?"

**Location Memory:**
- "Exact position where we saw that big school—let's start there tomorrow"
- "Track line for our best troll pattern today"

**Quick Review Steps:**
1. Stop the capture daemon (as in Post-Trip Procedures)
2. Open the archive directory for today's date
3. Data files are organized by hour—browse to see what was captured

### Weekly Patterns - Seeing the Bigger Picture

After a week of fishing, you can start seeing patterns:

**Tide and Timing:**
- Do fish show up at certain tide phases more than others?
- Is there a time-of-day pattern you hadn't noticed?

**Depth Consistency:**
- Are you consistently finding fish at particular depth ranges?
- Does that change with water temperature?

**Location Reliability:**
- Which spots produce consistently vs. occasionally?
- What conditions make the difference?

The system doesn't automatically answer these questions yet—that's coming in future versions. But having the data recorded means you can go back and investigate.

### Seasonal Intelligence - The Long View

Over a full season, the data becomes incredibly valuable:

**Migration Timing:**
- When did fish first show up in your usual spots?
- How did that compare to previous years?
- Did water temperature affect arrival timing?

**Depth Shifts:**
- How did preferred depth change through the season?
- Did that correlate with water temperature changes?
- What about light levels or tide strength?

**Spot Productivity:**
- Which spots were reliable all season?
- Which were hit-or-miss?
- What made the difference?

This is where the system really pays off—it remembers everything, so you don't have to rely on memory or incomplete logbooks.

---

## Part 6: Crew Integration - Training Your Deckhand

### Getting Your Crew On Board

Your crew is your biggest asset in making this system successful. A deckhand who understands the system can:

- Help troubleshoot issues on the water
- Notice when something isn't working right
- Use the data to improve fishing success

### Training Checklist for New Crew

**Day 1: Basic Awareness**
- [ ] Explain what the system does and why it matters
- [ ] Show where the wheelhouse computer is
- [ ] Demonstrate starting/stopping the capture daemon
- [ ] Explain that it runs in the background—no interaction needed while fishing

**Day 2: Understanding the Equipment**
- [ ] Show how the system connects to Furuno sounder
- [ ] Explain GPS integration
- [ ] Point out NMEA network connections
- [ ] Discuss what data is being captured

**Day 3: Basic Troubleshooting**
- [ ] Practice starting the system
- [ ] Practice stopping the system
- [ ] Review common issues and quick fixes
- [ ] Explain when to call for technical support

**Ongoing: Pattern Recognition**
- [ ] Discuss what the system is capturing during fishing
- [ ] Point out interesting moments (good marks, temperature changes)
- [ ] Encourage crew to notice correlations
- [ ] Use the data for crew discussions about strategy

### Shared Understanding - Building Crew Knowledge

The best fishing operations have a crew that thinks together. This system can help build that shared understanding:

**Morning Briefings:**
- Review yesterday's data briefly
- Point out patterns noticed
- Plan today's fishing with yesterday's insights in mind

**On the Water:**
- Call out interesting moments ("Good marks here—system is capturing this")
- Note conditions when fish are found
- Build shared mental models of what works

**End of Day:**
- Quick review of what the system captured
- Discuss patterns noticed
- Plan for tomorrow

---

## Part 7: Practical Fishing Applications

### Pattern Recognition for Fishing Spots

**Scenario:** You're trolling a familiar spot and see good marks. In the past, you'd note it mentally and maybe mark a waypoint on the chartplotter.

**With the System:**
1. The system captures the exact acoustic signature
2. It records the precise location and depth
3. It notes the tide phase, water temp, and troll direction
4. It saves this moment forever

**How to Use It:**
- Next time you approach this spot, review previous success data
- Check if conditions are similar (tide, temp, season)
- Start your troll pattern based on what worked before
- Compare what you're seeing now to what worked in the past

### Seasonal Migration Tracking

**Scenario:** You're wondering when the chum typically show up at your favorite spot off Cape Decision.

**With the System:**
- Query the data for that location across all dates
- See when you first started seeing marks each year
- Correlate with water temperature and tide patterns
- Plan your season timing accordingly

**Practical Application:**
- "The data shows chum typically arrive here when water temp hits 48°F"
- "Last three years, best fishing was July 20-25 at this spot"
- "Let's focus our effort here during that window this year"

### Depth/Temp/Tide Correlations

**Scenario:** You're catching consistently at 35 fathoms on the flood, but you're wondering if that pattern holds across other spots.

**With the System:**
- Query all your catch data across all spots
- Look for depth patterns that correlate with success
- Check if tide phase matters at different locations
- See if water temperature affects preferred depth

**Practical Application:**
- "Across all spots, 35 fathoms on flood is most productive"
- "But when water temp is below 46°F, fish move shallower"
- "Adjust troll depth based on temperature, not just spot"

### Fleet Intelligence Sharing

**Future Capability:** When multiple vessels are using this system, you can share insights without sharing exact spots:

**Collaborative Learning:**
- "Fleet reports: Chum showing at 30-40 fathoms when water temp 48-50°F"
- "Bite window starting 2 hours after flood slack"
- "Thermocline depth affecting distribution—adjust accordingly"

**Privacy Protected:**
- Your exact waypoints stay private
- You share patterns, not spots
- Learn from fleet without giving up your secret honey holes

---

## Part 8: System Maintenance - Keeping It Running

### Weekly Maintenance Tasks (5 Minutes)

**1. Check Disk Space**
- Make sure you have at least 20 GB free
- The system will automatically delete oldest data if space gets tight
- But it's better to archive important data manually

**2. Review System Logs**
```bash
# Check for any errors or warnings
type C:\data\vessel_agent\logs\*.log | findstr /i "error warning"
```

**3. Backup Important Trips**
- If you had a particularly good trip, consider backing up that data
- Copy the day's directory to external storage or cloud

### Monthly Maintenance Tasks (15 Minutes)

**1. Full System Health Check**
```bash
python capture_daemon.py doctor
```

**2. Archive Cleanup**
- Delete data from trips that weren't productive (if you want)
- Keep at least one full season of data for pattern recognition

**3. Software Updates**
- Check for system updates (your technical contact will notify you)
- Updates may include new features, bug fixes, or performance improvements

### Annual Maintenance Tasks (1 Hour)

**1. Full Season Archive**
- Backup the entire season's data to external storage
- This is your fishing history—protect it
- Consider keeping multiple backup copies

**2. Off-Season Review**
- Spend time reviewing the season's data
- Look for patterns you missed during the busy season
- Plan for next year based on what you learned

**3. System Updates**
- Major updates typically happen in the off-season
- Plan for system downtime during maintenance windows

---

## Part 9: Success Stories - Real-World Examples

### Story 1: The Thermocline Pattern

**The Situation:**
Captain noticed fish were consistently at 35 fathoms in early July, but by late July they seemed to disappear. He couldn't figure out where they went.

**What the Data Revealed:**
- Reviewing the acoustic data showed fish weren't gone—they'd moved deeper
- The thermocline had dropped 15 fathoms over three weeks
- Fish were still there, just 50 fathoms down instead of 35

**The Result:**
- Captain adjusted his gear depth based on thermocline position
- Caught fish consistently through late July when other boats were struggling
- Learned to check sounder for thermocline before setting gear depth

### Story 2: The Tide Window

**The Situation:**
Captain always thought the flood was best for fishing, but some days produced nothing while other days were excellent.

**What the Data Revealed:**
- It wasn't just tide phase—it was tide strength
- Strong flood (spring tides) pushed fish into rocky areas where gear would hang up
- Moderate flood (neap tides) kept fish in open water where they were catchable

**The Result:**
- Captain checks tide tables for strength, not just timing
- Focuses effort on moderate tide days
- Avoids certain spots during strong tides

### Story 3: The Temperature Correlation

**The Situation:**
Captain had a spot that produced well in July but not in August. He thought the fish had moved on.

**What the Data Revealed:**
- The spot was productive when water temperature was 48-50°F
- In August, temperature warmed to 53-54°F
- Fish were still there, but deeper and less active

**The Result:**
- Captain now checks temperature before fishing that spot
- If temp is in the productive range, he focuses there
- If temp is too warm, he adjusts tactics or moves to different areas

---

## Part 10: Looking Ahead - What's Coming

### Near-Term Improvements (Next 6 Months)

**Visual Data Review:**
- View your acoustic data on a map overlay
- Scrub through time to see what your sounder showed at any moment
- Compare multiple trips side-by-side

**Automatic Pattern Detection:**
- System highlights patterns it notices
- "You consistently find fish at this depth in these conditions"
- "This spot produces best on flood tide"

**Voice Annotations:**
- Record voice notes that sync with data capture
- "Good marks here—note this moment"
- Easy mental bookmarking for later review

### Long-Term Vision (Next 2-3 Years)

**Species Identification:**
- System learns to identify fish species from acoustic signatures
- "Those are chum marks at 35 fathoms"
- "That's a school of herring below us"

**Catch Prediction:**
- Based on conditions and location, predict likelihood of success
- "80% chance of chum encounter here in current conditions"
- Helps prioritize where to focus effort

**Fleet Intelligence:**
- Share patterns with other vessels (without sharing spots)
- Learn what's working across the fleet
- Collaborative intelligence while protecting competitive advantage

---

## Part 11: Technical Support and Resources

### When You Need Help

**For Technical Issues:**
- System crashes, errors, or hardware problems
- Contact: [Your Technical Support Contact]
- Include: Error messages, what you were doing, system status

**For Usage Questions:**
- How to interpret data, how to use features
- Contact: [Your System Administrator]
- Include: What you're trying to do, what you've tried

**For Feature Requests:**
- Ideas for improvements or new capabilities
- Contact: [Your System Developer]
- Include: What would help you fish better

### Quick Reference Card

**Start System:**
```bash
python capture_daemon.py run
```

**Stop System:**
```bash
python capture_daemon.py stop
```

**Check Health:**
```bash
python capture_daemon.py doctor
```

**Data Location:**
```
C:\data\vessel_agent\archive\year=YYYY\month=MM\day=DD\
```

**Key Files:**
- `capture_daemon.py` - Main system program
- `config.py` - System configuration
- `logs/` - System logs and error messages

### Emergency Procedures

**System Stops Working Mid-Trip:**
1. Don't panic—your regular electronics still work
2. Try restarting the capture daemon
3. If it won't restart, continue fishing and note the issue for troubleshooting
4. Your fishing day isn't ruined—this is just one tool among many

**Computer Crashes Completely:**
1. Your regular electronics (GPS, sounder, chartplotter) are independent
2. Restart the computer
3. Restart the capture daemon
4. If it keeps crashing, contact technical support after the trip

---

## Part 12: Glossary - Plain English Definitions

**Acoustic Data:** What your sounder "sees"—echoes returned from the water column, showing fish, bottom, and other objects

**Backscatter:** The reflected sound energy that creates the display on your echogram

**Dead Reckoning:** Estimating position between GPS updates based on speed and heading

**Echogram:** The display on your sounder showing depth and marks over time

**Furuno Sounder:** Your fish finder—sends sound pings and displays the echoes

**GPS (Global Positioning System):** Satellite navigation that provides position, speed, and heading

**H3 Index:** A way to divide the ocean into small grid cells for organizing data (like a specialized version of latitude/longitude)

**NMEA (National Marine Electronics Association):** Standard language for marine electronics to talk to each other

**Network Packet:** Data traveling between your sounder and display—what the system captures

**Parquet:** A file format for storing data efficiently (like a specialized ZIP file)

**Ping:** One sound pulse sent by your sounder and the echo that returns

**Spatial Index:** A way to organize data by location for easy retrieval

**Thermocline:** A layer in the water column where temperature changes rapidly—often where fish congregate

**Waypoint:** A saved GPS position marking a spot

---

## Final Thoughts

This system is a tool, not a replacement for your expertise. The best fishing captains combine their experience with every available tool—their eyes, their ears, their electronics, and now their data.

Your judgment on the water is still the most sophisticated system you have. This vessel agent system is just there to back you up with data, help you remember what worked, and help you see patterns you might otherwise miss.

Fishing is still about skill, patience, and being on the water. This system just helps you remember everything you learn while you're out there.

**Good fishing, and tight lines.**

---

**Document Version:** 1.0
**Last Updated:** July 25, 2026
**Vessel:** F/V EILEEN
**System Version:** 1.0 (Phase 0)

**For questions or support, contact:**
[Your Technical Support Contact]
[Your System Administrator]
[Your System Developer]
