"""
Processes keystroke files for filtered participants to calculate:
1. Interkey intervals for correctly typed letter bigrams (excludes spaces, Shift, etc.)
2. Sentence timing data (first to last letter press time) for correctly typed sentences
3. Word timing data (first to last letter press time per word) for correctly typed multi-letter words

Only includes data for keystrokes that match the expected target text (no typing errors).
Single-letter words are excluded from word timing analysis since they have no interkey intervals.
Bigrams and words with intervals <30ms or >3000ms are excluded.

Outputs:
- bigram_times.csv: bigram, interkey_interval (correct bigrams 30-3000ms only)
- sentence_times.csv: sentence, time (correct sentences only)
- word_times.csv: word, time (correct multi-letter words 30-3000ms only)

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
    """Process a single participant's keystroke file to extract bigram intervals, sentence times, and word times"""
    
    filename = os.path.join(keystroke_dir, f"{participant_id}_keystrokes.txt")
    bigram_intervals = []
    sentence_times = []
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
                return [], [], []
            
            # Group keystrokes by sentence with target text for comparison
            sentences_data = defaultdict(list)  # Store all keystroke data with target info
            sentence_targets = {}  # Store target text for each sentence
            
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
                    
                    # Store target sentence (assuming SENTENCE column contains the target text)
                    if sentence_key not in sentence_targets:
                        sentence_targets[sentence_key] = sentence
                    
                    # Collect all keystroke data
                    sentences_data[sentence_key].append((letter, press_time, user_input, sentence))
                        
                except ValueError:
                    continue
            
            
            # Process each sentence to extract correct bigrams, sentence times, and word times
            for sentence_key, keystrokes in sentences_data.items():
                # Sort by press time to ensure correct order
                keystrokes.sort(key=lambda x: x[1])
                
                if not keystrokes:
                    continue
                
                # Get target text for this sentence
                target_text = sentence_targets[sentence_key]
                expected_sequence = get_expected_sequence(target_text)
                expected_words = extract_words_from_sentence(target_text)
                
                if not expected_sequence:
                    continue
                
                # Track position in expected sequence and collect correct keystrokes
                expected_pos = 0
                correct_letters = []  # For sentence timing
                correct_all_chars = []  # For bigrams
                current_word_letters = []  # For word timing
                current_word_index = 0
                
                for keystroke in keystrokes:
                    char, press_time, user_input, target_sentence = keystroke
                    
                    # Skip non-typable characters except spaces
                    if not (is_typable_character(char) or char == ' '):
                        continue
                    
                    # Check if this character matches the expected character at current position
                    if expected_pos < len(expected_sequence) and char.lower() == expected_sequence[expected_pos]:
                        # Correct keystroke!
                        
                        if is_letter(char):
                            correct_letters.append((char, press_time, user_input))
                            current_word_letters.append((char.lower(), press_time))
                        
                        correct_all_chars.append((char, press_time))
                        expected_pos += 1
                        
                        # Check for word boundary (space or end of expected sequence)
                        if (char == ' ' or expected_pos >= len(expected_sequence) or 
                            (expected_pos < len(expected_sequence) and expected_sequence[expected_pos] == ' ')):
                            
                            # Process completed word if we have letters
                            if current_word_letters and current_word_index < len(expected_words):
                                # Check if the typed word matches the expected word
                                typed_word = ''.join([letter for letter, _ in current_word_letters])
                                expected_word = expected_words[current_word_index]
                                
                                if typed_word == expected_word and len(typed_word) > 1:
                                    # Only include words with more than 1 letter (need interkey intervals)
                                    # Single-letter words have no meaningful timing data (first=last letter)
                                    first_letter_time = current_word_letters[0][1]
                                    last_letter_time = current_word_letters[-1][1]
                                    word_duration = last_letter_time - first_letter_time
                                    
                                    # Only include words with reasonable timing (exclude outliers)
                                    if MIN_INTERVAL_MS <= word_duration <= MAX_INTERVAL_MS:
                                        word_times.append((expected_word, word_duration))
                                
                                current_word_index += 1
                            
                            # Reset for next word
                            current_word_letters = []
                    else:
                        # Incorrect keystroke - this breaks the sequence
                        # We could reset or continue, but for now we'll just skip this keystroke
                        pass
                
                # Calculate sentence timing from correct letters only
                if len(correct_letters) >= 2:
                    first_time = correct_letters[0][1]
                    last_time = correct_letters[-1][1]
                    sentence_duration = last_time - first_time
                    user_typed_sentence = correct_letters[0][2]  # Get the actual user input
                    sentence_times.append((user_typed_sentence, sentence_duration))
                
                # Calculate bigram intervals from correct characters only
                for i in range(len(correct_all_chars) - 1):
                    char1, time1 = correct_all_chars[i]
                    char2, time2 = correct_all_chars[i + 1]
                    
                    # Only create bigram if both characters are typable (not spaces)
                    if is_typable_character(char1) and is_typable_character(char2):
                        interval = time2 - time1  # milliseconds
                        
                        # Only include bigrams with reasonable intervals (exclude outliers)
                        if MIN_INTERVAL_MS <= interval <= MAX_INTERVAL_MS:
                            bigram = char1.lower() + char2.lower()
                            bigram_intervals.append((bigram, interval))
                    
    except FileNotFoundError:
        print(f"Warning: Keystroke file not found for participant {participant_id}")
        return [], [], []
    except Exception as e:
        print(f"Error processing keystroke file for participant {participant_id}: {e}")
        return [], [], []
    
    return bigram_intervals, sentence_times, word_times

