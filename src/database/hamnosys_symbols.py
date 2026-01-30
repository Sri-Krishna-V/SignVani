"""
HamNoSys Symbol Reference

Complete mapping of HamNoSys symbols for sign language notation.
Based on Hamburg Notation System (HamNoSys) 4.0 specification.

HamNoSys uses Unicode Private Use Area (PUA) characters in the HamNoSysUnicode font.
This module provides ASCII representations compatible with SiGML/CWASA.

Reference: https://www.sign-lang.uni-hamburg.de/dgs-korpus/hamnosys-97.html
"""

from dataclasses import dataclass
from typing import Dict, List

# =============================================================================
# HANDSHAPES - Basic hand configurations
# =============================================================================

HANDSHAPES = {
    # Fist variants
    'hamfist': 'Closed fist',
    'hamflathand': 'Flat hand, fingers together',
    'hamfinger2': 'Index finger extended',
    'hamfinger23': 'Index and middle fingers extended (V-shape)',
    'hamfinger23spread': 'Index and middle spread (V-spread)',
    'hamfinger2345': 'Four fingers extended (no thumb)',
    'hamfinger345': 'Middle, ring, pinky extended',
    'hampinch12': 'Thumb and index pinched',
    'hampinch12open': 'Thumb and index open pinch (C-shape)',
    'hampinchall': 'All fingers pinched to thumb',
    'hamceeall': 'C-shape with all fingers',
    'hamcee12': 'C-shape with thumb and index',
    'hamthumb': 'Thumb extended only',
    'hamfingerball': 'Fingers curved into ball',

    # Finger selection modifiers
    'hamthumboutmod': 'Thumb extended outward',
    'hamthumbacrossmod': 'Thumb across palm',
    'hamthumbopenmod': 'Thumb open/relaxed',
    'hamdoublebent': 'Fingers bent at both joints',
    'hamsinglefinger': 'Single finger',
    'hamdoublefinger': 'Two fingers',
}

# =============================================================================
# HAND ORIENTATION - Palm facing direction
# =============================================================================

PALM_ORIENTATIONS = {
    'hampalmu': 'Palm up (supinated)',
    'hampalmd': 'Palm down (pronated)',
    'hampalml': 'Palm left',
    'hampalmr': 'Palm right',
    'hampalmin': 'Palm inward (toward body)',
    'hampalmout': 'Palm outward (away from body)',
}

# =============================================================================
# EXTENDED FINGER DIRECTION
# =============================================================================

FINGER_DIRECTIONS = {
    'hamextfingeru': 'Extended fingers pointing up',
    'hamextfingerd': 'Extended fingers pointing down',
    'hamextfingerl': 'Extended fingers pointing left',
    'hamextfingerr': 'Extended fingers pointing right',
    'hamextfingero': 'Extended fingers pointing outward',
    'hamextfingeri': 'Extended fingers pointing inward',
    'hamextfingeruo': 'Extended fingers pointing up-outward',
    'hamextfingerdi': 'Extended fingers pointing down-inward',
    'hamextfingerui': 'Extended fingers pointing up-inward',
    'hamextfingerdo': 'Extended fingers pointing down-outward',
}

# =============================================================================
# LOCATIONS - Where the sign is made relative to the body
# =============================================================================

LOCATIONS = {
    # Head locations
    'hamhead': 'Head (general)',
    'hamforehead': 'Forehead',
    'hamheadtop': 'Top of head',
    'hameyes': 'Eyes',
    'hamnose': 'Nose',
    'hamear': 'Ear',
    'hamlips': 'Lips',
    'hammouth': 'Mouth',
    'hamchin': 'Chin',
    'hamcheek': 'Cheek',
    'hamneck': 'Neck',

    # Torso locations
    'hamshoulders': 'Shoulders',
    'hamshouldertop': 'Top of shoulder',
    'hamchest': 'Chest',
    'hamstomach': 'Stomach',
    'hambelowstomach': 'Below stomach',

    # Arm locations
    'hamupperarm': 'Upper arm',
    'hamelbow': 'Elbow',
    'hamlowerarm': 'Lower arm/forearm',
    'hamwrist': 'Wrist',

    # Hand locations (for two-handed signs)
    'hampalm': 'Palm of hand',
    'hamhandback': 'Back of hand',
    'hamthumbball': 'Ball of thumb',
    'hamfingertip': 'Fingertip',
    'hamfingerpad': 'Finger pad',
    'hamfingernail': 'Fingernail',
    'hamfingerside': 'Side of finger',

    # Space locations
    'hamneutralspace': 'Neutral signing space',
    'hamlrat': 'Left-right at',
    'hamclose': 'Close to body',
    'hamfar': 'Far from body',
}

