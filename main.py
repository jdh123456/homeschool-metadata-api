
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

def infer_age_range(description_or_tags):
    if not description_or_tags:
        return None
    text = " ".join(description_or_tags).lower()

    if any(k in text for k in ["picture book", "early reader", "ages 3", "ages 4", "preschool"]):
        return "3–6"
    elif any(k in text for k in ["early chapter", "ages 5", "grades k-2", "ages 6", "ages 7"]):
        return "5–7"
    elif any(k in text for k in ["middle grade", "juvenile fiction", "ages 8", "ages 9", "ages 10"]):
        return "8–12"
    elif any(k in text for k in ["young adult", "ya", "teen", "grades 7-9", "ages 13", "ages 14"]):
        return "12–16"
    elif "advanced" in text or "mature" in text:
        return "15+"
    elif "classic" in text:
        return "13+"
    return None

@app.route("/get_resource_metadata")
def get_resource_metadata():
    title = request.args.get("title", "")
    author = request.args.get("author", "")
    combined_query = f"{title} {author}".strip()

    result = {
        "title": title,
        "author": author,
        "subject": None,
        "topic": None,
        "age_range": None,
        "format": "Text",
        "availability": [],
        "source_url": None,
        "notes": None
    }

    # --- Query Open Library ---
    try:
        ol_resp = requests.get(f"https://openlibrary.org/search.json?title={title}&author={author}")
        if ol_resp.ok:
            data = ol_resp.json()
            if data["docs"]:
                doc = data["docs"][0]
                result["subject"] = doc.get("subject", [None])[0] if "subject" in doc else None
                result["topic"] = ", ".join(doc.get("subject", [])[:3]) if "subject" in doc else None
                result["notes"] = doc.get("first_sentence", {}).get("value") if isinstance(doc.get("first_sentence"), dict) else None
                result["source_url"] = f"https://openlibrary.org{doc['key']}"
                age_guess = infer_age_range(doc.get("subject", []))
                if age_guess:
                    result["age_range"] = age_guess
    except:
        pass

    # --- Query Google Books ---
    try:
        gb_resp = requests.get(f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}+inauthor:{author}")
        if gb_resp.ok:
            data = gb_resp.json()
            if data["items"]:
                volume = data["items"][0]["volumeInfo"]
                if not result["notes"]:
                    result["notes"] = volume.get("description")
                if not result["source_url"]:
                    result["source_url"] = volume.get("infoLink")
                if not result["subject"] and "categories" in volume:
                    result["subject"] = volume["categories"][0]
                if not result["topic"] and "categories" in volume:
                    result["topic"] = ", ".join(volume["categories"])
                if not result["age_range"]:
                    age_guess = infer_age_range([volume.get("description", "")])
                    if age_guess:
                        result["age_range"] = age_guess
    except:
        pass

    return jsonify(result)
