import re
from dataclasses import dataclass


def fre_score_mapping(score: float) -> tuple[str, str]:
    """
    Map Flesch Reading Ease Score to a readability level.

    Args:
        score: The Flesch Reading Ease Score

    Returns:
        A string representing the readability level and a grade
    """
    if score >= 90:
        return "Very Easy", "A+"
    elif score >= 80:
        return "Easy", "A"
    elif score >= 70:
        return "Fairly Easy", "B"
    elif score >= 60:
        return "Standard", "C"
    elif score >= 50:
        return "Fairly Difficult", "D"
    elif score >= 30:
        return "Difficult", "E"
    else:
        return "Very Difficult", "F"


@dataclass
class ReadabilityScores:
    flesh_reading_ease: float  # Flesch Reading Ease Score
    gunning_fog: float  # Gunning Fog Index
    automated_readability_index: float  # Automated Readability Index


def count_syllables(word: str):
    """
    Count the number of syllables in a word.
    Uses a simple heuristic based on vowel groups.
    """
    word = word.lower()
    # Remove non-alphabetic characters
    word = re.sub(r"[^a-z]", "", word)

    if len(word) == 0:
        return 0

    # Count vowel groups
    vowels = "aeiouy"
    syllable_count = 0
    previous_was_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            syllable_count += 1
        previous_was_vowel = is_vowel

    # Adjust for silent 'e'
    if word.endswith("e"):
        syllable_count -= 1

    # Ensure at least one syllable
    if syllable_count == 0:
        syllable_count = 1

    return syllable_count


def calculate_readability_scores(sentences: list[str]) -> ReadabilityScores:
    """
    Calculate readability scores for a list of sentences.

    Args:
        sentences: List of strings, each representing a sentence

    Returns:
        ReadabilityScores: A dataclass containing the calculated readability scores
        None: If there are no sentences or words to analyze
    """
    # Combine all sentences into one text
    text = " ".join(sentences)

    # Count sentences
    num_sentences = len(sentences)

    if num_sentences == 0:
        return ReadabilityScores(
            flesh_reading_ease=100.0,
            gunning_fog=6.0,
            automated_readability_index=1.0,
        )

    # Split into words (remove punctuation for word counting)
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    num_words = len(words)

    if num_words == 0:
        return ReadabilityScores(
            flesh_reading_ease=100.0,
            gunning_fog=6.0,
            automated_readability_index=1.0,
        )

    # Count characters (letters only)
    num_characters = sum(len(re.sub(r"[^a-zA-Z]", "", word)) for word in words)

    # Count syllables
    total_syllables = sum(count_syllables(word) for word in words)

    # Count polysyllabic words (3+ syllables)
    num_polysyllables = sum(1 for word in words if count_syllables(word) >= 3)

    # Calculate average values
    avg_words_per_sentence = num_words / num_sentences
    avg_syllables_per_word = total_syllables / num_words
    avg_characters_per_word = num_characters / num_words

    # 1. Flesch Reading Ease Score (FRES)
    # Formula: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
    fres = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)

    # 2. Gunning Fog Index (GFI)
    # Formula: 0.4 * [(words/sentences) + 100 * (polysyllables/words)]
    gfi = 0.4 * (avg_words_per_sentence + 100 * (num_polysyllables / num_words))

    # 3. Automated Readability Index (ARI)
    # Formula: 4.71 * (characters/words) + 0.5 * (words/sentences) - 21.43
    ari = (4.71 * avg_characters_per_word) + (0.5 * avg_words_per_sentence) - 21.43

    return ReadabilityScores(
        flesh_reading_ease=round(fres, 2),
        gunning_fog=round(gfi, 2),
        automated_readability_index=round(ari, 2),
    )
