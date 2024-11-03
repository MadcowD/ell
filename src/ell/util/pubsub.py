from functools import lru_cache
from typing import Optional

MAX_TOPIC_LENGTH = 65535

class TopicMatcher:
    def __init__(self):
        # Cache validation and matching results
        self._validate_publish_topic = lru_cache(maxsize=1024)(self._validate_publish_topic_impl)
        self._validate_subscription_pattern = lru_cache(maxsize=1024)(self._validate_subscription_pattern_impl)
        self.matches = lru_cache(maxsize=4096)(self.matches)

    def _validate_publish_topic_impl(self, topic: str) -> tuple[bool, Optional[str]]:
        """Internal implementation that returns (is_valid, error_message)"""
        if not topic:
            return False, "Topic cannot be empty"
        if len(topic) > MAX_TOPIC_LENGTH:
            return False, f"Topic exceeds maximum length of {MAX_TOPIC_LENGTH}"
        if "#" in topic or "+" in topic:
            return False, "Publish topics cannot contain wildcards (# or +)"
        return True, None

    def _validate_subscription_pattern_impl(self, pattern: str) -> tuple[bool, Optional[str]]:
        """Internal implementation that returns (is_valid, error_message)"""
        if not pattern:
            return False, "Subscription pattern cannot be empty"
        if len(pattern) > MAX_TOPIC_LENGTH:
            return False, f"Pattern exceeds maximum length of {MAX_TOPIC_LENGTH}"
        if "#/" in pattern:
            return False, "Multi-level wildcard (#) must be the last character in the pattern"
        
        for level in pattern.split("/"):
            if len(level) > 1:
                if "+" in level:
                    return False, "Single-level wildcard (+) must be alone in its level"
                if "#" in level:
                    return False, "Multi-level wildcard (#) must be alone in its level"
        return True, None

    def validate_publish_topic(self, topic: str) -> None:
        """Public method that raises ValueError with specific message if invalid"""
        is_valid, error = self._validate_publish_topic(topic)
        if not is_valid:
            raise ValueError(error)

    def validate_subscription_pattern(self, pattern: str) -> None:
        """Public method that raises ValueError with specific message if invalid"""
        is_valid, error = self._validate_subscription_pattern(pattern)
        if not is_valid:
            raise ValueError(error)

    def matches(self, topic: str, pattern: str) -> bool:
        """Check if a topic matches a wildcard pattern."""
        # Use cached validation methods
        self.validate_publish_topic(topic)
        self.validate_subscription_pattern(pattern)

        topic_parts = topic.split("/")
        pattern_parts = pattern.split("/")

        # Handle shared subscriptions
        if pattern_parts[0] == "$share":
            pattern_parts = pattern_parts[2:]

        def match_parts(t_parts: list[str], p_parts: list[str]) -> bool:
            if not t_parts:
                return not p_parts or p_parts[0] == "#"
            if not p_parts:
                return False
            if p_parts[0] == "#":
                return True
            if p_parts[0] == "+" or t_parts[0] == p_parts[0]:
                return match_parts(t_parts[1:], p_parts[1:])
            return False

        return match_parts(topic_parts, pattern_parts)

matcher = TopicMatcher()
topic_matches = matcher.matches
validate_publish_topic = matcher.validate_publish_topic
validate_subscription_pattern = matcher.validate_subscription_pattern