def calculate_all_data(filtered_file, keystroke_dir="."):
    """Process all filtered participants and calculate bigram intervals, sentence times, and word times"""
    
    print(f"Reading filtered participants from: {filtered_file}")
    participant_ids = read_filtered_participants(filtered_file)
    
    if not participant_ids:
        print("No participant IDs found. Exiting.")
        return
    
    print(f"Found {len(participant_ids)} filtered participants")
    print(f"Processing keystroke files from directory: {keystroke_dir}")
    
    all_bigrams = []
    all_sentence_times = []
    all_word_times = []
    processed_count = 0
    
    for participant_id in participant_ids:
        print(f"Processing participant {participant_id}...", end=" ")
        
        bigrams, sentence_times, word_times = process_keystroke_file(participant_id, keystroke_dir)
        
        if bigrams or sentence_times or word_times:
            all_bigrams.extend(bigrams)
            all_sentence_times.extend(sentence_times)
            all_word_times.extend(word_times)
            processed_count += 1
            print(f"✓ ({len(bigrams)} correct bigrams, {len(sentence_times)} correct sentences, {len(word_times)} correct multi-letter words)")
        else:
            print("✗ (no correct data)")
    
    print(f"\nProcessed {processed_count}/{len(participant_ids)} participants")
    print(f"Total correct bigrams collected: {len(all_bigrams)}")
    print(f"Total correct sentence times collected: {len(all_sentence_times)}")
    print(f"Total correct multi-letter word times collected: {len(all_word_times)}")
    
    # Write bigram results to CSV
    output_file = 'bigram_times.csv'
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['bigram', 'interkey_interval'])
            writer.writerows(all_bigrams)
        
        print(f"Correct bigram results ({MIN_INTERVAL_MS}-{MAX_INTERVAL_MS}ms) written to: {output_file}")
        
    except Exception as e:
        print(f"Error writing bigram output file: {e}")
    
    # Write sentence timing results to separate CSV
    sentence_output_file = 'sentence_times.csv'    
    try:
        with open(sentence_output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['sentence', 'time'])
            writer.writerows(all_sentence_times)
        
        print(f"Correct sentence timing results written to: {sentence_output_file}")
        
    except Exception as e:
        print(f"Error writing sentence timing output file: {e}")
    
    # Write word timing results to separate CSV
    word_output_file = 'word_times.csv'    
    try:
        with open(word_output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['word', 'time'])
            writer.writerows(all_word_times)
        
        print(f"Correct multi-letter word timing results ({MIN_INTERVAL_MS}-{MAX_INTERVAL_MS}ms) written to: {word_output_file}")
        
    except Exception as e:
        print(f"Error writing word timing output file: {e}")
    
    # Show statistics
    if all_bigrams:
        intervals = [interval for _, interval in all_bigrams]
        bigram_counts = defaultdict(int)
        for bigram, _ in all_bigrams:
            bigram_counts[bigram] += 1
        
        print(f"\nCorrect Bigram Statistics ({MIN_INTERVAL_MS}-{MAX_INTERVAL_MS}ms):")
        print(f"  Unique bigrams: {len(bigram_counts)}")
        print(f"  Mean interval: {sum(intervals)/len(intervals):.1f} ms")
        print(f"  Min interval: {min(intervals)} ms")
        print(f"  Max interval: {max(intervals)} ms")
        print(f"  Most common bigrams:")
        for bigram, count in sorted(bigram_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {bigram}: {count} occurrences")
    
    if all_sentence_times:
        times = [time for _, time in all_sentence_times]
        print(f"\nCorrect Sentence Timing Statistics:")
        print(f"  Mean sentence time: {sum(times)/len(times):.1f} ms")
        print(f"  Min sentence time: {min(times)} ms")
        print(f"  Max sentence time: {max(times)} ms")
    
    if all_word_times:
        times = [time for _, time in all_word_times]
        word_counts = defaultdict(int)
        for word, _ in all_word_times:
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
        print("  - bigram_times.csv: Bigram interkey intervals")
        print("  - sentence_times.csv: Sentence timing data")
        print("  - word_times.csv: Word timing data (multi-letter words only)")
        sys.exit(1)
    
    filtered_file = sys.argv[1]
    keystroke_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    
    print("Keystroke Data Analysis Tool")
    print("=" * 40)
    print(f"Filtering outliers: intervals outside {MIN_INTERVAL_MS}-{MAX_INTERVAL_MS}ms excluded")
    print("")
    
    calculate_all_data(filtered_file, keystroke_dir)

if __name__ == "__main__":
    main()