# =============================================================================
# MOVEMENTS - How the hand moves during the sign
# =============================================================================

MOVEMENTS = {
    # Directional movements
    'hammoveu': 'Move up',
    'hammoved': 'Move down',
    'hammovel': 'Move left',
    'hammover': 'Move right',
    'hammoveo': 'Move outward (away from body)',
    'hammovei': 'Move inward (toward body)',
    'hammoveuo': 'Move up and outward',
    'hammoveui': 'Move up and inward',
    'hammovedo': 'Move down and outward',
    'hammovedi': 'Move down and inward',

    # Curved/arc movements
    'hamarcu': 'Arc upward',
    'hamarcd': 'Arc downward',
    'hamarcl': 'Arc leftward',
    'hamarcr': 'Arc rightward',
    'hamarco': 'Arc outward',
    'hamarci': 'Arc inward',

    # Circular movements
    'hamcircle': 'Circular movement',
    'hamcircleu': 'Circle upward',
    'hamcircled': 'Circle downward',
    'hamcirclel': 'Circle leftward',
    'hamcircler': 'Circle rightward',
    'hamcircleo': 'Circle outward',
    'hamcirclei': 'Circle inward',

    # Wrist/hand internal movements
    'hamwristflex': 'Wrist flexion',
    'hamwristextend': 'Wrist extension',
    'hamwristrotate': 'Wrist rotation',

    # Finger movements
    'hamfingerplay': 'Finger wiggling/play',
    'hamfingerstraighten': 'Fingers straighten',
    'hamfingerbend': 'Fingers bend',

    # Modifiers
    'hamrepeat': 'Repeat movement',
    'hamrepeatfromstart': 'Repeat from starting position',
    'hamreplace': 'Replace/alternate',
    'hamaltmotion': 'Alternating motion',
    'hamsymmetry': 'Symmetric movement (both hands)',

    # Speed/manner modifiers
    'hamfast': 'Fast movement',
    'hamslow': 'Slow movement',
    'hamtense': 'Tense/sharp movement',
    'hamrelaxed': 'Relaxed movement',
}

# =============================================================================
# NON-MANUAL FEATURES - Facial expressions and body movements
# =============================================================================

NON_MANUAL = {
    # Eyebrows
    'hambrowsup': 'Eyebrows raised',
    'hambrowsdown': 'Eyebrows lowered/furrowed',

    # Eyes
    'hameyelidsclosed': 'Eyes closed',
    'hameyegazeup': 'Gaze upward',
    'hameyegazedown': 'Gaze downward',
    'hameyegazeleft': 'Gaze left',
    'hameyegazeright': 'Gaze right',

    # Mouth
    'hammouthopen': 'Mouth open',
    'hammouthclosed': 'Mouth closed/pursed',
    'hamtongueout': 'Tongue out',
    'hamsmilepictured': 'Smiling',
    'hamcheekspuff': 'Cheeks puffed',

    # Head movement
    'hamheadnod': 'Head nod',
    'hamheadshake': 'Head shake',
    'hamheadtilt': 'Head tilt',

    # Body
    'hambodylean': 'Body lean',
    'hamshouldersraised': 'Shoulders raised',
}

# =============================================================================
# SYMMETRY OPERATORS - For two-handed signs
# =============================================================================

