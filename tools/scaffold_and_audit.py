import os
import json

ROOT_DIR = "."  # प्रोजेक्ट का रूट पाथ

# इंडेक्स फ़ाइलों की लिस्ट
INDEX_FILES = [
    "Child_Development_and_Pedagogy/CDP_index.json",
    "Hindi/Hindi_index.json",
    "Mathematics/Maths_index.json",
    "Environmental_Studies/EVS_index.json",
    "English/Eng_index.json",
    "Sanskrit/Sanskrit_index.json"
]

def get_sample_content(asset_type, micro_id, micro_name):
    """विभिन्न एसेट्स के लिए मानक सैंपल डेटा जनरेट करता है"""
    if asset_type == "MCQ":
        return {
            "micro_topic_id": micro_id,
            "asset_type": "MCQ",
            "total_questions": 0,
            "questions": []
        }
    elif asset_type == "PYQ":
        return {
            "micro_topic_id": micro_id,
            "asset_type": "PYQ",
            "total_questions": 0,
            "questions": []
        }
    elif asset_type == "Concept":
        return {
            "micro_topic_id": micro_id,
            "title": micro_name,
            "asset_type": "Concept",
            "content": "अवधारणा विवरण यहाँ जोड़ें।"
        }
    elif asset_type == "Short_Notes":
        return {
            "micro_topic_id": micro_id,
            "title": f"Quick Notes - {micro_name}",
            "asset_type": "Short_Notes",
            "bullet_points": []
        }
    elif asset_type == "Practice":
        return {
            "micro_topic_id": micro_id,
            "asset_type": "Practice",
            "total_questions": 0,
            "questions": []
        }
    return None

def audit_and_scaffold():
    created_dirs = 0
    created_files = 0
    missing_assets = []

    print("[START] Scanning and Auditing Project Structure...\n")

    for index_rel_path in INDEX_FILES:
        index_full_path = os.path.join(ROOT_DIR, index_rel_path)

        if not os.path.exists(index_full_path):
            print(f"[WARNING] Index file not found: {index_full_path}. Skipping...")
            continue

        with open(index_full_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        subject_dir = data.get("subject", {}).get("directory", "")
        topics = data.get("topics", [])

        print(f"--> Checking Subject: {data.get('subject', {}).get('name_hi')} ({subject_dir})")

        for topic in topics:
            topic_folder = topic.get("folder", "")
            subtopics = topic.get("subtopics", [])

            for subtopic in subtopics:
                subtopic_folder = subtopic.get("folder", "")
                micro_topics = subtopic.get("micro_topics", [])

                for micro in micro_topics:
                    micro_id = micro.get("id")
                    micro_name = micro.get("name_hi", micro.get("slug"))
                    micro_folder = micro.get("folder", "")
                    assets_expected = micro.get("assets", ["MCQ", "PYQ"])

                    # पूर्ण फोल्डर पाथ बनाना
                    target_dir = os.path.join(ROOT_DIR, subject_dir, topic_folder, subtopic_folder, micro_folder)

                    # 1. यदि डायरेक्टरी मिसिंग है, तो बनाना
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir, exist_ok=True)
                        created_dirs += 1

                    # 2. आवश्यक सैंपल फ़ाइलें जांचना और जोड़ना
                    for asset in assets_expected:
                        if asset == "Mock_Test":
                            continue  # मॉक टेस्ट डायनामिक होता है, स्टैटिक फ़ाइल नहीं बनती

                        target_file = os.path.join(target_dir, f"{asset}.json")

                        if not os.path.exists(target_file):
                            sample_data = get_sample_content(asset, micro_id, micro_name)
                            if sample_data:
                                with open(target_file, "w", encoding="utf-8") as out_f:
                                    json.dump(sample_data, out_f, ensure_ascii=False, indent=2)
                                created_files += 1
                                missing_assets.append(target_file)

    print("\n" + "="*50)
    print("AUDIT & SCAFFOLDING REPORT:")
    print("="*50)
    print(f"Total New Directories Created: {created_dirs}")
    print(f"Total Sample Asset Files Generated: {created_files}")
    print("="*50)

if __name__ == "__main__":
    audit_and_scaffold()
