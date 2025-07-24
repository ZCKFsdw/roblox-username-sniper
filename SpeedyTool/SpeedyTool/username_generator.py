#!/usr/bin/env python3
"""Generate random usernames for testing."""

import random
import string

def generate_username():
    """Generate a random 5-character username."""
    patterns = [
        # Pure 5-character patterns (heavy weight)
        lambda: ''.join(random.choices(string.ascii_letters, k=5)),
        lambda: ''.join(random.choices(string.ascii_letters, k=5)),
        lambda: ''.join(random.choices(string.ascii_letters, k=5)),
        lambda: ''.join(random.choices(string.ascii_lowercase, k=5)),
        lambda: ''.join(random.choices(string.ascii_lowercase, k=5)),
        lambda: ''.join(random.choices(string.ascii_uppercase, k=5)),
        
        # 5-character with mixed case
        lambda: random.choice(string.ascii_uppercase) + ''.join(random.choices(string.ascii_lowercase, k=4)),
        lambda: random.choice(string.ascii_uppercase) + ''.join(random.choices(string.ascii_lowercase, k=4)),
        lambda: ''.join(random.choices(string.ascii_lowercase, k=2)) + random.choice(string.ascii_uppercase) + ''.join(random.choices(string.ascii_lowercase, k=2)),
        lambda: ''.join(random.choices(string.ascii_uppercase, k=2)) + ''.join(random.choices(string.ascii_lowercase, k=3)),
        lambda: ''.join(random.choices(string.ascii_lowercase, k=3)) + ''.join(random.choices(string.ascii_uppercase, k=2)),
        
        # 5-character with numbers
        lambda: ''.join(random.choices(string.ascii_lowercase, k=4)) + random.choice(string.digits),
        lambda: ''.join(random.choices(string.ascii_lowercase, k=3)) + ''.join(random.choices(string.digits, k=2)),
        lambda: ''.join(random.choices(string.ascii_letters, k=2)) + ''.join(random.choices(string.digits, k=3)),
        lambda: random.choice(string.ascii_uppercase) + ''.join(random.choices(string.ascii_lowercase, k=2)) + ''.join(random.choices(string.digits, k=2)),
        lambda: ''.join(random.choices(string.ascii_uppercase, k=2)) + ''.join(random.choices(string.ascii_lowercase, k=2)) + random.choice(string.digits),
        lambda: random.choice(string.digits) + ''.join(random.choices(string.ascii_letters, k=4)),
        lambda: ''.join(random.choices(string.ascii_letters, k=3)) + ''.join(random.choices(string.digits, k=2)),
        lambda: random.choice(string.digits) + ''.join(random.choices(string.ascii_lowercase, k=3)) + random.choice(string.digits),
        
        # Advanced 5-character patterns
        lambda: ''.join(random.choices(string.ascii_letters + string.digits, k=5)),
        lambda: random.choice('ABCDEFG') + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=4)),
        lambda: ''.join(random.choices('abcdefghijklmnopqr', k=3)) + ''.join(random.choices('0123456789', k=2)),
        lambda: ''.join(random.choices('ABCDEFGHIJK', k=2)) + ''.join(random.choices('abcdefghijklm', k=3)),
        lambda: random.choice('123456789') + ''.join(random.choices('ABCDEFGHIJabcdefghij', k=4)),
        lambda: ''.join(random.choices('abcdefghijk', k=2)) + random.choice('0123456789') + ''.join(random.choices('lmnopqrstuvwxyz', k=2)),
    ]
    
    pattern = random.choice(patterns)
    return pattern()

def generate_usernames(count: int) -> list:
    """Generate a list of unique 5-character usernames."""
    usernames = set()
    attempts = 0
    max_attempts = count * 5  # More attempts for larger generation
    
    print(f"🔄 Generating {count:,} unique 5-character usernames...")
    
    while len(usernames) < count and attempts < max_attempts:
        username = generate_username()
        # Only accept exactly 5-character usernames
        if len(username) == 5:
            usernames.add(username)
        attempts += 1
        
        # Progress indicator
        if attempts % 5000 == 0:
            print(f"   Progress: {len(usernames):,} unique usernames generated ({attempts:,} attempts)")
    
    return list(usernames)

if __name__ == "__main__":
    print("🎯 MASSIVE USERNAME GENERATION - 20,000+ 5-CHARACTER USERNAMES")
    print("=" * 60)
    
    # Generate 20,000+ usernames
    target_count = 22000  # Generate extra to ensure 20,000+
    usernames = generate_usernames(target_count)
    
    # Verify all are 5 characters
    five_char_only = [u for u in usernames if len(u) == 5]
    
    with open("usernames.txt", "w") as f:
        for username in five_char_only:
            f.write(username + "\n")
    
    print("=" * 60)
    print(f"✅ SUCCESS! Generated {len(five_char_only):,} unique 5-character usernames")
    print(f"📁 Saved to: usernames.txt")
    print(f"📊 Statistics:")
    print(f"   • Total unique usernames: {len(five_char_only):,}")
    print(f"   • All are exactly 5 characters: 100%")
    print(f"   • File size: ~{len(five_char_only) * 6 / 1024:.1f} KB")
    print("🎉 Ready for ultra-fast username checking!")