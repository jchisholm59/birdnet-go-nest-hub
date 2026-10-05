# BirdNET-Go → Google Nest Hub

A Home Assistant automation that shows every [BirdNET-Go](https://github.com/tphakala/birdnet-go) detection on a
Google Nest Hub: the bird's photo, common name, scientific name and confidence, for 30 seconds (or 1 or 5 minutes, or
until the next bird), then back to the clock. Optionally it says "American Crow heard, 92 percent sure" first, and plays
BirdNET-Go's own recording of the call, briefly louder than the Hub's everyday volume. All of it is set from one
dashboard card, so the household isn't narrated every time a crow calls.

It should work on any Google Cast display Home Assistant can see (Nest Hub / Hub Max, Lenovo Smart Display/Clock,
Chromecast with a TV). Voice-only speakers get just the spoken part.

BirdNET-Go's models know a few non-birds too. Ours shows the odd **coyote**, which the cats find very interesting.

Optionally it also shows a second site's birds, e.g. a cottage with its own Home Assistant and BirdNET-Go, labelled
"Cottage" (see [A second site](#a-second-site-optional)).

Community thread: [tphakala/birdnet-go#4486](https://github.com/tphakala/birdnet-go/discussions/4486)

## What it does
- Triggers on BirdNET-Go's MQTT topic and uses the detection JSON directly. You don't need extra sensors.
- **Skips stale messages:** if the topic is retained, HA gets the last detection again on every restart or broker
  reconnect. Anything with a `BeginTime` older than 2 minutes is ignored.
- Every detection goes up on screen, but the voice and recording only once per 15 minutes per species and site,
  so a chatty Blue Jay doesn't get announced over and over.
- Photos around the clock (owls and coyotes come out at night). The voice and the recording are skipped during quiet
  time, 21:00–07:00 by default and set on the card.
- Doesn't interrupt music or video someone else is casting to the display.
- Photo only by default. Toggles on the card add the spoken announcement and the bird's recording.
- **Recording:** plays BirdNET-Go's audio clip of the detection (`/api/v2/audio/<detectionId>`) with the bird's photo
  as cover art, at the card's "Recording volume", then puts the Hub's volume back and the photo back up. The volume is
  only raised once the cast session is open, so the session-start ding stays at the everyday volume.
- **Photo time:** Default (30 s), 1 minute, 5 minutes or Always on. A timer helper returns the Hub to ambient mode, but
  only if the bird photo is still what's showing. Changing the setting while a bird is up applies to that bird.
  The Hub drops a still photo by itself after about 10 minutes, so with Always on the last bird is re-sent every 9
  minutes (same cast session, so no ding). If the Hub has gone back to the clock (a reboot, someone else's cast), the
  refresh brings the last bird back, with one ding, so not in quiet time. Turn the automation off to get the Hub's
  usual screens back.
- The subtitle says where and when the bird was heard ("Home · 08:32 · Cyanocitta cristata · 69%"), and optionally
  the same goes on the photo itself, upper left (see "Photo tag").
- `mode: queued` (max 5), so a burst of detections plays one after another.
- No confidence filter of its own: it trusts BirdNET-Go's threshold. Add a condition like
  `"{{ bird.Confidence >= 0.8 }}"` if you want one.

## Setup
1. **BirdNET-Go:** Settings → Integrations → MQTT enabled. Note the topic (default `birdnet`). Home Assistant's MQTT
   integration must use the same broker.
2. **Helpers** (Settings → Devices & services → Helpers → Create helper). The names give these entity IDs:
   | Type | Name | Entity | Settings |
   |---|---|---|---|
   | Text | BirdNET last announced | `input_text.birdnet_last_announced` | max length 255 |
   | Toggle | Bird announcements voice | `input_boolean.bird_announcements_voice` | |
   | Toggle | BirdNET play recording | `input_boolean.birdnet_play_recording` | |
   | Dropdown | BirdNET display time | `input_select.birdnet_display_time` | options exactly: `Default (30 s)`, `1 minute`, `5 minutes`, `Always on` |
   | Number | BirdNET recording volume | `input_number.birdnet_recording_volume` | 5–100, step 5, slider, unit % |
   | Date and/or time | BirdNET quiet start | `input_datetime.birdnet_quiet_start` | time only; set to 21:00 |
   | Date and/or time | BirdNET quiet end | `input_datetime.birdnet_quiet_end` | time only; set to 07:00 |
   | Timer | BirdNET display | `timer.birdnet_display` | |
3. **Automation:** Settings → Automations → Create → ⋮ → Edit in YAML, then paste
   [`birdnet-nest-announce.yaml`](birdnet-nest-announce.yaml). Change:
   - `topic:` to your BirdNET-Go MQTT topic
   - `hub:` to your display's `media_player.*` entity
   - `birdnet:` to your BirdNET-Go web address (e.g. `http://192.168.1.50:8080`); the Hub fetches the clips from it
   - the `tts.speak` target to any TTS entity you have (e.g. Google Translate's `tts.google_en_com`)
4. **Card:** on your dashboard, Add card → Manual, and paste [`birdnet-card.yaml`](birdnet-card.yaml). Leave out the
   "Birds from" row if you only have one site.

Needs a recent Home Assistant (2025.4 or newer: the automation relies on the `variables` action updating a variable
set earlier in the run).

## Photo tag (optional)
Draws "Home 08:32" (site and time heard, 24-hour) in a dark box in the photo's upper-left corner. The Hub doesn't show
the subtitle all the time, so this keeps both on screen. [`birdnet_tag.py`](birdnet_tag.py) fetches the photo, scales
it to the Hub's 600 px height (so the label stays sharp), stamps it and saves `/config/www/birdnet/photo.jpg`, which
the Hub loads from HA's `/local/`. It uses only the Python and Pillow that come with Home Assistant. If it fails the
plain photo is shown.

1. Copy `birdnet_tag.py` to `/config/` (File editor or Studio Code Server add-on). Make sure `/config/www/` exists
   and existed when HA started.
2. Add to `configuration.yaml`, check the configuration and restart (the first `shell_command` needs a restart):
   ```yaml
   shell_command:
     birdnet_tag: python3 /config/birdnet_tag.py "{{ url }}" "{{ label }}" /config/www/birdnet/photo.jpg
   ```
3. In the automation set `tag_photos: true`, and `ha_url:` to HA's LAN address as the Hub reaches it.

## Mirror card (optional)
[`birdnet-mirror-card.yaml`](birdnet-mirror-card.yaml) shows the last bird sent to the Hub (photo, name, subtitle
and how long ago) on a dashboard. Handy on a tablet, or when the Hub is away or not working. It reads
`input_text.birdnet_last_announced`, so it shows exactly what the Hub got, filters included. For a full-screen view,
add a view of type "Panel (single card)" and paste the card into it (Add card → Manual).

## A second site (optional)
Ours is a cottage with its own Home Assistant and BirdNET-Go, joined to home over Tailscale. Its birds show on the
home Hub with "Cottage" in the subtitle, "heard at the cottage" in the voice, and their recordings. "Birds from" on
the card picks Home, Cottage or Both (Cottage alone is handy while we're away from home). The cottage's detections
never touch the home MQTT broker.

How it fits together:
- The cottage HA forwards each fresh detection to a webhook on the home HA
  ([`birdnet-forward-to-home.yaml`](birdnet-forward-to-home.yaml) plus a `rest_command`).
- The home automation's webhook trigger runs the same photo / voice / recording / quiet-time / photo-time steps.
- The Hub can't reach the cottage over the VPN, so for a recording the home HA downloads the cottage clip into
  `/config/www/birdnet/cottage-clip.wav` (overwritten each time) and the Hub plays it from HA's `/local/`.

Setup:
1. **Home HA:**
   - Helper: Dropdown "BirdNET sites" → `input_select.birdnet_sites`, options exactly `Home`, `Cottage`, `Both`.
   - Integration: **Downloader**, download folder `www` (the folder must exist, and must have existed when HA
     started, for `/local/` to serve it).
   - In the automation, set `webhook_id:` to something long and random (it's the only thing guarding the webhook),
     `cottage_birdnet:` to the cottage BirdNET-Go as the home HA reaches it, and `ha_url:` to the home HA's LAN
     address as the Hub reaches it (e.g. `http://192.168.1.10:8123`).
2. **Cottage HA:** add to `configuration.yaml`, then check the configuration and restart (the first `rest_command`
   needs a restart; later changes only a reload):
   ```yaml
   rest_command:
     birdnet_to_home:
       url: http://HOME_HA_ADDRESS/api/webhook/YOUR_WEBHOOK_ID   # as the cottage HA reaches the home HA
       method: POST
       content_type: application/json
       payload: "{{ payload }}"
   ```
   Then create an automation from [`birdnet-forward-to-home.yaml`](birdnet-forward-to-home.yaml) with the cottage's
   BirdNET-Go topic.
3. **Cottage BirdNET-Go:** raise Audio Gain as below, or its recordings will be too quiet too.

Gotcha: after restarting the cottage HA, give MQTT a minute before testing. Our first test birds were lost while it
reconnected.

## Notes and gotchas
- **The Hub's photo player sometimes wedges:** it accepts new photos but shows black, reports "idle", and ignores
  everything after that until it's closed. It seems to happen more when photos are swapped quickly. After each photo
  the automation checks that the Hub reports it showing; if not, it closes the player and sends the photo again (one
  ding). A repeat of the bird already on screen isn't re-sent, to keep swaps down. If the Hub ever stays black,
  rebooting it clears it.
- **The ding:** the Hub plays a short chime each time a cast session starts. Google doesn't offer a setting for it.
  Muting around the cast removes it, but the Hub then shows big "Media off" / "Media on" panels on every mute change,
  which is worse. Turn the Hub's volume down instead, and use "Recording volume" to hear the birds.
- **Quiet clips:** BirdNET-Go's clips can be very quiet. Ours measured −45 to −50 LUFS (normal audio is around −14 to
  −16), so even at full Hub volume a bird was hard to hear. Fix it at the source: BirdNET-Go → Settings → Audio →
  Recording → **Audio Gain** (15 dB here) only affects saved clips, not detection. Our clips went to about −24 LUFS,
  which is loud enough to play at the Hub's everyday volume.
- **The volume bar:** the Hub also pops up a big volume bar on every volume change. Set "Recording volume" to the
  Hub's everyday volume and the automation skips the change, so there's no bar.
- If HA restarts in the middle of a recording, the Hub keeps the recording volume. Set it back by hand.
- An image cast with `media_player.play_media` (`image/jpeg`) shows up in HA as `paused`. That's normal. The title and
  subtitle on screen come from `extra.metadata` with `metadataType: 0`.
- A template condition has to render `true`, not just something truthy. `{{ x is mapping and x.URL }}` renders the URL
  string and fails, so the YAML compares instead: `{{ photo != '' }}`.
- **Testing:** publish a fake detection to your topic (not retained, with a current `BeginTime`, a `CommonName` and a
  `BirdImage.URL`). Use the right species' photo, or you'll get a chickadee with a crow's picture.
- The photos come from BirdNET-Go's `BirdImage` (Avicommons and similar sources, 320 px). Their licences and authors
  are in the same JSON.

Tested on Home Assistant 2026.10 (beta) with a Google Nest Hub and BirdNET-Go publishing over MQTT.

## License
MIT
