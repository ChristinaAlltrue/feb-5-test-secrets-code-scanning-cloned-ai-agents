import hashlib
from urllib.parse import urlparse


def generate_storage_state_path(homepage_url: str, username: str, password: str) -> str:
    """
    Generate a unique storage state path based on domain, username, and password.

    Args:
        homepage_url: The homepage URL to extract domain from
        username: The username for authentication
        password: The password for authentication

    Returns:
        A unique storage state path in format: playwright/.auth/{domain_hash}/{username_hash}/{password_hash}/storage_state.json

    Raises:
        ValueError: If homepage_url, username, or password is empty or invalid
    """
    if not homepage_url or not homepage_url.strip():
        raise ValueError("homepage_url cannot be empty")
    if not username or not username.strip():
        raise ValueError("username cannot be empty")
    if not password or not password.strip():
        raise ValueError("password cannot be empty")

    # Validate input lengths to prevent DoS
    if len(homepage_url) > 1024:
        raise ValueError("homepage_url exceeds maximum length")
    if len(username) > 1024:
        raise ValueError("username exceeds maximum length")
    if len(password) > 1024:
        raise ValueError("password exceeds maximum length")

    # Proper URL parsing
    try:
        parsed = urlparse(homepage_url)
        # Get hostname (excludes port, credentials, path)
        domain = parsed.hostname
        if not domain:
            raise ValueError(
                f"Could not extract valid domain from homepage_url: {homepage_url}"
            )

        # Normalize domain to lowercase for consistency (domains are case-insensitive per RFC)
        domain = domain.lower()

    except ValueError:
        raise
    except (AttributeError, TypeError) as e:
        raise ValueError(f"Invalid URL format: {homepage_url}") from e

    # Hash username and password exactly as provided (preserve leading/trailing spaces)
    # Domain is already normalized to lowercase (domains are case-insensitive)
    # Username and password must be hashed as-is to prevent collision attacks
    # where "admin" and " admin" would map to the same hash after .strip()

    # Use hierarchical directory structure with domain/username/password hashes
    # File system paths provide natural collision resistance
    # Each component uses 16 chars (64 bits): collision requires 2^32 attempts per level
    # Total security: 2^32 × 2^32 × 2^32 = 2^96 for birthday collision
    # Preimage attack (accessing specific user): still requires 2^64 per component
    domain_hash = hashlib.sha256(domain.encode("utf-8")).hexdigest()[:16]
    username_hash = hashlib.sha256(username.encode("utf-8")).hexdigest()[:16]
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()[:16]

    return f"playwright/.auth/{domain_hash}/{username_hash}/{password_hash}/storage_state.json"
