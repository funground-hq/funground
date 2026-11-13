# Sources of the test data

## standing_woman_640.jpg

- **What:** a full-length photograph of one woman standing on a catwalk, one hand on her hip, the other hand by her side.
- **Where from:** Wikimedia Commons, "File:Lynda Carter at The Heart Truth 2009.jpg"
  <https://commons.wikimedia.org/wiki/File:Lynda_Carter_at_The_Heart_Truth_2009.jpg>
  (first published on Flickr by The Heart Truth, <https://www.flickr.com/photos/thehearttruth/3293995284/>).
- **Author:** The Heart Truth (a national programme of the US National Heart, Lung, and Blood Institute, part of the US
  Department of Health and Human Services). Taken 13 February 2009, Bryant Park, New York.
- **Licence:** public domain, a work of the US federal government. Commons tags it `{{PD-USGov-HHS}}` and its Flickr
  licence was reviewed on 8 March 2011.
- **What was done to it:** Commons' 960 px wide copy, scaled down to 640 x 960 and saved as a JPEG (quality 85, 60 KB).

The photograph is only used to run the pose and hand models in `test_models.py`.

## gandhi_london_rain.jpg

- **What:** a photograph of Mahatma Gandhi walking in the rain after landing at Folkestone (UK), 12 September 1931, under
  an umbrella held by someone beside him. One person is clearly the main subject, full length.
- **Where from:** Wikimedia Commons, "File:Gandhi London rain.jpg"
  <https://commons.wikimedia.org/wiki/File:Gandhi_London_rain.jpg>. Commons gives its source as
  <http://rena.wao.com/gandhi/jpg/MG48.jpg>.
- **Author:** unknown (Commons: `{{unknown|Author}}`).
- **Date:** 12 September 1931.
- **Licence tags (as on Commons):** `{{PD-UK-unknown}}` and `{{PD-1996}}`. Commons' `PD-1996` says the work was public domain
  in its source country on the date the US restored foreign copyrights (1996), so it is public domain in the US as well.
- **What was done to it:** nothing but a conversion from a greyscale JPEG to an RGB JPEG (quality 95). It is Commons' own
  original size, 330 x 454, not scaled.

The photograph is only used to run the pose model in `test_models.py`. `standing_woman_640.jpg` (above) is used for the hand tests.

## tts.wav

- **What:** a computer voice saying "Draw a red circle in the middle of the screen, then make it bounce off the walls and change
  color every time it hits one." 7.2 s, 16 kHz, mono.
- **Where from:** made on the maintainer's machine with Windows' own voice (System.Speech, Microsoft David) and resampled, in the
  S-231 speech spike.
- **Author and licence:** funground, CC0.

The sound is only used to run the words model in `test_words_model.py`, and the sound model in `test_hearing_model.py`.

## whistle.wav

- **What:** whistling, 4.9 s, 16 kHz, mono, 16-bit. It starts softly: the first second is quieter than the level rule of `ml.sound()` (0.02).
- **Where from:** from Wikimedia Commons
  <https://commons.wikimedia.org/wiki/File:Soft_whistle.ogg> (originally from pdsounds.org).
- **Author:** stilgar. **Licence:** public domain.
- **What was done to it:** decoded with ffmpeg, from 0.5 s on (up to 8 s, the clip ends first), made mono and resampled to 16 kHz, saved as 16-bit WAV.

## clapping.wav

- **What:** people clapping, 8 s, 16 kHz, mono, 16-bit.
- **Where from:** from Wikimedia Commons
  <https://commons.wikimedia.org/wiki/File:Clapping_hurray_(cropped).oga>.
- **Author:** Starlite. **Licence:** public domain.
- **What was done to it:** the first 8 s decoded with ffmpeg, made mono and resampled to 16 kHz, saved as 16-bit WAV.

These two sounds and `tts.wav` are used by `test_hearing_model.py` (the sound model) and by funground-web's `tools/test_models.py`. The names the
model gives them are checked by those tests.
