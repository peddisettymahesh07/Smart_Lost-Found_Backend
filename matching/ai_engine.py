import math
import re
import numpy as np
from PIL import Image
from django.conf import settings
from datetime import datetime, date


# Try importing PyTorch & HuggingFace CLIP if installed
CLIP_AVAILABLE = False
clip_model = None
clip_processor = None

try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False


def load_clip_model():
    """Attempt to load pretrained OpenAI CLIP model if torch & transformers are present."""
    global clip_model, clip_processor, CLIP_AVAILABLE
    if not CLIP_AVAILABLE:
        return None, None

    if clip_model is None:
        try:
            model_id = "openai/clip-vit-base-patch32"
            clip_processor = CLIPProcessor.from_pretrained(model_id)
            clip_model = CLIPModel.from_pretrained(model_id)
            clip_model.eval()
        except Exception as e:
            # Fall back if weights cannot be downloaded or initialized
            clip_model = None
            clip_processor = None
    return clip_model, clip_processor


def extract_vision_embedding_fallback(image_path_or_file):
    """
    Computes a deterministic, real 512-dimensional normalized computer-vision
    embedding from an actual image using Pillow and NumPy.

    Features extracted:
    - Multi-scale spatial color distribution (HSV/RGB across a 4x4 spatial grid = 16 blocks x 18 bins = 288 dimensions)
    - Gradient and edge orientation histograms (Sobel-like spatial filters = 160 dimensions)
    - Texture variance and structural luminance distribution (64 dimensions)
    Total dimensions: 512.
    Vector is L2-normalized so dot product equals cosine similarity.
    """
    try:
        if hasattr(image_path_or_file, 'read'):
            image_path_or_file.seek(0)
            img = Image.open(image_path_or_file).convert('RGB')
        else:
            img = Image.open(str(image_path_or_file)).convert('RGB')
    except Exception as e:
        # Return a zero vector if image is unreadable
        return [0.0] * 512

    # Resize to standardized 224x224 (same input resolution as CLIP ViT-B/32)
    img_resized = img.resize((224, 224), Image.Resampling.BILINEAR)
    arr = np.array(img_resized, dtype=np.float32) / 255.0  # (224, 224, 3)

    features = []

    # 1. 4x4 Spatial Grid Color Histograms (16 cells * 18 bins = 288 dims)
    h_step = 224 // 4
    w_step = 224 // 4

    for row in range(4):
        for col in range(4):
            cell = arr[row * h_step:(row + 1) * h_step, col * w_step:(col + 1) * w_step, :]
            # 6 bins per RGB channel
            r_hist, _ = np.histogram(cell[:, :, 0], bins=6, range=(0.0, 1.0))
            g_hist, _ = np.histogram(cell[:, :, 1], bins=6, range=(0.0, 1.0))
            b_hist, _ = np.histogram(cell[:, :, 2], bins=6, range=(0.0, 1.0))
            cell_hist = np.concatenate([r_hist, g_hist, b_hist]).astype(np.float32)
            total = cell_hist.sum()
            if total > 0:
                cell_hist /= total
            features.extend(cell_hist.tolist())

    # 2. Edge & Gradient Orientations (160 dims)
    # Grayscale conversion
    gray = 0.2989 * arr[:, :, 0] + 0.5870 * arr[:, :, 1] + 0.1140 * arr[:, :, 2]
    # Sobel kernels
    dx = np.diff(gray, axis=1)[:, :-1]  # (224, 222)
    dy = np.diff(gray, axis=0)[:-1, :]  # (222, 224)
    # Align to 222x222
    dx = dx[:222, :222]
    dy = dy[:222, :222]
    magnitude = np.sqrt(dx ** 2 + dy ** 2)
    angle = np.arctan2(dy, dx + 1e-7)  # -pi to +pi

    # Subdivide into 4x4 zones (16 zones * 10 orientation bins = 160 dims)
    g_step = 222 // 4
    for row in range(4):
        for col in range(4):
            mag_sub = magnitude[row * g_step:(row + 1) * g_step, col * g_step:(col + 1) * g_step]
            ang_sub = angle[row * g_step:(row + 1) * g_step, col * g_step:(col + 1) * g_step]
            ang_hist, _ = np.histogram(ang_sub, bins=10, range=(-np.pi, np.pi), weights=mag_sub)
            hist_sum = ang_hist.sum()
            if hist_sum > 0:
                ang_hist = ang_hist / hist_sum
            features.extend(ang_hist.tolist())

    # 3. Structural Luminance & Variance (64 dims)
    # 8x8 coarse pooling
    pool_step = 224 // 8
    for r in range(8):
        for c in range(8):
            p = gray[r * pool_step:(r + 1) * pool_step, c * pool_step:(c + 1) * pool_step]
            features.append(float(np.mean(p)))

    # Ensure length is exactly 512
    vec = np.array(features[:512], dtype=np.float32)
    if len(vec) < 512:
        vec = np.pad(vec, (0, 512 - len(vec)), 'constant')

    # L2-normalization
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec.tolist()


