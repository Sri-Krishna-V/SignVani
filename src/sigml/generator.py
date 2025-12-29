"""
SiGML Generator

Converts HamNoSys strings into SiGML (Signing Gesture Markup Language) XML.
This XML is consumed by the Avatar rendering engine.
"""

import logging
import time
import xml.etree.ElementTree as ET
from typing import List, Dict

from src.nlp.dataclasses import GlossPhrase, SiGMLOutput
from src.database.retriever import GlossRetriever

logger = logging.getLogger(__name__)


class SiGMLGenerator:
    """
    Generates SiGML XML from ISL GlossPhrases.
    """

    def __init__(self):
        """Initialize generator with database retriever."""
        self.retriever = GlossRetriever()

    def generate(self, gloss_phrase: GlossPhrase) -> SiGMLOutput:
        """
        Convert a GlossPhrase into a complete SiGML XML document.

        Structure:
        <sigml>
            <hns_sign gloss="HELLO">
                <hamnosys_nonmanual>...</hamnosys_nonmanual>
                <hamnosys_manual>...</hamnosys_manual>
            </hns_sign>
            ...
        </sigml>

        Args:
            gloss_phrase: The processed gloss phrase from NLP engine.

        Returns:
            SiGMLOutput object containing the XML string.
        """
        start_time = time.time()
        
        # Create root element
        root = ET.Element('sigml')

        valid_glosses = []

        for gloss in gloss_phrase.glosses:
            # Retrieve HamNoSys for the gloss
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
            else:
                logger.warning(f"No HamNoSys found for gloss '{gloss}' during SiGML generation.")

        # Convert to string
        # encoding='unicode' returns a string, not bytes
        xml_str = ET.tostring(root, encoding='unicode', method='xml')

        gen_time = (time.time() - start_time) * 1000
        logger.debug(f"SiGML generation took {gen_time:.2f}ms for {len(valid_glosses)} signs")

        return SiGMLOutput(
            sigml_xml=xml_str,
            glosses=valid_glosses,
            original_text=gloss_phrase.original_text
        )
