"""
Filters the metadata_participants.txt file:

  - LAYOUT = qwerty
  - FINGERS = 9-10
  - KEYBOARD_TYPE = full or laptop
  - ERROR_RATE < max_error_rate

  In the study, the average uncorrected error rate of participants is 1.167% (SD = 1.43%).

# Specify input and output files
python filter_participants.py metadata_participants.txt filtered_metadata_participants.txt
"""
import csv
import sys

max_error_rate = 1.167  # Maximum error rate threshold for filtering

def extract_filtered_rows(input_file, output_file=None):
    """
    Extract rows from metadata_participants.txt based on specified criteria:
    - LAYOUT = qwerty
    - FINGERS = 9-10
    - KEYBOARD_TYPE = full or laptop
    - ERROR_RATE < max_error_rate
    """
    
    filtered_rows = []
    header = None
    
    # Counters for each criterion
    total_participants = 0
    layout_matches = 0
    fingers_matches = 0
    keyboard_matches = 0
    error_rate_matches = 0
    
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as file:
            # Read tab-delimited file
            reader = csv.reader(file, delimiter='\t')
            
            # Get header row
            header = next(reader)
            filtered_rows.append(header)
            
            # Find column indices
            try:
                layout_idx = header.index('LAYOUT')
                fingers_idx = header.index('FINGERS')
                keyboard_type_idx = header.index('KEYBOARD_TYPE')
                error_rate_idx = header.index('ERROR_RATE')
            except ValueError as e:
                print(f"Error: Column not found in header - {e}")
                return
            
            # Process each row
            for row in reader:
                if len(row) < len(header):
                    continue  # Skip incomplete rows
                
                total_participants += 1
                
                # Check criteria
                layout = row[layout_idx].strip().lower()
                fingers = row[fingers_idx].strip()
                keyboard_type = row[keyboard_type_idx].strip().lower()
                
                try:
                    error_rate = float(row[error_rate_idx])
                except ValueError:
                    continue  # Skip rows with invalid error rate
                
                # Count individual criterion matches
                if layout == 'qwerty':
                    layout_matches += 1
                if fingers in ['7-8', '9-10']:
                    fingers_matches += 1
                if keyboard_type in ['full', 'laptop']:
                    keyboard_matches += 1
                if error_rate < 1.0:
                    error_rate_matches += 1
                
                # Apply all filters
                if (layout == 'qwerty' and 
                    fingers in ['7-8', '9-10'] and 
                    keyboard_type in ['full', 'laptop'] and 
                    error_rate < 1.0):
                    
                    filtered_rows.append(row)
                    #print(f"Match found: Participant {row[0]}")
    
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Print criterion breakdown
    print(f"\nCriterion Breakdown (Total participants: {total_participants}):")
    print(f"- LAYOUT = qwerty:        {layout_matches:4d} participants ({layout_matches/total_participants*100:.1f}%)")
    print(f"- FINGERS = 9-10:  {fingers_matches:4d} participants ({fingers_matches/total_participants*100:.1f}%)")
    print(f"- KEYBOARD_TYPE = full/laptop: {keyboard_matches:4d} participants ({keyboard_matches/total_participants*100:.1f}%)")
    print(f"- ERROR_RATE < {max_error_rate}:       {error_rate_matches:4d} participants ({error_rate_matches/total_participants*100:.1f}%)")
    print(f"- ALL criteria combined:  {len(filtered_rows)-1:4d} participants ({(len(filtered_rows)-1)/total_participants*100:.1f}%)")
    print("-" * 50)
    
    # Output results
    if output_file:
        # Write to output file
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter='\t')
                writer.writerows(filtered_rows)
            print(f"Filtered data written to '{output_file}'")
        except Exception as e:
            print(f"Error writing output file: {e}")
    else:
        # Print to console
        print(f"Filtered Results ({len(filtered_rows)-1} participants found):")
        print("=" * 50)
        for row in filtered_rows:
            print('\t'.join(row))
    
    # Analyze filtered participants statistics
    if len(filtered_rows) > 1:  # More than just header
        analyze_filtered_stats(filtered_rows, header)
    
    return filtered_rows

