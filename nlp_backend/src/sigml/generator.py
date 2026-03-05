"""
SiGML Generator

Converts HamNoSys strings into SiGML (Signing Gesture Markup Language) XML
and frontend-compatible hand sign animations.
This XML and animation data is consumed by the Avatar rendering engine.
"""

import logging
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional

from src.nlp.dataclasses import GlossPhrase, SiGMLOutput
from src.database.retriever import GlossRetriever
from .handsign_generator import HandSignGenerator

logger = logging.getLogger(__name__)


class SiGMLGenerator:
    """
    Generates SiGML XML from ISL GlossPhrases.
    """

    def __init__(self):
        """Initialize generator with database retriever and hand sign generator."""
        self.retriever = GlossRetriever()
        self.handsign_generator = HandSignGenerator()

    def _should_add_pause(self, current_gloss: str, next_gloss: str = None) -> bool:
        """
        Determine if a pause and hand restore should be added after current gloss.
        
        Args:
            current_gloss: Current gloss being processed
            next_gloss: Next gloss in sequence (None if last)
            
        Returns:
            True if pause should be added, False otherwise
        """
        # Add pause at the end of sentence (last gloss)
        if next_gloss is None:
            return True
            
        # Add pause before certain punctuation-like glosses
        pause_indicators = ['PERIOD', 'COMMA', 'QUESTION', 'EXCLAMATION']
        if next_gloss in pause_indicators:
            return True
            
        # Add pause for common sentence-ending patterns
        if current_gloss in ['THANK', 'GOODBYE', 'PLEASE', 'SORRY']:
            return True
            
        # Default: add pause between most signs for natural flow
        return True

    def generate(self, gloss_phrase: GlossPhrase) -> SiGMLOutput:
        """
        Convert a GlossPhrase into a complete SiGML XML document.

        Structure:
        <sigml>
            <hns_sign gloss="HELLO">
                <hamnosys_nonmanual>...</hamnosys_nonmanual>
                <hamnosys_manual>...</hamnosys_manual>
            </hns_sign>
            <!-- Pause and neutral position for punctuation -->
            <pause duration="500"/>
            <restore_hands/>
            ...
        </sigml>

        Args:
            gloss_phrase: The processed gloss phrase from NLP engine.

        Returns:
            SiGMLOutput object containing: XML string.
        """
        start_time = time.time()

        # Create root element
        root = ET.Element('sigml')

        valid_glosses = []

        for i, gloss in enumerate(gloss_phrase.glosses):
            # Retrieve HamNoSys for gloss
            hamnosys = self.retriever.get_hamnosys(gloss)

            if hamnosys:
                # Create sign element
                sign_elem = ET.SubElement(root, 'hns_sign')
                sign_elem.set('gloss', gloss)

                # Add manual component (the hand signs)
                manual_elem = ET.SubElement(sign_elem, 'hamnosys_manual')
                manual_elem.text = hamnosys

                # Non-manual component (facial expressions) - placeholder for now
                # nonmanual_elem = ET.SubElement(sign_elem, 'hamnosys_nonmanual')

                valid_glosses.append(gloss)
                
                # Check if this is the last gloss or if there's punctuation
                next_gloss = gloss_phrase.glosses[i + 1] if i + 1 < len(gloss_phrase.glosses) else None
                
                # Add pause and neutral position for end of sentence or before next sign
                if self._should_add_pause(gloss, next_gloss):
                    # Add pause element
                    pause_elem = ET.SubElement(root, 'pause')
                    pause_elem.set('duration', '500')  # 500ms pause
                    
                    # Add hands restore element
                    restore_elem = ET.SubElement(root, 'restore_hands')
                    
            else:
                logger.warning(
                    f"No HamNoSys found for gloss '{gloss}' during SiGML generation.")

        # Convert to string
        # encoding='unicode' returns a string, not bytes
        xml_str = ET.tostring(root, encoding='unicode', method='xml')

        gen_time = (time.time() - start_time) * 1000
        logger.debug(
            f"SiGML generation took {gen_time:.2f}ms for {len(valid_glosses)} signs")

        return SiGMLOutput(
            sigml_xml=xml_str,
            glosses=valid_glosses,
            original_text=gloss_phrase.original_text
        )

    def generate_handsign_animations(self, gloss_phrase: GlossPhrase) -> Dict[str, any]:
        """
        Generate frontend-compatible hand sign animations directly from NLP pipeline output.
        
        This method bypasses SiGML XML generation and creates animations that can be
        directly consumed by the frontend 3D avatar system.
        
        Args:
            gloss_phrase: The processed gloss phrase from NLP engine.
            
        Returns:
            Dictionary containing hand sign animations in frontend format.
        """
        start_time = time.time()
        
        # Generate hand sign sequence from NLP pipeline output
        handsign_sequence = self.handsign_generator.generate_from_gloss_phrase(gloss_phrase)
        
        # Convert to frontend-compatible format
        frontend_animations = self.handsign_generator.to_frontend_format(handsign_sequence)
        
        gen_time = (time.time() - start_time) * 1000
        logger.debug(
            f"Hand sign animation generation took {gen_time:.2f}ms for {len(handsign_sequence.animations)} animations")
        
        return frontend_animations
