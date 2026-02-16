# VIDEO WALKTHROUGH SCRIPT - 5 MINUTES
# NYC Urban Mobility Explorer

## PREPARATION (Before Recording)
1. Close unnecessary browser tabs and applications
2. Open VS Code with project folder
3. Have DB Browser for SQLite ready with mobility.db open
4. Start backend: python backend\app.py
5. Start frontend: python -m http.server 8000 (in frontend folder)
6. Open http://localhost:8000 in browser
7. Test that everything works
8. Use OBS Studio, Loom, or Windows Game Bar (Win+G) to record

---

## SEGMENT 1: INTRODUCTION (0:00 - 0:30)

**SCREEN**: Show dashboard in browser

**SAY**:
"Hello, I'm presenting the NYC Urban Mobility Explorer, a full-stack web application that analyzes 7.4 million taxi trip records from New York City. This project demonstrates data cleaning, custom algorithm implementation, database design, and interactive visualizations to reveal urban transportation patterns."

**ACTION**: 
- Briefly scroll through dashboard showing charts and map
- Point to filter controls

---

## SEGMENT 2: DATA CLEANING CODE (0:30 - 1:30)

**SCREEN**: VS Code - open backend/scripts/clean_data.py

**SAY**:
"Let me show you the data processing pipeline. This script implements a 7-step cleaning process."

**ACTION**: Scroll through code and highlight:

**Line 27-29**: "Step 1 removes duplicates"

**Line 32-41**: "Step 2 drops missing critical fields like pickup time, location IDs, and fare amount"

**Line 48-50**: "Step 3 removes impossible timestamps where dropoff occurs before pickup"

**Line 52-60**: "Step 4 removes outliers - trips over 100 miles, fares over $500, and passenger counts over 6"

**Line 68-74**: "Step 5 validates location IDs against the zone lookup table"

**Line 82-90**: "Step 6 removes unrealistic durations under 1 minute or over 3 hours"

**Line 95-96**: "Step 7 removes impossible speeds over 80 mph"

**SAY**:
"The script also engineers 5 derived features: trip duration, speed, fare per mile, time of day categories, and weekend flags. All cleaning operations are logged for transparency."

**ACTION**: Show cleaning_log.txt briefly

---

## SEGMENT 3: CUSTOM ALGORITHM (1:30 - 2:30)

**SCREEN**: VS Code - open backend/algorithms.py

**SAY**:
"This is the custom min-heap algorithm I implemented to find the top 15 busiest zones without using built-in sorting functions."

**ACTION**: Scroll through code and highlight:

**Lines 1-23**: "The docstring explains the algorithm has O(n log k) time complexity, which is faster than SQL's O(n log n) ORDER BY when k is much smaller than n."

**Lines 25-42**: "The MinHeap class maintains a heap of size k. When we add a zone, if the heap isn't full, we insert it. If the zone is busier than our minimum, we replace the minimum and restore the heap property."

**Lines 44-52**: "The bubble-up method moves items up the heap"

**Lines 54-70**: "The bubble-down method moves items down to maintain the min-heap property"

**Lines 72-81**: "Finally, we manually sort the results without using Python's built-in sorted function"

**SAY**:
"This algorithm is connected to the top-zones API endpoint, replacing SQL ORDER BY with our custom implementation."

**ACTION**: Briefly show app.py line 95-130 where algorithm is used

---

## SEGMENT 4: DATABASE SCHEMA (2:30 - 3:15)

**SCREEN**: DB Browser for SQLite with mobility.db open

**SAY**:
"The database uses a normalized star schema with a dimension table and a fact table."

**ACTION**: 

**Click "Database Structure" tab**:
- Show "zones" table: "This is the dimension table with 263 records containing borough, zone name, and service zone"
- Show "trips" table: "This is the fact table with 7.4 million records. It has foreign keys to the zones table via pu_location_id and do_location_id"

**Click "Browse Data" tab**:
- Select "zones" table: "Here's the zone lookup data"
- Select "trips" table: "And here are the trip records with all our derived features"

**Click back to "Database Structure"**:
- Expand "trips" table indexes: "We have 4 indexes for query optimization: pickup_datetime, pu_location_id, do_location_id, and time_of_day"

**SAY**:
"This normalized design ensures data integrity and enables efficient JOIN queries."

---

## SEGMENT 5: LIVE DASHBOARD DEMO (3:15 - 4:30)

**SCREEN**: Browser with dashboard at http://localhost:8000

**SAY**:
"Now let me demonstrate the interactive dashboard with its professional orange and green design."

**ACTION**:

**Point to header**: "The dashboard features an orange header with the project title."

**Point to filters**: "Below are three filter dropdowns for Borough, Time of Day, and Hour, with an orange Apply Filters button and green Reset button."

**Point to summary cards**: "At the top we have summary statistics with orange borders: 7.4 million total trips, average fare of $12.16, average distance of 2.83 miles, and average speed of 11.7 mph."

**Scroll down**: "The dashboard features a clean white background with professional orange and green color scheme."

**Point to map section**: "On the left, we have the choropleth map showing trip distribution by zone."

