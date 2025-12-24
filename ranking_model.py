from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from role_data import JOB_ROLES

# High-performance model for semantic understanding
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def get_semantic_score(role_name, resume_text):
    """Calculates similarity between a specific role and the resume."""
    role_info = JOB_ROLES[role_name]
    ideal_profile = f"{role_info['description']} Skills: {', '.join(role_info['skills'])} Certs: {', '.join(role_info['certifications'])}"
    
    vec1 = embedder.encode([ideal_profile])
    vec2 = embedder.encode([resume_text])
    return cosine_similarity(vec1, vec2)[0][0]

def analyze_skill_gap(role_name, resume_text):
    """Identifies top 3 missing skills based on the role data model."""
    role_info = JOB_ROLES[role_name]
    missing = [skill for skill in role_info["skills"] if skill.lower() not in resume_text.lower()]
    return missing[:3]

def get_semantic_score_simple(target_text, candidate_text):
    """Generic helper to compare two strings, used for Company Value matching."""
    vec1 = embedder.encode([target_text])
    vec2 = embedder.encode([candidate_text])
    return cosine_similarity(vec1, vec2)[0][0]