SYMMETRY = {
    'hamsymmpar': 'Symmetric parallel (both hands same shape, move together)',
    'hamsymmaltern': 'Symmetric alternating',
    'hamnondominant': 'Non-dominant hand specifier',
}


# =============================================================================
# SIGML ELEMENT BUILDERS - Helper functions for constructing SiGML
# =============================================================================

def build_hamnosys_string(
    handshape: str,
    orientation: str = None,
    finger_direction: str = None,
    location: str = None,
    movements: List[str] = None,
    non_manual: List[str] = None,
    symmetry: str = None
) -> str:
    """
    Build a HamNoSys string from component parts.

    Args:
        handshape: Base handshape symbol
        orientation: Palm orientation
        finger_direction: Direction extended fingers point
        location: Location relative to body
        movements: List of movement symbols
        non_manual: List of non-manual feature symbols
        symmetry: Symmetry operator for two-handed signs

    Returns:
        Comma-separated HamNoSys string for SiGML
    """
    parts = []

    if symmetry:
        parts.append(symmetry)

    parts.append(handshape)

    if orientation:
        parts.append(orientation)

    if finger_direction:
        parts.append(finger_direction)

    if location:
        parts.append(location)

    if movements:
        parts.extend(movements)

    if non_manual:
        parts.extend(non_manual)

    return ','.join(parts)


def validate_hamnosys(hamnosys_string: str) -> bool:
    """
    Validate a HamNoSys string contains recognized symbols.

    Args:
        hamnosys_string: Comma-separated HamNoSys notation

    Returns:
        True if all symbols are recognized
    """
    all_symbols = set()
    all_symbols.update(HANDSHAPES.keys())
    all_symbols.update(PALM_ORIENTATIONS.keys())
    all_symbols.update(FINGER_DIRECTIONS.keys())
    all_symbols.update(LOCATIONS.keys())
    all_symbols.update(MOVEMENTS.keys())
    all_symbols.update(NON_MANUAL.keys())
    all_symbols.update(SYMMETRY.keys())

    parts = hamnosys_string.split(',')
    for part in parts:
        part = part.strip()
        if part and part not in all_symbols:
            return False
    return True


def get_symbol_description(symbol: str) -> str:
    """
    Get human-readable description of a HamNoSys symbol.

    Args:
        symbol: HamNoSys symbol name

    Returns:
        Description string or 'Unknown symbol'
    """
    for category in [HANDSHAPES, PALM_ORIENTATIONS, FINGER_DIRECTIONS,
                     LOCATIONS, MOVEMENTS, NON_MANUAL, SYMMETRY]:
        if symbol in category:
            return category[symbol]
    return 'Unknown symbol'


if __name__ == '__main__':
    # Test the module
    print("HamNoSys Symbol Reference")
    print("=" * 60)

    # Example: Build HamNoSys for "HELLO" (waving hand)
    hello = build_hamnosys_string(
        handshape='hamflathand',
        orientation='hampalmo',
        finger_direction='hamextfingeru',
        location='hamshoulders',
        movements=['hammover', 'hamrepeat']
    )
    print(f"\nExample HELLO: {hello}")
    print(f"Valid: {validate_hamnosys(hello)}")

    # Print symbol counts
    print(f"\nSymbol Categories:")
    print(f"  Handshapes: {len(HANDSHAPES)}")
    print(f"  Palm Orientations: {len(PALM_ORIENTATIONS)}")
    print(f"  Finger Directions: {len(FINGER_DIRECTIONS)}")
    print(f"  Locations: {len(LOCATIONS)}")
    print(f"  Movements: {len(MOVEMENTS)}")
    print(f"  Non-Manual: {len(NON_MANUAL)}")
    print(f"  Symmetry: {len(SYMMETRY)}")
    total = sum(len(d) for d in [HANDSHAPES, PALM_ORIENTATIONS, FINGER_DIRECTIONS,
                                  LOCATIONS, MOVEMENTS, NON_MANUAL, SYMMETRY])
    print(f"  Total: {total} symbols")
