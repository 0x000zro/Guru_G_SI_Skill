#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SISKILL Question Bank Engine - Phase 1
File: sync_engine.py
Function: Monitors directory tree, parses MCQ.txt & PYQ.txt, appends to JSON, and archives text files.
"""

import os
import re
import json
import time
from datetime import datetime
import index_tracker

# ================= Configuration =================
ROOT_DIR = "."  # क्वेश्चन बैंक का रूट डायरेक्टरी पाथ
POLL_INTERVAL_SECONDS = 3  # डायरेक्टरी स्कैनिंग का अंतराल (सेकंड)

# जिन फ़ाइलों की निगरानी करनी है और उनका आउटपुट नाम
TARGET_INPUTS = {
    "MCQ.txt": "MCQ.json",
    "PYQ.txt": "PYQ.json"
}


# ================= Parsing Engine =================
def clean_text(text: str) -> str:
    """अनावश्यक स्पेस और न्यू-लाइन्स को साफ़ करता है।"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()


def parse_question_block(block: str, next_id: int) -> dict:
    """
    एक प्रश्न ब्लॉक को पार्स करता है।
    कॉम्पैक्ट स्कीमा: जो फ़ील्ड उपलब्ध नहीं होगा, वह key JSON में नहीं जुड़ेगी।
    """
    # 1. अनिवार्य: प्रश्न कथन (Question Text)
    # यह 'प्रश्न \d+:' से शुरू होकर विकल्प '(1)' तक का भाग लेता है
    q_match = re.search(r'प्रश्न\s*\d+\s*:\s*(.*?)(?=\(1\))', block, re.DOTALL)
    if not q_match:
        return None

    question_text = clean_text(q_match.group(1))

    # 2. अनिवार्य: चारों विकल्प (Options 1, 2, 3, 4)
    opt1 = re.search(r'\(1\)\s*(.*?)(?=\(2\))', block, re.DOTALL)
    opt2 = re.search(r'\(2\)\s*(.*?)(?=\(3\))', block, re.DOTALL)
    opt3 = re.search(r'\(3\)\s*(.*?)(?=\(4\))', block, re.DOTALL)
    opt4 = re.search(r'\(4\)\s*(.*?)(?=Correct Answer:)', block, re.DOTALL)

    if not (opt1 and opt2 and opt3 and opt4):
        return None

    options = {
        "1": clean_text(opt1.group(1)),
        "2": clean_text(opt2.group(1)),
        "3": clean_text(opt3.group(1)),
        "4": clean_text(opt4.group(1))
    }

    # 3. अनिवार्य: सही उत्तर (Correct Answer)
    ans_match = re.search(r'Correct Answer:\s*\(?([1-4])\)?', block)
    if not ans_match:
        return None
    correct_answer = ans_match.group(1).strip()

    # 4. अनिवार्य: विस्तृत व्याख्या (Detailed Explanation)
    # व्याख्या 'Detailed Explanation:' से लेकर किसी भी अगले मेटाडेटा या ब्लॉक के अंत तक
    exp_pattern = r'Detailed Explanation:\s*(.*?)(?=(?:Related Theory/Trend:|Exam Trick/Common Confusion:|Memory Tip:|Difficulty Rating:|Bloom Level:|Competency Tested:|Previous CTET Trend:|Exam Name:|Exam Year:|Paper:|$))'
    exp_match = re.search(exp_pattern, block, re.DOTALL)
    if not exp_match:
        return None
    detailed_explanation = clean_text(exp_match.group(1))

    # बेस ऑब्जेक्ट तैयार करना
    item = {
        "id": next_id,
        "question": question_text,
        "options": options,
        "correct_answer": correct_answer,
        "detailed_explanation": detailed_explanation
    }

    # 5. ऐच्छिक फ़ील्ड्स (स्पार्स स्कीमा - केवल मिलने पर ही जोड़ें)
    optional_patterns = [
        ("related_theory", r'Related Theory/Trend:\s*(.*?)(?=(?:Exam Trick/Common Confusion:|Memory Tip:|Difficulty Rating:|Bloom Level:|Competency Tested:|Previous CTET Trend:|Exam Name:|Exam Year:|Paper:|$))'),
        ("exam_trick", r'Exam Trick/Common Confusion:\s*(.*?)(?=(?:Memory Tip:|Difficulty Rating:|Bloom Level:|Competency Tested:|Previous CTET Trend:|Exam Name:|Exam Year:|Paper:|$))'),
        ("memory_tip", r'Memory Tip:\s*(.*?)(?=(?:Difficulty Rating:|Bloom Level:|Competency Tested:|Previous CTET Trend:|Exam Name:|Exam Year:|Paper:|$))'),
        ("difficulty_rating", r'Difficulty Rating:\s*(.*?)(?=(?:Bloom Level:|Competency Tested:|Previous CTET Trend:|Exam Name:|Exam Year:|Paper:|$))'),
        ("bloom_level", r'Bloom Level:\s*(.*?)(?=(?:Competency Tested:|Previous CTET Trend:|Exam Name:|Exam Year:|Paper:|$))'),
        ("competency_tested", r'Competency Tested:\s*(.*?)(?=(?:Previous CTET Trend:|Exam Name:|Exam Year:|Paper:|$))'),
        ("previous_trend", r'Previous CTET Trend:\s*(.*?)(?=(?:Exam Name:|Exam Year:|Paper:|$))'),
        ("exam_name", r'Exam Name:\s*(.*?)(?=(?:Exam Year:|Paper:|$))'),
        ("exam_year", r'Exam Year:\s*(.*?)(?=(?:Paper:|$))'),
        ("paper", r'Paper:\s*(.*?)(?=$)')
    ]

    for key, pattern in optional_patterns:
        match = re.search(pattern, block, re.DOTALL)
        if match:
            val = clean_text(match.group(1))
            if val:  # खाली न होने पर ही key जोड़ें
                item[key] = val

    return item