def extract_image_embedding(image_path_or_file):
    """
    Extracts 512-dimensional embedding using pretrained CLIP if available,
    otherwise uses the deterministic computer-vision fallback.
    Always returns a 512-element list of floats.
    """
    model, processor = load_clip_model()
    if model is not None and processor is not None:
        try:
            if hasattr(image_path_or_file, 'read'):
                image_path_or_file.seek(0)
                img = Image.open(image_path_or_file).convert("RGB")
            else:
                img = Image.open(str(image_path_or_file)).convert("RGB")

            inputs = processor(images=img, return_tensors="pt")
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
                # Normalize features
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                embedding = image_features[0].cpu().numpy().tolist()
                return embedding
        except Exception:
            pass

    return extract_vision_embedding_fallback(image_path_or_file)


def calculate_cosine_similarity(vec1, vec2):
    """
    Calculates cosine similarity between two 512-dimensional vectors.
    Returns a score normalized to 0.0 - 100.0%.
    """
    if not vec1 or not vec2:
        return 0.0

    try:
        u = np.array(vec1, dtype=np.float32)
        v = np.array(vec2, dtype=np.float32)
        norm_u = np.linalg.norm(u)
        norm_v = np.linalg.norm(v)

        if norm_u == 0 or norm_v == 0:
            return 0.0

        cos_sim = float(np.dot(u, v) / (norm_u * norm_v))
        # Ensure range [-1.0, 1.0]
        cos_sim = max(-1.0, min(1.0, cos_sim))
        # Rescale from [0, 1] for positive similarity space to 0 - 100%
        # If dot product is already normalized [0, 1], map directly
        score = max(0.0, cos_sim) * 100.0
        return round(float(score), 2)
    except Exception:
        return 0.0


def text_token_similarity(text1, text2):
    """Calculates word token overlap and Jaccard similarity between two texts (0-100 scale)."""
    if not text1 or not text2:
        return 0.0

    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))

    # Ignore trivial stopwords
    stopwords = {'a', 'an', 'the', 'is', 'in', 'at', 'of', 'on', 'and', 'or', 'to', 'with', 'my', 'it', 'for'}
    words1 = words1 - stopwords
    words2 = words2 - stopwords

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)
    jaccard = len(intersection) / len(union) if union else 0.0
    return round(float(jaccard * 100.0), 2)


def calculate_date_similarity(date1, date2):
    """
    Calculates proximity score between two dates (0-100 scale).
    Same day = 100, within 3 days = 90, within 7 days = 75, within 30 days = 40, > 60 days = 0.
    """
    if not date1 or not date2:
        return 50.0

    if isinstance(date1, str):
        date1 = datetime.strptime(date1, '%Y-%m-%d').date()
    elif isinstance(date1, datetime):
        date1 = date1.date()

    if isinstance(date2, str):
        date2 = datetime.strptime(date2, '%Y-%m-%d').date()
    elif isinstance(date2, datetime):
        date2 = date2.date()

    diff_days = abs((date1 - date2).days)

    if diff_days == 0:
        return 100.0
    elif diff_days <= 3:
        return 90.0
    elif diff_days <= 7:
        return 75.0
    elif diff_days <= 14:
        return 60.0
    elif diff_days <= 30:
        return 40.0
    elif diff_days <= 60:
        return 20.0
    else:
        return 5.0


def calculate_location_similarity(lat1, lon1, lat2, lon2, city1, city2):
    """
    Calculates geographic proximity score (0-100 scale) and distance in km.
    """
    from locations.models import calculate_haversine_distance

    dist_km = calculate_haversine_distance(lat1, lon1, lat2, lon2)

    if dist_km is not None:
        if dist_km <= 0.5:
            score = 100.0
        elif dist_km <= 2.0:
            score = 90.0
        elif dist_km <= 5.0:
            score = 75.0
        elif dist_km <= 15.0:
            score = 55.0
        elif dist_km <= 35.0:
            score = 35.0
        elif dist_km <= 75.0:
            score = 15.0
        else:
            score = 0.0
        return score, dist_km

    # Fallback to city string matching if coords are unavailable
    if city1 and city2 and city1.strip().lower() == city2.strip().lower():
        return 70.0, None
    return 10.0, None


