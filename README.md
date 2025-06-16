# README
Process the 136M Keystrokes dataset 
to analyze bigram and word typing speeds.

**Repository**: https://github.com/binarybottle/process_3.5M_keystrokes.git  
**Author**: Arno Klein (arnoklein.info)  
**License**: MIT License (136M Keystrokes datasetsee LICENSE)

## Data
The  contains keystroke data of over 168000 users 
typing 15 sentences each. The data was collected via an online typing test 
published at a free typing speed assessment webpage. 
https://userinterfaces.aalto.fi/136Mkeystrokes/
More details about the study and its procedure can be found in the paper:

Vivek Dhakal, Anna Maria Feit, Per Ola Kristensson, Antti Oulasvirta. 
Observations on Typing from 136 Million Keystrokes. 
In Proceedings of the 2018 CHI Conference on Human Factors in Computing Systems, ACM, 2018.

## Filtering participants
filter_participants.py filters the metadata_participants.txt file.

### OUTPUT: Filtered Participants Statistics (69062 participants)
Criterion Breakdown (Total participants: 168594):
- LAYOUT = qwerty:              165324 participants (98.1%)
- FINGERS = 9-10:               107063 participants (63.5%)
- KEYBOARD_TYPE = full/laptop:  165009 participants (97.9%)
- ERROR_RATE < 1.167:           103495 participants (61.4%)
- ALL criteria combined:         69062 participants (41.0%)

Filtered data written to 'filtered_metadata_participants.txt'

Age Distribution:
  Mean: 25.9 years
  Range: 0 - 120 years
  Std Dev: 11.1

Gender Distribution:
  female: 33876 (49.1%)
  male: 28312 (41.0%)
  none: 6874 (10.0%)

Typing Course Training:
  Trained: 27747 (40.2%)
  Untrained: 41315 (59.8%)

Country Distribution:
  US: 47754 (69.1%)
  PH: 3823 (5.5%)
  CA: 3507 (5.1%)
  IN: 3238 (4.7%)
  GB: 1870 (2.7%)
  ... and 189 other countries

Native Language Distribution:
  en: 59112 (85.6%)
  tl: 1743 (2.5%)
  zh: 1422 (2.1%)
  es: 1100 (1.6%)
  hi: 589 (0.9%)
  ... and 139 other languages

Time Spent Typing Distribution:
  0 hours/day: 4986 (7.2%)
  1 hours/day: 20814 (30.1%)
  2 hours/day: 11768 (17.0%)
  3 hours/day: 6396 (9.3%)
  4 hours/day: 5226 (7.6%)
  5 hours/day: 5176 (7.5%)
  6 hours/day: 3685 (5.3%)
  7 hours/day: 1375 (2.0%)
  8 hours/day: 5790 (8.4%)
  9 hours/day: 661 (1.0%)
  10 hours/day: 1462 (2.1%)
  11 hours/day: 35 (0.1%)
  12 hours/day: 671 (1.0%)
  ...

Typing Speed (WPM) Analysis:
  Mean: 58.1 WPM
  Range: 6.0 - 152.6 WPM
  Std Dev: 20.0

## Processing keystroke files
process_keystroke_data.py processes keystroke files for filtered participants to calculate:
1. Interkey intervals for correctly typed letter bigrams (excludes spaces, Shift, etc.)
2. Word timing data (first to last letter press time per word) for correctly typed multi-letter words

Only includes data for keystrokes that match the expected target text (no typing errors).
Single-letter words are excluded from word timing analysis since they have no interkey intervals.
Bigrams and words with intervals <30ms or >3000ms are excluded to filter out hardware issues and pauses.

### OUTPUT: Processed keystroke data
Processed 61603/69062 participants
Total correct bigrams collected: 19809877
Total correct multi-letter word times collected: 6158104
Correct bigram results (30-3000ms) written to: bigram_times.csv
Correct multi-letter word timing results (30-3000ms) written to: word_times.csv

Correct Bigram Statistics (30-3000ms):
  Unique bigrams: 413
  Mean interval: 172.2 ms
  Min interval: 30 ms
  Max interval: 3000 ms
  Most common bigrams:
    th: 708088 occurrences
    he: 589922 occurrences
    in: 504056 occurrences
    re: 376910 occurrences
    ou: 366279 occurrences
