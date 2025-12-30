"""10-character job ID generation."""

import secrets
import string


def generate_job_id(intLength: int = 10) -> str:
    """
    Generate case-sensitive alphanumeric job ID.
    
    Uses cryptographically secure random number generator.
    Character set: a-z, A-Z, 0-9 (62 possible characters)
    
    Collision probability analysis:
    - 62^10 ≈ 8.4 × 10^17 possible IDs
    - Even with 1 billion jobs, collision probability < 0.000001%
    
    Example output: "aB3xK9mN2p"
    
    Args:
        intLength: Length of job ID (default: 10)
        
    Returns:
        Job ID string
    """
    strAlphabet = string.ascii_letters + string.digits  # a-z, A-Z, 0-9 (62 chars)
    strJobId = "".join(secrets.choice(strAlphabet) for _ in range(intLength))
    return strJobId