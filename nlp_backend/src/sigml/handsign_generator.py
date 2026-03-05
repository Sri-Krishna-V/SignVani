"""
SiGML to HandSign Converter

Converts HamNoSys codes from NLP pipeline into frontend-compatible hand sign animations.
This bridges the gap between the NLP pipeline output and the 3D avatar animation system.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.nlp.dataclasses import GlossPhrase, SiGMLOutput

logger = logging.getLogger(__name__)


@dataclass
class HandSignAnimation:
    """Represents a hand sign animation for the frontend."""
    gloss: str
    hamnosys: str
    keyframes: List[Dict[str, Any]]
    duration: float = 1000.0  # Default 1 second per sign


@dataclass
class HandSignSequence:
    """Complete sequence of hand sign animations with pauses."""
    animations: List[HandSignAnimation]
    original_text: str
    total_duration: float
    has_pauses: bool = True


class HamNoSysToKeyframeConverter:
    """
    Converts HamNoSys notation to frontend keyframe animations.
    
    Maps HamNoSys symbols to Three.js bone transformations compatible with the avatar model.
    """
    
    def __init__(self):
        """Initialize converter with HamNoSys to bone mapping."""
        self.hamnosys_mappings = self._load_hamnosys_mappings()
        self.bone_mappings = self._load_bone_mappings()
        
    def _load_hamnosys_mappings(self) -> Dict[str, Dict[str, Any]]:
        """
        Load HamNoSys symbol to animation parameter mappings.
        
        Returns:
            Dictionary mapping HamNoSys symbols to animation parameters
        """
        return {
            # Hand Shape Symbols
            "hamflathand": {
                "type": "hand_shape",
                "bones": {
                    "mixamorigLeftHandIndex1": {"rotation": {"z": 0}},
                    "mixamorigLeftHandIndex2": {"rotation": {"z": 0}},
                    "mixamorigLeftHandIndex3": {"rotation": {"z": 0}},
                    "mixamorigLeftHandMiddle1": {"rotation": {"z": 0}},
                    "mixamorigLeftHandMiddle2": {"rotation": {"z": 0}},
                    "mixamorigLeftHandMiddle3": {"rotation": {"z": 0}},
                    "mixamorigLeftHandRing1": {"rotation": {"z": 0}},
                    "mixamorigLeftHandRing2": {"rotation": {"z": 0}},
                    "mixamorigLeftHandRing3": {"rotation": {"z": 0}},
                    "mixamorigLeftHandPinky1": {"rotation": {"z": 0}},
                    "mixamorigLeftHandPinky2": {"rotation": {"z": 0}},
                    "mixamorigLeftHandPinky3": {"rotation": {"z": 0}},
                    "mixamorigLeftHandThumb1": {"rotation": {"y": 0}},
                }
            },
            "hamfist": {
                "type": "hand_shape",
                "bones": {
                    "mixamorigLeftHandIndex1": {"rotation": {"z": -3.14159/2}},
                    "mixamorigLeftHandIndex2": {"rotation": {"z": -3.14159/2}},
                    "mixamorigLeftHandIndex3": {"rotation": {"z": -3.14159/2}},
                    "mixamorigLeftHandMiddle1": {"rotation": {"z": -3.14159/2}},
                    "mixamorigLeftHandMiddle2": {"rotation": {"z": -3.14159/2}},
                    "mixamorigLeftHandMiddle3": {"rotation": {"z": -3.14159/2}},
                    "mixamorigLeftHandRing1": {"rotation": {"z": -3.14159/2}},
                    "mixamorigLeftHandRing2": {"rotation": {"z": -3.14159/2}},
                    "mixamorigLeftHandRing3": {"rotation": {"z": -3.14159/2}},
                    "mixamorigLeftHandPinky1": {"rotation": {"z": -3.14159/2}},
                    "mixamorigLeftHandPinky2": {"rotation": {"z": -3.14159/2}},
                    "mixamorigLeftHandPinky3": {"rotation": {"z": -3.14159/2}},
                    "mixamorigLeftHandThumb1": {"rotation": {"y": -3.14159/4}},
                }
            },
            "hamthumboutmod": {
                "type": "hand_modifier",
                "bones": {
                    "mixamorigLeftHandThumb1": {"rotation": {"x": 3.14159/4}},
                    "mixamorigLeftHandThumb2": {"rotation": {"x": 3.14159/4}},
                    "mixamorigLeftHandThumb3": {"rotation": {"x": 3.14159/4}},
                }
            },
            
            # Palm Orientation
            "hampalmu": {"type": "palm_orientation", "rotation": {"x": 0, "y": 0, "z": 0}},
            "hampalmout": {"type": "palm_orientation", "rotation": {"x": 3.14159, "y": 0, "z": 0}},
            "hampalmd": {"type": "palm_orientation", "rotation": {"x": 3.14159/2, "y": 0, "z": 0}},
            "hampalml": {"type": "palm_orientation", "rotation": {"x": -3.14159/2, "y": 0, "z": 0}},
            
            # Location/Space
            "hamneutralspace": {"type": "location", "position": {"x": 0, "y": 1.2, "z": 0.3}},
            "hamchin": {"type": "location", "position": {"x": 0, "y": 1.4, "z": 0.2}},
            "hamforehead": {"type": "location", "position": {"x": 0, "y": 1.6, "z": 0.1}},
            "hamchest": {"type": "location", "position": {"x": 0, "y": 1.0, "z": 0.3}},
            
            # Movement
            "hammoveu": {"type": "movement", "direction": "up", "distance": 0.2},
            "hammoved": {"type": "movement", "direction": "down", "distance": 0.2},
            "hammovel": {"type": "movement", "direction": "left", "distance": 0.2},
            "hammover": {"type": "movement", "direction": "right", "distance": 0.2},
            "hammoveo": {"type": "movement", "direction": "out", "distance": 0.2},
            "hammovei": {"type": "movement", "direction": "in", "distance": 0.2},
            
            # Finger Extensions
            "hamfinger2": {"type": "finger", "finger": "index", "state": "extended"},
            "hamfinger3": {"type": "finger", "finger": "middle", "state": "extended"},
            "hamfinger4": {"type": "finger", "finger": "ring", "state": "extended"},
            "hamfinger5": {"type": "finger", "finger": "pinky", "state": "extended"},
            "hamextfingero": {"type": "finger", "finger": "index", "state": "extended_out"},
            
            # Circular/Complex Movements
            "hamcircle": {"type": "movement", "direction": "circular", "radius": 0.1},
            "hamarci": {"type": "movement", "direction": "arc", "radius": 0.15},
            
            # Arm Position
            "hamlowerarm": {"type": "arm_position", "rotation": {"x": 3.14159/6}},
        }
    
    def _load_bone_mappings(self) -> Dict[str, str]:
        """
        Load Three.js bone name mappings.
        
        Returns:
            Dictionary mapping generic bone names to Three.js specific names
        """
        return {
            "thumb": "mixamorigLeftHandThumb",
            "index": "mixamorigLeftHandIndex", 
            "middle": "mixamorigLeftHandMiddle",
            "ring": "mixamorigLeftHandRing",
            "pinky": "mixamorigLeftHandPinky",
            "forearm": "mixamorigLeftForeArm",
            "arm": "mixamorigLeftArm",
        }
    
    def parse_hamnosys(self, hamnosys_string: str) -> List[Dict[str, Any]]:
        """
        Parse HamNoSys string into individual symbols.
        
        Args:
            hamnosys_string: Comma-separated HamNoSys symbols
            
        Returns:
            List of parsed HamNoSys symbols with their parameters
        """
        if not hamnosys_string:
            return []
            
        symbols = []
        for symbol in hamnosys_string.split(','):
            symbol = symbol.strip()
            if symbol in self.hamnosys_mappings:
                symbols.append(self.hamnosys_mappings[symbol])
            else:
                logger.warning(f"Unknown HamNoSys symbol: {symbol}")
                
        return symbols
    
    def convert_to_keyframes(self, hamnosys_string: str, gloss: str) -> List[Dict[str, Any]]:
        """
        Convert HamNoSys string to frontend keyframe animations.
        
        Args:
            hamnosys_string: HamNoSys notation string
            gloss: The gloss name for this sign
            
        Returns:
            List of keyframe animations compatible with frontend
        """
        symbols = self.parse_hamnosys(hamnosys_string)
        keyframes = []
        
        # Initial keyframe (neutral position)
        initial_keyframe = {
            "time": 0,
            "transformations": self._get_neutral_transformations()
        }
        keyframes.append(initial_keyframe)
        
        # Process each HamNoSys symbol
        current_transformations = {}
        cumulative_time = 200  # Start after 200ms
        
        for symbol in symbols:
            symbol_transformations = self._symbol_to_transformations(symbol)
            current_transformations.update(symbol_transformations)
            
            keyframe = {
                "time": cumulative_time,
                "transformations": list(current_transformations.items())
            }
            keyframes.append(keyframe)
            
            # Add time for this symbol's animation
            cumulative_time += 300  # 300ms per symbol
        
        # Final keyframe (return to neutral)
        final_keyframe = {
            "time": cumulative_time + 200,
            "transformations": self._get_neutral_transformations()
        }
        keyframes.append(final_keyframe)
        
        return keyframes
    
    def _get_neutral_transformations(self) -> List[List[str]]:
        """
        Get neutral/rest position transformations.
        
        Returns:
            List of neutral bone transformations
        """
        return [
            ["mixamorigLeftHandIndex1", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandIndex2", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandIndex3", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandMiddle1", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandMiddle2", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandMiddle3", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandRing1", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandRing2", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandRing3", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandPinky1", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandPinky2", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandPinky3", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandThumb1", "rotation", "y", "0", "+"],
            ["mixamorigLeftForeArm", "rotation", "x", "0", "+"],
            ["mixamorigLeftArm", "rotation", "x", "0", "+"],
        ]
    
    def _symbol_to_transformations(self, symbol: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Convert a HamNoSys symbol to bone transformations.
        
        Args:
            symbol: HamNoSys symbol definition
            
        Returns:
            Dictionary of bone transformations
        """
        transformations = {}
        symbol_type = symbol.get("type", "")
        
        if symbol_type == "hand_shape":
            for bone, params in symbol.get("bones", {}).items():
                if "rotation" in params:
                    for axis, value in params["rotation"].items():
                        transformations[bone] = [bone, "rotation", axis, str(value), "+"]
                        
        elif symbol_type == "palm_orientation":
            # Apply palm orientation to forearm
            bone = "mixamorigLeftForeArm"
            for axis, value in symbol.get("rotation", {}).items():
                transformations[bone] = [bone, "rotation", axis, str(value), "+"]
                
        elif symbol_type == "location":
            # Apply location to arm position
            bone = "mixamorigLeftArm"
            position = symbol.get("position", {})
            for axis, value in position.items():
                transformations[bone] = [bone, "position", axis, str(value), "+"]
                
        elif symbol_type == "movement":
            # Apply movement as animation
            bone = "mixamorigLeftForeArm"
            direction = symbol.get("direction", "")
            distance = symbol.get("distance", 0.1)
            
            if direction == "up":
                transformations[bone] = [bone, "position", "y", str(distance), "+"]
            elif direction == "down":
                transformations[bone] = [bone, "position", "y", str(-distance), "+"]
            elif direction == "left":
                transformations[bone] = [bone, "position", "x", str(-distance), "+"]
            elif direction == "right":
                transformations[bone] = [bone, "position", "x", str(distance), "+"]
            elif direction == "out":
                transformations[bone] = [bone, "position", "z", str(distance), "+"]
            elif direction == "in":
                transformations[bone] = [bone, "position", "z", str(-distance), "+"]
                
        elif symbol_type == "finger":
            finger = symbol.get("finger", "")
            state = symbol.get("state", "")
            bone_map = {
                "index": "mixamorigLeftHandIndex1",
                "middle": "mixamorigLeftHandMiddle1", 
                "ring": "mixamorigLeftHandRing1",
                "pinky": "mixamorigLeftHandPinky1"
            }
            
            if finger in bone_map:
                bone = bone_map[finger]
                if state == "extended":
                    transformations[bone] = [bone, "rotation", "z", "0", "+"]
                elif state == "extended_out":
                    transformations[bone] = [bone, "rotation", "z", str(3.14159/4), "+"]
        
        return transformations


