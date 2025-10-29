import json
import glob
import os

SOURCE_DIR = "data/Wuthering Waves/"
TARGET_DIR = "data/Wuthering Waves/"

print(f"Starting conversion of .jsonl files in {SOURCE_DIR} to .md")

def stream_json_objects(file_path):
    """A robust generator to stream JSON objects from a file that might be
    a proper JSONL (one object per line) or a minified file with multiple
    objects concatenated on a single line.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        decoder = json.JSONDecoder()
        idx = 0
        while idx < len(content):
            # Skip leading whitespace
            if content[idx].isspace():
                idx += 1
                continue
            
            try:
                obj, end_idx = decoder.raw_decode(content, idx)
                yield obj
                idx = end_idx
            except json.JSONDecodeError:
                # This handles cases where there might be multiple objects on one line
                # separated by newlines, or other minor format errors.
                # We try to find the next opening brace.
                next_brace = content.find('{', idx)
                if next_brace == -1:
                    break # No more objects
                idx = next_brace

    except Exception as e:
        print(f"  - ERROR: Could not read or process {file_path}. Reason: {e}")


jsonl_files = glob.glob(os.path.join(SOURCE_DIR, "*.jsonl"))

if not jsonl_files:
    print("No .jsonl files found to convert.")
else:
    print(f"Found {len(jsonl_files)} files to convert.")

for source_path in jsonl_files:
    file_name = os.path.basename(source_path)
    target_name = os.path.splitext(file_name)[0] + ".md"
    target_path = os.path.join(TARGET_DIR, target_name)
    
    print(f"Processing {source_path} -> {target_path}...")
    
    try:
        with open(target_path, 'w', encoding='utf-8') as md_file:
            count = 0
            for obj in stream_json_objects(source_path):
                if count > 0:
                    md_file.write("\n\n---\n\n")

                # Safely get metadata, providing defaults
                doc_id = obj.get('doc_id', 'N/A')
                quest_name = obj.get('quest_name', '')
                chapter_title = obj.get('chapter_title', '')
                section_title = obj.get('section_title', '')
                text_content = obj.get('text', '')

                # Write formatted markdown
                md_file.write(f"### `doc_id`: {doc_id}\n\n")
                if quest_name:
                    md_file.write(f"**任务:** {quest_name}\n")
                if chapter_title:
                    md_file.write(f"**章节:** {chapter_title}\n")
                if section_title:
                    md_file.write(f"**小节:** {section_title}\n")
                
                if any([quest_name, chapter_title, section_title]):
                    md_file.write("\n---\n\n")

                md_file.write(text_content)
                
                count += 1
        print(f"  - Successfully converted {count} objects.")
    except Exception as e:
        print(f"  - FAILED to convert {source_path}. Reason: {e}")

print("\nConversion script finished.")
