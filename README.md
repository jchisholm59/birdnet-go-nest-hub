# BirdNET-Go → Google Nest Hub

A Home Assistant automation that shows every [BirdNET-Go](https://github.com/tphakala/birdnet-go) detection on a
Google Nest Hub: the bird's photo, common name, scientific name and confidence, for 30 seconds, then back to the
clock. Optionally it says "American Crow heard, 92 percent sure" first. That's behind a toggle, so the household isn't
narrated every time a crow calls.

It should work on any Google Cast display Home Assistant can see (Nest Hub / Hub Max, Lenovo Smart Display/Clock,
Chromecast with a TV). Voice-only speakers get just the spoken part.

BirdNET-Go's models know a few non-birds too. Ours shows the odd **coyote**, which the cats find very interesting.

Community thread: [tphakala/birdnet-go#4486](https://github.com/tphakala/birdnet-go/discussions/4486)

## What it does
- Triggers on BirdNET-Go's MQTT topic and uses the detection JSON directly. You don't need extra sensors.
- **Skips stale messages:** if the topic is retained, HA gets the last detection again on every restart or broker
  reconnect. Anything with a `BeginTime` older than 2 minutes is ignored.
- Each species at most once per 15 minutes, while a new species always gets through.
- Quiet hours 21:00–07:00.
- Doesn't interrupt music or video someone else is casting to the display.
- Photo only by default; spoken too while the "Bird announcements voice" toggle is on.
- After 30 seconds it returns the Hub to ambient mode, but only if the bird photo is still what's showing.
- `mode: queued` (max 3), so a burst of detections plays one after another.
- No confidence filter of its own: it trusts BirdNET-Go's threshold. Add a condition like
  `"{{ bird.Confidence >= 0.8 }}"` if you want one.

## Setup
1. **BirdNET-Go:** Settings → Integrations → MQTT enabled. Note the topic (default `birdnet`). Home Assistant's MQTT
   integration must use the same broker.
2. **Helpers** (Settings → Devices & services → Helpers → Create helper):
   - Text: name "BirdNET last announced", max length 255 → `input_text.birdnet_last_announced`
   - Toggle: name "Bird announcements voice" → `input_boolean.bird_announcements_voice` (off = photo only)
3. **Automation:** Settings → Automations → Create → ⋮ → Edit in YAML, then paste
   [`birdnet-nest-announce.yaml`](birdnet-nest-announce.yaml). Change:
   - `topic:` to your BirdNET-Go MQTT topic
   - `hub:` to your display's `media_player.*` entity
   - the `tts.speak` target to any TTS entity you have (e.g. Google Translate's `tts.google_en_com`)
4. Optional: add a **Tile** card for `input_boolean.bird_announcements_voice` to your dashboard, as a one-tap voice
   switch.

## Notes and gotchas
- **The ding:** the Hub plays a short chime each time a cast session starts. Google doesn't offer a setting for it.
  Muting around the cast removes it, but the Hub then shows big "Media off" / "Media on" panels on every mute change,
  which is worse. Turn the Hub's volume down instead.
- An image cast with `media_player.play_media` (`image/jpeg`) shows up in HA as `paused`. That's normal. The title and
  subtitle on screen come from `extra.metadata` with `metadataType: 0`.
- A template condition has to render `true`, not just something truthy. `{{ x is mapping and x.URL }}` renders the URL
  string and fails, so the YAML uses `{{ (bird.BirdImage.URL | default('', true)) != '' }}`.
- **Testing:** publish a fake detection to your topic (not retained, with a current `BeginTime`, a `CommonName` and a
  `BirdImage.URL`). Use the right species' photo, or you'll get a chickadee with a crow's picture.
- The photos come from BirdNET-Go's `BirdImage` (Avicommons and similar sources, 320 px). Their licences and authors
  are in the same JSON.

Tested on Home Assistant 2026.10 (beta) with a Google Nest Hub and BirdNET-Go publishing over MQTT.

## License
MIT