class HandSignGenerator:
    """
    Main generator that converts NLP pipeline output to hand sign animations.
    """
    
    def __init__(self):
        """Initialize generator with HamNoSys converter."""
        self.converter = HamNoSysToKeyframeConverter()
        
    def generate_from_gloss_phrase(self, gloss_phrase: GlossPhrase) -> HandSignSequence:
        """
        Convert NLP pipeline GlossPhrase to hand sign animations.
        
        Args:
            gloss_phrase: Output from NLP pipeline with glosses
            
        Returns:
            Complete hand sign animation sequence
        """
        animations = []
        total_duration = 0
        
        for i, gloss in enumerate(gloss_phrase.glosses):
            # Get HamNoSys for this gloss (simulated - would come from database)
            hamnosys = self._get_hamnosys_for_gloss(gloss)
            
            if hamnosys:
                # Convert HamNoSys to keyframes
                keyframes = self.converter.convert_to_keyframes(hamnosys, gloss)
                
                # Create animation
                animation = HandSignAnimation(
                    gloss=gloss,
                    hamnosys=hamnosys,
                    keyframes=keyframes,
                    duration=max(kf["time"] for kf in keyframes) if keyframes else 1000
                )
                
                animations.append(animation)
                total_duration += animation.duration
                
                # Add pause between signs
                if i < len(gloss_phrase.glosses) - 1:
                    pause_animation = self._create_pause_animation()
                    animations.append(pause_animation)
                    total_duration += pause_animation.duration
        
        return HandSignSequence(
            animations=animations,
            original_text=gloss_phrase.original_text,
            total_duration=total_duration,
            has_pauses=True
        )
    
    def generate_from_sigml_output(self, sigml_output: SiGMLOutput) -> HandSignSequence:
        """
        Convert SiGMLOutput to hand sign animations.
        
        Args:
            sigml_output: Output from SiGML generator
            
        Returns:
            Complete hand sign animation sequence
        """
        # Parse SiGML XML to extract glosses and HamNoSys
        glosses = self._parse_sigml_xml(sigml_output.sigml_xml)
        
        # Create temporary GlossPhrase
        gloss_phrase = GlossPhrase(
            glosses=glosses,
            original_text=sigml_output.original_text
        )
        
        return self.generate_from_gloss_phrase(gloss_phrase)
    
    def _get_hamnosys_for_gloss(self, gloss: str) -> Optional[str]:
        """
        Get HamNoSys notation for a gloss.
        
        Args:
            gloss: Gloss name
            
        Returns:
            HamNoSys string or None if not found
        """
        # This would typically query the database
        # For now, return some example mappings
        hamnosys_mappings = {
            "HELLO": "hamflathand,hampalmu,hamchin,hammoveo,hammoved",
            "THANK": "hamflathand,hampalmu,hamchin,hammoveo,hammoved",
            "YOU": "hamfinger2,hamextfingero,hampalmout,hamneutralspace",
            "QUESTION": "hamfinger2,hamextfingero,hampalmout,hamneutralspace,hamarci",
            "HOW": "hamfist,hamthumboutmod,hampalmu,hamneutralspace,hamcircle",
            "MORNING": "hamflathand,hampalmu,hamlowerarm,hammoveu",
            "GOOD": "hamflathand,hampalmu,hamchin,hammoveo",
        }
        
        return hamnosys_mappings.get(gloss.upper())
    
    def _parse_sigml_xml(self, sigml_xml: str) -> List[str]:
        """
        Parse SiGML XML to extract glosses.
        
        Args:
            sigml_xml: SiGML XML string
            
        Returns:
            List of gloss names
        """
        import xml.etree.ElementTree as ET
        
        try:
            root = ET.fromstring(sigml_xml)
            glosses = []
            
            for sign_elem in root.findall('hns_sign'):
                gloss = sign_elem.get('gloss')
                if gloss:
                    glosses.append(gloss)
                    
            return glosses
            
        except ET.ParseError as e:
            logger.error(f"Error parsing SiGML XML: {e}")
            return []
    
    def _create_pause_animation(self) -> HandSignAnimation:
        """
        Create a pause animation (hands return to neutral).
        
        Returns:
            Pause animation with neutral keyframes
        """
        neutral_keyframes = [{
            "time": 0,
            "transformations": self.converter._get_neutral_transformations()
        }]
        
        return HandSignAnimation(
            gloss="PAUSE",
            hamnosys="",
            keyframes=neutral_keyframes,
            duration=500  # 500ms pause
        )
    
    def to_frontend_format(self, sequence: HandSignSequence) -> Dict[str, Any]:
        """
        Convert hand sign sequence to frontend-compatible format.
        
        Args:
            sequence: Hand sign sequence
            
        Returns:
            Dictionary in frontend animation format
        """
        frontend_data = {
            "original_text": sequence.original_text,
            "total_duration": sequence.total_duration,
            "animations": []
        }
        
        for animation in sequence.animations:
            animation_data = {
                "gloss": animation.gloss,
                "hamnosys": animation.hamnosys,
                "duration": animation.duration,
                "keyframes": animation.keyframes
            }
            frontend_data["animations"].append(animation_data)
        
        return frontend_data
