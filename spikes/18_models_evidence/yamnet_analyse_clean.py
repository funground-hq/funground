"""Spike 18: ESC-50 classes that map cleanly to AudioSet names (shared by yamnet_analyse.py and yamnet_learner.py)."""
# ESC-50 class -> the AudioSet names a learner would accept as "right" (first = the plain name). Chosen before looking at results.
CLEAN = {"dog": ["Dog", "Bark"], "cat": ["Cat", "Meow"], "crying_baby": ["Baby cry, infant cry"], "clapping": ["Clapping"],
         "door_wood_knock": ["Knock"], "church_bells": ["Church bell"], "siren": ["Siren"], "sneezing": ["Sneeze"],
         "coughing": ["Cough"], "snoring": ["Snoring"], "laughing": ["Laughter"], "crow": ["Crow"], "frog": ["Frog"],
         "sheep": ["Sheep", "Bleat"], "pig": ["Pig", "Oink"], "cow": ["Cattle, bovinae", "Moo"], "rooster": ["Chicken, rooster", "Crowing, cock-a-doodle-doo"],
         "hen": ["Chicken, rooster"], "rain": ["Rain", "Rain on surface", "Raindrop"], "sea_waves": ["Waves, surf"],
         "helicopter": ["Helicopter"], "chainsaw": ["Chainsaw"], "train": ["Train"], "clock_tick": ["Tick-tock", "Tick"],
         "clock_alarm": ["Alarm clock"], "vacuum_cleaner": ["Vacuum cleaner"], "toilet_flush": ["Toilet flush"],
         "airplane": ["Fixed-wing aircraft, airplane", "Aircraft"], "car_horn": ["Vehicle horn, car horn, honking"],
         "footsteps": ["Walk, footsteps"], "brushing_teeth": ["Toothbrush"], "keyboard_typing": ["Typing", "Computer keyboard"],
         "thunderstorm": ["Thunderstorm", "Thunder"], "wind": ["Wind", "Wind noise (microphone)"], "pouring_water": ["Pour"],
         "fireworks": ["Fireworks"], "hand_saw": ["Sawing"], "chirping_birds": ["Bird vocalization, bird call, bird song", "Chirp, tweet", "Bird"],
         "crickets": ["Cricket"], "insects": ["Insect"], "glass_breaking": ["Shatter", "Glass"], "breathing": ["Breathing"],
         "crackling_fire": ["Crackle", "Fire"], "door_wood_creaks": ["Creak"], "water_drops": ["Drip"], "engine": ["Engine"]}