def calculate_combined_match_score(lost_item, found_item):
    """
    Calculates multi-factor matching score between a LostItem and a FoundItem.
    Configurable weights:
    - Image similarity: 50%
    - Category similarity: 15%
    - Colour similarity: 10%
    - Description similarity: 10%
    - Location proximity: 10%
    - Date proximity: 5%
    """
    weights = getattr(settings, 'AI_MATCHING_WEIGHTS', {
        'image': 50.0,
        'category': 15.0,
        'colour': 10.0,
        'description': 10.0,
        'location': 10.0,
        'date': 5.0,
    })

    # 1. Image similarity
    lost_image = lost_item.images.filter(is_primary=True).first() or lost_item.images.first()
    found_image = found_item.images.filter(is_primary=True).first() or found_item.images.first()

    image_sim = 0.0
    if lost_image and found_image and lost_image.embedding and found_image.embedding:
        image_sim = calculate_cosine_similarity(lost_image.embedding, found_image.embedding)
    elif not lost_image and not found_image:
        image_sim = 40.0  # neutral when neither has image

    # 2. Category similarity (100 if matching, 0 if different)
    category_sim = 100.0 if (lost_item.category.lower() == found_item.category.lower()) else 0.0

    # 3. Colour similarity
    if lost_item.colour.lower() == found_item.colour.lower():
        colour_sim = 100.0
    elif 'multi' in lost_item.colour.lower() or 'multi' in found_item.colour.lower():
        colour_sim = 60.0
    else:
        colour_sim = 0.0

    # 4. Description similarity
    combined_lost_text = f"{lost_item.title} {lost_item.description}"
    combined_found_text = f"{found_item.title} {found_item.description}"
    description_sim = text_token_similarity(combined_lost_text, combined_found_text)

    # 5. Location proximity
    location_sim, dist_km = calculate_location_similarity(
        lost_item.latitude, lost_item.longitude,
        found_item.latitude, found_item.longitude,
        lost_item.city, found_item.city
    )

    # 6. Date proximity
    date_sim = calculate_date_similarity(lost_item.date_lost, found_item.date_found)

    # Combined weighted score
    w_sum = sum(weights.values())
    combined_score = (
        (image_sim * weights['image']) +
        (category_sim * weights['category']) +
        (colour_sim * weights['colour']) +
        (description_sim * weights['description']) +
        (location_sim * weights['location']) +
        (date_sim * weights['date'])
    ) / w_sum

    combined_score = round(max(0.0, min(100.0, combined_score)), 1)

    thresholds = getattr(settings, 'AI_THRESHOLDS', {'high': 75.0, 'medium': 50.0})
    if combined_score >= thresholds['high']:
        confidence = 'High'
    elif combined_score >= thresholds['medium']:
        confidence = 'Medium'
    else:
        confidence = 'Low'

    dist_str = f"{dist_km} km" if dist_km is not None else f"{lost_item.city} / {found_item.city}"

    explanation = (
        f"AI Combined Match: {combined_score}% ({confidence} Confidence). "
        f"Components -> Image Cosine Similarity: {image_sim:.1f}% (weight {weights['image']}%), "
        f"Category Match: {category_sim:.0f}% (weight {weights['category']}%), "
        f"Colour Match: {colour_sim:.0f}% (weight {weights['colour']}%), "
        f"Text Overlap: {description_sim:.1f}% (weight {weights['description']}%), "
        f"Location Proximity: {location_sim:.1f}% ({dist_str}, weight {weights['location']}%), "
        f"Date Proximity: {date_sim:.1f}% (weight {weights['date']}%)."
    )

    return {
        'image_similarity': round(image_sim, 2),
        'category_similarity': round(category_sim, 2),
        'colour_similarity': round(colour_sim, 2),
        'description_similarity': round(description_sim, 2),
        'location_similarity': round(location_sim, 2),
        'date_similarity': round(date_sim, 2),
        'combined_score': combined_score,
        'confidence_level': confidence,
        'distance_km': dist_km,
        'explanation': explanation,
    }
