#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
EMVCo QR Code Parser for Thai Bank Slips.
Decodes Tag-Length-Value (TLV) format used in Thai QR Payment (PromptPay / Bank Transfer)
to verify slip details (transaction amount, bank transaction ID, biller IDs, etc.)
"""

import re
import logging

logger = logging.getLogger(__name__)

class EMVCoParser:
    @staticmethod
    def parse_tlv(payload: str) -> dict:
        """
        Parses an EMVCo string into a dictionary of {tag: value}.
        Each tag has a 2-character ID, followed by a 2-character length, followed by 'length' characters of value.
        """
        parsed = {}
        if not payload or not isinstance(payload, str):
            return parsed
            
        # Clean whitespaces or formatting if any
        payload = re.sub(r'\s+', '', payload)
        
        index = 0
        length_str_len = 2
        tag_str_len = 2
        
        while index < len(payload):
            if index + tag_str_len + length_str_len > len(payload):
                break
                
            tag = payload[index:index+tag_str_len]
            length_str = payload[index+tag_str_len:index+tag_str_len+length_str_len]
            
            try:
                length = int(length_str)
            except ValueError:
                logger.warning(f"Invalid length string '{length_str}' at index {index+tag_str_len}")
                break
                
            value_start = index + tag_str_len + length_str_len
            value_end = value_start + length
            
            if value_end > len(payload):
                logger.warning(f"Length {length} exceeds payload boundaries for tag '{tag}'")
                break
                
            value = payload[value_start:value_end]
            parsed[tag] = value
            index = value_end
            
        return parsed

    @classmethod
    def parse_sub_tlv(cls, tag_value: str) -> dict:
        """
        Parses a tag value that is known to contain nested TLV fields.
        """
        return cls.parse_tlv(tag_value)

    @classmethod
    def decode_slip_qr(cls, qr_string: str) -> dict:
        """
        Decodes a Thai QR bank slip string.
        Returns a dictionary with normalized information for slip verification.
        
        Standard tags:
          - Tag '00': Payload Format Indicator
          - Tag '30': Domestic Merchant Account Information (Thai QR standard)
             - Sub-tag '00': AID (PromptPay / Bank Specific)
             - Sub-tag '01': Sending / Receiving bank ID or Transfer detail
             - Sub-tag '02': Transaction Reference ID / API Reference
          - Tag '54': Net Amount (String representation of a float)
          - Tag '53': Currency code (764 for THB)
          - Tag '58': Country code (TH)
          - Tag '62': Additional Data Field Template (Optional)
             - Sub-tag '01': Bill Number / Ref 1
             - Sub-tag '02': Mobile Number / Ref 2
             - Sub-tag '05': Transaction ID / Ref 3
        """
        result = {
            "is_valid_emvco": False,
            "amount": None,
            "transaction_id": None,
            "sending_bank_id": None,
            "biller_id": None,
            "ref1": None,
            "ref2": None,
            "raw_tags": {}
        }
        
        if not qr_string or not isinstance(qr_string, str):
            return result
            
        qr_string = qr_string.strip()
        
        # EMVCo payloads must start with '00' tag
        if not qr_string.startswith("00"):
            # Check if there is EMVCo payload hidden inside (e.g. from OCR garbage)
            match = re.search(r'000201[0-9]{4,}', qr_string)
            if match:
                qr_string = qr_string[match.start():]
            else:
                return result
                
        try:
            raw_tags = cls.parse_tlv(qr_string)
            result["raw_tags"] = raw_tags
            
            if "00" in raw_tags:
                result["is_valid_emvco"] = True
                
            # Extract Net Amount (Tag 54)
            if "54" in raw_tags:
                try:
                    result["amount"] = float(raw_tags["54"])
                except ValueError:
                    logger.warning(f"Could not parse Tag 54 amount: {raw_tags['54']}")
                    
            # Extract Merchant Account Info (Tag 30) - commonly holds Thai slip details
            if "30" in raw_tags:
                sub_tags = cls.parse_sub_tlv(raw_tags["30"])
                # Sub-tag 01: Biller/Bank identification
                if "01" in sub_tags:
                    result["sending_bank_id"] = sub_tags["01"]
                # Sub-tag 02: Transaction Reference ID (The unique bank reference printed on slip)
                if "02" in sub_tags:
                    result["transaction_id"] = sub_tags["02"]
                    
            # Check Tag 29 as fallback for promptpay/domestic transfer
            if not result["transaction_id"] and "29" in raw_tags:
                sub_tags = cls.parse_sub_tlv(raw_tags["29"])
                if "02" in sub_tags:
                    result["transaction_id"] = sub_tags["02"]
                    
            # Extract Additional Data Field (Tag 62)
            if "62" in raw_tags:
                sub_tags = cls.parse_sub_tlv(raw_tags["62"])
                if "01" in sub_tags:
                    result["ref1"] = sub_tags["01"]
                if "02" in sub_tags:
                    result["ref2"] = sub_tags["02"]
                if "05" in sub_tags:
                    # In some banks, the Transaction ID is embedded in Ref 3 (sub-tag 05)
                    if not result["transaction_id"]:
                        result["transaction_id"] = sub_tags["05"]
                        
        except Exception as e:
            logger.error(f"Error parsing EMVCo payload: {e}", exc_info=True)
            
        return result

# Simple self test
if __name__ == "__main__":
    # Standard PromptPay QR with amount 150.00 THB
    sample_qr = "00020101021130830016A00000067701011101130002010214202605291234565406150.0053037645802TH6304D1C4"
    parser = EMVCoParser()
    res = parser.decode_slip_qr(sample_qr)
    print("Test decoding standard Thai QR slip code:")
    print(f"Is Valid EMVCo: {res['is_valid_emvco']}")
    print(f"Amount: {res['amount']}")
    print(f"Transaction ID: {res['transaction_id']}")
    print(f"Bank/Biller ID: {res['sending_bank_id']}")
