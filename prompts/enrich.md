Using the provided IMDb list export, produce a csv with the following fields for each video in the list:  

- year: the release year of the video
- artist: artist credit
- title: the track title
- album: album which the track appears on
- label: record label, normalized to direct label for filtering.
- genre: primary genre of the track, normalized to broad genres such as Hip Hop/R&B, Rock, Pop, Metal, or Country.
- director: if available from the IMDb list. If this is not available, leave the field empty.
- tag: If the release year of the video was 1990-1999, use "90s", if 1980-1989, "80s", 2000-2009, "00s".
- youtube_url: a YouTube URL for the video. Channel/uploader preference order: artist or label, then an official source such as VEVO, then any uploader. Provide plain text URLs.
- youtube_channel: the name of the source channel or uploader which matches the youtube_url.

Use the field names exactly as written above. Fetch all data using IMDb's API and other sources as required.
Produce the first 20 fully enriched rows in chat for review, then continue processing 20 rows at a time.
The final deliverable is a complete enriched dataset, as a downloadable .csv file, containing all 100 entries.

Prioritize accuracy. Begin processing now and deliver the report when ready.
