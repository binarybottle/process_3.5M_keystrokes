"""
Processes keystroke files for filtered participants to calculate:
1. Interkey intervals for correctly typed letter bigrams (excludes spaces, Shift, etc.)
2. Word timing data (first to last letter press time per word) for correctly typed multi-letter words

Only includes data for keystrokes that match the expected target text (no typing errors).
Single-letter words are excluded from word timing analysis since they have no interkey intervals.
Bigrams and words with intervals <30ms or >3000ms are excluded to filter out hardware issues and thinking pauses.

Outputs:
- bigram_times.csv: participant_id, sentence_id, bigram, interkey_interval, timestamp1, timestamp2
- word_times.csv: participant_id, sentence_id, word, time, start_timestamp, end_timestamp

- Reads filtered participants: Gets participant IDs from your filtered metadata file
- Processes keystroke files: Finds and reads each #_keystrokes.txt file
- Validates correctness: Compares actual keystrokes against expected target text
- Filters actual letters: Ignores special keys like SHIFT, only processes real letters
- Groups by sentence: Calculates intervals within sentences (avoids cross-sentence gaps)
- Chronological ordering: Sorts keystrokes by press time to ensure correct sequence
- Bigram creation: Creates letter pairs (e.g., "th", "he") with their intervals for correct typing only
- Word timing: Calculates time from first to last letter of each correctly typed multi-letter word
- Outlier filtering: Excludes intervals <30ms or >3000ms to focus on realistic typing behavior

Usage:
python process_keystroke_data.py filtered_metadata_participants.txt data/files/
"""
import csv
import sys
import os
import re
from collections import defaultdict

# Maximum and minimum allowed intervals in milliseconds
MAX_INTERVAL_MS = 3000  # 3 seconds - exclude thinking pauses
MIN_INTERVAL_MS = 30    # 30ms - exclude hardware issues/accidental presses