**Point to fare chart**: "On the right, the Average Fare chart displays side-by-side with the map."

**Scroll to charts**: "Below, we have three more visualizations in a grid layout. All charts use consistent green coloring for data visualization:"

**Chart 1 - Trips by Hour**: "This green bar chart shows peak demand at 6-7 PM during evening rush hour, with a secondary peak at 9 AM. Notice the evening peak is 18% higher than morning, revealing concentrated office departure times."

**Chart 2 - Average Fare**: "This green line chart shows late-night trips between 2-5 AM have 50-67% higher fares due to longer distances and reduced transit alternatives."

**Chart 3 - Top Zones**: "This vertical green bar chart shows the busiest pickup zones, generated using our custom heap algorithm. Airport zones and Manhattan business districts dominate."

**Chart 4 - Borough Comparison**: "Manhattan accounts for over 90% of trips. This green bar chart shows the trip distribution across all five boroughs."

**Scroll to map**: "The choropleth map color-codes zones by trip volume. Darker red indicates higher activity. Notice the map has dark gray borders matching our design theme."

**ACTION**: Hover over Manhattan zones to show tooltips

**SAY**:
"Now let me demonstrate the filtering system."

**ACTION**:
- Select "Manhattan" from Borough dropdown
- Select "Evening" from Time of Day dropdown
- Click orange "Apply Filters" button
- Wait for charts to reload

**SAY**:
"Notice all charts update dynamically. The filters apply across all visualizations simultaneously, allowing us to analyze specific patterns like Manhattan evening rush hour."

**ACTION**: Click green "Reset" button to clear filters

---

## SEGMENT 6: TECHNICAL HIGHLIGHTS (4:30 - 5:00)

**SCREEN**: Split screen or quick cuts between VS Code and browser

**SAY**:
"To summarize the technical implementation:"

**ACTION**: Show quick flashes of:
- clean_data.py: "7-step data cleaning pipeline with transparency logging"
- algorithms.py: "Custom min-heap algorithm with O(n log k) complexity"
- database.py: "Normalized schema with 4 indexes"
- app.py: "7 RESTful API endpoints with dynamic filtering"
- Browser dashboard: "Interactive frontend with real-time visualizations"

**SAY**:
"This project demonstrates full-stack development skills, algorithmic thinking, database design, and the ability to extract meaningful insights from large datasets. The system successfully processes 7.4 million trip records to reveal urban mobility patterns that inform transportation policy and business decisions."

**SCREEN**: Show dashboard one final time

**SAY**:
"Thank you for watching."

---

## RECORDING TIPS

**Software Options**:
- OBS Studio (free, professional)
- Loom (easy, free for 5 min)
- Windows Game Bar (Win+G, built-in)
- Zoom (record yourself)

**Settings**:
- Resolution: 1920x1080 (1080p)
- Frame rate: 30 fps
- Audio: Clear microphone, no background noise
- Cursor: Make visible and slightly larger

**Best Practices**:
- Speak clearly and at moderate pace
- Practice once before final recording
- Use a script but sound natural
- Zoom in on code when needed (Ctrl + mouse wheel)
- Keep mouse movements smooth
- Pause briefly between segments
- If you make a mistake, pause 3 seconds and restart that sentence (easy to edit)

**Editing** (Optional):
- Use DaVinci Resolve (free) or Windows Video Editor
- Cut out long pauses
- Add title slide at start
- Add "Thank you" slide at end
- Export as MP4

**Upload**:
- YouTube (unlisted or public)
- Google Drive (set to "Anyone with link can view")
- Loom (generates link automatically)

**Add Link to README**:
Replace `[Add your video link here]` with your actual video URL

---

## BACKUP PLAN (If Something Breaks During Recording)

**If backend crashes**: 
- Say "Let me restart the backend server"
- Restart and continue

**If charts don't load**:
- Say "The system is processing 7.4 million records"
- Wait 5 seconds
- If still broken, show static screenshots from docs

**If you forget what to say**:
- Pause, take a breath
- Say "As you can see here..." and continue

**If time runs over 5 minutes**:
- Skip the detailed code walkthrough in Segment 2
- Just show the file and say "This implements the 7-step cleaning pipeline"
- Focus more on the live demo

---

## CHECKLIST BEFORE RECORDING

□ Backend running (python backend\app.py)
□ Frontend running (python -m http.server 8000)
□ Dashboard loads at http://localhost:8000
□ All charts display correctly
□ Filters work when tested
□ DB Browser has mobility.db open
□ VS Code has project open
□ All files mentioned in script are easy to access
□ Recording software tested
□ Microphone tested
□ No notifications will interrupt (turn on Do Not Disturb)
□ Browser bookmarks bar hidden (Ctrl+Shift+B)
□ Desktop clean (close unnecessary windows)

---

## AFTER RECORDING

1. Watch the video once
2. Check audio quality
3. Verify all segments are visible
4. Upload to YouTube/Drive/Loom
5. Get shareable link
6. Add link to README.md
7. Test link works (open in incognito)
8. Submit project
