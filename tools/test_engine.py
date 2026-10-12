#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SISKILL Question Bank Engine - Phase 3
File: test_engine.py
Function: Dynamic Mock Test Generator enforcing 70:30 (PYQ:MCQ) ratio across Topic, Subject, and Full Exam levels.
"""

import os
import json
import random
import argparse
from datetime import datetime

# ================= Configuration =================
ROOT_DIR = "."
DEFAULT_DURATION_30Q = 30    # मिनट
DEFAULT_DURATION_150Q = 150  # मिनट

SUBJECT_CONFIG = {
    "CDP": {
        "name_hi": "बाल विकास एवं शिक्षण शास्त्र",
        "index_file": "Child_Development_and_Pedagogy/CDP_index.json",
        "dir": "Child_Development_and_Pedagogy"
    },
    "HINDI": {
        "name_hi": "हिन्दी भाषा एवं शिक्षण शास्त्र",
        "index_file": "Hindi/Hindi_index.json",
        "dir": "Hindi"
    },
    "MATH": {
        "name_hi": "गणित एवं शिक्षण शास्त्र",
        "index_file": "Mathematics/Maths_index.json",
        "dir": "Mathematics"
    },
    "EVS": {
        "name_hi": "पर्यावरण अध्ययन एवं शिक्षण शास्त्र",
        "index_file": "Environmental_Studies/EVS_index.json",
        "dir": "Environmental_Studies"
    },
    "ENG": {
        "name_hi": "अंग्रेजी भाषा एवं शिक्षण शास्त्र",
        "index_file": "English/Eng_index.json",
        "dir": "English"
    },
    "SAN": {
        "name_hi": "संस्कृत भाषा एवं शिक्षण शास्त्र",
        "index_file": "Sanskrit/Sanskrit_index.json",
        "dir": "Sanskrit"
    }
}


# ================= Data Harvesting =================
def load_questions_from_dir(target_dir: str):
    """दिए गए डायरेक्टरी पाथ से MCQ और PYQ प्रश्नों को लोड करता है।"""
    mcqs = []
    pyqs = []

    mcq_path = os.path.join(target_dir, "MCQ.json")
    pyq_path = os.path.join(target_dir, "PYQ.json")

    if os.path.exists(mcq_path):
        try:
            with open(mcq_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for q in data.get("questions", []):
                    q_copy = dict(q)
                    q_copy["source_type"] = "MCQ"
                    q_copy["origin_dir"] = os.path.relpath(target_dir, ROOT_DIR)
                    mcqs.append(q_copy)
        except Exception:
            pass

    if os.path.exists(pyq_path):
        try:
            with open(pyq_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for q in data.get("questions", []):
                    q_copy = dict(q)
                    q_copy["source_type"] = "PYQ"
                    q_copy["origin_dir"] = os.path.relpath(target_dir, ROOT_DIR)
                    pyqs.append(q_copy)
        except Exception:
            pass

    return mcqs, pyqs


def collect_subject_questions(subject_id: str, root_dir: str = ROOT_DIR):
    """किसी विषय के सभी माइक्रो-टॉपिक फोल्डरों से प्रश्नों का संकलन करता है।"""
    conf = SUBJECT_CONFIG.get(subject_id)
    if not conf:
        return [], []

    index_path = os.path.join(root_dir, conf["index_file"])
    all_mcqs = []
    all_pyqs = []

    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            idx = json.load(f)
        sub_dir = idx.get("subject", {}).get("directory", conf["dir"])

        for topic in idx.get("topics", []):
            t_folder = topic.get("folder", "")
            for st in topic.get("subtopics", []):
                st_folder = st.get("folder", "")
                for mt in st.get("micro_topics", []):
                    mt_folder = mt.get("folder", "")
                    full_p = os.path.join(root_dir, sub_dir, t_folder, st_folder, mt_folder)
                    m_list, p_list = load_questions_from_dir(full_p)
                    all_mcqs.extend(m_list)
                    all_pyqs.extend(p_list)
    else:
        # फ़ॉलबैक: डायरेक्टरी स्कैन
        sub_path = os.path.join(root_dir, conf["dir"])
        if os.path.exists(sub_path):
            for r, _, files in os.walk(sub_path):
                if "MCQ.json" in files or "PYQ.json" in files:
                    m_list, p_list = load_questions_from_dir(r)
                    all_mcqs.extend(m_list)
                    all_pyqs.extend(p_list)

    return all_mcqs, all_pyqs


# ================= Ratio Sampling Engine =================
def select_with_ratio(mcq_pool: list, pyq_pool: list, total_needed: int = 30, pyq_ratio: float = 0.70):
    """
    70% PYQ और 30% MCQ अनुपात को लागू करता है।
    यदि किसी एक पूल में प्रश्न कम हों, तो दूसरे पूल से सुरक्षित रूप से क्षतिपूर्ति करता है।
    """
    target_pyq = int(round(total_needed * pyq_ratio))
    target_mcq = total_needed - target_pyq

    # उपलब्ध प्रश्न संख्या
    avail_pyq = len(pyq_pool)
    avail_mcq = len(mcq_pool)

    # 1. प्राथमिक चयन
    actual_pyq_count = min(target_pyq, avail_pyq)
    actual_mcq_count = min(target_mcq, avail_mcq)

    selected_pyqs = random.sample(pyq_pool, actual_pyq_count) if actual_pyq_count > 0 else []
    selected_mcqs = random.sample(mcq_pool, actual_mcq_count) if actual_mcq_count > 0 else []

    # 2. फ़ॉलबैक क्षतिपूर्ति (यदि कोई पूल कम पड़ जाए)
    deficit = total_needed - (len(selected_pyqs) + len(selected_mcqs))

    if deficit > 0:
        # यदि PYQ कम पड़े तो अतिरिक्त MCQ लें
        remaining_mcqs = [q for q in mcq_pool if q not in selected_mcqs]
        extra_mcqs = min(deficit, len(remaining_mcqs))
        if extra_mcqs > 0:
            selected_mcqs.extend(random.sample(remaining_mcqs, extra_mcqs))
            deficit -= extra_mcqs

    if deficit > 0:
        # यदि MCQ कम पड़े तो अतिरिक्त PYQ लें
        remaining_pyqs = [q for q in pyq_pool if q not in selected_pyqs]
        extra_pyqs = min(deficit, len(remaining_pyqs))
        if extra_pyqs > 0:
            selected_pyqs.extend(random.sample(remaining_pyqs, extra_pyqs))
            deficit -= extra_pyqs

    combined = selected_pyqs + selected_mcqs
    random.shuffle(combined)

    # टेस्ट के लिए क्रम संख्या (q_number) सेट करना
    for idx, q in enumerate(combined, 1):
        q["q_number"] = idx

    return combined, len(selected_pyqs), len(selected_mcqs)


# ================= Test Assemblers =================
def generate_topic_test(micro_dir_path: str, count: int = 30):
    """किसी एक माइक्रो-टॉपिक फ़ोल्डर से 30 प्रश्नों का टेस्ट बनाता है।"""
    mcqs, pyqs = load_questions_from_dir(micro_dir_path)
    questions, p_cnt, m_cnt = select_with_ratio(mcqs, pyqs, total_needed=count)

    return {
        "test_id": f"TOPIC_{int(datetime.now().timestamp())}",
        "test_type": "Topic_Wise_Mock",
        "created_at": datetime.now().isoformat(),
        "target_path": os.path.relpath(micro_dir_path, ROOT_DIR),
        "total_questions": len(questions),
        "duration_minutes": DEFAULT_DURATION_30Q,
        "ratio_stats": {"pyq_count": p_cnt, "mcq_count": m_cnt},
        "questions": questions
    }


def generate_subject_test(subject_id: str, count: int = 30):
    """किसी एक विषय से 30 प्रश्नों का टेस्ट बनाता है।"""
    mcqs, pyqs = collect_subject_questions(subject_id)
    questions, p_cnt, m_cnt = select_with_ratio(mcqs, pyqs, total_needed=count)

    return {
        "test_id": f"{subject_id}_{int(datetime.now().timestamp())}",
        "test_type": "Subject_Wise_Mock",
        "subject_id": subject_id,
        "subject_name_hi": SUBJECT_CONFIG.get(subject_id, {}).get("name_hi", ""),
        "created_at": datetime.now().isoformat(),
        "total_questions": len(questions),
        "duration_minutes": DEFAULT_DURATION_30Q,
        "ratio_stats": {"pyq_count": p_cnt, "mcq_count": m_cnt},
        "questions": questions
    }


def generate_full_mock(lang2: str = "ENG"):
    """
    150 प्रश्नों का सम्पूर्ण पेपर बनाता है:
    CDP (30) + HINDI (30) + MATH (30) + EVS (30) + LANG2 (30)
    """
    sections_order = ["CDP", "HINDI", "MATH", "EVS", lang2.upper()]
    sections_output = []
    overall_questions = []

    total_p = 0
    total_m = 0
    global_q_num = 1

    for s_id in sections_order:
        s_mcqs, s_pyqs = collect_subject_questions(s_id)
        s_selected, p_cnt, m_cnt = select_with_ratio(s_mcqs, s_pyqs, total_needed=30)

        total_p += p_cnt
        total_m += m_cnt

        for q in s_selected:
            q["q_number"] = global_q_num
            q["section_id"] = s_id
            overall_questions.append(q)
            global_q_num += 1

        sections_output.append({
            "section_id": s_id,
            "section_name_hi": SUBJECT_CONFIG.get(s_id, {}).get("name_hi", ""),
            "questions_count": len(s_selected),
            "pyq_count": p_cnt,
            "mcq_count": m_cnt
        })

    return {
        "test_id": f"FULL_MOCK_{int(datetime.now().timestamp())}",
        "test_type": "Full_Exam_Mock_150Q",
        "exam_scope": "UPTET_CTET",
        "created_at": datetime.now().isoformat(),
        "duration_minutes": DEFAULT_DURATION_150Q,
        "total_questions": len(overall_questions),
        "marking_scheme": {"correct": 1.0, "negative": 0.0},
        "ratio_stats": {"total_pyq": total_p, "total_mcq": total_m},
        "sections": sections_output,
        "questions": overall_questions
    }


# ================= CLI Interface =================
def main():
    parser = argparse.ArgumentParser(description="SISKILL Mock Test Assembly Engine")
    parser.add_argument("--mode", choices=["topic", "subject", "full"], required=True,
                        help="मॉक टेस्ट का स्तर: topic, subject, या full")
    parser.add_argument("--subject", choices=list(SUBJECT_CONFIG.keys()),
                        help="विषय कोड (CDP, HINDI, MATH, EVS, ENG, SAN)")
    parser.add_argument("--dir", help="माइक्रो-टॉपिक फ़ोल्डर पाथ (केवल --mode topic के लिए)")
    parser.add_argument("--lang2", choices=["ENG", "SAN"], default="ENG",
                        help="फुल मॉक हेतु द्वितीय भाषा (डिफ़ॉल्ट: ENG)")
    parser.add_argument("--output", default="test_session.json", help="आउटपुट JSON फ़ाइल नाम")

    args = parser.parse_args()

    if args.mode == "topic":
        if not args.dir or not os.path.isdir(args.dir):
            print("[ERROR] --mode topic के लिए एक मान्य फ़ोल्डर पाथ (--dir) आवश्यक है।")
            return
        result = generate_topic_test(args.dir)

    elif args.mode == "subject":
        if not args.subject:
            print("[ERROR] --mode subject के लिए --subject (जैसे CDP, HINDI) आवश्यक है।")
            return
        result = generate_subject_test(args.subject)

    elif args.mode == "full":
        result = generate_full_mock(lang2=args.lang2)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n[SUCCESS] Mock Test Generated: {args.output}")
    print(f"Type: {result.get('test_type')}")
    print(f"Total Questions: {result.get('total_questions')}")
    print(f"Ratio Stats: {result.get('ratio_stats')}\n")


if __name__ == "__main__":
    main()