def read_filtered_participants(filtered_file):
    """Read participant IDs from the filtered metadata file"""
    participant_ids = []
    
    try:
        with open(filtered_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            header = next(reader)  # Skip header
            
            # Find PARTICIPANT_ID column
            try:
                participant_idx = header.index('PARTICIPANT_ID')
            except ValueError:
                print("Error: PARTICIPANT_ID column not found in filtered file")
                return []
            
            for row in reader:
                if len(row) > participant_idx:
                    try:
                        participant_id = int(row[participant_idx])
                        participant_ids.append(participant_id)
                    except ValueError:
                        continue
                        
    except FileNotFoundError:
        print(f"Error: Filtered participants file '{filtered_file}' not found.")
        return []
    except Exception as e:
        print(f"Error reading filtered participants file: {e}")
        return []
    
    return participant_ids

def is_letter(letter_str):
    """Check if the keystroke represents an actual letter (not special keys)"""
    if not letter_str or len(letter_str) != 1:
        return False
    return letter_str.isalpha()

def is_typable_character(letter_str):
    """Check if the keystroke represents a typable character (letters, punctuation, but not spaces or special keys)"""
    if not letter_str or len(letter_str) != 1:
        return False
    # Include letters, punctuation, and numbers, but exclude spaces and special keys
    return letter_str.isalpha() or letter_str in '.,!?;:"\'`~@#$%^&*()_+-=[]{}|\\<>/0123456789'

def is_word_separator(char):
    """Check if character is a word separator (space, punctuation, etc.)"""
    if not char or len(char) != 1:
        return True
    return char.isspace() or char in '.,!?;:"\'`~@#$%^&*()_+-=[]{}|\\<>/'

def extract_words_from_sentence(sentence_text):
    """Extract individual words from a sentence, removing punctuation"""
    if not sentence_text:
        return []
    
    # Split by whitespace and punctuation, then filter out empty strings
    words = re.findall(r'[a-zA-Z]+', sentence_text.lower())
    return words

def normalize_text_for_comparison(text):
    """Normalize text for comparison by removing extra whitespace and converting to lowercase"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip().lower())

def get_expected_sequence(target_text):
    """Convert target text to a sequence of expected characters for keystroke comparison"""
    if not target_text:
        return []
    
    # Convert to lowercase and create sequence of expected typable characters
    expected_chars = []
    for char in target_text.lower():
        if is_typable_character(char) or char == ' ':
            expected_chars.append(char)
    
    return expected_chars

def process_keystroke_file(participant_id, keystroke_dir="."):
    """Process a single participant's keystroke file to extract bigram intervals and word times"""
    
    filename = os.path.join(keystroke_dir, f"{participant_id}_keystrokes.txt")
    bigram_intervals = []
    word_times = []
    
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            header = next(reader)
            
            # Find required column indices
            try:
                letter_idx = header.index('LETTER')
                press_time_idx = header.index('PRESS_TIME')
                sentence_idx = header.index('SENTENCE')
                user_input_idx = header.index('USER_INPUT')
                test_section_idx = header.index('TEST_SECTION_ID')
            except ValueError as e:
                print(f"Error: Required column not found in {filename} - {e}")
                return [], []
            
            # Collect data by sentence
            sentence_data = defaultdict(list)
            sentence_targets = {}
            
            for row in reader:
                if len(row) <= max(letter_idx, press_time_idx, sentence_idx, user_input_idx, test_section_idx):
                    continue
                
                letter = row[letter_idx].strip()
                sentence = row[sentence_idx].strip()
                user_input = row[user_input_idx].strip()
                test_section = row[test_section_idx].strip()
                
                try:
                    press_time = int(row[press_time_idx])
                    sentence_key = f"{test_section}_{sentence}"
                    
                    sentence_targets[sentence_key] = sentence
                    sentence_data[sentence_key].append((letter, press_time, user_input, sentence))
                        
                except ValueError:
                    continue
            
            # Process each sentence
            for sentence_key, keystrokes in sentence_data.items():
                keystrokes.sort(key=lambda x: x[1])  # Sort by timestamp
                
                if not keystrokes:
                    continue
                
                target_text = sentence_targets[sentence_key]
                expected_sequence = get_expected_sequence(target_text)
                expected_words = extract_words_from_sentence(target_text)
                
                if not expected_sequence or not expected_words:
                    continue
                
                # Extract word timings
                letter_keystrokes = [(char.lower(), press_time) for char, press_time, _, _ in keystrokes if is_letter(char)]
                used_positions = set()
                
                for expected_word in expected_words:
                    if len(expected_word) <= 1:
                        continue
                    
                    for start_pos in range(len(letter_keystrokes) - len(expected_word) + 1):
                        if any(pos in used_positions for pos in range(start_pos, start_pos + len(expected_word))):
                            continue
                        
                        candidate_chars = []
                        candidate_times = []
                        
                        for i in range(len(expected_word)):
                            if start_pos + i < len(letter_keystrokes):
                                char, press_time = letter_keystrokes[start_pos + i]
                                candidate_chars.append(char)
                                candidate_times.append(press_time)
                        
                        if len(candidate_chars) == len(expected_word):
                            candidate_word = ''.join(candidate_chars)
                            
                            if candidate_word == expected_word:
                                word_start_time = candidate_times[0]
                                word_end_time = candidate_times[-1]
                                word_duration = word_end_time - word_start_time
                                
                                if MIN_INTERVAL_MS <= word_duration <= MAX_INTERVAL_MS:
                                    word_times.append((participant_id, sentence_key, expected_word, word_duration, word_start_time, word_end_time))
                                    
                                    for pos in range(start_pos, start_pos + len(expected_word)):
                                        used_positions.add(pos)
                                    break
                
                # Extract bigram intervals from correctly identified words only
                letter_keystrokes = [(char.lower(), press_time) for char, press_time, _, _ in keystrokes if is_letter(char)]
                used_positions_for_bigrams = set()
                
                for expected_word in expected_words:
                    if len(expected_word) <= 1:
                        continue
                    
                    for start_pos in range(len(letter_keystrokes) - len(expected_word) + 1):
                        if any(pos in used_positions_for_bigrams for pos in range(start_pos, start_pos + len(expected_word))):
                            continue
                        
                        candidate_chars = []
                        candidate_times = []
                        
                        for i in range(len(expected_word)):
                            if start_pos + i < len(letter_keystrokes):
                                char, press_time = letter_keystrokes[start_pos + i]
                                candidate_chars.append(char)
                                candidate_times.append(press_time)
                        
                        if len(candidate_chars) == len(expected_word):
                            candidate_word = ''.join(candidate_chars)
                            
                            if candidate_word == expected_word:
                                # Extract bigrams from this correctly typed word
                                for i in range(len(candidate_chars) - 1):
                                    char1 = candidate_chars[i]
                                    char2 = candidate_chars[i + 1]
                                    time1 = candidate_times[i]
                                    time2 = candidate_times[i + 1]
                                    
                                    interval = time2 - time1
                                    
                                    if MIN_INTERVAL_MS <= interval <= MAX_INTERVAL_MS:
                                        bigram = char1 + char2
                                        bigram_intervals.append((participant_id, sentence_key, bigram, interval, time1, time2))
                                
                                # Mark positions as used
                                for pos in range(start_pos, start_pos + len(expected_word)):
                                    used_positions_for_bigrams.add(pos)
                                break
                                                
    except FileNotFoundError:
        print(f"Warning: Keystroke file not found for participant {participant_id}")
        return [], []
    except Exception as e:
        print(f"Error processing keystroke file for participant {participant_id}: {e}")
        return [], []
    
    return bigram_intervals, word_times

def calculate_all_data(filtered_file, keystroke_dir="."):
    """Process all filtered participants and calculate bigram intervals and word times"""
    
    print(f"Reading filtered participants from: {filtered_file}")
    participant_ids = read_filtered_participants(filtered_file)
    
    if not participant_ids:
        print("No participant IDs found. Exiting.")
        return
    
    print(f"Found {len(participant_ids)} filtered participants")
    print(f"Processing keystroke files from directory: {keystroke_dir}")
    
    all_bigrams = []
    all_word_times = []
    processed_count = 0
    
    for participant_id in participant_ids:
        print(f"Processing participant {participant_id}...", end=" ")
        
        bigrams, word_times = process_keystroke_file(participant_id, keystroke_dir)
        
        if bigrams or word_times:
            all_bigrams.extend(bigrams)
            all_word_times.extend(word_times)
            processed_count += 1
            print(f"✓ ({len(bigrams)} correct bigrams, {len(word_times)} correct multi-letter words)")
        else:
            print("✗ (no correct data)")
    
    print(f"\nProcessed {processed_count}/{len(participant_ids)} participants")
    print(f"Total correct bigrams collected: {len(all_bigrams)}")
    print(f"Total correct multi-letter word times collected: {len(all_word_times)}")
    
    # Write bigram results to CSV
    output_file = 'bigram_times.csv'
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['participant_id', 'sentence_id', 'bigram', 'interkey_interval', 'timestamp1', 'timestamp2'])
            writer.writerows(all_bigrams)
        
        print(f"Correct bigram results ({MIN_INTERVAL_MS}-{MAX_INTERVAL_MS}ms) written to: {output_file}")
        
    except Exception as e:
        print(f"Error writing bigram output file: {e}")
    
    # Write word timing results to separate CSV
    word_output_file = 'word_times.csv'    
    try:
        with open(word_output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['participant_id', 'sentence_id', 'word', 'time', 'start_timestamp', 'end_timestamp'])
            writer.writerows(all_word_times)
        
        print(f"Correct multi-letter word timing results ({MIN_INTERVAL_MS}-{MAX_INTERVAL_MS}ms) written to: {word_output_file}")
        
    except Exception as e:
        print(f"Error writing word timing output file: {e}")
    
    # Show statistics
    if all_bigrams:
        intervals = [interval for _, _, _, interval, _, _ in all_bigrams]
        bigram_counts = defaultdict(int)
        for _, _, bigram, _, _, _ in all_bigrams:
            bigram_counts[bigram] += 1
        
        print(f"\nCorrect Bigram Statistics ({MIN_INTERVAL_MS}-{MAX_INTERVAL_MS}ms):")
        print(f"  Unique bigrams: {len(bigram_counts)}")
        print(f"  Mean interval: {sum(intervals)/len(intervals):.1f} ms")
        print(f"  Min interval: {min(intervals)} ms")
        print(f"  Max interval: {max(intervals)} ms")
        print(f"  Most common bigrams:")
        for bigram, count in sorted(bigram_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {bigram}: {count} occurrences")
    
    if all_word_times:
        times = [time for _, _, _, time, _, _ in all_word_times]
        word_counts = defaultdict(int)
        for _, _, word, _, _, _ in all_word_times:
            word_counts[word] += 1
        
        print(f"\nCorrect Multi-Letter Word Timing Statistics ({MIN_INTERVAL_MS}-{MAX_INTERVAL_MS}ms):")
        print(f"  Unique words: {len(word_counts)}")
        print(f"  Mean word time: {sum(times)/len(times):.1f} ms")
        print(f"  Min word time: {min(times)} ms")
        print(f"  Max word time: {max(times)} ms")
        print(f"  Most common words:")
        for word, count in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {word}: {count} occurrences")

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("Usage: python process_keystroke_data.py <filtered_participants_file> [keystroke_directory]")
        print("Example: python process_keystroke_data.py filtered_metadata_participants.txt ./data/files/")
        print(f"\nOutputs (correctly typed data with {MIN_INTERVAL_MS}-{MAX_INTERVAL_MS}ms intervals only):")
        print("  - bigram_times.csv: participant_id, sentence_id, bigram, interkey_interval, timestamp1, timestamp2")
        print("  - word_times.csv: participant_id, sentence_id, word, time, start_timestamp, end_timestamp")
        sys.exit(1)
    
    filtered_file = sys.argv[1]
    keystroke_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    
    print("Keystroke Data Analysis Tool")
    print("=" * 40)
    print(f"Filtering outliers: intervals outside {MIN_INTERVAL_MS}-{MAX_INTERVAL_MS}ms excluded")
    print("Processing: Bigrams and Words only")
    print("")
    
    calculate_all_data(filtered_file, keystroke_dir)

if __name__ == "__main__":
    main()