def parse_raw_file(file_path: str, starting_id: int) -> list:
    """टेक्स्ट फ़ाइल को पढ़कर प्रश्नों की सूची तैयार करता है।"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 'प्रश्न \d+:' के आधार पर प्रश्नों को अलग करना
    raw_blocks = re.split(r'(?=प्रश्न\s*\d+\s*:)', content.strip())
    parsed_questions = []
    current_id = starting_id

    for block in raw_blocks:
        if not block.strip():
            continue
        q_obj = parse_question_block(block, current_id)
        if q_obj:
            parsed_questions.append(q_obj)
            current_id += 1

    return parsed_questions


# ================= Storage & Append Engine =================
def process_file(dirpath: str, input_filename: str, output_filename: str):
    """
    टेक्स्ट फ़ाइल को पार्स करके संबंधित JSON में अपेंड करता है
    और टेक्स्ट फ़ाइल को आर्काइव (.processed.txt) करता है।
    """
    input_path = os.path.join(dirpath, input_filename)
    output_path = os.path.join(dirpath, output_filename)

    # 1. सुरक्षित फ़ाइल आकार जांच (ताकि पेस्ट करते समय अधूरी फ़ाइल न पढ़ी जाए)
    try:
        initial_size = os.path.getsize(input_path)
        time.sleep(0.5)
        if os.path.getsize(input_path) != initial_size:
            print(f"[WAIT] File is being written: {input_path}")
            return
    except OSError:
        return

    # 2. मौजूदा JSON डेटा पढ़ना (यदि उपलब्ध हो)
    existing_data = {
        "micro_topic": os.path.basename(dirpath),
        "asset_type": "MCQ" if "MCQ" in output_filename else "PYQ",
        "total_questions": 0,
        "questions": []
    }
    starting_id = 1

    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                questions_list = existing_data.get("questions", [])
                if questions_list:
                    max_id = max(q.get("id", 0) for q in questions_list)
                    starting_id = max_id + 1
        except Exception as e:
            print(f"[WARN] Error reading existing JSON {output_path}: {e}. Creating backup.")
            os.rename(output_path, f"{output_path}.bak_{int(time.time())}")

    # 3. नए प्रश्नों को पार्स करना
    new_questions = parse_raw_file(input_path, starting_id)
    if not new_questions:
        print(f"[SKIP] No valid questions parsed from: {input_path}")
        return

    # 4. डेटा अपेंड करना एवं JSON सेव करना
    existing_data["questions"].extend(new_questions)
    existing_data["total_questions"] = len(existing_data["questions"])
    existing_data["last_updated"] = datetime.now().isoformat()

    # एटॉमिक राइट (Temporary file लिखकर replace करना)
    temp_output_path = f"{output_path}.tmp"
    with open(temp_output_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    os.replace(temp_output_path, output_path)

    print(f"[SUCCESS] Appended {len(new_questions)} questions to {output_path} (Total: {existing_data['total_questions']})")

    # 5. ओरिजिनल फ़ाइल को रीनेम करके आर्काइव करना
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = input_filename.replace(".txt", f".processed_{timestamp}.txt")
    archive_path = os.path.join(dirpath, archive_name)
    os.rename(input_path, archive_path)
    print(f"[ARCHIVE] Renamed {input_filename} -> {archive_name}")
    index_tracker.sync_master_manifest(ROOT_DIR)


# ================= Monitoring Daemon =================
def run_monitor():
    """बैकग्राउंड डायरेक्टरी ट्री मॉनिटर लूप।"""
    print("=" * 60)
    print(f"[SISKILL ENGINE] Background Sync Daemon Active")
    print(f"Monitoring Root: {os.path.abspath(ROOT_DIR)}")
    print(f"Checking every {POLL_INTERVAL_SECONDS} seconds for MCQ.txt / PYQ.txt...")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    while True:
        try:
            for root, dirs, files in os.walk(ROOT_DIR):
                for input_file, output_file in TARGET_INPUTS.items():
                    if input_file in files:
                        print(f"\n[DETECTED] New input file found: {os.path.join(root, input_file)}")
                        process_file(root, input_file, output_file)

            time.sleep(POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\n[STOPPED] Sync Engine cleanly stopped by user.")
            break
        except Exception as err:
            print(f"[UNEXPECTED ERROR] {err}")
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_monitor()