def analyze_filtered_stats(filtered_rows, header):
    """Analyze and display statistics for filtered participants"""
    from collections import Counter
    
    print(f"\nFiltered Participants Statistics ({len(filtered_rows)-1} participants):")
    print("=" * 60)
    
    # Skip header row for analysis
    data_rows = filtered_rows[1:]
    
    # Get column indices
    try:
        age_idx = header.index('AGE')
        gender_idx = header.index('GENDER') 
        training_idx = header.index('HAS_TAKEN_TYPING_COURSE')
        country_idx = header.index('COUNTRY')
        language_idx = header.index('NATIVE_LANGUAGE')
        time_typing_idx = header.index('TIME_SPENT_TYPING')
        wpm_idx = header.index('AVG_WPM_15')
    except ValueError as e:
        print(f"Warning: Could not find column for analysis - {e}")
        return
    
    # Age analysis
    ages = []
    for row in data_rows:
        try:
            ages.append(int(row[age_idx]))
        except (ValueError, IndexError):
            pass
    
    if ages:
        print(f"Age Distribution:")
        print(f"  Mean: {sum(ages)/len(ages):.1f} years")
        print(f"  Range: {min(ages)} - {max(ages)} years")
        print(f"  Std Dev: {(sum([(x - sum(ages)/len(ages))**2 for x in ages])/len(ages))**0.5:.1f}")
    
    # Gender distribution
    genders = [row[gender_idx].strip() for row in data_rows if len(row) > gender_idx]
    gender_counts = Counter(genders)
    print(f"\nGender Distribution:")
    for gender, count in gender_counts.most_common():
        print(f"  {gender}: {count} ({count/len(data_rows)*100:.1f}%)")
    
    # Training status
    training = [row[training_idx].strip() for row in data_rows if len(row) > training_idx]
    trained_count = sum(1 for t in training if t == '1')
    untrained_count = sum(1 for t in training if t == '0')
    print(f"\nTyping Course Training:")
    print(f"  Trained: {trained_count} ({trained_count/len(data_rows)*100:.1f}%)")
    print(f"  Untrained: {untrained_count} ({untrained_count/len(data_rows)*100:.1f}%)")
    
    # Country distribution
    countries = [row[country_idx].strip() for row in data_rows if len(row) > country_idx]
    country_counts = Counter(countries)
    print(f"\nCountry Distribution:")
    for country, count in country_counts.most_common(5):  # Top 5 countries
        print(f"  {country}: {count} ({count/len(data_rows)*100:.1f}%)")
    if len(country_counts) > 5:
        print(f"  ... and {len(country_counts)-5} other countries")
    
    # Native language distribution
    languages = [row[language_idx].strip() for row in data_rows if len(row) > language_idx]
    language_counts = Counter(languages)
    print(f"\nNative Language Distribution:")
    for language, count in language_counts.most_common(5):  # Top 5 languages
        print(f"  {language}: {count} ({count/len(data_rows)*100:.1f}%)")
    if len(language_counts) > 5:
        print(f"  ... and {len(language_counts)-5} other languages")
    
    # Time spent typing distribution
    time_typing = [row[time_typing_idx].strip() for row in data_rows if len(row) > time_typing_idx]
    time_counts = Counter(time_typing)
    print(f"\nTime Spent Typing Distribution:")
    for time_val, count in sorted(time_counts.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999):
        print(f"  {time_val} hours/day: {count} ({count/len(data_rows)*100:.1f}%)")
    
    # WPM performance analysis
    wpms = []
    for row in data_rows:
        try:
            wpms.append(float(row[wpm_idx]))
        except (ValueError, IndexError):
            pass
    
    if wpms:
        print(f"\nTyping Speed (WPM) Analysis:")
        print(f"  Mean: {sum(wpms)/len(wpms):.1f} WPM")
        print(f"  Range: {min(wpms):.1f} - {max(wpms):.1f} WPM")
        print(f"  Std Dev: {(sum([(x - sum(wpms)/len(wpms))**2 for x in wpms])/len(wpms))**0.5:.1f}")
    
    print("=" * 60)

def main():
    """Main function to run the script"""
    
    # Default input file
    input_file = "metadata_participants.txt"
    output_file = None
    
    # Parse command line arguments if provided
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    print(f"Processing file: {input_file}")
    print("Filtering criteria:")
    print("- LAYOUT = qwerty")
    print("- FINGERS = 9-10") 
    print("- KEYBOARD_TYPE = full or laptop")
    print(f"- ERROR_RATE < {max_error_rate}")
    print("-" * 50)
    
    # Extract filtered rows
    filtered_data = extract_filtered_rows(input_file, output_file)

if __name__ == "__main__":
    main()