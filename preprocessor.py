import json
import re
import itertools
from pathlib import Path

# --- Strategy for characters.jsonl ---

# Define hard-coded thematic groups for character voice lines
VOICE_THEMES = {
    "COMBAT": ["受击", "重伤", "力竭", "共鸣技能", "共鸣解放", "变奏技能", "重击", "普攻", "常态攻击", "空中攻击", "成功闪避", "逆势回击", "极限闪避", "声骸异能", "进战提醒"],
    "MOVEMENT": ["滑翔", "钩索", "冲刺", "纵跑", "感知"],
}

def _get_character_voice_theme(title):
    """Check if a title belongs to a hard-coded theme."""
    for theme, keywords in VOICE_THEMES.items():
        if title in keywords:
            return theme
    return None

def process_character_file(file_path):
    """
    Processes the character file with a 3-tier grouping strategy.
    1. Auto-group by topic (e.g., 心声·一, 心声·二 -> 心声).
    2. Hard-code group specific single-line topics (e.g., combat, movement).
    3. Treat all others (long stories, unique entries) as standalone documents.
    """
    print(f"--- Applying CHARACTER strategy to {file_path} ---")
    lines_with_data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines_with_data = [json.loads(line) for line in f if line.strip()]

    # Group all lines by character name first
    lines_with_data.sort(key=lambda x: x['doc_id'].split('_')[1])
    for char_name, group in itertools.groupby(lines_with_data, key=lambda x: x['doc_id'].split('_')[1]):
        
        auto_grouped_items = {}
        themed_grouped_items = {}
        
        # First pass: sort all lines for the current character
        for item in group:
            doc_id = item.get('doc_id', '')
            topic_part = '_'.join(doc_id.split('_')[2:])

            if '·' in topic_part:
                base_topic = topic_part.split('·')[0]
                if base_topic not in auto_grouped_items:
                    auto_grouped_items[base_topic] = []
                auto_grouped_items[base_topic].append(item)
            else:
                theme = _get_character_voice_theme(topic_part)
                if theme:
                    if theme not in themed_grouped_items:
                        themed_grouped_items[theme] = []
                    themed_grouped_items[theme].append(item)
                else:
                    item['metadata'] = {'source_file': str(file_path), 'original_doc_id': item['doc_id']}
                    yield item

        # Assemble and yield auto-grouped documents
        for base_topic, items in auto_grouped_items.items():
            full_text = f"标题: {base_topic}\n" + "\n".join([item['text'].split('\n', 1)[-1] for item in items])
            new_doc_id = f"character_{char_name}_{base_topic}"
            yield {
                "doc_id": new_doc_id,
                "text": full_text,
                "metadata": {'source_file': str(file_path)}
            }

        # Assemble and yield themed documents
        for theme, items in themed_grouped_items.items():
            full_text = f"标题: {char_name} {theme}语音\n" + "\n".join([item['text'] for item in items])
            new_doc_id = f"character_{char_name}_VOICES_{theme}"
            yield {
                "doc_id": new_doc_id,
                "text": full_text,
                "metadata": {'source_file': str(file_path)}
            }


# --- Strategy for dialogues_...jsonl ---
def process_dialogue_file(file_path):
    """
    Groups dialogue lines by conversation block (flow_id + state_id).
    """
    print(f"--- Applying DIALOGUE strategy to {file_path} ---")
    lines_with_data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines_with_data = [json.loads(line) for line in f if line.strip()]

    def get_dialogue_key(item):
        parts = item['doc_id'].split('_')
        return "_".join(parts[:-1])

    for key, group in itertools.groupby(lines_with_data, key=get_dialogue_key):
        group_lines = list(group)
        if not group_lines:
            continue
        
        first_line = group_lines[0]
        full_text = "\n".join([line['text'] for line in group_lines])
        
        new_doc = first_line.copy()
        new_doc['doc_id'] = key
        new_doc['text'] = full_text
        new_doc['metadata'] = {'source_file': str(file_path), 'original_start_doc_id': first_line['doc_id']}
        yield new_doc

# --- Strategy for achievements.jsonl ---
def process_achievement_file(file_path):
    """
    Groups achievements into fixed-size chunks.
    """
    print(f"--- Applying ACHIEVEMENT strategy to {file_path} ---")
    lines_with_data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines_with_data = [json.loads(line) for line in f if line.strip()]

    CHUNK_SIZE = 10
    for i in range(0, len(lines_with_data), CHUNK_SIZE):
        chunk = lines_with_data[i:i + CHUNK_SIZE]
        if not chunk:
            continue
        
        full_text = "\n".join([line['text'] for line in chunk])
        group_num = (i // CHUNK_SIZE) + 1
        new_doc_id = f"achievement_group_{group_num}"
        
        yield {
            "doc_id": new_doc_id,
            "text": full_text,
            "metadata": {'source_file': str(file_path)}
        }

# --- Default Strategy ---
def process_default_file(file_path):
    """
    Default strategy: one line becomes one document.
    """
    print(f"--- Applying DEFAULT strategy to {file_path} ---")
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                doc = json.loads(line)
                doc['metadata'] = {'source_file': str(file_path), 'original_doc_id': doc['doc_id']}
                yield doc

# --- Main Dispatcher ---
def get_processed_docs(file_path):
    """
    Dispatcher function that yields processed documents from a given file path.
    """
    filename = Path(file_path).name

    player_name_regex = re.compile(r'\{PlayerName\}\{Male=.*?Female=.*?\}|\{PlayerName\}')

    if "dialogs" in filename:
        strategy_func = process_dialogue_file
    elif "characters" in filename:
        strategy_func = process_character_file
    elif "achievements" in filename:
        strategy_func = process_achievement_file
    else:
        strategy_func = process_default_file
        
    for doc in strategy_func(file_path):
        if 'text' in doc and doc['text']:
            doc['text'] = player_name_regex.sub('漂泊者', doc['text'])
        yield doc
