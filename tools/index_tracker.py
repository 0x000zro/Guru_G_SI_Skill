#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SISKILL Question Bank Engine - Phase 2
File: index_tracker.py
Function: Scans all micro-topic JSONs, updates subject-level *_index.json, and syncs root manifest.json.
"""

import os
import json
from datetime import datetime

# ================= Configuration =================
ROOT_DIR = "."
MANIFEST_FILE = "manifest.json"

# विषय निर्देशिकाओं और उनकी इंडेक्स फ़ाइलों की मैपिंग
SUBJECT_MANIFEST_MAP = {
    "CDP": {
        "directory": "Child_Development_and_Pedagogy",
        "index_file": "Child_Development_and_Pedagogy/CDP_index.json"
    },
    "HINDI": {
        "directory": "Hindi",
        "index_file": "Hindi/Hindi_index.json"
    },
    "MATH": {
        "directory": "Mathematics",
        "index_file": "Mathematics/Maths_index.json"
    },
    "EVS": {
        "directory": "Environmental_Studies",
        "index_file": "Environmental_Studies/EVS_index.json"
    },
    "ENG": {
        "directory": "English",
        "index_file": "English/Eng_index.json"
    },
    "SAN": {
        "directory": "Sanskrit",
        "index_file": "Sanskrit/Sanskrit_index.json"
    }
}


def read_question_count(json_path: str) -> int:
    """फ़ाइल से प्रश्नों की वास्तविक संख्या पढ़ता है।"""
    if not os.path.exists(json_path):
        return 0
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # यदि total_questions कुंजी उपलब्ध है तो वह लें, अन्यथा questions सूची की लंबाई
            if "total_questions" in data and isinstance(data["total_questions"], int):
                return data["total_questions"]
            return len(data.get("questions", []))
    except Exception:
        return 0


def update_subject_index(subject_id: str, config: dict, root_dir: str) -> dict:
    """
    किसी एक विषय की सभी माइक्रो-टॉपिक फ़ाइलों को स्कैन कर
    उसके संबंधित *_index.json को अपडेट करता है।
    """
    index_path = os.path.join(root_dir, config["index_file"])
    if not os.path.exists(index_path):
        return {"mcq": 0, "pyq": 0, "total": 0}

    with open(index_path, "r", encoding="utf-8") as f:
        subject_data = json.load(f)

    subject_dir = subject_data.get("subject", {}).get("directory", config["directory"])
    total_subject_mcq = 0
    total_subject_pyq = 0

    topics = subject_data.get("topics", [])
    for topic in topics:
        topic_folder = topic.get("folder", "")
        for subtopic in topic.get("subtopics", []):
            subtopic_folder = subtopic.get("folder", "")
            for micro in subtopic.get("micro_topics", []):
                micro_folder = micro.get("folder", "")

                # माइक्रो-टॉपिक डायरेक्टरी का पूर्ण पाथ
                target_dir = os.path.join(root_dir, subject_dir, topic_folder, subtopic_folder, micro_folder)

                mcq_file = os.path.join(target_dir, "MCQ.json")
                pyq_file = os.path.join(target_dir, "PYQ.json")

                mcq_count = read_question_count(mcq_file)
                pyq_count = read_question_count(pyq_file)

                # माइक्रो-टॉपिक स्तर पर गणना दर्ज करना
                micro["mcq_count"] = mcq_count
                micro["pyq_count"] = pyq_count
                micro["total_questions"] = mcq_count + pyq_count

                total_subject_mcq += mcq_count
                total_subject_pyq += pyq_count

    # विषय स्तर पर संचयी आँकड़े जोड़ना
    subject_data["stats"] = {
        "total_mcqs": total_subject_mcq,
        "total_pyqs": total_subject_pyq,
        "total_questions": total_subject_mcq + total_subject_pyq,
        "last_synced": datetime.now().isoformat()
    }

    # सुरक्षित एटॉमिक राइट
    temp_index = f"{index_path}.tmp"
    with open(temp_index, "w", encoding="utf-8") as f:
        json.dump(subject_data, f, ensure_ascii=False, indent=2)
    os.replace(temp_index, index_path)

    return {
        "mcq": total_subject_mcq,
        "pyq": total_subject_pyq,
        "total": total_subject_mcq + total_subject_pyq
    }


def sync_master_manifest(root_dir: str = ROOT_DIR):
    """
    सभी 6 विषयों के इंडेक्स को स्कैन कर रूट manifest.json को
    ग्लोबल आंकड़ों के साथ अद्यतन (Sync) करता है।
    """
    manifest_path = os.path.join(root_dir, MANIFEST_FILE)
    if not os.path.exists(manifest_path):
        print(f"[ERROR] Master manifest not found at {manifest_path}")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    grand_total_mcq = 0
    grand_total_pyq = 0
    subject_summaries = {}

    print(f"\n[SYNC] Starting Real-time Index State Tracker at {datetime.now().strftime('%H:%M:%S')}...")

    # 1. सभी विषयों का व्यक्तिगत इंडेक्स अपडेट करना
    for sub_id, sub_conf in SUBJECT_MANIFEST_MAP.items():
        stats = update_subject_index(sub_id, sub_conf, root_dir)
        subject_summaries[sub_id] = stats
        grand_total_mcq += stats["mcq"]
        grand_total_pyq += stats["pyq"]
        print(f"  └─ [{sub_id}] MCQs: {stats['mcq']:<4} | PYQs: {stats['pyq']:<4} | Total: {stats['total']}")

    # 2. रूट मैनिफ़ेस्ट में विषयवार प्रगति दर्ज करना
    for subject_entry in manifest_data.get("subjects", []):
        sid = subject_entry.get("id")
        if sid in subject_summaries:
            subject_entry["mcq_count"] = subject_summaries[sid]["mcq"]
            subject_entry["pyq_count"] = subject_summaries[sid]["pyq"]
            subject_entry["total_questions"] = subject_summaries[sid]["total"]

    # 3. ग्लोबल आंकड़े अद्यतन करना
    manifest_data["global_stats"] = {
        "overall_mcq_count": grand_total_mcq,
        "overall_pyq_count": grand_total_pyq,
        "overall_total_questions": grand_total_mcq + grand_total_pyq,
        "last_synced": datetime.now().isoformat()
    }

    # सुरक्षित एटॉमिक राइट
    temp_manifest = f"{manifest_path}.tmp"
    with open(temp_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    os.replace(temp_manifest, manifest_path)

    print(f"[COMPLETED] Master Manifest Synced. Overall Bank: {grand_total_mcq + grand_total_pyq} Qs (PYQ: {grand_total_pyq}, MCQ: {grand_total_mcq})\n")


if __name__ == "__main__":
    sync_master_manifest()
