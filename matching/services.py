from .models import MatchRecord, ItemImage
from .ai_engine import calculate_combined_match_score
from notifications.services import create_notification
from lost_items.models import LostItem
from found_items.models import FoundItem


def run_matching_for_lost_item(lost_item):
    """
    Evaluates a lost item against all active found items.
    Saves or updates MatchRecord and notifies user if high/medium match is found.
    """
    found_candidates = FoundItem.objects.exclude(status='closed').order_by('-created_at')[:100]
    generated_matches = []

    for found in found_candidates:
        score_data = calculate_combined_match_score(lost_item, found)

        # Only store matches with a plausible score (> 25%)
        if score_data['combined_score'] >= 25.0:
            match_record, created = MatchRecord.objects.update_or_create(
                lost_item=lost_item,
                found_item=found,
                defaults={
                    'image_similarity': score_data['image_similarity'],
                    'category_similarity': score_data['category_similarity'],
                    'colour_similarity': score_data['colour_similarity'],
                    'description_similarity': score_data['description_similarity'],
                    'location_similarity': score_data['location_similarity'],
                    'date_similarity': score_data['date_similarity'],
                    'combined_score': score_data['combined_score'],
                    'confidence_level': score_data['confidence_level'],
                    'distance_km': score_data['distance_km'],
                    'explanation': score_data['explanation'],
                }
            )
            generated_matches.append(match_record)

            # If created and confidence is High or Medium, notify both lost item owner and finder
            if created and score_data['confidence_level'] in ['High', 'Medium']:
                create_notification(
                    user=lost_item.user,
                    title=f"Potential Match Found for '{lost_item.title}'",
                    message=(
                        f"AI identified a {score_data['confidence_level']} match ({score_data['combined_score']}%) "
                        f"with found item '{found.title}' reported in {found.city}."
                    ),
                    notification_type='match_found',
                    related_item_type='match',
                    related_item_id=match_record.id,
                )
                create_notification(
                    user=found.user,
                    title=f"Your found item '{found.title}' matches a reported lost item",
                    message=(
                        f"A reported lost item '{lost_item.title}' in {lost_item.city} matches your found report "
                        f"with {score_data['combined_score']}% similarity."
                    ),
                    notification_type='new_match',
                    related_item_type='match',
                    related_item_id=match_record.id,
                )

    return generated_matches


def run_matching_for_found_item(found_item):
    """
    Evaluates a found item against all active lost items.
    """
    lost_candidates = LostItem.objects.exclude(status='closed').order_by('-created_at')[:100]
    generated_matches = []

    for lost in lost_candidates:
        score_data = calculate_combined_match_score(lost, found_item)

        if score_data['combined_score'] >= 25.0:
            match_record, created = MatchRecord.objects.update_or_create(
                lost_item=lost,
                found_item=found_item,
                defaults={
                    'image_similarity': score_data['image_similarity'],
                    'category_similarity': score_data['category_similarity'],
                    'colour_similarity': score_data['colour_similarity'],
                    'description_similarity': score_data['description_similarity'],
                    'location_similarity': score_data['location_similarity'],
                    'date_similarity': score_data['date_similarity'],
                    'combined_score': score_data['combined_score'],
                    'confidence_level': score_data['confidence_level'],
                    'distance_km': score_data['distance_km'],
                    'explanation': score_data['explanation'],
                }
            )
            generated_matches.append(match_record)

            if created and score_data['confidence_level'] in ['High', 'Medium']:
                create_notification(
                    user=lost.user,
                    title=f"New AI Match Found for '{lost.title}'",
                    message=(
                        f"A newly found item '{found_item.title}' in {found_item.city} matches your lost item "
                        f"with a {score_data['combined_score']}% score."
                    ),
                    notification_type='match_found',
                    related_item_type='match',
                    related_item_id=match_record.id,
                )

    return generated_matches


def run_global_matching():
    """Batch re-evaluates all open lost items with available found items."""
    lost_items = LostItem.objects.exclude(status='closed')
    all_matches = []
    for item in lost_items:
        matches = run_matching_for_lost_item(item)
        all_matches.extend(matches)
    return all_matches
