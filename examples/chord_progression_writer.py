from typing import List, Optional
import ell
from midiutil import MIDIFile
import pygame
import time



CHORD_FORMAT = "| Chord | Chord | ... |"



@ell.simple(model="gpt-4o", temperature=0.5)
def write_a_chord_progression_for_song(genre: Optional[str], key : Optional[str]) :
    return [
        ell.system(f"You are a world class music theorist and composer. Your goal is to write chord progressions to songs given parameters. They should be fully featured and compositionally sound. Feel free to use advanced chords of your choosing. Only answer with the chord progression in {CHORD_FORMAT} format. Do not provide any additional text. Feel free to occaisonally use 13 chrods and complex chords if necessary etc."),
        ell.user(f"Write a chord progression for a song {'in ' + genre if genre else ''} {'in the key of ' + key if key else ''}.")

    ]

@ell.simple(model="gpt-4o", temperature=0.0)
def parse_chords_to_midi(chords : List[str]) -> str:
    """You are MusicGPT. You are extremely skilled at all music related tasks."""

    return f"Convert the following chord symbols to its composite Midi Note representation. Only answer with the Midi Note representation per chord in the format 'Note,Note,Note' seperating chords by newlines.\n{'\n'.join(chord.strip() for chord in chords)}"




def create_midi_file(parsed_chords, output_file="chord_progression.mid"):
    midi = MIDIFile(1)
    track = 0
    time = 0
    midi.addTrackName(track, time, "Chord Progression")
    midi.addTempo(track, time, 60)  # Slower tempo (60 BPM)

    # Set the instrument to Rhodes Piano (MIDI program 4)
    midi.addProgramChange(track, 0, time, 4)

    for chord in parsed_chords:
        notes = [int(note) for note in chord.split(',')]
        for note in notes:
            midi.addNote(track, 0, note, time, 2, 80)  # Longer duration (2 beats) and slightly lower velocity
        time += 2  # Move to the next chord after 2 beats

    with open(output_file, "wb") as output_file:
        midi.writeFile(output_file)

def play_midi_file(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(1)


from ell.stores.sql import SQLiteStore

if __name__ == "__main__":
    ell.init(store='./logdir', autocommit=True, verbose=True)
    
    genre = input("Enter the genre of the song (or press Enter to skip): ").strip() or None
    key = input("Enter the key of the song (or press Enter to skip): ").strip() or None

    progression = write_a_chord_progression_for_song(genre=genre, key=key)
    parsed_chords = parse_chords_to_midi([chord for chord in progression.split("|") if chord.strip()]).split('\n')
    parsed_chords_with_midi = [
        [int(note) for note in chord.split(',')] for chord in parsed_chords
    ]

    midi_file = "chord_progression.mid"
    create_midi_file(parsed_chords, midi_file)
    print(f"MIDI file created: {midi_file}")
    
    print("Playing chord progression...")
    play_midi_file(midi_file)
    

    midi_file = "chord_progression.mid"
    create_midi_file(parsed_chords, midi_file)
    print(f"MIDI file created: {midi_file}")
    
    print("Playing chord progression...")
    play_midi_file(midi_file)
